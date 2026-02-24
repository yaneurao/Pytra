# EAST1/EAST2/EAST3 移行計画（実装順）

この文書は、`EAST1 -> EAST2 -> EAST3` 構成へ安全に移行するための実装計画を定義する。  
前提仕様は `docs-ja/spec/spec-east123.md` とする。

## 1. 目的

- `EAST2 -> EAST3` で意味論を確定し、backend/hook の再解釈をなくす。
- hooks を構文差分専任へ縮退する。
- `py2cpp.py` を「EAST3 -> C++ 写像」に集中させる。

## 2. スコープ

- 対象:
  - `src/pytra/compiler/transpile_cli.py`
  - `src/pytra/compiler/east_parts/`
  - `src/py2cpp.py`
  - `src/hooks/cpp/`
  - `test/unit/`
- 非対象:
  - 新規最適化器の導入
  - 全言語 backend の同時全面書き換え

## 3. 現状整理（着手時点）

- `EAST1` API は存在するが、実体は `load_east_document` 経由の薄い stage 差し替え。
- `EAST1 -> EAST2` は最小（ほぼ `east_stage` 更新）。
- `EAST2 -> EAST3` は `east3_lowering.py` に実装済み。
- `py2cpp.py` は `--east-stage {2,3}` の二重運用。
- hooks は補助レイヤだが、意味論ロジック残存リスクがある。

## 3.1 現行/移行後の責務対応表（2026-02-24）

`EAST1/EAST2/EAST3` の責務境界を、現行実装と移行後配置で 1:1 に対応付ける。

| 段 | 責務 | 現行実装（着手時点） | 移行後の正本 |
| --- | --- | --- | --- |
| EAST1 | parser 直後 IR 生成 | `src/pytra/compiler/east_parts/core.py` | `src/pytra/compiler/east_parts/core.py`（維持） |
| EAST1 | EAST1 入口 API（`load_east1_document`） | `src/pytra/compiler/east_parts/east1.py`（`transpile_cli.py` 互換ラッパ経由） | `src/pytra/compiler/east_parts/east1.py` |
| EAST1 | EAST1 ルート正規化（`east_stage=1` 固定） | `src/pytra/compiler/east_parts/east1.py` | `src/pytra/compiler/east_parts/east1.py` |
| EAST2 | EAST1 -> EAST2 正規化 API（`normalize_east1_to_east2_document`） | `src/pytra/compiler/east_parts/east2.py`（`transpile_cli.py` 互換ラッパ + selfhost fallback） | `src/pytra/compiler/east_parts/east2.py` |
| EAST2 | ルート契約補助（meta/dispatch 正規化） | `src/pytra/compiler/east_parts/east_io.py` | `src/pytra/compiler/east_parts/east2.py` + `east_io.py` |
| EAST3 | EAST2 -> EAST3 lower 本体 | `src/pytra/compiler/east_parts/east3_lowering.py` | `src/pytra/compiler/east_parts/east3_lowering.py`（維持） |
| EAST3 | EAST3 入口 API（`load_east3_document`） | `src/pytra/compiler/east_parts/east3.py`（`transpile_cli.py` 互換ラッパ経由） | `src/pytra/compiler/east_parts/east3.py` |
| Bridge | backend 入口（C++） | `src/py2cpp.py`（`--east-stage {2,3}` 二重運用） | `src/py2cpp.py`（`EAST3` 主経路 + `EAST2` 互換） |
| CLI 互換 | 旧 API 互換公開 | `src/pytra/compiler/transpile_cli.py` | `src/pytra/compiler/transpile_cli.py`（互換ラッパ専任） |

現状は stage 境界 API が `transpile_cli.py` に集中して見通しが悪い。  
本移行では、段階責務を `east_parts/east1.py`, `east_parts/east2.py`, `east_parts/east3.py` へ分離し、`transpile_cli.py` を互換ラッパ中心へ縮退する。

## 3.2 `py2cpp.py` の `--east-stage` 分岐棚卸し（P0-EASTMIG-03-S1 / P0-EASTMIG-03-S2）

`P0-EASTMIG-03-S1` で、loop 系の `EAST2` 依存を次のように整理した。

- 入口分岐（`load_east(..., east_stage=...)`）:
  - `east_stage=3`: `load_east3_document` を使用（従来どおり）。
  - `east_stage=2`: 互換入力を許容しつつ、backend 側で `ForRange` / runtime `For` を `ForCore` bridge へ寄せる。
- backend 既定ディスパッチ（`CppEmitter._emit_stmt_kind_fallback`）:
  - `ForRange`: `emit_for_range` 直呼びを縮退し、`_forrange_stmt_to_forcore` -> `emit_for_core` へ置換。
  - `For`: runtime `For` と `RangeExpr` `For` を `_for_stmt_to_forcore` -> `emit_for_core` へ置換。
  - `For` static-fastpath（既存 C++ range-for）は互換維持のため当面残す。
- `iter_plan`:
  - `StaticRangeForPlan` は `range_mode` を明示保持（bridge 時に補完）。
  - `RuntimeIterForPlan` は `dispatch_mode` を `meta.dispatch_mode` から補完。
- Any/object 境界（型付き代入/return/yield）:
  - `P0-EASTMIG-03-S2` で `AnnAssign` / `Assign` / `Return` / `Yield` の Any -> 型付き変換を `Unbox` 命令写像優先に置換。
  - source node が存在する経路は `_coerce_any_expr_to_target_via_unbox` で `Unbox` ノード経由に統一し、backend 側の文字列キャスト再判断を縮退。
- type_id / built-in lower:
  - `P0-EASTMIG-03-S3` で `east_stage=3` 時の未 lower fallback を fail-fast 化し、`type_id` Name-call（`isinstance` / `issubclass`）と `runtime_call` 未設定 BuiltinCall を拒否。
  - `east_stage=2` + selfhost 互換モードでは既存 fallback を維持し、移行期間の後方互換を確保。
- 回帰基線:
  - `P0-EASTMIG-03-S4` で `check_py2cpp_transpile`（131件）と `check_selfhost_cpp_diff --mode allow-not-implemented`（mismatches=0）を基線として固定。

## 4. 移行方針

1. まず「無挙動変更」で責務分離する。  
2. 次に `EAST3` 経路を主経路化する。  
3. 最後に `EAST2` 依存と意味論 hook を削る。

## 5. フェーズ計画

## Phase 0: 固定化（先にガードを作る）

目的:
- 後続変更で仕様逸脱しないよう、契約テストを先に固定する。

作業:
1. `EAST3` ルート必須項目（`east_stage=3`, `schema_version`, `meta.dispatch_mode`）のテストを明文化。
2. `ForCore.iter_mode` / `RuntimeIterForPlan.dispatch_mode` の必須性テスト追加。
3. `--object-dispatch-mode` が `EAST2 -> EAST3` でのみ反映されることをテスト化。

完了条件:
- `test/unit/test_east3_lowering.py`
- `test/unit/test_east3_cpp_bridge.py`
が常時グリーン。

## Phase 1: API 分離（無挙動変更）

目的:
- 現在 `transpile_cli.py` に集まっている段階責務をファイル分離する。

作業:
1. `src/pytra/compiler/east_parts/east1.py` 追加  
   - `load_east1_document(...)`  
   - EAST1 ルート正規化 helper
2. `src/pytra/compiler/east_parts/east2.py` 追加  
   - `normalize_east1_to_east2_document(...)`  
   - EAST2 ルート契約 helper
3. `src/pytra/compiler/east_parts/east3.py` 追加  
   - `load_east3_document(...)`  
   - `lower_east2_to_east3(...)` への公開 API 委譲
4. `transpile_cli.py` は互換ラッパ化（import 委譲のみ）。

完了条件:
- 生成結果差分ゼロ（既知差分のみ）
- `load_east_document(...)` / `load_east3_document(...)` の既存呼び出し互換維持

## Phase 2: `EAST3` 主経路化（C++）

目的:
- `py2cpp.py` の標準経路を `EAST3` 前提へ寄せる。

作業:
1. CI で `--east-stage 3` をデフォルト検証経路へ昇格。
2. `py2cpp.py` の `EAST2` 再判断ロジックを棚卸しし、`EAST3` 命令入力へ置換。
3. `For/Any/object` 境界の fallback を段階撤去。

完了条件:
- `--east-stage 3` で主要 fixture が安定通過。
- `ForCore` / `Obj*` / `Box/Unbox` 経路で backend 再判断が減少。

## Phase 3: hook 分離（移行専用）

目的:
- stage 混在による hook 肥大化を防ぐ。

作業:
1. C++ hooks を `east2_hooks` と `east3_hooks` に分離（移行期間限定）。
2. loader で `east_stage` に応じて hook セット選択。
3. `east3_hooks` では意味論変更 hook を禁止（構文差分のみ）。

完了条件:
- hook 実装で `EAST2/EAST3` 条件分岐が減少。
- 新規意味論 hook の流入を CI で検出可能。

## Phase 4: `EAST2` 経路縮退

目的:
- 実運用を `EAST3` 一本化へ収束。

作業:
1. `py2cpp.py` の `--east-stage` 既定を `3` に固定（移行アナウンス後）。
2. `EAST2` 専用 hook を削除。
3. `EAST2` 入力サポートを互換モードへ格下げ、最終的に撤去判断。

完了条件:
- 日次CIが `EAST3` 経路のみで成立。
- hooks が構文差分専任で維持される。

## 6. 実装順（最短実行列）

1. Phase 0（契約テスト強化）  
2. Phase 1（API分離）  
3. Phase 2（C++主経路化）  
4. Phase 3（hook分離）  
5. Phase 4（EAST2縮退）

## 7. 成果物一覧（フェーズ別）

- P0: 契約テスト追加/更新
- P1: `east1.py`, `east2.py`, `east3.py` 新規
- P2: `py2cpp.py` の EAST3 前提化差分
- P3: `hooks/cpp` 分離 + loader 修正
- P4: `EAST2` 互換モード縮退ドキュメント

## 8. 受け入れ基準（計測可能）

1. `EAST3` 単独で backend 生成が可能。  
2. `--object-dispatch-mode` が `EAST2 -> EAST3` でのみ意味適用される。  
3. `py2cpp.py` の `EAST2` 再判断ロジックが段階的に減る。  
4. hooks に意味論実装が新規流入しない。  
5. selfhost/クロスターゲット回帰が維持される。

## 9. 最低確認コマンド

```bash
python3 tools/check_py2cpp_transpile.py
python3 tools/check_py2js_transpile.py
python3 tools/check_py2ts_transpile.py
python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented
```

### 9.1 EAST3 主経路の標準回帰導線（P0-EASTMIG-05-S2）

- 実行順は `check_py2cpp_transpile` -> `check_py2js_transpile` -> `check_py2ts_transpile` -> `check_selfhost_cpp_diff` とする。
- 受け入れ判定は次を満たすこと:
  - `check_py2*` 系: `fail=0`。
  - `check_selfhost_cpp_diff --mode allow-not-implemented`: `mismatches=0`。
- `EAST3` 主経路変更時は上記 4 コマンドを同一コミット前に実行し、結果を `docs-ja/plans/plan-east123-migration.md` の `決定ログ` へ記録する。

## 10. リスクと回避

1. リスク: `EAST1/EAST2` 分離で既存CLI互換が崩れる。  
   回避: `transpile_cli.py` に互換ラッパを残し、先に互換テストを追加する。
2. リスク: `EAST3` 主経路化で未移行 built-in が落ちる。  
   回避: `--east-stage 2` を一時フォールバックに残し、機能単位で切替える。
3. リスク: hooks 分離で重複管理コストが増える。  
   回避: 分離は移行期間限定と明記し、削除期限を設定する。
