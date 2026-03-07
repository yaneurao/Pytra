# P0: `@abi` mode を `value` / `value_mut` に整理する

最終更新: 2026-03-08

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-RUNTIME-ABI-MODE-SIMPLIFY-01`

背景:
- 現行の `@abi` は引数 mode として `default`, `value`, `value_readonly` を持つ。
- しかし運用上、mutable container 引数に対して欲しい通常ケースは「read-only value ABI」であり、`py_join` のような helper に毎回 `value_readonly` を書くのは冗長である。
- 実際、`py_join` の `parts` が read-only であることは call graph 解析を待たず関数本体の局所検査だけで分かる。
- 一方で、将来 writable な value ABI が必要な helper は残り得るため、単純に `readonly` 概念を消すのではなく、rare case を別 mode へ追い出す方が surface として自然である。

目的:
- `@abi` の public mode 名を `default`, `value`, `value_mut` に整理する。
- 引数側の `value` は「read-only value ABI」を意味する canonical mode にする。
- writable value ABI が必要なケースだけ `value_mut` を明示させる。
- parser / metadata / validator / docs / tests / representative runtime helper を新 naming に揃える。

対象:
- `docs/ja/spec/spec-abi.md`
- `docs/ja/spec/spec-east.md`
- `src/toolchain/ir/core.py`
- `src/toolchain/frontends/runtime_abi.py`
- `src/pytra/std/abi.py` 相当の surface と decorator metadata
- `src/pytra/built_in/string_ops.py` など既存 `@abi` 利用箇所
- `test/unit/ir`, `test/unit/tooling`, `test/unit/common`, `test/unit/backends/cpp` の関連回帰

非対象:
- `@abi` 自体を不要にする設計変更
- runtime helper を linked-program に統合して `@abi` 依存を縮める長期計画
- `value_mut` を必要とする新 helper の追加
- C++ runtime helper の意味論変更

受け入れ基準:
- public docs の canonical mode 名が `default`, `value`, `value_mut` に統一される。
- 引数側 `value` は read-only value ABI として定義される。
- `value_mut` は writable value ABI として定義される。
- `value_readonly` は少なくとも canonical surface から外れる。
- 既存 `@abi(args={"parts": "value_readonly"}, ret="value")` などは `value` へ移行される。
- validator / parser / diagnostics / metadata test が新 naming を基準に通る。
- representative C++ runtime helper / codegen 回帰が壊れない。

基本方針:
1. まず仕様上の意味を固定し、`value` を引数側 read-only value ABI へ再定義する。
2. parser / metadata は新 mode 名を source of truth とする。
3. `value_readonly` を完全廃止するか、移行期 alias として一時受理して canonical metadata では `value` へ正規化するかを明示する。
4. writable case は `value_mut` だけで表し、rare case を明示化する。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east_core.py' -k abi`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/link -p 'test_global_optimizer.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_pytra_built_in_string_ops.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_codegen_issues.py' -k abi`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_ir2lang_cli.py'`

## 分解

- [ ] [ID: P0-RUNTIME-ABI-MODE-SIMPLIFY-01-S1-01] 現行 `default/value/value_readonly` 契約を棚卸しし、`value=value_readonly`, `value_mut=旧 mutable value ABI` の移行方針を固定する。
- [ ] [ID: P0-RUNTIME-ABI-MODE-SIMPLIFY-01-S1-02] spec/plan に canonical naming と移行ルールを書き、`value_readonly` の扱いを決める。
- [ ] [ID: P0-RUNTIME-ABI-MODE-SIMPLIFY-01-S2-01] parser / decorator metadata / validator が `value` / `value_mut` を受理し、新 canonical metadata を出すよう更新する。
- [ ] [ID: P0-RUNTIME-ABI-MODE-SIMPLIFY-01-S2-02] diagnostics / error message / target support check を新 naming に合わせる。
- [ ] [ID: P0-RUNTIME-ABI-MODE-SIMPLIFY-01-S3-01] 既存 helper（`py_join`, `py_split`, `py_range` など）の注釈と generated/runtime 側期待を新 naming に移行する。
- [ ] [ID: P0-RUNTIME-ABI-MODE-SIMPLIFY-01-S3-02] representative regression を更新し、C++ helper/codegen で非退行を確認する。
- [ ] [ID: P0-RUNTIME-ABI-MODE-SIMPLIFY-01-S4-01] docs と how-to-use を新 naming に同期し、移行注意点を記録する。
- [ ] [ID: P0-RUNTIME-ABI-MODE-SIMPLIFY-01-S4-02] 完了結果を記録し、計画を archive へ移して閉じる。

## フェーズ詳細

### Phase 1: 契約固定

やること:
- `value` / `value_readonly` / `value_mut` の意味を整理する。
- 引数側 `value` を read-only value ABI に寄せることを正式決定する。
- `value_readonly` を非推奨 alias にするか即廃止するか決める。

成果物:
- naming 決定
- 移行ルール

### Phase 2: surface / metadata 更新

やること:
- parser と decorator 解析を更新する。
- canonical `runtime_abi_v1` metadata を新 naming にする。
- diagnostics も新 naming に揃える。

成果物:
- 新 mode 名を受理する frontend
- 整理された error message

### Phase 3: helper / regression 移行

やること:
- 既存 `@abi` 利用箇所を新 naming に移行する。
- C++ helper / codegen representative test を更新する。

成果物:
- migrated helper annotations
- green regression

### Phase 4: 運用固定

やること:
- docs 更新
- archive

成果物:
- docs
- archive 済み plan

## 決定ログ

- 2026-03-08: ユーザー指示により、`value_readonly` を簡約し、`@abi` mode 名を `value` / `value_mut` へ整理する P0 を起票する。
- 2026-03-08: 本計画では `value` を引数側 read-only value ABI として扱う。rare case の mutable value ABI は `value_mut` へ退避する。
- 2026-03-08: 本計画の主眼は naming と contract の整理であり、`@abi` 自体の必要性や runtime SoT linked-program 統合の是非は別計画で扱う。
