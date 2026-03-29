<a href="../../en/plans/p0-east3-cpp-empty-init-shorthand.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: EAST3 マーカー経由で C++ 空初期化を `= {};` へ縮退

最終更新: 2026-03-02

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-EAST3-CPP-EMPTY-INIT-SHORTHAND-01`

背景:
- 現行 C++ 出力では、`dict<str, int64> env = dict<str, int64>{};` のように、左辺型と同一の空初期化が冗長に出る。
- C++ としては `dict<str, int64> env = {};`（または `env{}`）で等価に表現でき、可読性が高い。
- ただし `Any/object` 境界や型曖昧ケースで単純置換すると意味変更リスクがあるため、EAST3 側で安全条件を確定したい。

目的:
- EAST3 で「空初期化 shorthand 適用可能」な代入/宣言へ明示マーカーを付与し、C++ emitter がそれを参照して `= {};` を出力する。
- マーカー欠落・不一致時は現行出力を維持し、fail-closed を保つ。

対象:
- `src/pytra/compiler/east_parts/east3_opt_passes/*`（新規 pass 追加または既存 pass 拡張）
- `src/hooks/cpp/emitter/stmt.py` / `src/hooks/cpp/emitter/collection_expr.py`
- `tools/unittest/test_east3_cpp_bridge.py` / `tools/unittest/test_py2cpp_codegen_issues.py`
- `sample/cpp/18_mini_language_interpreter.cpp`（再生成確認）

非対象:
- 空初期化以外の式縮退（括弧削減・cast削減など）
- Rust/Scala/Java など他 backend 出力の変更
- C++ runtime コンテナ型の仕様変更

受け入れ基準:
- EAST3 で安全条件を満たす `AnnAssign/Assign` の空 `List/Dict/Set` 初期化にマーカーが付与される。
- C++ emitter はマーカー付きかつ型一致時のみ `= {};` を出力する。
- `Any/object` / union / runtime-boxing 経路では現行の明示型初期化（例: `dict<...>{}` / `make_object(...)`）を維持する。
- `check_py2cpp_transpile.py` と関連 unit が通過し、`sample/cpp/18` で対象箇所の縮退を確認できる。

確認コマンド（予定）:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check/check_py2cpp_transpile.py`
- `python3 tools/gen/regenerate_samples.py --langs cpp --stems 18_mini_language_interpreter --force`

決定ログ:
- 2026-03-02: ユーザー指示により、EAST3 で安全性マーカーを付与し、C++ emitter 側で `= {};` へ縮退する方針で `P0` 起票。
- 2026-03-02: `EmptyInitShorthandPass` を追加し、`Assign/AnnAssign` の空 `List/Dict/Set` かつ `target_type` が `list/dict/set[...]`・非 `Any/object/union` のケースだけ `cpp_empty_init_shorthand_v1`（`version/target_type/rhs_kind`）を付与する実装に確定（不一致時はマーカー削除で fail-closed）。
- 2026-03-02: `CppEmitter` 側へマーカー参照経路を追加し、ヒント整合時のみ `rendered_value` を `{}` へ縮退するよう更新。ヒント欠落/不整合/非空初期化時は既存 `T{}` 出力を維持。
- 2026-03-02: unit + sample + transpile チェックを実行し、`sample/cpp/18` の空初期化が `= {};` へ縮退したことを確認。
  - `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_optimizer.py' -v`（51 tests, OK）
  - `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -v`（92 tests, OK）
  - `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`（98 tests, OK）
  - `python3 tools/gen/regenerate_samples.py --langs cpp --stems 18_mini_language_interpreter --force`（regen=1 fail=0）
  - `python3 tools/check/check_py2cpp_transpile.py`（checked=136 ok=136 fail=0 skipped=6）

## 分解

- [x] [ID: P0-EAST3-CPP-EMPTY-INIT-SHORTHAND-01-S1-01] 適用条件（左辺型=右辺空コンテナ型、非Any/object、非boxing）を仕様化する。
- [x] [ID: P0-EAST3-CPP-EMPTY-INIT-SHORTHAND-01-S1-02] EAST3 マーカースキーマ（例: `cpp_empty_init_shorthand_v1`）と fail-closed 条件を定義する。
- [x] [ID: P0-EAST3-CPP-EMPTY-INIT-SHORTHAND-01-S2-01] EAST3 optimizer pass で対象ノードへマーカーを付与する。
- [x] [ID: P0-EAST3-CPP-EMPTY-INIT-SHORTHAND-01-S2-02] C++ emitter をマーカー参照型に切替え、`T x = T{};` を `T x = {};` へ縮退する。
- [x] [ID: P0-EAST3-CPP-EMPTY-INIT-SHORTHAND-01-S2-03] マーカー不在/不整合時の fallback を実装し、既存出力へ戻す。
- [x] [ID: P0-EAST3-CPP-EMPTY-INIT-SHORTHAND-01-S3-01] unit テストを追加し、誤適用（Any/object 経路）と再発を検知可能にする。
- [x] [ID: P0-EAST3-CPP-EMPTY-INIT-SHORTHAND-01-S3-02] `sample/cpp/18` 再生成と transpile チェックで非退行を確認する。
