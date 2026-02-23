# TASK GROUP: TG-P1-CEH

最終更新: 2026-02-23

関連 TODO:
- `docs-jp/todo.md` の `ID: P1-CEH-01`
- `docs-jp/todo.md` の `ID: P1-CEH-01-S1` 〜 `P1-CEH-01-S4`

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

サブタスク実行順（todo 同期）:

1. `P1-CEH-01-S1`: `py2cpp.py` 側の profile/hook 境界違反ケースを棚卸しし、移行優先順位を確定する。
2. `P1-CEH-01-S2`: hooks へ移しやすいケースから順に `CodeEmitter` 側へ移管し、`py2cpp.py` 条件分岐を削減する。
3. `P1-CEH-01-S3`: hook 化困難ケースは profile 表現力を拡張して吸収し、target 固有分岐の再増殖を防ぐ。
4. `P1-CEH-01-S4`: selfhost/fixture 回帰で生成差分を確認し、残る `py2cpp.py` 分岐を撤去する。

決定ログ:
- 2026-02-22: 初版作成。
- 2026-02-23: docs-jp/todo.md の P1-CEH-01 を -S1 〜 -S4 に分割したため、本 plan に同粒度の実行順を追記した。
