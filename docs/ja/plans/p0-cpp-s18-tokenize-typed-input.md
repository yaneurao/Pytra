# P0: sample/18 `tokenize` 入力の typed 化（`object` 退化撤去）

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-S18-TOKENIZE-TYPED-IN-01`

背景:
- 現在の `sample/18` 生成 C++ では `tokenize(object lines)` になっており、冒頭で `py_to_str_list_from_object(lines)` を介する。
- 変換元は `lines: list[str]` が既知であり、ここで `object` 化すると copy/cast と可読性悪化が同時に発生する。

目的:
- `tokenize` 境界で `list[str]` 型を維持し、`object` への退化と再変換を撤去する。

対象:
- `src/hooks/cpp/emitter/*`（関数シグネチャ/型橋渡し/呼び出し側整合）
- `test/unit/test_py2cpp_codegen_issues.py`
- `sample/cpp/18_mini_language_interpreter.cpp`（再生成確認）

非対象:
- mini language の文法変更
- runtime API の全面刷新

受け入れ基準:
- `sample/18` の `tokenize` が `object` 引数を取らず、`list<str>` 直受けになる。
- `tokenize` 内に `py_to_str_list_from_object(lines)` が出力されない。
- 生成結果・単体テスト・transpile check が非退行で通る。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 src/py2cpp.py sample/py/18_mini_language_interpreter.py -o sample/cpp/18_mini_language_interpreter.cpp`

決定ログ:
- 2026-03-01: sample/18 追加最適化として `tokenize` 境界の `object` 退化撤去を P0 で起票。
- 2026-03-01: `emit_function` に `pyobj + list[str]` 引数の typed 署名出力（`const list<str>&`）を追加し、`tokenize` 引数を `object` から `list<str>` へ変更した。
- 2026-03-01: `ForCore` の typed enumerate 復元で「typed `list[str]` パラメータ名」のときは `py_enumerate(lines)` を優先し、`py_to_str_list_from_object(lines)` を関数内から撤去した。
- 2026-03-01: callsite coercion に `list[str]` 専用の `py_to_str_list_from_object(...)` 変換を追加し、`pyobj` 由来 `object` 変数（`demo_lines`/`source_lines`）から typed `tokenize` へ安全に接続する方針へ固定した。
- 2026-03-01: `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`（80件）、`python3 tools/check_py2cpp_transpile.py`（`checked=134 ok=134 fail=0 skipped=6`）、`python3 tools/runtime_parity_check.py --case-root sample --targets cpp 18_mini_language_interpreter --ignore-unstable-stdout`（PASS）で非退行を確認した。

## 分解

- [x] [ID: P0-CPP-S18-TOKENIZE-TYPED-IN-01] `tokenize` 引数の `object` 退化を撤去し、`list[str]` 型を境界越しに維持する。
- [x] [ID: P0-CPP-S18-TOKENIZE-TYPED-IN-01-S1-01] 現在 `object` に落ちる型決定経路（関数定義/呼び出し）を棚卸しし、fail-closed 条件を固定する。
- [x] [ID: P0-CPP-S18-TOKENIZE-TYPED-IN-01-S2-01] C++ emitter の型橋渡しを更新し、`tokenize(lines)` を typed 署名へ出力する。
- [x] [ID: P0-CPP-S18-TOKENIZE-TYPED-IN-01-S2-02] sample/18 回帰を追加し、`py_to_str_list_from_object(lines)` 非出力を固定する。
- [x] [ID: P0-CPP-S18-TOKENIZE-TYPED-IN-01-S3-01] transpile/unit/sample 再生成を実行し、非退行を確認する。
