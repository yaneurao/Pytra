# TASK GROUP: TG-P1-CEH

最終更新: 2026-02-22

関連 TODO:
- `docs-jp/todo.md` の `ID: P1-CEH-01`

背景:
- `py2cpp.py` 側に条件分岐が残ると、profile/hook での拡張性と多言語整合が崩れる。

目的:
- profile で表現困難な差分のみ hooks へ寄せ、`py2cpp.py` 側分岐を最小化する。

対象:
- `CodeEmitter` / hooks 境界整理
- `py2cpp.py` 側の分岐撤去

非対象:
- runtime API 仕様の大幅変更

受け入れ基準:
- profile + hooks で言語固有差分を表現可能
- `py2cpp.py` 側条件分岐が縮退

確認コマンド:
- `python3 tools/check_py2cpp_transpile.py`
- `python3 test/unit/test_code_emitter.py`

決定ログ:
- 2026-02-22: 初版作成。
