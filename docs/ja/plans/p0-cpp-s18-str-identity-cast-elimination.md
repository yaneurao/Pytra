# P0: sample/18 `str -> str` 同型変換の撤去（`py_to_string` 縮退）

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-S18-STR-IDENTITY-CAST-01`

背景:
- sample/18 生成 C++ の parser 経路に `py_to_string(this->expect(...)->text)` が残っている。
- `text` がすでに `str` のため、同型変換は不要で可読性と実行効率を損なう。

目的:
- C++ backend で `str` 既知経路の同型変換を削減し、sample/18 の不要 wrapper を撤去する。

対象:
- `src/hooks/cpp/emitter/*`（cast 判定/式出力）
- `src/pytra/compiler/east_parts/east3_opt_passes/*`（必要時）
- `test/unit/test_east3_cpp_bridge.py`
- `test/unit/test_py2cpp_codegen_issues.py`

非対象:
- `object/Any` 経路まで一律削減する unsafe 最適化
- `str` 以外の全面 cast ルール刷新

受け入れ基準:
- sample/18 で `py_to_string(...->text)` が出力されない。
- 型既知 `str` のみ縮退し、`object/unknown` 経路の安全変換は維持される。
- 回帰テストで fail-closed を担保し、非退行を確認する。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`

決定ログ:
- 2026-03-01: sample/18 追加最適化として `str -> str` 同型 cast 削減を P0 で起票。
- 2026-03-01: `sample/18` の `let_name/assign_name` 代入 AST が `Unbox(target=str)` で、`value` 側 `Attribute` の `resolved_type` が `unknown` のため `py_to_string(...)` が残ることを確認した。
- 2026-03-01: C++ emitter に `class_method_return_types` と `class_field_types` を持たせ、`Call(Attribute)`（例: `self.expect(...)`）とそのフィールドアクセス（`Token.text`）の型推論を補強した。
- 2026-03-01: `_render_expr_kind_unbox` に「source/target 同型なら素通し」ガードを追加し、`py_to_string(this->expect(\"IDENT\")->text)` を `this->expect(\"IDENT\")->text` へ縮退した。
- 2026-03-01: `test_py2cpp_codegen_issues.py` に sample/18 回帰（`IDENT.text` の `py_to_string` 不要化）を追加し、`PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`（81件）、`python3 tools/check_py2cpp_transpile.py`（`checked=134 ok=134 fail=0 skipped=6`）、`runtime_parity_check`（sample/18 cpp PASS）で非退行を確認した。

## 分解

- [x] [ID: P0-CPP-S18-STR-IDENTITY-CAST-01] `str` 既知経路の `py_to_string` 同型変換を縮退する。
- [x] [ID: P0-CPP-S18-STR-IDENTITY-CAST-01-S1-01] `str` 同型変換の現状箇所を棚卸しし、適用条件/除外条件を固定する。
- [x] [ID: P0-CPP-S18-STR-IDENTITY-CAST-01-S2-01] emitter（必要なら EAST3 pass）へ縮退実装を追加し、`object` 経路は維持する。
- [x] [ID: P0-CPP-S18-STR-IDENTITY-CAST-01-S2-02] sample/18 回帰を追加し、`py_to_string` 不要出力の再発を防止する。
- [x] [ID: P0-CPP-S18-STR-IDENTITY-CAST-01-S3-01] transpile/unit/sample 再生成で非退行を確認する。
