# TASK GROUP: TG-P0-EAST123

最終更新: 2026-02-23

関連 TODO:
- `docs-jp/todo.md` の `ID: P0-EAST123-*`

背景:
- 単一 EAST + backend hooks 運用では、意味論 lowering が backend 側へ漏れやすく、hooks が肥大化する。
- `Any/object` 境界、`dispatch mode`、iterable 契約の責務境界を backend 非依存で固定する必要がある。
- `docs-jp/spec/spec-east123.md` に三段構成（EAST1/EAST2/EAST3）の設計ドラフトを追加済みであり、これを実装計画へ落とし込む段階に入った。

目的:
- `spec-east123` を最優先仕様として実装へ接続し、EAST3 を意味論の単一正本にする。
- `EAST2 -> EAST3` で `--object-dispatch-mode` を一括適用し、後段再判断を禁止する。
- hooks を「構文差分の最終調整」に限定し、意味論実装を core lowering 側へ回収する。

対象:
- EAST ルートスキーマ（`east_stage`, `schema_version`, `meta.dispatch_mode`）の導入
- 現行 `EAST2`（`EAST1 + EAST2` 混在）の段階分離（`EAST1`: parser 直後、`EAST2`: normalize 専任）
- `ForCore` / `RuntimeIterForPlan` / `Any/object` 境界命令の段階導入
- `type_id` 関連 lower を EAST3 命令化し、backend 側は命令写像に限定する
- `type_id` 以外の言語非依存意味論（boxing/unboxing, iterable, truthy/len/str, 主要 built-in lower）も EAST3 命令化へ段階移行する
- backend の意味論再解釈禁止（hooks 責務境界の明確化）
- hooks 縮退の定量管理（意味論 hook の撤去数、構文差分 hook の残存数）
- schema/例外契約/回帰テストの整備

非対象:
- 全ノード一括置換
- 新規最適化器の全面導入
- 既存 backend の全面 rewrite

受け入れ基準:
1. `docs-jp/spec/spec-east123.md` の契約（stage/scheme/dispatch 固定点）と実装仕様の差分が解消されている。
2. `EAST3.meta.dispatch_mode` と `RuntimeIterForPlan.dispatch_mode` が導入され、後段で mode 再判定しない。
3. hooks での意味論変更（dispatch 再判断、boxing/iterable 再実装）が段階的に撤去される。
4. `EAST3` 契約を unit/codegen/selfhost 回帰で検証できる。
5. hooks の責務が「構文差分のみ」に収束し、意味論 hook の残存箇所が一覧化・縮退管理されている。
6. `EAST1` と `EAST2` の責務が分離され、`EAST1` から normalize なしの parser 出力を取得できる。
7. `type_id` 判定 lower は EAST3 経由へ統一され、backend での C++ 直書き判定生成が原則なくなる。
8. `type_id` 以外の言語非依存意味論でも、backend/hook 側の直接実装が段階的に縮退し、EAST3 命令写像へ集約される。

確認コマンド（最低）:
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/check_py2js_transpile.py`
- `python3 tools/check_py2ts_transpile.py`
- `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`

サブタスク実行順（todo 同期）:
1. `P0-EAST123-01-S1`: ルートスキーマ（`east_stage`, `schema_version`, `meta.dispatch_mode`）の仕様統一。
2. `P0-EAST123-01-S2`: `dispatch mode` 適用点と後段再判断禁止の仕様固定。
3. `P0-EAST123-01-S3`: `spec-east` / `spec-type_id` / `spec-boxing` / `spec-iterable` / `spec-dev` の整合調整。
4. `P0-EAST123-01-S4`: `spec-east123` を上位仕様、`spec-linker` を下位仕様として確定し、参照順を明文化。
5. `P0-EAST123-02-S1`: `For` / `ForRange` の `ForCore + iter_plan` lower 実装。
6. `P0-EAST123-02-S2`: `Any/object` 境界命令の EAST3 lower 実装。
7. `P0-EAST123-02-S3`: `--object-dispatch-mode` の単一点適用実装。
8. `P0-EAST123-06-S1`: parser 直後 `EAST1` 出力 API 追加。
9. `P0-EAST123-06-S2`: `EAST1 -> EAST2` normalize pass 分離 + `load_east(...)` 互換維持。
10. `P0-EAST123-07-S1`: `type_id` 判定（`isinstance` / `issubclass` / subtype）の EAST3 命令化。
11. `P0-EAST123-07-S2`: backend 側 `type_id` 直書き判定生成の撤去（runtime API 写像へ統一）。
12. `P0-EAST123-08-S1`: IR-first 移行対象（boxing/unboxing, iterable, truthy/len/str, built-in lower）の優先度確定。
13. `P0-EAST123-08-S2`: 第1陣（boxing/unboxing, iterable, truthy/len/str）の EAST3 移行。
14. `P0-EAST123-08-S3`: 第2陣（主要 built-in lower）の EAST3 移行。
15. `P0-EAST123-03-S1`: C++ hooks / `py2cpp.py` の意味論実装経路棚卸し。
16. `P0-EAST123-03-S2-S1`: CppEmitter 側で EAST3 命令ノード受理（`ForCore`, `Box/Unbox`, `Obj*`）を追加。
17. `P0-EAST123-03-S2-S2`: `For` / `iter_mode` / Any 境界の backend 再判断を EAST3 命令入力へ置換。
18. `P0-EAST123-03-S2-S3`: `py2cpp.py` と `hooks/cpp` の `runtime_call` / built-in 分岐重複を撤去。
19. `P0-EAST123-05-S1`: hooks 分類と縮退メトリクス基線を確定。
20. `P0-EAST123-05-S2`: 意味論 hook 新規流入を防ぐ CI ルール追加。
21. `P0-EAST123-04-S1`: schema テスト整備（必須項目、`iter_plan` 形状、`dispatch_mode`）。
22. `P0-EAST123-04-S2`: lowering 契約テスト（`EAST2 -> EAST3`）整備。
23. `P0-EAST123-04-S3`: selfhost + クロスターゲット回帰導線へ統合。

## P0-EAST123-08-S1 IR-first 移行順（確定）

目的:
- `type_id` 以外の言語非依存意味論を、backend/hook 実装から `EAST3` 命令へ順次移す実行順を固定する。

移行優先度（高 -> 低）:
1. `truthy/len/str`（`ObjBool` / `ObjLen` / `ObjStr`）
   - 理由: 分岐条件・ループ条件・標準ライブラリでの使用頻度が高く、誤差分が全体挙動へ波及しやすい。
   - 完了条件: backend 側の bool/len/str 判定分岐が `EAST3` 命令写像のみに収束する。
2. `iterable`（`ObjIterInit` / `ObjIterNext` + `ForCore.iter_plan`）
   - 理由: `for` 系の再判断が backend 側へ残りやすく、hooks 肥大化の主因になっている。
   - 完了条件: `iter_mode`/`iter_plan` の意味論再判断を backend/hook で行わない。
3. `boxing/unboxing`（`Box` / `Unbox` / `CastOrRaise`）
   - 理由: 代入・引数・戻り値の境界処理が広範囲に分散しており、段階導入の影響面が大きい。
   - 完了条件: Any 境界の注入/解除ロジックが `EAST3` 命令入力へ統一される。
4. 主要 built-in lower（list/set/dict/str/special）
   - 理由: API 数が多く差分面積が大きいため、前段の境界命令が安定してから移行する。
   - 完了条件: `runtime_call` 直分岐の新規追加を停止し、既存分岐を EAST3 命令写像へ段階置換する。

分割実行規約:
- `P0-EAST123-08-S2`: 上記 1〜3（truthy/len/str + iterable + boxing/unboxing）を第1陣として実装する。
- `P0-EAST123-08-S3`: 上記 4（主要 built-in lower）を第2陣として実装する。
- `P0-EAST123-08-S3-S1`: `list/set` 系 built-in lower を IR-first へ移行する。
- `P0-EAST123-08-S3-S2`: `dict` 系 built-in lower を IR-first へ移行する。
- `P0-EAST123-08-S3-S3`: `str/special` 系 built-in lower を IR-first へ移行する。
- `P0-EAST123-08-S3-S4`: backend 直分岐を整理し、EAST3 命令写像 + 構文差分 hook のみに収束させる。

## P0-EAST123-03-S1 棚卸し（C++ hooks / py2cpp）

目的:
- `dispatch/boxing/iterable/built-in` の意味論実装がどこに残っているかを列挙し、`P0-EAST123-03-S2` の撤去対象を固定する。

### dispatch（type_id / isinstance）

- `src/py2cpp.py:3500` `_render_isinstance_name_call`
- `src/py2cpp.py:3528` `_render_isinstance_type_check`
- `src/py2cpp.py:3702` `Call(Name="isinstance")` の直接分岐
- `src/py2cpp.py:4061` `render_call_expr` 系の `isinstance` 補助分岐

現状:
- `type_id` 判定式生成が `py2cpp.py` に直書きされている（`PYTRA_TID_*`, `Class::PYTRA_TYPE_ID`）。

### boxing / unboxing（Any 境界）

- `src/py2cpp.py:722` `_coerce_py_assert_args`（`make_object(...)` 注入）
- `src/py2cpp.py:1504` `_box_expr_if_needed`
- `src/py2cpp.py:1726`, `src/py2cpp.py:2354`, `src/py2cpp.py:2380` 代入系での `make_object(...)`
- `src/py2cpp.py:3823`, `src/py2cpp.py:3921`, `src/py2cpp.py:4370` 呼び出し/式評価時の boxing
- `src/hooks/cpp/hooks/cpp_hooks.py:207`, `src/hooks/cpp/hooks/cpp_hooks.py:214`, `src/hooks/cpp/hooks/cpp_hooks.py:237` dict 系 default での `make_object(...)`

現状:
- Any 境界の boxing 判断が emitter/hooks の両方に分散している。

### iterable（for / runtime protocol）

- `src/py2cpp.py:2700` `_resolve_for_iter_mode`（`static_fastpath/runtime_protocol` 決定）
- `src/py2cpp.py:2742` `_emit_for_each_runtime`（`py_dyn_range(...)`）
- `src/py2cpp.py:2723` `_emit_target_unpack_runtime`（`py_at(...)`）
- `src/py2cpp.py:2611` `_emit_for_each`（通常 for / range 系）

現状:
- iterable 意味論（mode 決定、runtime 反復、unpack）が backend 側で決定・実装されている。

### built-in lower（runtime_call 分岐）

- `src/py2cpp.py` `_render_builtin_call`
- `src/py2cpp.py` `_render_builtin_runtime_list_ops`
- `src/py2cpp.py` `_render_builtin_runtime_set_ops`
- `src/py2cpp.py` `_render_builtin_runtime_dict_ops`
- `src/py2cpp.py` `_render_builtin_runtime_str_ops`
- `src/py2cpp.py` `_render_builtin_runtime_special_ops`
- `src/py2cpp.py` `_render_builtin_runtime_fallback`
- `src/hooks/cpp/hooks/cpp_hooks.py` `on_render_call`（no-op）

現状:
- `runtime_call` / built-in 分岐は `py2cpp.py` 側へ集約し、`hooks/cpp` の `on_render_call` は構文差分専任の no-op へ縮退した。

`P0-EAST123-03-S2` での置換方針（本棚卸しからの確定）:
- 上記カテゴリを `EAST3` 命令写像へ段階移行し、hooks は構文差分専任へ縮退する。

## P0-EAST123-05-S1 hooks 分類・基線（2026-02-23）

実行コマンド:
- `python3 tools/check_cpp_hooks_semantic_budget.py`

計測結果:
- `total=11`
- `semantic=4`（`on_for_range_mode`, `on_render_binop`, `on_render_expr_kind`, `on_render_object_method`）
- `syntax=6`（`on_emit_stmt_kind`, `on_render_class_method`, `on_render_expr_complex`, `on_render_expr_leaf`, `on_render_module_method`, `on_stmt_omit_braces`）
- `noop=1`（`on_render_call`）
- `unknown=0`

記録方針:
- `tools/check_cpp_hooks_semantic_budget.py` を基線計測コマンドとして扱う。
- 次段 (`P0-EAST123-05-S2`) でこの基線を上限とする流入防止チェックを追加する。

決定ログ:
- 2026-02-23: 初版作成。`docs-jp/spec/spec-east123.md` を最優先事項として `todo` の `P0` へ昇格し、実装導入の作業枠を定義した。
- 2026-02-23: `EAST3` 導入効果を明示するため、`ID: P0-EAST123-05`（hooks 縮退の定量管理）を TODO/plan に追加した。
- 2026-02-23: 現行 `EAST2` が `EAST1 + EAST2` 相当である課題を反映し、`ID: P0-EAST123-06`（EAST1/EAST2 分離）を TODO/plan に追加した。
- 2026-02-23: `type_id` 関連 lower を backend 直書きではなく EAST3 命令化へ統一する方針を反映し、`ID: P0-EAST123-07` を TODO/plan に追加した。
- 2026-02-23: `type_id` に限らず IR-first を徹底するため、`ID: P0-EAST123-08`（言語非依存意味論の EAST3 命令化と C++ hooks 縮退）を TODO/plan に追加した。
- 2026-02-23: 実行単位を小さく保つため、`P0-EAST123-01-S1` を起点に `-S1/-S2/...` 形式で約20サブタスクへ再分割した。
- 2026-02-23: `spec-east123` を上位仕様、`spec-linker` を下位仕様として扱う順序を `P0-EAST123-01-S4` として TODO/plan へ追加した。
- 2026-02-23: [ID: P0-EAST123-01-S4] `spec-east123` と `spec-linker` に仕様優先順位（`east123` 上位 / `linker` 下位）を明記した。
- 2026-02-23: `P0-EAST123-01-S1` / `P0-EAST123-01-S2` / `P0-EAST123-01-S3` として、`spec-east123` のルート契約（`east_stage`/`schema_version`/`meta.dispatch_mode`）、dispatch mode 単一点適用（`EAST2 -> EAST3`）、および `spec-east`/`spec-dev`/`spec-type_id`/`spec-boxing`/`spec-iterable` の参照整合を同期した。
- 2026-02-23: [ID: P0-EAST123-02-S1] `src/pytra/compiler/east_parts/east3_lowering.py` に最小 `EAST2 -> EAST3` pass を追加し、`For` / `ForRange` を `ForCore + iter_plan`（`RuntimeIterForPlan` / `StaticRangeForPlan`）へ lower する契約を `test/unit/test_east3_lowering.py` で固定した。
- 2026-02-23: [ID: P0-EAST123-02-S2] `east3_lowering` で `Any/object` 境界命令 lower（`Box`/`Unbox`/`ObjBool`/`ObjLen`/`ObjStr`/`ObjIterInit`/`ObjIterNext`）を追加し、`test/unit/test_east3_lowering.py` に境界命令化テストを拡張した。
- 2026-02-23: [ID: P0-EAST123-02-S3] `lower_east2_to_east3(..., object_dispatch_mode=...)` と `load_east3_document(..., object_dispatch_mode=...)` を追加し、dispatch mode を `EAST2 -> EAST3` エントリで一度だけ確定して `EAST3.meta.dispatch_mode` と `RuntimeIterForPlan.dispatch_mode` へ反映するテストを追加した。
- 2026-02-23: [ID: P0-EAST123-03-S1] `py2cpp.py` と `hooks/cpp` の意味論実装経路（dispatch/boxing/iterable/built-in）を棚卸しし、`P0-EAST123-03-S2` の置換対象として固定した。
- 2026-02-23: [ID: P0-EAST123-03-S2-S1] `py2cpp.py` に `ForCore` / `Box` / `Unbox` / `Obj*` 受理を追加し、`test/unit/test_east3_cpp_bridge.py` で C++ 写像と `ForCore` のシンボル収集（`transpile_cli` 側）を固定した。
- 2026-02-23: [ID: P0-EAST123-03-S2-S2] `py2cpp` に `--east-stage {2,3}` / `--object-dispatch-mode` を追加し、`load_east(..., east_stage=\"3\")` で `EAST2 -> EAST3` を通す経路を導入して `ForCore` / Any 境界を backend 再判断なしで受理できるようにした。
- 2026-02-23: [ID: P0-EAST123-03-S2-S3] `runtime_call` / built-in の list/set/dict/str/special 分岐を `py2cpp.py` へ移管し、`hooks/cpp` の `on_render_call` は no-op 化した。`test_cpp_hooks.py` / `test_py2cpp_codegen_issues.py` / `test_east3_cpp_bridge.py` で回帰確認済み。
- 2026-02-23: [ID: P0-EAST123-04-S1] `test/unit/test_east3_lowering.py` に schema 契約テストを追加し、`EAST3` ルート必須項目、`ForCore.iter_plan` 形状（`RuntimeIterForPlan` / `StaticRangeForPlan`）、および `meta.dispatch_mode` と runtime plan の一貫性を固定した。
- 2026-02-23: [ID: P0-EAST123-04-S2] `test/unit/test_east3_lowering.py` に lowering 契約テストを追加し、`For -> ForCore` の `iter_mode` 正規化、non-Any builtin call 非変換、同型代入での Box/Unbox 非挿入を固定した。
- 2026-02-23: [ID: P0-EAST123-04-S3] `check_selfhost_cpp_diff.py` / `check_py2js_transpile.py` / `check_py2ts_transpile.py` に EAST3 契約テストの preflight（`test_east3_lowering.py`, `test_east3_cpp_bridge.py`）を組み込み、`run_local_ci.py` に JS/TS クロスターゲットチェックを追加した。
- 2026-02-23: [ID: P0-EAST123-05-S1] `tools/check_cpp_hooks_semantic_budget.py` を追加し、C++ hooks の semantic/syntax/no-op 分類と基線メトリクス（`total=11`, `semantic=4`, `syntax=6`, `noop=1`, `unknown=0`）を記録した。
- 2026-02-23: [ID: P0-EAST123-05-S2] `run_local_ci.py` に `tools/check_cpp_hooks_semantic_budget.py --max-semantic 4` を追加し、semantic hook の新規流入を失敗扱いにするチェック導線を常時実行化した。
- 2026-02-23: [ID: P0-EAST123-06-S1] `load_east1_document(...)` を `transpile_cli` に追加し、既存のエラー分類/ルート契約を維持したまま `east_stage=1` を返す parser 直後 API を導入した。`test_py2cpp_features.py` に helper 契約テストを追加し、`prepare_selfhost_source` の import 行除去を prefix 判定へ更新して回帰を解消した。
- 2026-02-23: [ID: P0-EAST123-06-S2] `normalize_east1_to_east2_document(...)` を `transpile_cli` に追加し、`load_east_document(...)` で `EAST1 -> EAST2` 正規化（stage `1 -> 2`）を通す構成へ分離した。`load_east_document` の既存呼び出し互換を維持するため、stage1 JSON 入力の正規化を `test_py2cpp_features.py` で固定した。
- 2026-02-24: [ID: P0-EAST123-07-S1] `EAST2 -> EAST3` lowering に `ObjTypeId` / `IsInstance` / `IsSubclass` / `IsSubtype` を追加し、`isinstance` / `issubclass` / `py_*subtype` 系 call を EAST3 命令へ正規化した。`py2cpp` で新命令を runtime API（`py_runtime_type_id`, `py_isinstance`, `py_issubclass`, `py_is_subtype`）へ写像し、`test_east3_lowering.py` / `test_east3_cpp_bridge.py` / `test_py2cpp_codegen_issues.py` で回帰確認した。
- 2026-02-24: [ID: P0-EAST123-07-S2] `Call(Name=...)` の `isinstance`/`issubclass`/`py_*type_id` 分岐で EAST3 型判定ノード（`IsInstance`/`IsSubclass`/`IsSubtype`/`ObjTypeId`）を構築して `render_expr` 経由へ統一し、backend の直接判定文字列組み立て経路を縮退した。`_render_repr_expr` の `isinstance` も `py_isinstance + type_id` 経路へ更新し、`test_py2cpp_codegen_issues.py` / `test_east3_cpp_bridge.py` / `test_east3_lowering.py` / `tools/check_py2cpp_transpile.py` で回帰確認した。
- 2026-02-24: [ID: P0-EAST123-08-S1] `type_id` 以外の IR-first 移行順を確定し、優先度を `truthy/len/str -> iterable -> boxing/unboxing -> 主要 built-in` と定義した。実装段は `P0-EAST123-08-S2`（第1陣: 1〜3）/`P0-EAST123-08-S3`（第2陣: 4）に固定した。
- 2026-02-24: [ID: P0-EAST123-08-S2] 第1陣の初回パッチとして、stage2 の `Call(Name=bool/len/str/iter/next)`（Any/object 引数）を EAST3 境界ノード（`ObjBool`/`ObjLen`/`ObjStr`/`ObjIterInit`/`ObjIterNext`）へ寄せ、`render_expr` の命令写像経路へ統一した。`test_py2cpp_codegen_issues.py`（新規ケース追加）/`test_east3_cpp_bridge.py`/`test_east3_lowering.py`/`tools/check_py2cpp_transpile.py` で回帰確認した。
- 2026-02-24: [ID: P0-EAST123-08-S2] 第1陣の2パッチ目として、`_render_builtin_call`（`BuiltinCall/runtime_call` 経路）の Any/object 境界も `Obj*` 命令（`ObjBool`/`ObjLen`/`ObjStr`/`ObjIterInit`/`ObjIterNext`）へ集約した。`test_east3_cpp_bridge.py` に helper 契約テストを追加し、`test_py2cpp_codegen_issues.py` / `test_east3_lowering.py` / `tools/check_py2cpp_transpile.py` で回帰確認した。
- 2026-02-24: [ID: P0-EAST123-08-S2] 第1陣の3パッチ目として、`_coerce_call_arg` の Any 境界を `Box/Unbox` ノード構築 + `render_expr` 経路へ寄せ、call-arg の boxing/unboxing 直組み立てを縮退した。`Unbox.ctx` を導入して既存エラーメッセージ文脈（`call_arg:*`）互換を維持し、`test_east3_cpp_bridge.py` / `test_py2cpp_codegen_issues.py` / `test_east3_lowering.py` / `tools/check_py2cpp_transpile.py` で回帰確認した。
- 2026-02-24: [ID: P0-EAST123-08-S2] 第1陣の4パッチ目として、`_emit_for_each_runtime` / `_emit_target_unpack_runtime` の object->typed 変換を `Unbox` ノード経由へ移し、runtime iterable 経路の型変換直実装を縮退した。`test_east3_cpp_bridge.py` に `For(iter_mode=runtime_protocol)` の typed target 回帰を追加し、`test_py2cpp_codegen_issues.py` / `test_east3_lowering.py` / `tools/check_py2cpp_transpile.py` で回帰確認した。
- 2026-02-24: [ID: P0-EAST123-08-S2] 第1陣の5パッチ目として、`AnnAssign` / `Assign` の Any ターゲット代入 boxing を `Box` ノード経由（`_box_any_target_value`）へ寄せ、`None -> object{}` と既存 `make_object(...)` 互換を維持した。`test_east3_cpp_bridge.py` に helper 回帰（plain/Any/None）を追加し、`test_py2cpp_codegen_issues.py` / `test_east3_lowering.py` / `tools/check_py2cpp_transpile.py` / `tools/check_selfhost_cpp_diff.py --mode allow-not-implemented` で確認した（selfhost 差分は既知3件で増加なし）。
- 2026-02-24: [ID: P0-EAST123-08-S2] 第1陣の6パッチ目として、`_coerce_args_for_module_function` / `_coerce_py_assert_args` / `_coerce_dict_key_expr` / `dict.get(default)` の Any 境界 boxing を `Box` ノード経由へ寄せた。`test_east3_cpp_bridge.py` に module 引数・dict[Any,*] key の回帰を追加し、`test_py2cpp_codegen_issues.py` / `test_east3_lowering.py` / `tools/check_py2cpp_transpile.py` / `tools/check_selfhost_cpp_diff.py --mode allow-not-implemented` で確認した（selfhost 差分は既知3件維持）。
- 2026-02-24: [ID: P0-EAST123-08-S2] 第1陣の7パッチ目として、`list.append`（`list[Any]`）と `list/set comprehension` の Any boxing を `Box` ノード経由（`_render_append_call_object_method`, `_box_any_target_value`）へ寄せた。`test_east3_cpp_bridge.py` に `list[Any].append` 回帰を追加し、`test_py2cpp_codegen_issues.py` / `test_east3_lowering.py` / `tools/check_py2cpp_transpile.py` / `tools/check_selfhost_cpp_diff.py --mode allow-not-implemented` で確認した（selfhost 差分は既知3件維持）。
- 2026-02-24: [ID: P0-EAST123-08-S2] 第1陣の8パッチ目として、`render_cond` の Any/object 条件判定を `ObjBool` 命令経路へ統一し、`if/while` の truthy 評価を backend 直書きから IR-first 写像へ寄せた。`test_east3_cpp_bridge.py` に `render_cond(Any)` 回帰を追加し、`test_py2cpp_codegen_issues.py` / `test_east3_lowering.py` / `tools/check_py2cpp_transpile.py` / `tools/check_selfhost_cpp_diff.py --mode allow-not-implemented` で確認した（selfhost 差分は既知3件維持）。
- 2026-02-24: [ID: P0-EAST123-08-S2] 第1陣（boxing/unboxing, iterable, truthy/len/str）の移行が完了したため、`docs-jp/todo.md` 側で `P0-EAST123-08-S2` を完了済みに更新した。
- 2026-02-24: [ID: P0-EAST123-08-S3] 第2陣（主要 built-in lower）の着手単位を `S3-S1..S3-S4` へ分割し、`list/set -> dict -> str/special -> backend分岐整理` の順で実装する方針を固定した。
- 2026-02-24: [ID: P0-EAST123-08-S3-S1] `list.append` の BuiltinCall lower に `ListAppend` IR ノード経路を追加し、`render_expr` 側で `list[Any]` の boxing を含む append 生成を命令写像として受理した。`test_east3_cpp_bridge.py` に `ListAppend` ノード単体と BuiltinCall 経路の回帰を追加し、`tools/check_py2cpp_transpile.py` / `tools/check_selfhost_cpp_diff.py --mode allow-not-implemented` で確認した（selfhost 差分は既知3件維持）。
- 2026-02-24: [ID: P0-EAST123-08-S3-S1] `list.extend` の BuiltinCall lower に `ListExtend` IR ノード経路を追加し、`render_expr` で `xs.insert(xs.end(), ys.begin(), ys.end())` へ写像する命令経路を受理した。`test_east3_cpp_bridge.py` に `ListExtend` ノード単体と BuiltinCall 経路の回帰を追加し、`tools/check_py2cpp_transpile.py` / `tools/check_selfhost_cpp_diff.py --mode allow-not-implemented` で確認した（selfhost 差分は既知3件維持）。
- 2026-02-24: [ID: P0-EAST123-08-S3-S1] `set.add` の BuiltinCall lower に `SetAdd` IR ノード経路を追加し、`render_expr` 側で `set.insert(value)` へ写像する命令経路を受理した。`test_east3_cpp_bridge.py` に `SetAdd` ノード単体と BuiltinCall 経路の回帰を追加し、`tools/check_py2cpp_transpile.py` / `tools/check_selfhost_cpp_diff.py --mode allow-not-implemented` で確認した（selfhost 差分は既知3件維持）。
- 2026-02-24: [ID: P0-EAST123-08-S3-S1] `list.pop` / `list.clear` の BuiltinCall lower に `ListPop` / `ListClear` IR ノード経路を追加し、`render_expr` 側で no-index pop と clear を命令写像として受理した。`test_east3_cpp_bridge.py` にノード単体と BuiltinCall 経路の回帰を追加し、`tools/check_py2cpp_transpile.py` / `tools/check_selfhost_cpp_diff.py --mode allow-not-implemented` で確認した（selfhost 差分は既知3件維持）。
- 2026-02-24: [ID: P0-EAST123-08-S3-S1] `set.remove/discard` / `set.clear` の BuiltinCall lower に `SetErase` / `SetClear` IR ノード経路を追加し、`render_expr` 側で erase/clear を命令写像として受理した。`test_east3_cpp_bridge.py` にノード単体と BuiltinCall 経路の回帰を追加し、`tools/check_py2cpp_transpile.py` / `tools/check_selfhost_cpp_diff.py --mode allow-not-implemented` で確認した（selfhost 差分は既知3件維持）。
- 2026-02-24: [ID: P0-EAST123-08-S3-S1] `list.reverse` / `list.sort` の BuiltinCall lower に `ListReverse` / `ListSort` IR ノード経路を追加し、`render_expr` 側で `std::reverse/sort` へ写像する命令経路を受理した。`test_east3_cpp_bridge.py` にノード単体と BuiltinCall 経路の回帰を追加し、`tools/check_py2cpp_transpile.py` / `tools/check_selfhost_cpp_diff.py --mode allow-not-implemented` で確認した（selfhost 差分は既知3件維持）。
- 2026-02-24: [ID: P0-EAST123-08-S3-S1] 現行 `runtime_call` 契約（list: append/extend/pop/clear/reverse/sort, set: add/discard/remove/clear）は IR ノード経路へ移行完了とし、`docs-jp/todo.md` 側で `P0-EAST123-08-S3-S1` を完了済みに更新した。
- 2026-02-24: [ID: P0-EAST123-08-S3-S2] `dict.items` / `dict.keys` / `dict.values` の BuiltinCall lower に `DictItems` / `DictKeys` / `DictValues` IR ノード経路を追加し、`render_expr` 側で dict view 系写像を命令経路として受理した。`test_east3_cpp_bridge.py` にノード単体と BuiltinCall 経路の回帰を追加し、`tools/check_py2cpp_transpile.py` / `tools/check_selfhost_cpp_diff.py --mode allow-not-implemented` で確認した（selfhost 差分は既知3件維持）。
- 2026-02-24: [ID: P0-EAST123-08-S3-S2] `dict.pop` の default なし経路を `DictPop` IR ノードへ移行し、`render_expr` 側で key 型整形（`_coerce_dict_key_expr`）込みの `pop` 写像を受理した。`test_east3_cpp_bridge.py` にノード単体と BuiltinCall 経路の回帰を追加し、`tools/check_py2cpp_transpile.py` / `tools/check_selfhost_cpp_diff.py --mode allow-not-implemented` で確認した（selfhost 差分は既知3件維持）。
- 2026-02-24: [ID: P0-EAST123-08-S3-S2] `dict.get` の default なし経路を `DictGetMaybe` IR ノードへ移行し、`render_expr` 側で key 型整形（`_coerce_dict_key_expr`）込みの `py_dict_get_maybe` 写像を受理した。`test_east3_cpp_bridge.py` にノード単体と BuiltinCall 経路の回帰を追加し、`tools/check_py2cpp_transpile.py` / `tools/check_selfhost_cpp_diff.py --mode allow-not-implemented` で確認した（selfhost 差分は既知3件維持）。
- 2026-02-24: [ID: P0-EAST123-08-S3-S2] `dict.get` の default あり経路を `DictGetDefault` IR ノードへ移行し、`render_expr` 側で objectish 判定・key 型整形・default の nullopt 補正を含む既存写像を受理した。`test_east3_cpp_bridge.py` にノード単体と BuiltinCall 経路の回帰を追加し、`tools/check_py2cpp_transpile.py` / `tools/check_selfhost_cpp_diff.py --mode allow-not-implemented` で確認した（selfhost 差分は既知3件維持）。
- 2026-02-24: [ID: P0-EAST123-08-S3-S2] `dict.pop` の default あり経路を `DictPopDefault` IR ノードへ移行し、`render_expr` 側で key 型整形（`_coerce_dict_key_expr`）と default nullopt 補正を含む既存写像を受理した。`test_east3_cpp_bridge.py` にノード単体と BuiltinCall 経路の回帰を追加し、`tools/check_py2cpp_transpile.py` / `tools/check_selfhost_cpp_diff.py --mode allow-not-implemented` で確認した（selfhost 差分は既知3件維持）。
- 2026-02-24: [ID: P0-EAST123-08-S3-S2] 現行 `dict` runtime_call 契約（`get/pop/items/keys/values`）の IR ノード経路移行が完了したため、`docs-jp/todo.md` 側で `P0-EAST123-08-S3-S2` を完了済みに更新した。
- 2026-02-24: [ID: P0-EAST123-08-S3-S3] `py_strip` / `py_lstrip` / `py_rstrip` の BuiltinCall lower に `StrStripOp` IR ノード経路を追加し、`render_expr` 側で mode + optional chars に応じた strip 系写像を受理した。`test_east3_cpp_bridge.py` にノード単体と BuiltinCall 経路の回帰を追加し、`tools/check_py2cpp_transpile.py` / `tools/check_selfhost_cpp_diff.py --mode allow-not-implemented` で確認した（selfhost 差分は既知3件維持）。
