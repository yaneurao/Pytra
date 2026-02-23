# TASK GROUP: TG-P1-CED

最終更新: 2026-02-23

関連 TODO:
- `docs-jp/todo.md` の `ID: P1-CED-*`

背景:
- selfhost で static 束縛前提が強く、共通化時に派生実装へ到達しない経路が発生する。

目的:
- `render_expr` / `emit_stmt` を hook 主体に再設計し、共通化と selfhost 安定を両立する。

対象:
- kind 単位の hook 注入
- CppEmitter の hook 優先 + fallback 2段構成
- fallback の段階削減
- py2cpp/py2rs の共通化候補整理

非対象:
- 一括での全面 rewrite

受け入れ基準:
- hooks 有効時の生成結果が既存と一致
- selfhost diff で `mismatches=0`
- `py2cpp.py` 本体分岐が段階的に短縮

確認コマンド:
- `python3 tools/check_selfhost_cpp_diff.py`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 test/unit/test_code_emitter.py`
- `python3 test/unit/test_py2cpp_features.py`

サブタスク実行順（todo 同期）:
1. `P1-CED-01-S1`: `CodeEmitter` へ kind 専用 hook 名（`on_render_expr_<kind>`）の解決 API を追加し、`py2cpp` `render_expr` から呼び出せるようにする。
2. `P1-CED-01-S2`: 非 C++ emitter（`rs/cs/js/ts`）へ同一の kind 専用 hook 呼び出しを適用する。
3. `P1-CED-01-S3`: kind 専用 hook の登録規約を hooks/profile ドキュメントへ反映し、selfhost 回帰で挙動を固定する。

決定ログ:
- 2026-02-22: 初版作成。
- 2026-02-23: [ID: P1-CED-01-S1] として `CodeEmitter` に `hook_on_render_expr_kind_specific()` と kind 正規化（`Name` -> `on_render_expr_name`, `IfExp` -> `on_render_expr_if_exp`）を追加し、`py2cpp` `render_expr` の優先順を「kind専用hook -> 既存 `on_render_expr_kind`」へ変更した。`python3 test/unit/test_code_emitter.py`、`python3 test/unit/test_py2cpp_features.py Py2CppFeatureTest.test_render_expr_kind_specific_hook_precedes_generic_kind_hook Py2CppFeatureTest.test_emit_stmt_fallback_works_when_dynamic_hooks_disabled Py2CppFeatureTest.test_emit_stmt_dispatch_table_handles_continue_and_unknown`、`python3 test/unit/test_cpp_hooks.py`、`python3 tools/check_py2cpp_transpile.py` で回帰を確認する。
- 2026-02-23: [ID: P1-CED-01-S2] として `js/cs/rs` emitter の `render_expr` 先頭へ `hook_on_render_expr_kind_specific()` 呼び出しを追加し、kind 専用 hook の優先順を `py2cpp` と揃えた。`ts` は専用 emitter 未実装のため `transpile_to_js()` 経由で同一経路を使うことを `test_py2ts_smoke.py::test_ts_preview_uses_js_transpile_pipeline` で固定した。`python3 test/unit/test_py2js_smoke.py Py2JsSmokeTest.test_render_expr_kind_specific_hook_precedes_leaf_hook`、`python3 test/unit/test_py2cs_smoke.py Py2CsSmokeTest.test_render_expr_kind_specific_hook_precedes_leaf_hook`、`python3 test/unit/test_py2rs_smoke.py Py2RsSmokeTest.test_render_expr_kind_specific_hook_precedes_leaf_hook`、`python3 test/unit/test_py2ts_smoke.py Py2TsSmokeTest.test_ts_preview_uses_js_transpile_pipeline`、`python3 tools/check_py2js_transpile.py`、`python3 tools/check_py2cs_transpile.py`、`python3 tools/check_py2rs_transpile.py`、`python3 tools/check_py2ts_transpile.py` で回帰なしを確認した。
