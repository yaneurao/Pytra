# TASK GROUP: TG-P0-EAST123-MIGRATION

最終更新: 2026-02-26

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-EASTMIG-01`
- `docs/ja/todo/index.md` の `ID: P0-EASTMIG-02`
- `docs/ja/todo/index.md` の `ID: P0-EASTMIG-03`
- `docs/ja/todo/index.md` の `ID: P0-EASTMIG-04`
- `docs/ja/todo/index.md` の `ID: P0-EASTMIG-05`
- `docs/ja/todo/index.md` の `ID: P0-EASTMIG-06`

背景:
- 現状は `EAST1/EAST2/EAST3` の責務がファイル上で見えにくく、`transpile_cli.py` に集約されている。
- `EAST2 -> EAST3` は `east3_lowering.py` が担うが、入口 API と backend 側の責務境界が追いにくい。
- hooks を最小化する設計方針に対して、移行ステップと削除順が明文化されていない。

目的:
- `EAST1`/`EAST2`/`EAST3` の責務をモジュール単位で固定し、入口 API を明確化する。
- `py2cpp.py` の主経路を `EAST3` 前提に寄せ、backend 側の意味論再判断を縮退する。
- hooks を最終的に `EAST3` 向け構文差分専任へ収束させる。

対象:
- `src/pytra/compiler/transpile_cli.py`
- `src/pytra/compiler/east_parts/`
- `src/py2cpp.py`
- `src/hooks/cpp/`
- `test/unit/`

非対象:
- 新規最適化器の導入
- 全 backend の同時全面 rewrite
- runtime API の大規模仕様変更

受け入れ基準:
1. `EAST1 -> EAST2` と `EAST2 -> EAST3` の責務が API と実装ファイルで分離される。
2. `py2cpp.py` が `EAST3` を標準入力経路として扱い、`EAST2` 再判断の新規追加を禁止する。
3. `--object-dispatch-mode` は `EAST2 -> EAST3` で一度だけ適用される。
4. hooks の意味論実装は段階的に撤去され、構文差分専任に近づく。
5. 主要回帰コマンドが継続して成功する。

確認コマンド（最低）:
- `python3 -m pytest -q test/unit/test_east3_lowering.py`
- `python3 -m pytest -q test/unit/test_east3_cpp_bridge.py`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/check_py2js_transpile.py`
- `python3 tools/check_py2ts_transpile.py`
- `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`

標準回帰導線（`P0-EASTMIG-05-S2`）:
1. `python3 tools/check_py2cpp_transpile.py`
2. `python3 tools/check_py2js_transpile.py`
3. `python3 tools/check_py2ts_transpile.py`
4. `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`

判定基準:
- `check_py2*` 系は `fail=0`。
- selfhost 差分検証は `mismatches=0`。

EAST2 互換撤去方針（2026-02-26 更新）:
1. 既定運用は `--east-stage 3` 固定とする。
2. `py2cpp.py` に加えて、非 C++ 8変換器（`py2rs.py`, `py2cs.py`, `py2js.py`, `py2ts.py`, `py2go.py`, `py2java.py`, `py2kotlin.py`, `py2swift.py`）も `--east-stage 2` を受理しない。
3. 非 C++ 8変換器では `load_east_document_compat` / `normalize_east3_to_legacy` / `east3_legacy_compat.py` 依存を撤去し、`EAST3` 直結へ統一する。
4. 段階境界は「`EAST2 -> EAST3` lower は compiler 側で一度だけ適用、backend/hook は `EAST3` の構文写像専任」を維持する。

## P3-EAST3-ONLY-01 反映事項（本計画への追補）

- 8本 CLI の `--east-stage 2` は警告運用からエラー停止へ変更済み。
- 非 C++ 8本 CLI は `load_east3_document` 単一路線に統一済み。
- `src/pytra/compiler/east_parts/east3_legacy_compat.py` は削除済み。
- `js/rs/cs` emitter は `ForCore` / `Obj*` / `Is*` / `Box/Unbox` の `EAST3` ノードを直接受理する。
- `tools/check_noncpp_east3_contract.py` は非 C++ 8本に対し以下を静的契約として検査する。
  - `--east-stage 2` 拒否（エラー）
  - `load_east_document_compat` 非依存
  - `normalize_east3_to_legacy` 非依存

## 回帰導線（EAST3 only）

- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/check_noncpp_east3_contract.py`
- `python3 tools/check_py2rs_transpile.py`
- `python3 tools/check_py2cs_transpile.py`
- `python3 tools/check_py2js_transpile.py`
- `python3 tools/check_py2ts_transpile.py`
- `python3 tools/check_py2go_transpile.py`
- `python3 tools/check_py2java_transpile.py`
- `python3 tools/check_py2kotlin_transpile.py`
- `python3 tools/check_py2swift_transpile.py`
- `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`

## 注記

- 本ファイルの 2026-02-24 以前の記録には「`--east-stage 2` 互換モード」前提の履歴が含まれるが、現行契約では非 C++ 8本も `EAST3 only` で運用する。
- 互換モード時代の記述は履歴として保持し、運用判断には本更新（2026-02-26）以降の節を正本とする。

## C++ hooks 棚卸し（P0-EASTMIG-04-S1）

`src/hooks/cpp/hooks/cpp_hooks.py` の現行 hook を「意味論」「構文差分」に分類する。

| hook | 分類 | 根拠 | `P0-EASTMIG-04-S2` 方針 |
| --- | --- | --- | --- |
| `on_stmt_omit_braces` | 構文差分 | brace の有無のみ制御し、意味論を変更しない。 | 維持（構文差分専任）。 |
| `on_render_expr_complex` | 構文差分 | `JoinedStr`/`Lambda` の描画経路選択のみ。 | 維持（構文差分専任）。 |
| `on_render_module_method` | 意味論 | `runtime_call` 解決と module 関数ディスパッチを実施。 | `EAST3` 命令写像または共通層へ移管候補。 |
| `on_render_class_method` | 意味論 | クラスメソッドのシグネチャ解決と引数 coercion を実施。 | `EAST3` 命令写像または共通層へ移管候補。 |
| `on_render_expr_leaf` | 意味論寄り | `Attribute` で module/runtime 解決と `Path` 特殊扱いを実施。 | module/runtime 解決を共通層へ寄せ、hook は構文差分に縮退。 |

決定ログ:
- 2026-02-24: [ID: `P0-EASTMIG-06`] `S0` から `S7` の実装は完了したが、`check_selfhost_cpp_diff --mode allow-not-implemented` の差分（2件）を `S10` で切り分けるまでクローズ保留とした。
- 2026-02-24: [ID: `P0-EASTMIG-06-S7`] `render_human_east3_cpp.py` を追加し、`render_east_human_cpp` 互換 wrapper から `east_stage=3` で自動委譲する経路を導入。`test_render_human_east3_cpp` を追加して ForCore/Obj*/type_id ノードの可視化を固定した。
- 2026-02-24: [ID: `P0-EASTMIG-06-S6`] `spec-east#east1-build-boundary` の受け入れ基準へ selfhost diff 実行を明記した。現時点の実行結果は `mismatches=2`（`sample/py/01_mandelbrot.py`, `sample/py/17_monte_carlo_pi.py`）で、差分は継続追跡対象とする。
- 2026-02-24: [ID: `P0-EASTMIG-06-S5`] `spec-east` / `spec-dev` を更新し、`EAST3` 既定・`EAST2` 互換モード（`--east-stage 2` 警告付き）の現行運用と回帰導線を仕様へ同期した。
- 2026-02-24: [ID: `P0-EASTMIG-06-S4`] `test_east3_lowering` に non-cpp 契約ガード実行テストを追加し、`tools/check_py2*_transpile.py` で既定実行時の stage2 互換警告を失敗扱いに統一した。`check_py2cpp_transpile` と `check_noncpp_east3_contract`、`test_east3_*` の回帰が通過。
- 2026-02-24: [ID: `P0-EASTMIG-06-S3-S9`] `tools/check_noncpp_east3_contract.py` と `test_noncpp_east3_contract_guard.py` を追加し、非 C++ 8変換器の `--east-stage` 既定値・警告文言・回帰導線を統一した。`run_local_ci` の非 C++ 導線は同スクリプトへ統合。
- 2026-02-24: [ID: `P0-EASTMIG-06-S3-S8`] `py2swift.py` に `--east-stage` / `--object-dispatch-mode` を追加し、既定を `EAST3` に切替えた。`stage=2` は警告付き互換モードへ縮退。`EAST3` ノード互換は `east3_legacy_compat` を利用し、`test_py2swift_smoke` と `check_py2swift_transpile` を通過させた。
- 2026-02-24: [ID: `P0-EASTMIG-06-S3-S7`] `py2kotlin.py` に `--east-stage` / `--object-dispatch-mode` を追加し、既定を `EAST3` に切替えた。`stage=2` は警告付き互換モードへ縮退。`EAST3` ノード互換は `east3_legacy_compat` を利用し、`test_py2kotlin_smoke` と `check_py2kotlin_transpile` を通過させた。
- 2026-02-24: [ID: `P0-EASTMIG-06-S3-S6`] `py2java.py` に `--east-stage` / `--object-dispatch-mode` を追加し、既定を `EAST3` に切替えた。`stage=2` は警告付き互換モードへ縮退。`EAST3` ノード互換は `east3_legacy_compat` を利用し、`test_py2java_smoke` と `check_py2java_transpile` を通過させた。
- 2026-02-24: [ID: `P0-EASTMIG-06-S3-S5`] `py2go.py` に `--east-stage` / `--object-dispatch-mode` を追加し、既定を `EAST3` に切替えた。`stage=2` は警告付き互換モードへ縮退。`EAST3` ノード互換は `east3_legacy_compat` を利用し、`test_py2go_smoke` と `check_py2go_transpile` を通過させた。
- 2026-02-24: [ID: `P0-EASTMIG-06-S3-S4`] `py2ts.py` に `--east-stage` / `--object-dispatch-mode` を追加し、既定を `EAST3` に切替えた。`stage=2` は警告付き互換モードへ縮退。`EAST3` ノード互換は `east3_legacy_compat` を利用し、`test_py2ts_smoke` と `check_py2ts_transpile` を通過させた。
- 2026-02-24: [ID: `P0-EASTMIG-06-S3-S3`] `py2js.py` に `--east-stage` / `--object-dispatch-mode` を追加し、既定を `EAST3` に切替えた。`stage=2` は警告付き互換モードへ縮退。`EAST3` ノード互換は `east3_legacy_compat` を利用し、`test_py2js_smoke` と `check_py2js_transpile` を通過させた。
- 2026-02-24: [ID: `P0-EASTMIG-06-S3-S2`] `py2cs.py` に `--east-stage` / `--object-dispatch-mode` を追加し、既定を `EAST3` に切替えた。`stage=2` は警告付き互換モードへ縮退。`EAST3` ノード互換は `east3_legacy_compat` を共通利用し、`test_py2cs_smoke` と `check_py2cs_transpile` を通過させた。
- 2026-02-24: [ID: `P0-EASTMIG-06-S3-S1`] `py2rs.py` に `--east-stage` / `--object-dispatch-mode` を追加し、既定を `EAST3` に切替えた。`stage=2` は警告付き互換モードへ縮退。`EAST3` ノード互換は `east3_legacy_compat` を利用し、`test_py2rs_smoke` と `check_py2rs_transpile` を通過させた。
- 2026-02-24: [ID: `P0-EASTMIG-06-S0`] `S0-S1` から `S0-S5` 完了により、`EAST1/EAST2/EAST3` 境界固定ゲートをクローズした。以後の `P0-EASTMIG-06` は `S3` 以降（非 C++ 変換器主経路化）を最上位未完了として進める。
- 2026-02-24: [ID: `P0-EASTMIG-06-S2`] `py2cpp` の既定 `east_stage` を `3` へ切替え、`stage=2` は互換警告付き運用へ縮退した。`parse_py2cpp_argv` 初期値・`load_east`/`build_module_east_map`/`main` 既定を更新し、`check_py2cpp_transpile`（131件）と境界ガード通過を確認した。
- 2026-02-24: [ID: `P0-EASTMIG-06-S1`] 全 `py2*.py`（`py2cpp` + 非 C++ 8変換器）の EAST 読み込み経路を棚卸しし、`load_east_document_compat` 依存と `east_stage="2"` 既定値の残存箇所を表形式で固定した。後続は `S2`（cpp 既定切替）と `S3-*`（非 cpp 主経路化）へ受け渡す。
- 2026-02-24: [ID: `P0-EASTMIG-06-S0-S5`] `S0-S1` から `S0-S4` の成果物を本計画へ集約し、`P0-EASTMIG-06-S0` を `P0` 先行ゲートとして確定した。以降の `S1` 以降は境界契約を破壊しないことを受け入れ条件とする。
- 2026-02-24: [ID: `P0-EASTMIG-06-S0-S4`] `tools/check_east_stage_boundary.py` と `test/unit/test_east_stage_boundary_guard.py` を追加し、`east2.py` での `EAST3` lower 流入と `code_emitter.py` での stage 再解釈 API 流入を静的検査で拒否するガードを導入した。`tools/run_local_ci.py` に同ガードを組み込んだ。
- 2026-02-24: [ID: `P0-EASTMIG-06-S0-S3`] `transpile_cli.py` / `east_parts` の段階横断残存を棚卸しし、`load_east_document` の `EAST1->EAST2` 即時正規化、`east_stage=2` 既定補完、`load_east_document_compat` 依存、`render_human_east2_cpp` 専用実装などを一覧化して後続タスクへの受け渡しを固定した。
- 2026-02-24: [ID: `P0-EASTMIG-06-S0-S2`] `docs/ja/spec/spec-dev.md` の責務境界へ「CodeEmitter は EAST3 以降の構文写像専任」「意味論 lower 禁止」「backend/hook 側の再解釈禁止」を明記した。
- 2026-02-24: [ID: `P0-EASTMIG-06-S0-S1`] `docs/ja/spec/spec-east.md` の `16.1.1` に段階境界表（入力/出力/禁止事項/担当ファイル）を追加し、`EAST1/EAST2/EAST3` の責務固定を仕様として明文化した。
- 2026-02-24: 本計画を `materials/refs/` に `plans` 形式で追加。
- 2026-02-24: dispatch 方針は単一オプション `--object-dispatch-mode`（既定 `native`）を維持。
- 2026-02-24: `docs/ja/plans/plan-east123-migration.md` として採用し、`docs/ja/todo/index.md` へ `P0-EASTMIG-*` タスク群を登録する。
- 2026-02-24: `P0-EASTMIG-02-S1` として `src/pytra/compiler/east_parts/east1.py` を追加し、`load_east1_document` の実処理を `transpile_cli.py` 互換ラッパから分離した。
- 2026-02-24: `P0-EASTMIG-02-S2` として `src/pytra/compiler/east_parts/east2.py` を追加し、`normalize_east1_to_east2_document` を段階モジュールへ移設した（`transpile_cli.py` 側は selfhost 互換 fallback を維持）。
- 2026-02-24: `P0-EASTMIG-02-S3` として `src/pytra/compiler/east_parts/east3.py` を追加し、`load_east3_document` と `lower_east2_to_east3` 公開委譲を段階モジュールへ集約した。
- 2026-02-24: P0-EASTMIG-02-S4 として、`transpile_cli.py` の段階 API を stage module 委譲ラッパへ整理し、互換テスト（wrapper 委譲 + selfhost 抽出）を追加した。
- 2026-02-24: `P0-EASTMIG-03-S1` として `py2cpp.py` の loop 分岐を棚卸しし、`ForRange` と runtime `For` を `ForCore` bridge（`_forrange_stmt_to_forcore`, `_for_stmt_to_forcore`）経由へ置換した。`For` static-fastpath は既存 C++ range-for を維持し、次段 (`P0-EASTMIG-03-S2/S3`) で縮退を継続する。
- 2026-02-24: `P0-EASTMIG-03-S2` として Any/object 境界の型付き変換（AnnAssign/Assign/Return/Yield）を `Unbox` 命令写像優先へ切り替え、`_coerce_any_expr_to_target_via_unbox` を追加した。source node が存在する経路では legacy 文字列キャスト再判断を通らず、`EAST3` ノード経由で backend 生成する。
- 2026-02-24: `P0-EASTMIG-03-S3` として `type_id` / built-in lower の未 lower fallback を `EAST3` 主経路で fail-fast 化した。`east_stage=3` では `isinstance`/`issubclass` Name-call と `runtime_call` 未設定 BuiltinCall を拒否し、`east_stage=2` + selfhost 互換のみ legacy fallback を残す。
- 2026-02-24: P0-EASTMIG-03-S4 として回帰基線を固定した。`python3 test/unit/test_east3_cpp_bridge.py`（71件）/ `python3 tools/check_py2cpp_transpile.py`（checked=131, fail=0）/ `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（mismatches=0）/ `python3 tools/check_todo_priority.py` を通過し、P0-EASTMIG-03 をクローズ。
- 2026-02-24: `P0-EASTMIG-04-S1` として `src/hooks/cpp/hooks/cpp_hooks.py` の hook 5件を分類し、意味論 3件（`on_render_module_method`, `on_render_class_method`, `on_render_expr_leaf`）と構文差分 2件（`on_stmt_omit_braces`, `on_render_expr_complex`）の棚卸し表を本計画へ記録した。
- 2026-02-24: `P0-EASTMIG-04-S2` として `src/hooks/cpp/hooks/cpp_hooks.py` から意味論 hook（`on_render_module_method`, `on_render_class_method`, `on_render_expr_leaf`）を撤去し、hooks を構文差分（`on_stmt_omit_braces`, `on_render_expr_complex`）専任へ縮退した。
- 2026-02-24: P0-EASTMIG-04-S3 として hooks 回帰ガードを `test/unit/test_cpp_hooks.py` へ追加し、`build_cpp_hooks()` が構文差分 hook のみ（`on_stmt_omit_braces`, `on_render_expr_complex`）を登録することを固定した。P0-EASTMIG-04 をクローズ。
- 2026-02-24: `P0-EASTMIG-05-S1` として `test/unit/test_east3_lowering.py` / `test/unit/test_east3_cpp_bridge.py` を拡充し、既存 `ForCore` 入力に対しても `RuntimeIterForPlan.dispatch_mode` を `object_dispatch_mode` へ正規化する契約を追加した（lowering 19件 / bridge 72件とも通過）。
- 2026-02-24: `P0-EASTMIG-05-S2` として `check_py2{cpp,js,ts}_transpile` + `check_selfhost_cpp_diff --mode allow-not-implemented` を `EAST3` 主経路の標準回帰導線として固定し、実測結果（各 `checked=131 fail=0`、`mismatches=0`）を確認した。
- 2026-02-24: P0-EASTMIG-05-S3 として `--east-stage 2` を移行互換モードに位置づける縮退手順（互換維持 -> 警告 -> 撤去判定）を plan/spec に固定し、P0-EASTMIG-05 をクローズ。
- 2026-02-24: `P0-EASTMIG-06` を再オープンした。`py2cpp.py` の既定 stage と非 C++ 変換器の `EAST2` 既定経路が残存しており、全変換器での `EAST3` 主経路統一が未完了のため。
- 2026-02-24: EAST責務境界を先に固定しないと CodeEmitter 作業が肥大化するリスクを反映し、`P0-EASTMIG-06-S0`（境界固定ゲート）を最優先サブタスクとして追加した。
- 2026-02-24: `P0-EASTMIG-06-S3` の粒度が大きいため、非 C++ 8変換器を `P0-EASTMIG-06-S3-S1` から `P0-EASTMIG-06-S3-S8` へ分割し、最後に `S3-S9` で既定値/警告文言/回帰導線の統一を固定する構成へ更新した。
- 2026-02-24: 「各言語 `py2<lang>.py` の selfhost / 多段 selfhost 成立」は `P0-EASTMIG-06-S8` 系として保持しつつ、全体低優先の保留バックログへ退避した（`P0` 本線完了後に `todo` 再投入）。
- 2026-02-24: `P0-EASTMIG-06-S6` として `docs/ja/spec/spec-east.md#east1-build-boundary` を追加し、`east1_build.py` 分離仕様（`load_east_document_compat` エラー契約互換、selfhost diff 実行、`EAST1` build での `EAST2` 非変換）を受け入れ基準へ固定した。
- 2026-02-24: `east_parts/human.py` を `render_human_east2_cpp.py` へ改名し、`P0-EASTMIG-06-S7`（低優先）として `render_human_east3_cpp.py` 追加タスクを `todo`/plan に登録した。
