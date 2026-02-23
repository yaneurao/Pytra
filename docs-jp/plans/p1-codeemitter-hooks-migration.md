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

`P1-CEH-01-S1` 棚卸し（2026-02-23）:

- 高優先:
  - `src/py2cpp.py:1784` `emit_stmt` の kind 分岐ツリーが C++ 固有分岐と共通文スケルトンを同居させている。`CodeEmitter` hook（`emit_stmt_kind` 系）へ移し、`py2cpp.py` 側は C++ 固有差分のみ保持する。
  - `src/py2cpp.py:2520` / `src/py2cpp.py:2580` `emit_for_range` / `emit_for_each` が loop 骨格と最適化/プロトコル選択を直書きしている。`For`/`ForRange` 骨格は共通層へ、C++ 固有（型名・`py_iter_or_raise` 経路）は hook へ分離する。
  - `src/py2cpp.py:3277` / `src/py2cpp.py:3332` Builtin runtime fallback が `py_len` / `py_print` / `py_replace` などの関数名分岐を直書きしている。profile の runtime map + hook へ移して `py2cpp.py` 固定 if 連鎖を削減する。
- 中優先:
  - `src/py2cpp.py:4029` `_render_call_fallback` が `len`/`isinstance`/`print` を直接 lower している。`Call` fallback は共通層へ寄せ、C++ 差分は hook で後段上書きする。
  - `src/py2cpp.py:3155` `_render_binop_expr` が `Div`/`FloorDiv`/`Mod`/`Mult` の型依存最適化を内包している。profile 化（演算子 policy）と hook 化（特殊 case）へ分割し、`py2cpp.py` の演算子 if 連鎖を縮退する。
  - `src/py2cpp.py:748` `_resolve_runtime_call_for_imported_symbol` が namespace fallback を C++ 固有で持っている。import 解決共通 API に寄せ、C++ namespace 連結は profile/hook で注入する。
- 低優先:
  - `src/py2cpp.py:185` / `src/py2cpp.py:222` `load_cpp_type_map` / `load_cpp_identifier_rules` の静的定義は profile へ移し替え可能。機能回帰リスクが低いため後段で対応する。

移行優先順位（S2 着手順）:
1. `emit_stmt` / `emit_for_each` / `emit_for_range` の文スケルトン（高優先、回収効果が大きい）。
2. Builtin runtime fallback（`_render_builtin_runtime_fallback` 系）を profile/hook へ移管。
3. `_render_call_fallback` と `_render_binop_expr` の分岐縮退。
4. import namespace fallback と type/rule 定義の profile 化。

決定ログ:
- 2026-02-22: 初版作成。
- 2026-02-23: docs-jp/todo.md の P1-CEH-01 を -S1 〜 -S4 に分割したため、本 plan に同粒度の実行順を追記した。
- 2026-02-23: `P1-CEH-01-S1` として `py2cpp.py` の profile/hook 境界違反ケースを棚卸しし、`高/中/低` 優先で移行順を確定した。
