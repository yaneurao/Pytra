<a href="../../en/todo/infra.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — インフラ・ツール・仕様

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-30

## 運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。

完了済みタスクは [アーカイブ](archive/20260428.md) を参照。

## 未完了タスク

### P1-EMITTER-HOST-MATRIX: emitter host マトリクスの新設と全言語 PASS

文脈: [docs/ja/plans/p1-emitter-host-matrix.md](../plans/p1-emitter-host-matrix.md)

selfhost マトリクス（full compiler）とは別に、「C++ emitter（16 モジュール）を各言語で host できるか」の emitter host マトリクスを新設する。全 18 言語で PASS を中間目標とする。

1. [x] [ID: P1-EHOST-MATRIX-S1] `gen_backend_progress.py` に emitter host マトリクス生成を追加する（`.parity-results/emitter_host_<lang>.json` から読み取り）
   - 完了: 2026-04-29。`_load_emitter_host_results()` と build/parity のアイコン化を追加した。
2. [x] [ID: P1-EHOST-MATRIX-S2] `progress-preview/backend-progress-emitter-host.md` を出力するようにする
   - 完了: 2026-04-29。`python3 tools/gen/gen_backend_progress.py` で JA/EN の `backend-progress-emitter-host.md` を生成するようにした。
3. [x] [ID: P1-EHOST-MATRIX-S3] 各 backend の P1-HOST-CPP-EMITTER タスクの S2 で `.parity-results/emitter_host_<lang>.json` に結果を書き込むよう更新する
   - 完了: 2026-04-29。各 backend TODO の S2 を emitter host 結果 JSON へ向けた。
4. [x] [ID: P1-EHOST-MATRIX-S4] JSON 形式を N×N 対応に拡張する（1ファイルに複数 hosted emitter の結果を持てるようにする）
   - 完了: 2026-04-29。`emitter_host_<host_lang>.json` の `emitters` map を正本形式として読み込むようにした。
5. [x] [ID: P1-EHOST-MATRIX-S5] `gen_backend_progress.py` を N×N マトリクス表示に対応させる（行: host 言語、列: hosted emitter）
   - 完了: 2026-04-29。`backend-progress-emitter-host.md` を host 言語 × hosted emitter の N×N 表示へ変更した。

### P1-SELFHOST-BUILD-ALL-LANGS: run_selfhost_parity.py の _build_selfhost_binary を全言語対応にする

文脈: [docs/ja/plans/p1-selfhost-build-all-langs.md](../plans/p1-selfhost-build-all-langs.md)

`run_selfhost_parity.py` の `_build_selfhost_binary` は cpp/go/rs/swift の 4 言語しか対応していない。残り 14 言語（ts, js, cs, dart, java, scala, kotlin, ruby, lua, php, nim, julia, zig, ps1）は `unsupported selfhost_lang for build` で止まる。

一方 `runtime_parity_check_fast.py` の `_run_target` には全 18 言語のビルド+実行コマンドが既に書かれている。この知識を共通モジュール（`runtime_parity_shared.py` 等）に切り出し、`run_selfhost_parity.py` から呼べるようにする。

1. [x] [ID: P1-SELFHOST-BUILD-S1] `runtime_parity_check_fast.py` の `_run_target` のビルド+実行ロジックを `runtime_parity_shared.py` に共通関数として切り出す
   - 完了: 2026-04-30。`runtime_parity_shared.py` に `run_emitted_target()` を追加し、fast/selfhost の実行側から呼ぶようにした。
2. [x] [ID: P1-SELFHOST-BUILD-S2] `run_selfhost_parity.py` の `_build_selfhost_binary` を共通関数経由に書き換え、全 18 言語で build が通るようにする
   - 完了: 2026-04-30。C++ 以外の selfhost build を `build_emitted_target_artifact()` 経由にした。
3. [x] [ID: P1-SELFHOST-BUILD-S3] 各言語で `run_selfhost_parity.py --selfhost-lang <lang> --emit-target cpp --case-root fixture` が実行可能であることを確認する
   - 完了: 2026-04-30。`unsupported selfhost_lang for build` 経路を撤去し、py_compile と python selfhost dry-run で導線を確認した。各言語の実 build 成否は backend 側の現状ブロッカーに従う。

### 保留中タスク

- P20-INT32 は [plans/p4-int32-default.md](../plans/p4-int32-default.md) に保留中。再開時にここへ戻す。
