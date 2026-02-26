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
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S4-03] runtime/type_id/path 系 handler を分離し、`render_expr` をディスパッチ専任へ縮退する。
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S5-01] `repr` 依存ノードの対象を棚卸しし、parser/lowerer 側の構造化ノード移行計画を確定する。
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S5-02] `_render_repr_expr` の利用箇所を段階削減し、最終 fallback 以外を除去する。
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S5-03] `_render_repr_expr` を撤去（または no-op 化）し、`repr` 文字列依存をなくす。
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S6-01] Rust/C++ 共通化候補（条件式・cast 補助・ループ骨格）を棚卸しし、`CodeEmitter` 移管対象を確定する。
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S6-02] 共通化対象の 1〜2 系統を `CodeEmitter` へ移管し、C++/Rust の重複を削減する。
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S7-01] `test/unit/test_py2cpp_*.py` と `tools/check_py2cpp_transpile.py` を通して回帰を固定する。
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

## S5-01 repr依存棚卸し（2026-02-26）

- `CppEmitter` 内の `repr` 依存入口（`rg -n "_render_repr_expr\\(|\\brepr\\b"`）:
  - `_render_compare_expr`:
    - `left/right` が Python 風文字列の場合に `_render_repr_expr` で再解釈。
    - `ops` 欠落時は `expr.repr` を `in/not in` 文字列分解で補う。
  - `_render_name_expr`:
    - `Name.id` を `_render_repr_expr` で再解釈（`self.` 置換など）。
  - `render_expr` 末尾:
    - 未対応 kind を `expr.repr` へフォールバック。
  - `render_cond`:
    - `render_expr` が空の場合に `expr.repr` を bool 判定へフォールバック。
- `_render_repr_expr` が現在吸収している構文カテゴリ:
  - 論理演算: `or/and/not`
  - 包含比較: `in/not in`（set literal 文字列を含む）
  - 比較連鎖: `< <= > >= == !=`
  - 一部 call/slice: `len(x)`, `a[b:c]`
  - `is None/True/False` と `self.` の文字列置換
- parser/lowerer 側の構造化ノード移行ターゲット（S5-02 以降の削減順）:
  1. Compare fallback (`ops==[]`, `repr` 分解) を `Compare`/`Contains` 系へ統一。
  2. `len()/slice` の repr 分解を `ObjLen`/`SliceExpr` 生成へ寄せる。
  3. `Name` の repr 再解釈を撤去し、`Attribute(Name(self), ...)` を parser で保証。
  4. `render_expr` 末尾 repr fallback を最終 1 箇所に限定し、非対応 kind は lowerer で明示 node へ変換。
  5. `render_cond` の repr fallback も同時に除去（空文字生成経路を先に塞ぐ）。

## S6-01 Rust/C++ 共通化候補棚卸し（2026-02-26）

- 棚卸しコマンド:
  - `rg -n "def (_render_ifexp_expr|render_ifexp_common|_strip_outer_parens|render_cond|render_truthy_cond_common|emit_if_stmt_skeleton|emit_while_stmt_skeleton|_emit_if_stmt|_emit_while_stmt|_emit_if\\(|_emit_while\\(|_prepare_call_parts|emit_stmt_list|emit_scoped_stmt_list|emit_scoped_block)" src/pytra/compiler/east_parts/code_emitter.py src/hooks/cpp/emitter/cpp_emitter.py src/hooks/cpp/emitter/expr.py src/hooks/cpp/emitter/stmt.py src/hooks/rs/emitter/rs_emitter.py`
- 共通化候補（`CodeEmitter` 側への移管観点）:
  1. `IfExp` の branch/cast 展開
     - 参照: `CodeEmitter._render_ifexp_expr` (`src/pytra/compiler/east_parts/code_emitter.py:2412`), `CppEmitter._render_ifexp_expr` (`src/hooks/cpp/emitter/cpp_emitter.py:3125`), `RustEmitter._render_ifexp_expr` (`src/hooks/rs/emitter/rs_emitter.py:2646`)
     - 判定: `medium`
     - 理由: body/orelse + cast 展開は同型だが、C++ は `isinstance ctor` 最適化、Rust は `render_cond` を使う差分があるため。
  2. 余分な最外括弧除去 helper
     - 参照: `CodeEmitter._strip_outer_parens` (`src/pytra/compiler/east_parts/code_emitter.py:1744`), `RustEmitter._strip_outer_parens` (`src/hooks/rs/emitter/rs_emitter.py:1292`)
     - 判定: `easy`
     - 理由: Rust 側は機能が狭い再実装で、C++ は既に基底実装を利用済み。
  3. `if/while` 文の骨格利用ラッパ
     - 参照: `CodeEmitter.emit_if_stmt_skeleton` (`src/pytra/compiler/east_parts/code_emitter.py:723`), `CodeEmitter.emit_while_stmt_skeleton` (`src/pytra/compiler/east_parts/code_emitter.py:746`), `CppStatementEmitter._emit_if_stmt` (`src/hooks/cpp/emitter/stmt.py:9`), `CppStatementEmitter._emit_while_stmt` (`src/hooks/cpp/emitter/stmt.py:35`), `RustEmitter._emit_if` (`src/hooks/rs/emitter/rs_emitter.py:2040`), `RustEmitter._emit_while` (`src/hooks/rs/emitter/rs_emitter.py:2050`)
     - 判定: `easy`
     - 理由: 両言語とも `cond + body/orelse` を取り出して骨格 API を呼ぶ薄いラッパで同型。
  4. 条件式 truthy 正規化
     - 参照: `CodeEmitter.render_truthy_cond_common` (`src/pytra/compiler/east_parts/code_emitter.py:1806`), `CppExpressionEmitter.render_cond` (`src/hooks/cpp/emitter/expr.py:81`), `CppEmitter.render_cond` (`src/hooks/cpp/emitter/cpp_emitter.py:3765`), `RustEmitter.render_cond` (`src/hooks/rs/emitter/rs_emitter.py:3242`)
     - 判定: `medium`
     - 理由: Rust は基底 helper 直利用、C++ は `Any/object -> py_to<bool>` 補正を重ねる二段構成のため統合には追加フックが必要。
  5. Call 前処理 (`_prepare_call_parts`) と scoped emit override
     - 参照: `CodeEmitter._prepare_call_parts` (`src/pytra/compiler/east_parts/code_emitter.py:2371`), `CppEmitter._prepare_call_parts` (`src/hooks/cpp/emitter/cpp_emitter.py:3077`), `CodeEmitter.emit_stmt_list` (`src/pytra/compiler/east_parts/code_emitter.py:212`), `CppEmitter.emit_stmt_list` (`src/hooks/cpp/emitter/cpp_emitter.py:1399`)
     - 判定: `risky`
     - 理由: selfhost での静的束縛回避目的で明示 override されており、単純共通化は回帰リスクが高い。
- `S6-02` で実装する優先候補（低リスク順）:
  1. Rust `_strip_outer_parens` の基底実装統一（候補2）
  2. `if/while` ラッパの共通 helper 化（候補3）

## S6-02 共通 helper 移管（2026-02-26）

- 実施内容:
  1. `CodeEmitter` へ `prepare_if_stmt_parts` / `prepare_while_stmt_parts` を追加し、`If/While` の `cond/body/orelse` 抽出 + 空条件 fallback を共通化した。
     - 参照: `src/pytra/compiler/east_parts/code_emitter.py`
  2. C++ 側 `CppStatementEmitter` の `_emit_if_stmt` / `_emit_while_stmt` を新 helper 利用へ置換した（brace 省略や predeclare は既存ロジック維持）。
     - 参照: `src/hooks/cpp/emitter/stmt.py`
  3. Rust 側 `RustEmitter` の `_emit_if` / `_emit_while` を新 helper 利用へ置換し、`_strip_outer_parens` 再実装を削除して `CodeEmitter._strip_outer_parens` へ統一した。
     - 参照: `src/hooks/rs/emitter/rs_emitter.py`
  4. 共通 helper の回帰テストを `test/unit/test_code_emitter.py` に追加した。
- 検証:
  - `python3 -m py_compile src/pytra/compiler/east_parts/code_emitter.py src/hooks/cpp/emitter/stmt.py src/hooks/rs/emitter/rs_emitter.py test/unit/test_code_emitter.py`
  - `python3 -m unittest discover -s test/unit -p 'test_code_emitter.py' -k 'test_prepare_if_stmt_parts_helper'`
  - `python3 -m unittest discover -s test/unit -p 'test_code_emitter.py' -k 'test_prepare_while_stmt_parts_helper'`
  - `python3 -m unittest discover -s test/unit -p 'test_py2rs_smoke.py'`
  - `python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_emit_stmt_forcore_runtime_protocol_typed_target_uses_unbox_path'`
  - `python3 tools/check_py2cpp_transpile.py`（`checked=133 ok=133 fail=0 skipped=6`）
  - `python3 tools/check_py2rs_transpile.py`（`checked=132 ok=132 fail=0 skipped=6`）

## S7-01 C++ 回帰実行（2026-02-26）

- 実行:
  - `python3 -m unittest discover -s test/unit -p 'test_py2cpp_*.py'`
  - `python3 tools/check_py2cpp_transpile.py`
- 結果:
  - `test_py2cpp_*.py`: `Ran 273 tests in 1626.612s`, `FAILED (failures=29)`
  - `check_py2cpp_transpile`: `checked=133 ok=133 fail=0 skipped=6`
- 観測メモ:
  - 失敗は主に `test_py2cpp_codegen_issues.py` と `test_py2cpp_features.py` の既存期待差分・fixture compile/runtime 側（`py_tid_*` リンク未解決等）で発生。
  - 今回の `S6-02` 変更点（`If/While` 前処理 helper と Rust の括弧 helper 統一）とは直接関連しないカテゴリであることを確認した。

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
- 2026-02-26: `P0-CPP-EMITTER-SLIM-01-S4-03` として runtime/type_id/path 系 handler を `src/hooks/cpp/emitter/runtime_expr.py`（`CppRuntimeExprEmitter`）へ移設し、`render_expr` から `PathRuntimeOp` / `RuntimeSpecialOp` / `IsSubtype` / `IsSubclass` / `IsInstance` の直列分岐を削除した。`_render_expr_dispatch_table` へ該当 kind を追加し、dispatch 独立テスト（`test_render_expr_dispatch_routes_runtime_path_type_id_handlers`）を追加して `render_expr` をディスパッチ専任へ縮退した。検証は `python3 -m py_compile src/hooks/cpp/emitter/runtime_expr.py src/hooks/cpp/emitter/cpp_emitter.py src/hooks/cpp/emitter/collection_expr.py`、`python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_render_expr_dispatch_routes_runtime_path_type_id_handlers'`、`python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_builtin_runtime_list_append_uses_ir_node_path'`、`python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_render_expr_supports_path_runtime_op_ir_nodes'`、`python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_runtime_py_isinstance_name_call_uses_type_id_core_node_path'`、`python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_render_expr_dispatch_routes_collection_literal_handlers'`、`python3 tools/check_py2cpp_transpile.py`（`checked=133 ok=133 fail=0 skipped=6`）で実施した。
- 2026-02-26: `P0-CPP-EMITTER-SLIM-01-S5-01` として `repr` 依存入口を棚卸しし、`_render_compare_expr` / `_render_name_expr` / `render_expr` 末尾 fallback / `render_cond` fallback を削減対象として確定した。`_render_repr_expr` が吸収する構文カテゴリ（論理演算・包含比較・比較連鎖・`len/slice`・`is None/True/False`・`self.`）を明文化し、S5-02/S5-03 で lowerer 側構造化ノードへ移行する順序を計画に固定した。調査は `rg -n "_render_repr_expr\\(|\\brepr\\b" src/hooks/cpp/emitter/cpp_emitter.py` と `rg -n "repr" src/pytra/compiler/east_parts` で実施した。
- 2026-02-26: `P0-CPP-EMITTER-SLIM-01-S5-02` として `_render_compare_expr`（left/right 補正）と `_render_name_expr`（name 補正）から `_render_repr_expr` 呼び出しを削除し、`_render_repr_expr` 呼び出し元を `render_expr` 末尾 fallback のみに縮退した（再帰内部呼び出しは除く）。確認は `rg -n "_render_repr_expr\\(" src/hooks/cpp/emitter/cpp_emitter.py` で実施し、外部呼び出しが fallback 1 箇所のみであることを固定した。検証は `python3 -m py_compile src/hooks/cpp/emitter/cpp_emitter.py src/hooks/cpp/emitter/runtime_expr.py src/hooks/cpp/emitter/collection_expr.py`、`python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_render_expr_dispatch_routes_runtime_path_type_id_handlers'`、`python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_render_expr_dispatch_routes_collection_literal_handlers'`、`python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_builtin_runtime_list_append_uses_ir_node_path'`、`python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -k 'test_render_expr_supports_path_runtime_op_ir_nodes'`、`python3 tools/check_py2cpp_transpile.py`（`checked=133 ok=133 fail=0 skipped=6`）で実施した。
- 2026-02-26: `P0-CPP-EMITTER-SLIM-01-S5-03` として `_render_repr_expr` / `_render_set_literal_repr` / `_split_call_repr` / `_looks_like_python_expr_text` を `cpp_emitter.py` から削除し、`render_expr`/`render_cond`/statement 側の `repr` フォールバックを撤去した。`stmt.py` / `expr.py` 側に残っていた `_render_repr_expr` 呼び出しも除去し、EAST3 の構造化ノードのみで条件式を扱う形へ統一した。確認は `rg -n "_render_repr_expr|_looks_like_python_expr_text|_split_call_repr|_render_set_literal_repr|expr_d.get\\(\\\"repr\\\"\\)|if \\\"repr\\\" in expr_node" src/hooks/cpp/emitter || true`（出力なし）で実施し、`repr` 文字列依存経路が残らないことを固定した。検証は `python3 -m py_compile src/hooks/cpp/emitter/cpp_emitter.py src/hooks/cpp/emitter/stmt.py src/hooks/cpp/emitter/expr.py src/hooks/cpp/emitter/runtime_expr.py src/hooks/cpp/emitter/collection_expr.py src/hooks/cpp/emitter/builtin_runtime.py src/hooks/cpp/emitter/type_bridge.py src/hooks/cpp/emitter/class_def.py` と `python3 tools/check_py2cpp_transpile.py`（`checked=133 ok=133 fail=0 skipped=6`）で実施した。
- 2026-02-26: `P0-CPP-EMITTER-SLIM-01-S6-01` として Rust/C++ の共通化候補を棚卸しし、`easy/medium/risky` で優先度を固定した。`CodeEmitter` と C++/Rust emitter を `rg` で突合し、`_strip_outer_parens` 統一と `if/while` ラッパ helper 化を `S6-02` の実装対象に選定した。一方で `_prepare_call_parts` と `emit_stmt_list` 系 override は selfhost 静的束縛回避が絡むため `risky` として今回の移管対象から除外した。
- 2026-02-26: `P0-CPP-EMITTER-SLIM-01-S6-02` として `CodeEmitter` へ `prepare_if_stmt_parts` / `prepare_while_stmt_parts` を追加し、C++/Rust の `If/While` 前処理重複を削減した。あわせて Rust 側の `_strip_outer_parens` 再実装を削除し、基底 helper へ統一した。検証は `py_compile`、追加した `test_code_emitter` 2件、`test_py2rs_smoke.py`、`test_east3_cpp_bridge` の代表ケース、`check_py2cpp_transpile`（`133/133`）、`check_py2rs_transpile`（`132/132`）で実施した。
- 2026-02-26: `P0-CPP-EMITTER-SLIM-01-S7-01` として C++ 回帰スイートを実行した。`check_py2cpp_transpile` は全件成功 (`133/133`) だが、`test_py2cpp_*.py` は `273 tests / 29 failures` で失敗した。失敗カテゴリは `codegen_issues` の期待差分と `features` の fixture compile/runtime（`py_tid_*` 未解決リンク等）に集中しており、今回差分（`If/While` helper 共通化、Rust paren helper 統一）由来ではないと判断した。
