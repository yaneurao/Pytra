# TASK GROUP: TG-P1-CEH

最終更新: 2026-02-23

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-CEH-01`
- `docs/ja/todo/index.md` の `ID: P1-CEH-01-S1` 〜 `P1-CEH-01-S4`

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
- 2026-02-23: docs/ja/todo/index.md の P1-CEH-01 を -S1 〜 -S4 に分割したため、本 plan に同粒度の実行順を追記した。
- 2026-02-23: `P1-CEH-01-S1` として `py2cpp.py` の profile/hook 境界違反ケースを棚卸しし、`高/中/低` 優先で移行順を確定した。
- 2026-02-23: `P1-CEH-01-S2` の第1段として、`CppEmitter.hook_on_emit_stmt_kind` を override し、`super().hook_on_emit_stmt_kind(...)`（dynamic hook）で未処理だった場合に `_emit_stmt_kind_fallback(...)` で C++ 既定ディスパッチする構成へ変更した。これにより `emit_stmt` 本体の kind if 連鎖を撤去し、`CodeEmitter` hook 経由へ統一した。`python3 test/unit/test_py2cpp_features.py Py2CppFeatureTest.test_emit_stmt_fallback_works_when_dynamic_hooks_disabled Py2CppFeatureTest.test_runtime_module_tail_and_namespace_support_compiler_tree`、`python3 test/unit/test_cpp_hooks.py`、`python3 tools/check_py2cpp_transpile.py`（`checked=131 ok=131 fail=0 skipped=6`）で回帰なしを確認した。
- 2026-02-23: `P1-CEH-01-S3` として profile 表現力を拡張。`load_cpp_type_map(profile)` / `load_cpp_identifier_rules(profile)` を追加し、`CppEmitter.__init__` から `self.profile` を渡すよう変更した。これにより type map・識別子予約語/rename prefix の target 固有ハードコードを profile オーバーレイ可能にした。`python3 test/unit/test_py2cpp_features.py Py2CppFeatureTest.test_load_cpp_type_map_allows_profile_overlay Py2CppFeatureTest.test_load_cpp_identifier_rules_allows_profile_override`、`python3 tools/check_py2cpp_transpile.py`（`checked=131 ok=131 fail=0 skipped=6`）で回帰なしを確認した。
- 2026-02-23: [ID: P1-CEH-01-S4] として `CppEmitter._emit_stmt_kind_fallback` の残存 if 連鎖を kind->handler ディスパッチテーブルへ置換し、`test_emit_stmt_dispatch_table_handles_continue_and_unknown` を追加した。`python3 test/unit/test_py2cpp_features.py Py2CppFeatureTest.test_emit_stmt_fallback_works_when_dynamic_hooks_disabled Py2CppFeatureTest.test_emit_stmt_dispatch_table_handles_continue_and_unknown Py2CppFeatureTest.test_load_cpp_type_map_allows_profile_overlay Py2CppFeatureTest.test_load_cpp_identifier_rules_allows_profile_override`、`python3 test/unit/test_cpp_hooks.py`、`python3 tools/check_py2cpp_transpile.py`（`checked=131 ok=131 fail=0 skipped=6`）に加えて、selfhost 基線として `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知）、`python3 tools/verify_selfhost_end_to_end.py --skip-build --cases sample/py/01_mandelbrot.py sample/py/17_monte_carlo_pi.py test/fixtures/control/if_else.py`（`failures=1`, 既知 `sample/py/01_mandelbrot.py`）、`python3 tools/check_selfhost_direct_compile.py --cases sample/py/01_mandelbrot.py sample/py/17_monte_carlo_pi.py test/fixtures/control/if_else.py`（`failures=0`）を確認した。あわせて `src/pytra/compiler/transpiler_versions.json` の `cpp` を `0.275.0 -> 0.276.0` へ更新し、`python3 tools/check_transpiler_version_gate.py` を通過させた。
