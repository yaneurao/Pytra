# TASK GROUP: TG-P0-EAST123-MIGRATION

最終更新: 2026-02-24

関連 TODO:
- `docs-ja/todo.md` の `ID: P0-EASTMIG-01`
- `docs-ja/todo.md` の `ID: P0-EASTMIG-02`
- `docs-ja/todo.md` の `ID: P0-EASTMIG-03`
- `docs-ja/todo.md` の `ID: P0-EASTMIG-04`
- `docs-ja/todo.md` の `ID: P0-EASTMIG-05`

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

サブタスク実行順（todo 同期）:
1. `P0-EASTMIG-01`: stage 名と責務境界（`EAST1/2/3`）を `spec` と `plan` で同期する。
   - `P0-EASTMIG-01-S1`: `spec-east123-migration` に責務対応表を固定する。
   - `P0-EASTMIG-01-S2`: 本計画の実行順と `todo` 実行順を同期する。
   - `P0-EASTMIG-01-S3`: `spec-east123` / `spec/index` から移行仕様への導線を固定する。
2. `P0-EASTMIG-02`: `transpile_cli.py` に集中している段階 API を `east_parts/east1.py`, `east_parts/east2.py`, `east_parts/east3.py` へ分離する。
   - `P0-EASTMIG-02-S1`: `east1.py` へ `load_east1_document` と EAST1 正規化 helper を移す。
   - `P0-EASTMIG-02-S2`: `east2.py` へ `normalize_east1_to_east2_document` と EAST2 helper を移す。
   - `P0-EASTMIG-02-S3`: `east3.py` へ `load_east3_document` と公開委譲を集約する。
   - `P0-EASTMIG-02-S4`: `transpile_cli.py` を互換ラッパ中心へ縮退する。
3. `P0-EASTMIG-03`: `py2cpp.py` を `EAST3` 主経路化し、`EAST2` 再判断ロジックを段階縮退する。
4. `P0-EASTMIG-04`: hooks を `EAST3` 前提で棚卸しし、意味論 hook の流入を禁止する。
5. `P0-EASTMIG-05`: `--east-stage 3` 主経路の回帰導線を標準化し、`EAST2` 互換を移行モードへ格下げする。

実行メモ:
- `EAST3 lower` は `EAST2 -> EAST3` 変換のことを指す。
- `EAST1 -> EAST2` は parser 出力正規化層であり、意味論確定は行わない。
- backend hooks は移行期間中に分離してもよいが、最終形は `EAST3` 向け最小 hook 集合に収束させる。

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
- 2026-02-24: 本計画を `materials/refs/` に `plans` 形式で追加。
- 2026-02-24: dispatch 方針は単一オプション `--object-dispatch-mode`（既定 `native`）を維持。
- 2026-02-24: `docs-ja/plans/plan-east123-migration.md` として採用し、`docs-ja/todo.md` へ `P0-EASTMIG-*` タスク群を登録する。
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
