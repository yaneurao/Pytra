# P0: pytra-cli C++ max最適化で linked-program build を使う

最終更新: 2026-03-08

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-PYTRACLI-CPP-MAXOPT-LINKED-01`

背景:
- 現在の `pytra-cli --target cpp --build` は、`src/py2x.py` の C++ compat route をそのまま通しており、linked-program optimizer を経由しない。
- そのため、`EAST3` の global 最適化で変わる `rc<>` / list / call graph / non-escape の効果が、`pytra-cli` の通常 build 導線では実行ファイルへ反映されない。
- 一方で、ユーザーが期待する「最大最適化」は、単なる C++ compiler の `-O3` ではなく、frontend / linker / backend を含む Pytra 側最適化の最大段まで含むべきである。
- 2026-03-08 時点の手動検証では、`sample/py -> dump-east3-dir -> eastlink -> linked module -> C++ emit` を通すと `sample/cpp` に差分が出ることを確認済みであり、global 最適化がコード生成へ実際に効いている。

目的:
- `pytra-cli --target cpp --build --codegen-opt 3` を、linked-program optimizer を含む C++ max codegen route にする。
- 同時に、`pytra-cli --target cpp --codegen-opt 3` の transpile-only でも、linked-program 最適化を反映した C++ 出力を得られるようにする。
- この route を sample parity で確認し、「max 最適化で build しても sample が壊れない」ことを固定する。

対象:
- `src/pytra-cli.py`
- 必要なら `src/py2x.py`, `src/eastlink.py`, `src/ir2lang.py`
- C++ build/transpile 導線のテスト
- sample parity 確認コマンドと docs

非対象:
- 全 target へ同じ max-opt semantics を広げること
- `sample/cpp` single-file 生成の正規 route をこの P0 で全面整理すること
- `runtime/cpp` 自体の意味論変更
- linked-program IR schema の再設計

受け入れ基準:
- `pytra-cli --target cpp --build --codegen-opt 3` が linked-program optimizer を経由して実行ファイルを生成する。
- `pytra-cli --target cpp --codegen-opt 3` の transpile-only でも、global 最適化結果を反映した C++ を出力する。
- `--codegen-opt 0/1/2` の既存意味論を壊さないか、壊すなら docs/CLI 契約で明示する。
- representative CLI test が、`--codegen-opt 3` で linked-program route を踏むことを固定する。
- C++ sample parity が green を維持する。
- 必要なら `sample/cpp` 再生成の手順も docs/plan に記録する。

基本方針:
1. まず `pytra-cli` の `codegen-opt` と `py2x` / `eastlink` / `ir2lang` / `py2cpp` の各最適化フラグの対応を固定する。
2. `codegen-opt=3` を「legacy compat route ではなく linked-program route を使う」スイッチとして扱う。
3. build と transpile-only の両方で同じ linked-program optimized module 群を source of truth にする。
4. 変更後は sample parity と representative CLI regression で非退行を確認する。

## 現状棚卸し（2026-03-08）

| layer / entry | 現在の入力 | 現在の最適化段 | 備考 |
| --- | --- | --- | --- |
| `pytra-cli --codegen-opt N` | `--codegen-opt {0,1,2,3}` | `py2x.py` へ aggregate `-ON` をそのまま passthrough | `--opt -O3` とは別物。`--opt` は C++ compiler flag |
| `py2x.py --target cpp` | `.py` | 通常は `backends.cpp.cli` compat route | linked-program route は `--dump-east3-dir` / `--link-only` / `--from-link-output` 指定時だけ |
| `backends.cpp.cli` compat route | raw `.py` | `east3_opt_level` + `cpp_opt_level` を内部解決 | aggregate `-O3` は通るが、linked-program global optimizer は通らない |
| `eastlink.py` | `link-input.json` | linked-program optimizer | `type_id` / `non_escape_summary` / `container_ownership_hints_v1` を確定する canonical global phase |
| `ir2lang.py` | raw `EAST3` or `link-output.json` | backend-only emit | linked module 群から restart できる |

現状のズレ:
- `pytra-cli --target cpp --build --codegen-opt 3` は、ユーザー期待としては「最大 Pytra 最適化」に見えるが、実際には `py2x.py` の C++ compat route に `-O3` を渡しているだけで、linked-program global optimization は通っていない。
- linked-program optimizer を使う正規導線は `py2x.py --dump-east3-dir` / `eastlink.py` / `ir2lang.py` だが、これは debug / restart 導線としてしか exposed されていない。

本 P0 で固定する semantics:
- `pytra-cli --target cpp --codegen-opt 0/1/2`
  - 従来どおりの compat route を使う。
- `pytra-cli --target cpp --codegen-opt 3`
  - 「max Pytra codegen route」として扱い、linked-program optimizer を必ず経由する。
- `pytra-cli --target cpp --build --opt -O3`
  - これは引き続き C++ compiler optimization だけを意味する。
- C++ max-opt route の non-regression は representative CLI test に加えて `sample` parity を acceptance gate とする。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_pytra_cli.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_py2x_cli.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/link -p 'test_*.py'`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples`
- 必要なら `python3 tools/verify_sample_outputs.py --samples ... --compile-flags=\"-O2\"`

## 分解

- [ ] [ID: P0-PYTRACLI-CPP-MAXOPT-LINKED-01-S1-01] `pytra-cli` の `--codegen-opt` と `py2x/eastlink/ir2lang/py2cpp` の最適化段対応表を棚卸しし、`codegen-opt=3` の目標 semantics を固定する。
- [ ] [ID: P0-PYTRACLI-CPP-MAXOPT-LINKED-01-S1-02] `pytra-cli` max-opt C++ route の CLI 契約と sample parity gate を spec/plan に固定する。
- [x] [ID: P0-PYTRACLI-CPP-MAXOPT-LINKED-01-S2-01] `pytra-cli --target cpp --build --codegen-opt 3` が linked-program optimizer を経由する build route を実装する。
- [x] [ID: P0-PYTRACLI-CPP-MAXOPT-LINKED-01-S2-02] `pytra-cli --target cpp --codegen-opt 3` の transpile-only route も linked-program optimizer を使うよう揃える。
- [x] [ID: P0-PYTRACLI-CPP-MAXOPT-LINKED-01-S3-01] representative CLI regression を追加し、`codegen-opt=3` の route 選択と manifest/build/run を固定する。
- [ ] [ID: P0-PYTRACLI-CPP-MAXOPT-LINKED-01-S3-02] sample parity を回し、max-opt route でも C++ sample が green であることを確認する。
- [ ] [ID: P0-PYTRACLI-CPP-MAXOPT-LINKED-01-S4-01] `pytra-cli` / how-to-use / 必要な docs に max-opt C++ route と sample parity 手順を反映する。
- [ ] [ID: P0-PYTRACLI-CPP-MAXOPT-LINKED-01-S4-02] 完了結果を記録し、計画を archive へ移して閉じる。

## フェーズ詳細

### Phase 1: 契約固定

やること:
- `codegen-opt` が現在どこへ伝播しているかを明文化する。
- `codegen-opt=3` を「max compiler opt」ではなく「max Pytra codegen route」として定義するかを決める。
- `sample parity` を acceptance gate に含める。

成果物:
- 対応表
- CLI 契約
- parity を含む受け入れ基準

### Phase 2: ルーティング実装

やること:
- `pytra-cli` の C++ route で、`codegen-opt=3` のとき linked-program optimizer を通す。
- build と transpile-only の両方で route を合わせる。
- compat route と linked route の分岐を最小限に保つ。

成果物:
- `pytra-cli` max-opt C++ build
- `pytra-cli` max-opt C++ transpile

### Phase 3: 検証

やること:
- representative CLI test を追加する。
- `sample` parity を回し、global 最適化が入っても output/runtime が壊れていないことを確認する。
- 必要なら `sample/cpp` 再生成の確認も行う。

成果物:
- test 固定
- parity green

### Phase 4: 運用固定

やること:
- docs と how-to-use を更新する。
- 完了ログを残す。

成果物:
- docs
- archive 済み plan

## 決定ログ

- 2026-03-08: ユーザー指示により、`pytra-cli` の C++ max 最適化で linked-program global optimization を自動で使う後続 P0 を起票する。
- 2026-03-08: 本計画には sample parity check を明示的に含める。理由は、route 変更だけ通して runtime parity を見ないと、`max-opt build はできるが sample が壊れる` 状態を見逃すためである。
- 2026-03-08: `sample/cpp` single-file 生成の最終的な正規化は本 P0 の主題ではない。まずは `pytra-cli` の build/transpile 導線に linked-program optimizer を載せることを優先する。
- 2026-03-08: 現行 `pytra-cli --target cpp --codegen-opt 3` は linked-program route ではなく compat route を通っている。したがって本 P0 では `codegen-opt=3` の意味を「max Pytra codegen route」へ明示的に変更する。
- 2026-03-08: `--codegen-opt 0/1/2` の既存意味論は維持し、route semantics を変えるのは C++ の `codegen-opt=3` のみに限定する。
- 2026-03-08: `S2-01` では `pytra-cli` から `py2x.py --link-only` と `py2x.py --from-link-output` を連続実行する。中間 bundle は `output_dir/.pytra_linked/` に置き、build の manifest 正本は最終 output root の `manifest.json` を使う。
- 2026-03-08: `codegen-opt=3` の build route では aggregate `-O3` を `py2x` に渡さず、stage 1 へ `--east3-opt-level 2`、stage 2 へ `--optimizer-option cpp_opt_level=2` を既定で補う。明示 override がある場合はユーザー指定を優先する。
- 2026-03-08: `S2-02` では transpile-only も同じ linked-program route に統一する。linked C++ route は multi-file emit 前提なので、`--target cpp --codegen-opt 3` では `--output` を禁止し、`--output-dir` を canonical output surface とする。
- 2026-03-08: `S3-01` の representative regression は `test_pytra_cli.py` に追加し、`codegen-opt=3` で `--link-only -> --from-link-output` の 2 段 route、manifest 解決、`--run` 時の `make run` fallback を固定した。
