# P0: sample/13 向け `cpp_list_model=pyobj` の typed list 拡張

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-S13-TYPED-LIST-EXPAND-01`

背景:
- `sample/13` では `grid/stack/dirs/frames` が `object` 経路へ落ち、`py_at/py_set_at/py_to` の多段アクセスが増えている。
- 現行の pyobj list typed 例外は限定的で、`list[list[int64]]` や `list[tuple[...]]` を十分に value/list 型へ戻せていない。

目的:
- `cpp_list_model=pyobj` でも「要素型が concrete で Any/unknown を含まない list」を typed list として扱い、sample/13 の object 退化を減らす。

対象:
- `src/hooks/cpp/emitter/type_bridge.py`（pyobj list 判定）
- `src/hooks/cpp/emitter/stmt.py` / `collection_expr.py`（typed list 生成・反復）
- `test/unit/test_py2cpp_codegen_issues.py`

非対象:
- list を PyObj ベースへ全面移行する設計変更
- `cpp_list_model=value` の仕様変更

受け入れ基準:
- sample/13 で `grid/stack/dirs/frames` が typed list 出力へ寄る。
- `object(py_at(grid, ...))` 依存が主要経路から減る。
- `check_py2cpp_transpile` と unit が通る。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/regenerate_samples.py --langs cpp --force`

決定ログ:
- 2026-03-01: ユーザー要望により、sample/13 の冗長性改善として pyobj list typed 拡張を P0 起票した。

## 分解

- [ ] [ID: P0-CPP-S13-TYPED-LIST-EXPAND-01-S1-01] `cpp_list_model=pyobj` の typed list 判定拡張条件（concrete 要素型）を仕様化する。
- [ ] [ID: P0-CPP-S13-TYPED-LIST-EXPAND-01-S2-01] emitter 実装を更新し、sample/13 の `grid/stack/dirs/frames` を typed list へ寄せる。
- [ ] [ID: P0-CPP-S13-TYPED-LIST-EXPAND-01-S3-01] sample/13 断片回帰を追加し、transpile/check を通す。
