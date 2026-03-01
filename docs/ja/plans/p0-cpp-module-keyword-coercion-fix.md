# P0: C++ module import 関数の keyword 引数型伝播修正（冗長 `int64(py_to<int64>(...))` 撤去）

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-MODULE-KW-COERCE-01`

背景:
- `sample/15` の C++ 出力で `save_gif(..., delay_cs=4, loop=0)` が `int64(py_to<int64>(4))` のような冗長変換になっている。
- 原因は、module import 関数呼び出しで keyword 引数を位置引数へマージする際、値ノード（`kw_nodes`）が型強制処理へ渡らず、`unknown` 扱いになるため。
- その結果 `_coerce_args_for_module_function()` が fail-closed で runtime cast を付与し、リテラルでも冗長 cast が残る。

目的:
- module import 関数の引数マージ後に「文字列引数」と「対応 AST ノード」を同一順序で保持し、型強制で正しく利用する。
- `save_gif(..., delay_cs=4, loop=0)` のような既知 `int64` リテラルで冗長 `int64(py_to<int64>(...))` を生成しない。

対象:
- `src/hooks/cpp/emitter/call.py`（import 関数経路の args/kw merge と node 伝播）
- `src/hooks/cpp/emitter/module.py`（module 関数型強制）
- `test/unit/test_py2cpp_codegen_issues.py`（sample/15 断片回帰）
- 必要に応じて `test/unit/test_east3_cpp_bridge.py` / `tools/check_py2cpp_transpile.py`

非対象:
- class method / local function call の keyword マージ仕様変更
- module 関数シグネチャ抽出器（`extract_function_signatures_from_python_source`）の設計変更
- runtime API 変更

受け入れ基準:
- `sample/15` の `save_gif` 呼び出しで `..., 4, 0)` が出力され、`int64(py_to<int64>(4))` / `int64(py_to<int64>(0))` が消える。
- keyword 順序入替（`loop=0, delay_cs=4`）でも引数順と型が正しく維持される。
- `check_py2cpp_transpile` と関連 unit が通る。
- unknown/Any 経路は従来どおり fail-closed を維持する。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/regenerate_samples.py --langs cpp --force`

決定ログ:
- 2026-03-01: ユーザー報告（sample/15 の `int64(py_to<int64>(4))`）を受け、原因を「module import 関数 keyword 引数の AST ノード未伝播」と特定し、P0 タスクとして起票した。
- 2026-03-01: まずは callsite の args/kw ノード整合を修正し、補助的な文字列リテラル推論は後続最適化として切り分ける方針を確定した。

## 分解

- [ ] [ID: P0-CPP-MODULE-KW-COERCE-01-S1-01] module import 関数呼び出しで `args` と `kw` をマージする際、`arg_nodes` と `kw_nodes` も同順序でマージする。
- [ ] [ID: P0-CPP-MODULE-KW-COERCE-01-S2-01] `_coerce_args_for_module_function()` に正しい merged nodes を渡し、keyword リテラルの型既知経路で冗長 cast を抑止する。
- [ ] [ID: P0-CPP-MODULE-KW-COERCE-01-S2-02] sample/15 と keyword 順序入替ケースの回帰テストを追加し、`..., 4, 0)` 形を固定する。
- [ ] [ID: P0-CPP-MODULE-KW-COERCE-01-S3-01] transpile check / unit / sample 再生成で非退行を確認する。
