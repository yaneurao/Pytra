# P0: sample/13 `while stack` の `.empty()` fastpath

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-S13-WHILE-EMPTY-FASTPATH-01`

背景:
- sample/13 では `while stack:` が `while (py_len(stack) != 0)` に展開される。
- `stack` が typed list と確定する経路では `.empty()` のほうが簡潔でコストも低い。

目的:
- typed list 経路の `while py_len(list) != 0` / `== 0` を `!list.empty()` / `list.empty()` へ変換する fastpath を追加する。

対象:
- `src/hooks/cpp/emitter/cpp_emitter.py` / `stmt.py`（条件式描画）
- `test/unit/test_east3_cpp_bridge.py` / `test/unit/test_py2cpp_codegen_issues.py`

非対象:
- object/Any 経路の条件式仕様変更
- list 以外コンテナへの適用

受け入れ基準:
- sample/13 で `while (py_len(stack) != 0)` が `while (!stack.empty())` 相当へ縮退する。
- unknown/object 経路は現行どおり fail-closed を維持する。
- transpile/unit が通る。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`

決定ログ:
- 2026-03-01: ユーザー要望により、sample/13 の `while stack` 表現縮退を独立 P0 として起票。

## 分解

- [ ] [ID: P0-CPP-S13-WHILE-EMPTY-FASTPATH-01-S1-01] typed list 条件式の fastpath 適用条件（`py_len(list) ==/!= 0`）を定義する。
- [ ] [ID: P0-CPP-S13-WHILE-EMPTY-FASTPATH-01-S2-01] 条件式描画へ `.empty()` fastpath を実装する。
- [ ] [ID: P0-CPP-S13-WHILE-EMPTY-FASTPATH-01-S3-01] sample/13 回帰を追加し、transpile/check を通す。
