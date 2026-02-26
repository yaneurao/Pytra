# P0: C++ emitter 肥大化の段階縮退

最終更新: 2026-02-26

関連 TODO:
- `docs-ja/todo/index.md` の `ID: P0-CPP-EMITTER-SLIM-01`

背景:
- `src/hooks/cpp/emitter/cpp_emitter.py` は約 6.6k 行規模で、`render_expr` の分岐集中と C++ 固有責務の同居により変更衝突が起きやすい。
- EAST3 主経路を採用している一方で、`stage2/self_hosted` 互換・legacy type_id 名呼び出しなどの互換分岐が残っている。
- import/include/namespace/class/type/runtime-call などの責務が単一ファイルへ集中し、局所変更でも回帰範囲が広い。

目的:
- `cpp_emitter.py` を「オーケストレーション + ディスパッチ」中心へ縮退し、互換層を撤去した EAST3 単一契約へ寄せる。

対象:
- `src/hooks/cpp/emitter/cpp_emitter.py`
- `src/hooks/cpp/emitter/` 配下（`call.py` / `expr.py` / `stmt.py` / `operator.py` / `tmp.py` / `trivia.py` と新規分割モジュール）
- 必要時: `src/pytra/compiler/east_parts/code_emitter.py`（共通化対象のみ）
- テスト/検証: `test/unit/test_py2cpp_*.py`, `tools/check_py2cpp_transpile.py`, `tools/check_selfhost_cpp_diff.py`, `tools/verify_selfhost_end_to_end.py`

非対象:
- C++ runtime API の仕様変更
- sample プログラム仕様の変更
- 非C++ emitter の機能追加（別タスク管理）

受け入れ基準:
- `stage2/self_hosted` 互換の C++ emitter 内 legacy 分岐（builtin/type_id/For bridge）が撤去され、EAST3 契約に統一される。
- `render_expr` がディスパッチ中心に縮退し、巨大分岐を局所 handler へ分離できる。
- `cpp_emitter.py` の最終メトリクスを記録し、少なくとも以下を満たす。
  - ファイル行数: 2500 行以下（目安）
  - `render_expr` 行数: 200 行以下（目安）
  - legacy 互換関数残数: 0
- C++ 回帰（unit/smoke/selfhost）が基線を維持する。

## 分解

- [x] [ID: P0-CPP-EMITTER-SLIM-01-S1-01] `cpp_emitter.py` の行数・メソッド数・長大メソッドを計測し、基準値を文書化する。
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S1-02] `sample` と `test/unit` の C++ 生成差分基線を固定する。
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S2-01] stage2/self_hosted 由来の legacy builtin compat 経路を撤去する。
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S2-02] `For`/`ForRange` <-> `ForCore` bridge を撤去し、`ForCore` 直接受理へ統一する。
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S2-03] legacy `isinstance/issubclass` Name-call 許容を撤去し、type_id 系を EAST3 ノード前提に統一する。
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S3-01] import/include/namespace/module-init の責務を専用モジュールへ分離する。
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S3-02] class emit（`virtual/override`・`PYTRA_TYPE_ID`）責務を専用モジュールへ分離する。
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S3-03] 型変換 (`_cpp_type_text`) と Any 境界補正 helper を専用モジュールへ分離する。
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S3-04] built-in runtime_call（list/set/dict/str/path/special）分岐を専用ディスパッチへ分離する。
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S4-01] `render_expr` の `kind -> handler` テーブル駆動の骨格を導入する。
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S4-02] collection literal/comprehension 系 handler を分離し、回帰テストを追加する。
- [ ] [ID: P0-CPP-EMITTER-SLIM-01-S4-03] runtime/type_id/path 系 handler を分離し、`render_expr` をディスパッチ専任へ縮退する。
- [ ] [ID: P0-CPP-EMITTER-SLIM-01-S5-01] `repr` 依存ノードの対象を棚卸しし、parser/lowerer 側の構造化ノード移行計画を確定する。
- [ ] [ID: P0-CPP-EMITTER-SLIM-01-S5-02] `_render_repr_expr` の利用箇所を段階削減し、最終 fallback 以外を除去する。
- [ ] [ID: P0-CPP-EMITTER-SLIM-01-S5-03] `_render_repr_expr` を撤去（または no-op 化）し、`repr` 文字列依存をなくす。
- [ ] [ID: P0-CPP-EMITTER-SLIM-01-S6-01] Rust/C++ 共通化候補（条件式・cast 補助・ループ骨格）を棚卸しし、`CodeEmitter` 移管対象を確定する。
- [ ] [ID: P0-CPP-EMITTER-SLIM-01-S6-02] 共通化対象の 1〜2 系統を `CodeEmitter` へ移管し、C++/Rust の重複を削減する。
- [ ] [ID: P0-CPP-EMITTER-SLIM-01-S7-01] `test/unit/test_py2cpp_*.py` と `tools/check_py2cpp_transpile.py` を通して回帰を固定する。
- [ ] [ID: P0-CPP-EMITTER-SLIM-01-S7-02] `tools/check_selfhost_cpp_diff.py` / `tools/verify_selfhost_end_to_end.py` で selfhost 回帰を確認する。
- [ ] [ID: P0-CPP-EMITTER-SLIM-01-S7-03] 最終メトリクスを再計測し、完了判定（行数・`render_expr` 行数・legacy 0件）を記録する。

## S1-01 基線メトリクス（2026-02-26）

- 計測コマンド:
  - `python3 - <<'PY' ... ast.parse(...) ... PY`（`src/hooks/cpp/emitter/cpp_emitter.py` を対象）
  - `wc -l src/hooks/cpp/emitter/cpp_emitter.py`
- 基準値:
  - ファイル行数: `6814`
  - `CppEmitter` メソッド数: `164`
  - `render_expr` 行数: `869`（`L5812-L6680`）
  - legacy/compat 名付きメソッド数: `3`
- 長大メソッド（上位5件）:
  - `render_expr`: `869` 行
  - `_render_builtin_runtime_special_ops`: `359` 行
  - `emit_class`: `259` 行
  - `transpile`: `236` 行
  - `emit_assign`: `166` 行

決定ログ:
- 2026-02-25: `cpp_emitter.py` の肥大要因分析（互換層残存 + 責務集中 + 巨大 `render_expr`）に基づき、最優先タスクとして追加。
- 2026-02-26: `P0-CPP-EMITTER-SLIM-01-S1-01` として現状メトリクスを固定した。`file_lines=6814`、`method_count=164`、`render_expr_lines=869`、`legacy_named_methods=3`（`_render_legacy_builtin_call_compat` / `_render_legacy_builtin_method_call_compat` / `_allows_legacy_type_id_name_call`）を基線として、以後の縮退効果をこの値との差分で判定する。
- 2026-02-26: `P0-CPP-EMITTER-SLIM-01-S1-02` として C++ 生成差分の基線を固定した。`tools/check_selfhost_cpp_diff.py` に既知差分基線ファイル（`tools/selfhost_cpp_diff_expected.txt`）を導入し、default case（`sample` + `test/fixtures`）では「既知差分のみ許容・新規差分のみ失敗」に変更した。検証は `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented --skip-east3-contract-tests`（`mismatches=0 known_diffs=6 skipped=0`）、`python3 tools/check_sample_regen_clean.py`（`[OK] sample outputs are clean`）、`python3 tools/check_py2cpp_transpile.py`（`checked=133 ok=133 fail=0 skipped=6`）で実施した。
- 2026-02-26: `P0-CPP-EMITTER-SLIM-01-S2-01` として `src/hooks/cpp/emitter/cpp_emitter.py` の legacy builtin compat 関数（`_render_legacy_builtin_call_compat` / `_render_legacy_builtin_method_call_compat`）と呼び出し分岐を削除し、`BuiltinCall`/builtin method は self_hosted/stage2 入力でも EAST3 lower 済み前提でエラー化する単一路線に統一した。`test/unit/test_east3_cpp_bridge.py` の該当ケースをエラー期待へ更新し、検証は `python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_builtin_call_without_runtime_call_rejected_for_stage2_selfhost'`、`python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_plain_builtin_method_call_rejected_for_self_hosted_parser'`、`python3 tools/check_py2cpp_transpile.py`（`checked=133 ok=133 fail=0 skipped=6`）で実施した。
- 2026-02-26: `P0-CPP-EMITTER-SLIM-01-S2-02` として `For`/`ForRange` の bridge（`_for_stmt_to_forcore` / `_forrange_stmt_to_forcore`）と `ForCore` からの逆写像（`_target_expr_from_target_plan` 経由で `emit_for_range` / `emit_for_each` を呼ぶ経路）を撤去した。`emit_stmt` は `For`/`ForRange` を即エラー化し、`emit_for_core` は `target_plan` / `iter_plan` を直接解釈して static-range/runtime-protocol を描画する。検証は `python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_emit_stmt_forcore_runtime_protocol_typed_target_uses_unbox_path'`、`python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_emit_stmt_rejects_legacy_forrange_node'`、`python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_emit_stmt_rejects_legacy_for_node'`、`python3 tools/check_py2cpp_transpile.py`（`checked=133 ok=133 fail=0 skipped=6`）で実施した。
- 2026-02-26: `P0-CPP-EMITTER-SLIM-01-S2-03` として legacy `isinstance/issubclass` Name-call 許容を撤去した。`_allows_legacy_type_id_name_call` と legacy 展開分岐を削除し、`isinstance/issubclass` は `east_stage` に関わらず `type_id call must be lowered to EAST3 node` で失敗させる一方、`py_isinstance` など runtime 名は既存サポートを維持した。検証は `python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_legacy_type_id_name_call_rejected_in_east3'`、`python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_legacy_type_id_name_call_rejected_in_east2_compat'`、`python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_runtime_py_isinstance_name_call_uses_type_id_core_node_path'`、`python3 tools/check_py2cpp_transpile.py`（`checked=133 ok=133 fail=0 skipped=6`）で実施した。
- 2026-02-26: `P0-CPP-EMITTER-SLIM-01-S3-01` として import/include/namespace/module-init 関連の helper 群を `src/hooks/cpp/emitter/module.py`（`CppModuleEmitter`）へ移設した。`cpp_emitter.py` 側は `_attach_cpp_emitter_helper_methods` で mixin を注入するだけに縮退し、旧実装を削除した。`CodeEmitter` 既定実装を上書きできるよう helper 注入条件を `hasattr` ではなく `target_cls.__dict__` ベースに変更し、継承スタブではなく移設先実装が必ず使われる状態にした。検証は `python3 -m py_compile src/hooks/cpp/emitter/module.py src/hooks/cpp/emitter/cpp_emitter.py`、`python3 -m unittest discover -s test/unit -p 'test_py2cpp_features.py' -k 'test_math_module_call_uses_runtime_call_map'`、`python3 -m unittest discover -s test/unit -p 'test_py2cpp_features.py' -k 'test_from_import_symbol_uses_runtime_call_map'`、`python3 -m unittest discover -s test/unit -p 'test_py2cpp_features.py' -k 'test_import_module_alias_uses_runtime_call_map'`、`python3 tools/check_py2cpp_transpile.py`（`checked=133 ok=133 fail=0 skipped=6`）で実施した。
- 2026-02-26: `P0-CPP-EMITTER-SLIM-01-S3-02` として class emit 責務を `src/hooks/cpp/emitter/class_def.py`（`CppClassEmitter`）へ移設し、`emit_class` / `_class_has_base_method` を `cpp_emitter.py` 本体から除去した。`CppEmitter` 側は mixin 注入のみで class 生成ロジックを参照する構成へ縮退し、`virtual/override` 判定と `PYTRA_TYPE_ID` 生成経路を専用モジュールに集約した。検証は `python3 -m py_compile src/hooks/cpp/emitter/class_def.py src/hooks/cpp/emitter/cpp_emitter.py`、`python3 -m unittest discover -s test/unit -p 'test_cpp_runtime_type_id.py'`、`python3 -m unittest discover -s test/unit -p 'test_py2cpp_smoke.py'`、`python3 -m unittest discover -s test/unit -p 'test_py2cpp_features.py' -k 'test_class_storage_strategy_case15_case34'`、`python3 tools/check_py2cpp_transpile.py`（`checked=133 ok=133 fail=0 skipped=6`）で実施した。
- 2026-02-26: `P0-CPP-EMITTER-SLIM-01-S3-03` として型変換/Any 境界補正 helper を `src/hooks/cpp/emitter/type_bridge.py`（`CppTypeBridgeEmitter`）へ移設した。`cpp_emitter.py` から `cpp_type` / `_cpp_type_text` / `_build_{box,unbox}_expr_node` / `_build_any_boundary_expr_from_builtin_call` / `_coerce_any_expr_to_target*` / `_coerce_call_arg` / `_coerce_args_by_signature` / `_coerce_args_for_known_function` を除去し、mixin 注入に一本化した。検証は `python3 -m py_compile src/hooks/cpp/emitter/type_bridge.py src/hooks/cpp/emitter/class_def.py src/hooks/cpp/emitter/cpp_emitter.py`、`python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_render_unbox_honors_ctx_for_refclass_cast'`、`python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_builtin_any_boundary_helper_builds_obj_nodes'`、`python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_coerce_args_for_module_function_boxes_any_target_param'`、`python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_emit_stmt_forcore_runtime_protocol_typed_target_uses_unbox_path'`、`python3 tools/check_py2cpp_transpile.py`（`checked=133 ok=133 fail=0 skipped=6`）で実施した。
- 2026-02-26: `P0-CPP-EMITTER-SLIM-01-S3-04` として built-in runtime_call 分岐を `src/hooks/cpp/emitter/builtin_runtime.py`（`CppBuiltinRuntimeEmitter`）へ移設した。`cpp_emitter.py` から `_render_builtin_call` / `_builtin_runtime_owner_node` / `_render_builtin_runtime_{list,set,dict,str,special}_ops` と keyword helper を除去し、list/set/dict/str/path/special ルートを専用ディスパッチ mixin へ集約した。検証は `python3 -m py_compile src/hooks/cpp/emitter/builtin_runtime.py src/hooks/cpp/emitter/cpp_emitter.py src/hooks/cpp/emitter/type_bridge.py src/hooks/cpp/emitter/class_def.py`、`python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_builtin_runtime_list_append_uses_ir_node_path'`、`python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_builtin_runtime_set_add_uses_ir_node_path'`、`python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_builtin_runtime_dict_views_use_ir_node_path'`、`python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_builtin_runtime_dict_get_with_default_uses_ir_node_path'`、`python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_builtin_runtime_path_special_ops_use_ir_node_path'`、`python3 tools/check_py2cpp_transpile.py`（`checked=133 ok=133 fail=0 skipped=6`）で実施した。
- 2026-02-26: `P0-CPP-EMITTER-SLIM-01-S4-01` として `render_expr` 先頭へ `kind -> handler` テーブル（`_render_expr_dispatch_table`）を導入し、`Name/Constant/Attribute/Call/Box/Unbox/CastOrRaise/Obj*/Subscript/JoinedStr/Lambda` の経路をテーブル経由へ切替えた。既存 if 分岐は段階移行前提で温存しつつ、S4-02/S4-03 で分離するための骨格を固定した。検証は `python3 -m py_compile src/hooks/cpp/emitter/cpp_emitter.py src/hooks/cpp/emitter/builtin_runtime.py src/hooks/cpp/emitter/type_bridge.py src/hooks/cpp/emitter/class_def.py`、`python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_builtin_runtime_list_append_uses_ir_node_path'`、`python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_render_expr_supports_str_char_class_ir_node'`、`python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_runtime_py_isinstance_name_call_uses_type_id_core_node_path'`、`python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_call_fallback_rejects_parser_lowered_builtins'`、`python3 tools/check_py2cpp_transpile.py`（`checked=133 ok=133 fail=0 skipped=6`）で実施した。
- 2026-02-26: `P0-CPP-EMITTER-SLIM-01-S4-02` として collection literal/comprehension 系 handler を `src/hooks/cpp/emitter/collection_expr.py`（`CppCollectionExprEmitter`）へ移設し、`render_expr` の `List/Tuple/Set/Dict/ListComp/SetComp/DictComp` 直列分岐を削除した。`_render_expr_dispatch_table` へ該当 kind を追加し、`test/unit/test_east3_cpp_bridge.py` に dispatch 直結の独立テスト（`test_render_expr_dispatch_routes_collection_literal_handlers` / `test_render_expr_dispatch_routes_collection_comprehension_handlers`）を追加した。検証は `python3 -m py_compile src/hooks/cpp/emitter/collection_expr.py src/hooks/cpp/emitter/cpp_emitter.py test/unit/test_east3_cpp_bridge.py`、`python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_render_expr_dispatch_routes_collection_literal_handlers'`、`python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_render_expr_dispatch_routes_collection_comprehension_handlers'`、`python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_builtin_runtime_list_append_uses_ir_node_path'`、`python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_render_expr_supports_str_char_class_ir_node'`、`python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_runtime_py_isinstance_name_call_uses_type_id_core_node_path'`、`python3 tools/check_py2cpp_transpile.py`（`checked=133 ok=133 fail=0 skipped=6`）で実施した。
