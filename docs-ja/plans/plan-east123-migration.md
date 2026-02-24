# TASK GROUP: TG-P0-EAST123-MIGRATION

最終更新: 2026-02-24

関連 TODO:
- `docs-ja/todo/index.md` の `ID: P0-EASTMIG-01`
- `docs-ja/todo/index.md` の `ID: P0-EASTMIG-02`
- `docs-ja/todo/index.md` の `ID: P0-EASTMIG-03`
- `docs-ja/todo/index.md` の `ID: P0-EASTMIG-04`
- `docs-ja/todo/index.md` の `ID: P0-EASTMIG-05`
- `docs-ja/todo/index.md` の `ID: P0-EASTMIG-06`

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

EAST2 互換モード縮退方針（P0-EASTMIG-05-S3）:
1. 既定運用は `--east-stage 3` とし、`--east-stage 2` は移行互換モードとする。
2. 互換モードは既存入力の受け皿に限定し、新規意味論を追加しない。
3. 警告フェーズを経て、`EAST3` 単独運用が安定した段階で `EAST2` 互換を段階撤去する。

サブタスク実行順（todo 同期）:
1. `P0-EASTMIG-01`: stage 名と責務境界（`EAST1/2/3`）を `spec` と `plan` で同期する。
   - `P0-EASTMIG-01-S1`: `spec-east`（`#east-file-mapping`）に責務対応表を固定する。
   - `P0-EASTMIG-01-S2`: 本計画の実行順と `todo` 実行順を同期する。
   - `P0-EASTMIG-01-S3`: `spec-east` / `spec/index` から移行仕様への導線を固定する。
2. `P0-EASTMIG-02`: `transpile_cli.py` に集中している段階 API を `east_parts/east1.py`, `east_parts/east2.py`, `east_parts/east3.py` へ分離する。
   - `P0-EASTMIG-02-S1`: `east1.py` へ `load_east1_document` と EAST1 正規化 helper を移す。
   - `P0-EASTMIG-02-S2`: `east2.py` へ `normalize_east1_to_east2_document` と EAST2 helper を移す。
   - `P0-EASTMIG-02-S3`: `east3.py` へ `load_east3_document` と公開委譲を集約する。
   - `P0-EASTMIG-02-S4`: `transpile_cli.py` を互換ラッパ中心へ縮退する。
3. `P0-EASTMIG-03`: `py2cpp.py` を `EAST3` 主経路化し、`EAST2` 再判断ロジックを段階縮退する。
4. `P0-EASTMIG-04`: hooks を `EAST3` 前提で棚卸しし、意味論 hook の流入を禁止する。
5. `P0-EASTMIG-05`: `--east-stage 3` 主経路の回帰導線を標準化し、`EAST2` 互換を移行モードへ格下げする。
6. `P0-EASTMIG-06`: 全変換器で `EAST3` を主経路へ統一し、`EAST2` 既定経路を撤去する。
   - `P0-EASTMIG-06-S0`: 境界固定を先行ゲートとして実施する（CodeEmitter 肥大化防止）。
     - `P0-EASTMIG-06-S0-S1`: `spec-east` に stage の入力/出力/禁止事項/担当ファイル表を追加。
     - `P0-EASTMIG-06-S0-S2`: `spec-dev` に CodeEmitter/hook の責務境界（意味論 lower 禁止）を明記。
     - `P0-EASTMIG-06-S0-S3`: `east_parts` と `transpile_cli` の段階横断残存箇所を棚卸し。
     - `P0-EASTMIG-06-S0-S4`: stage 境界違反を検出する unit/tools ガードを追加。
     - `P0-EASTMIG-06-S0-S5`: `todo`/`plan` へ反映し、境界固定を P0 の先行ゲートとして確定。
   - `P0-EASTMIG-06-S1`: 全 `py2*.py` の `EAST2` 既定経路を棚卸しする。
   - `P0-EASTMIG-06-S2`: `py2cpp.py` の既定 `--east-stage` を `3` へ切替える。
   - `P0-EASTMIG-06-S3`: 非 C++ 変換器へ `EAST3` 主経路を導入する。
     - `P0-EASTMIG-06-S3-S1`: `py2rs.py` の既定経路を `EAST3` 主経路へ切替。
     - `P0-EASTMIG-06-S3-S2`: `py2cs.py` の既定経路を `EAST3` 主経路へ切替。
     - `P0-EASTMIG-06-S3-S3`: `py2js.py` の既定経路を `EAST3` 主経路へ切替。
     - `P0-EASTMIG-06-S3-S4`: `py2ts.py` の既定経路を `EAST3` 主経路へ切替。
     - `P0-EASTMIG-06-S3-S5`: `py2go.py` の既定経路を `EAST3` 主経路へ切替。
     - `P0-EASTMIG-06-S3-S6`: `py2java.py` の既定経路を `EAST3` 主経路へ切替。
     - `P0-EASTMIG-06-S3-S7`: `py2kotlin.py` の既定経路を `EAST3` 主経路へ切替。
     - `P0-EASTMIG-06-S3-S8`: `py2swift.py` の既定経路を `EAST3` 主経路へ切替。
     - `P0-EASTMIG-06-S3-S9`: 非 C++ 8変換器の既定値・警告文言・回帰導線を統一。
   - `P0-EASTMIG-06-S4`: `EAST3` 主経路を回帰導線の既定へ固定する。
   - `P0-EASTMIG-06-S5`: `spec-east` / `spec-dev` の記述を同期する。
   - `P0-EASTMIG-06-S6`: `EAST1` build 責務境界を `docs-ja/spec/spec-east.md#east1-build-boundary` へ正式化する。
   - `P0-EASTMIG-06-S7`: （低優先）`render_human_east3_cpp.py` を追加し、`EAST3` 命令ノードの人間可読レンダラを整備する。

## P0-EASTMIG-06 再オープン理由

- `P0-EASTMIG-05` で方針（`EAST3` 主経路化）を確定したが、実装は部分的に `EAST2` 既定が残っている。
- 具体的には、`py2cpp.py` の既定 `--east-stage` はまだ `2`、非 C++ 変換器は `load_east_document_compat`（EAST2 互換）経路が主流である。
- この状態で各言語 CodeEmitter を先に拡張すると、責務境界が曖昧なまま backend に意味論実装が再流入し、修正範囲が肥大化する。
- そのため、未完了分を `P0-EASTMIG-06` として再オープンし、「境界固定（S0） -> 全変換器で EAST3 既定主経路化」の順を完了条件に置く。

実行メモ:
- `EAST3 lower` は `EAST2 -> EAST3` 変換のことを指す。
- `EAST1 -> EAST2` は parser 出力正規化層であり、意味論確定は行わない。
- backend hooks は移行期間中に分離してもよいが、最終形は `EAST3` 向け最小 hook 集合に収束させる。
- `P0-EASTMIG-06-S0` が完了するまでは、CodeEmitter の新規意味論実装（段階境界を曖昧にする変更）へ着手しない。

## 段階横断残存一覧（`P0-EASTMIG-06-S0-S3`）

`src/pytra/compiler/east_parts/` と `src/pytra/compiler/transpile_cli.py` の責務境界を棚卸しし、段階横断が残る箇所を固定する。

| 箇所 | 現状（段階横断の内容） | リスク | 後続での解消先 |
| --- | --- | --- | --- |
| `src/pytra/compiler/transpile_cli.py::load_east_document` | `.py/.json` 入力から `normalize_east1_to_east2_document` を即時適用し、`EAST1` build と `EAST2` 正規化が同一関数で混在。 | `EAST1` 専用入口の責務が不明瞭化。 | `P0-EASTMIG-06-S0-S5` で委譲境界を固定。 |
| `src/pytra/compiler/transpile_cli.py::normalize_east_root_document` | `east_stage` 未指定時に `2` を補完し、stage 契約補完と段階変換前提が同居。 | 旧入力で `EAST2` 既定が温存される。 | `P0-EASTMIG-06-S1` / `S2` で既定経路見直し。 |
| `src/pytra/compiler/transpile_cli.py::normalize_east1_to_east2_document` | stage module 委譲と selfhost 互換 fallback（`stage==1 -> 2` 書換え）が同居。 | `EAST2` 互換処理の残存箇所が見えづらい。 | `P0-EASTMIG-06-S5` で互換モード文言を同期。 |
| `src/pytra/compiler/transpile_cli.py::load_east_document_compat` | 非 C++ CLI 互換 API が `load_east_document` へ依存し、段階境界より互換挙動を優先。 | 非 C++ 変換器で `EAST2` 既定が継続。 | `P0-EASTMIG-06-S3-*` で各変換器を `EAST3` 主経路化。 |
| `src/pytra/compiler/transpile_cli.py::_parse_cli_args_dict` | `east_stage` の既定値が `"2"`。 | CLI 既定が `EAST2` 固定となり移行が遅延。 | `P0-EASTMIG-06-S2`（cpp）と `S3-*`（非 cpp）で切替。 |
| `src/pytra/compiler/east_parts/east_io.py::_normalize_east_root` | ルート補完で `east_stage` 未指定時に `2` を補完。 | stage 既定が util 層で固定化される。 | `P0-EASTMIG-06-S5` で契約文書と実装を同期。 |
| `src/pytra/compiler/east_parts/render_human_east2_cpp.py` | human renderer が `EAST2` 専用実装のみ。 | `EAST3` 可視化が不足し段階差分が追跡しにくい。 | `P0-EASTMIG-06-S7` で `render_human_east3_cpp.py` を追加。 |

## 段階境界ガード（`P0-EASTMIG-06-S0-S4`）

`stage` 境界違反の再流入を防ぐため、静的ガード + unit 実行ガードを追加する。

- `tools/check_east_stage_boundary.py`
  - `src/pytra/compiler/east_parts/east2.py` で `EAST3` lower API（`lower_east2_to_east3*`, `load_east3_document`）の import/call を禁止。
  - `src/pytra/compiler/east_parts/code_emitter.py` で stage load/lower API（`load_east_document*`, `normalize_east1_to_east2_document`, `lower_east2_to_east3*`, `convert_*`）の import/call を禁止。
- `test/unit/test_east_stage_boundary_guard.py`
  - 上記ガードを subprocess 実行し、CI で return code を固定する。
- `tools/run_local_ci.py`
  - `tools/check_east_stage_boundary.py` を標準チェック列へ追加する。

## 先行ゲート確定（`P0-EASTMIG-06-S0-S5`）

`P0-EASTMIG-06-S0` は `S0-S1` から `S0-S4` を満たした時点で「境界固定ゲート完了」と判定し、以降の `P0-EASTMIG-06-S1` 以降へ進む。

- `S0-S1` 完了: `docs-ja/spec/spec-east.md` で stage 境界表（入力/出力/禁止事項/担当ファイル）を固定。
- `S0-S2` 完了: `docs-ja/spec/spec-dev.md` で CodeEmitter/hook の責務境界（意味論 lower 禁止）を固定。
- `S0-S3` 完了: `transpile_cli.py` / `east_parts` の段階横断残存を一覧化。
- `S0-S4` 完了: `tools/check_east_stage_boundary.py` + unit guard により境界違反の再流入を検出。

ゲート運用:
- `P0-EASTMIG-06-S1` 以降の実装では、上記 4 成果物を「破壊しない」ことを受け入れ条件に含める。
- 境界契約の変更が必要な場合は、先に `docs-ja/spec/spec-east.md` / `docs-ja/spec/spec-dev.md` と本計画を更新してから実装変更を行う。

## 保留バックログ（低優先）

次は重要だが、`P0` 本線（`P0-EASTMIG-06`）完了までは `todo` へ再投入しない保留項目。

- `P0-EASTMIG-06-S8`: 非 C++ 各言語の selfhost / 多段 selfhost を成立状態へ収束する。
  - `P0-EASTMIG-06-S8-S1`: 現在の `stage1/stage2/stage3` 状態と pass 条件を受け入れ基準付きで再固定。
  - `P0-EASTMIG-06-S8-S2`: `rs/cs/js` の stage2/stage3 失敗要因を解消し pass へ収束。
  - `P0-EASTMIG-06-S8-S3`: `ts/go/java/swift/kotlin` の preview 脱却と stage2/stage3 実行経路を整備。
  - `P0-EASTMIG-06-S8-S4`: selfhost suite 全言語 pass を固定し、status 文書を同期。

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
- 2026-02-24: [ID: `P0-EASTMIG-06-S0-S5`] `S0-S1` から `S0-S4` の成果物を本計画へ集約し、`P0-EASTMIG-06-S0` を `P0` 先行ゲートとして確定した。以降の `S1` 以降は境界契約を破壊しないことを受け入れ条件とする。
- 2026-02-24: [ID: `P0-EASTMIG-06-S0-S4`] `tools/check_east_stage_boundary.py` と `test/unit/test_east_stage_boundary_guard.py` を追加し、`east2.py` での `EAST3` lower 流入と `code_emitter.py` での stage 再解釈 API 流入を静的検査で拒否するガードを導入した。`tools/run_local_ci.py` に同ガードを組み込んだ。
- 2026-02-24: [ID: `P0-EASTMIG-06-S0-S3`] `transpile_cli.py` / `east_parts` の段階横断残存を棚卸しし、`load_east_document` の `EAST1->EAST2` 即時正規化、`east_stage=2` 既定補完、`load_east_document_compat` 依存、`render_human_east2_cpp` 専用実装などを一覧化して後続タスクへの受け渡しを固定した。
- 2026-02-24: [ID: `P0-EASTMIG-06-S0-S2`] `docs-ja/spec/spec-dev.md` の責務境界へ「CodeEmitter は EAST3 以降の構文写像専任」「意味論 lower 禁止」「backend/hook 側の再解釈禁止」を明記した。
- 2026-02-24: [ID: `P0-EASTMIG-06-S0-S1`] `docs-ja/spec/spec-east.md` の `16.1.1` に段階境界表（入力/出力/禁止事項/担当ファイル）を追加し、`EAST1/EAST2/EAST3` の責務固定を仕様として明文化した。
- 2026-02-24: 本計画を `materials/refs/` に `plans` 形式で追加。
- 2026-02-24: dispatch 方針は単一オプション `--object-dispatch-mode`（既定 `native`）を維持。
- 2026-02-24: `docs-ja/plans/plan-east123-migration.md` として採用し、`docs-ja/todo/index.md` へ `P0-EASTMIG-*` タスク群を登録する。
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
- 2026-02-24: `P0-EASTMIG-06-S6` として `docs-ja/spec/spec-east.md#east1-build-boundary` を追加し、`east1_build.py` 分離仕様（`load_east_document_compat` エラー契約互換、selfhost diff 実行、`EAST1` build での `EAST2` 非変換）を受け入れ基準へ固定した。
- 2026-02-24: `east_parts/human.py` を `render_human_east2_cpp.py` へ改名し、`P0-EASTMIG-06-S7`（低優先）として `render_human_east3_cpp.py` 追加タスクを `todo`/plan に登録した。
