# P0: backend の runtime/stdlib 責務境界を再設計する（設計是正）

最終更新: 2026-03-05

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-BACKEND-BOUNDARY-REALIGN-01`

背景:
- `audit-runtime` 監査で、`src/backends/` に `math` / `gif` / `png` が多数出現した。
- これは「文字列を消すこと」が本質ではなく、runtime/stdlib 解決責務が emitter 側へ漏れている設計不整合の症状である。
- 正しい責務境界は、EAST3 までで module/call/attr/type を解決し、backend は解決済み情報を描画するだけに限定すること。

監査結果（2026-03-05）:
- 検出ファイル（11件）
  - `src/backends/cpp/emitter/cpp_emitter.py`
  - `src/backends/cpp/emitter/module.py`
  - `src/backends/cs/emitter/cs_emitter.py`
  - `src/backends/go/emitter/go_native_emitter.py`
  - `src/backends/js/emitter/js_emitter.py`
  - `src/backends/kotlin/emitter/kotlin_native_emitter.py`
  - `src/backends/lua/emitter/lua_native_emitter.py`
  - `src/backends/nim/emitter/nim_native_emitter.py`
  - `src/backends/php/emitter/php_native_emitter.py`
  - `src/backends/rs/emitter/rs_emitter.py`
  - `src/backends/scala/emitter/scala_native_emitter.py`

S1-01 分類結果（違反タイプ別）:
- 監査生ログ: `work/logs/backend_boundary_audit_hits_20260305_s1_01.txt`（179件）
- 分類CSV: `work/logs/backend_boundary_audit_classified_20260305_s1_01.csv`

| backend file | branch | dispatch | runtime実装混在 | total |
| --- | ---: | ---: | ---: | ---: |
| `src/backends/lua/emitter/lua_native_emitter.py` | 4 | 25 | 20 | 49 |
| `src/backends/scala/emitter/scala_native_emitter.py` | 12 | 16 | 11 | 39 |
| `src/backends/rs/emitter/rs_emitter.py` | 2 | 15 | 14 | 31 |
| `src/backends/cs/emitter/cs_emitter.py` | 11 | 9 | 0 | 20 |
| `src/backends/php/emitter/php_native_emitter.py` | 3 | 15 | 0 | 18 |
| `src/backends/go/emitter/go_native_emitter.py` | 2 | 8 | 0 | 10 |
| `src/backends/nim/emitter/nim_native_emitter.py` | 5 | 0 | 1 | 6 |
| `src/backends/js/emitter/js_emitter.py` | 0 | 0 | 2 | 2 |
| `src/backends/kotlin/emitter/kotlin_native_emitter.py` | 1 | 0 | 1 | 2 |
| `src/backends/cpp/emitter/cpp_emitter.py` | 1 | 0 | 0 | 1 |
| `src/backends/cpp/emitter/module.py` | 0 | 1 | 0 | 1 |

修正順序（S1-01 確定）:
1. `lua -> scala -> rs`（`runtime実装混在` が高密度）
2. `cs -> php -> go`（分岐/dispatch の比率が高い）
3. `nim -> js -> kotlin -> cpp`（低密度残件）

目的:
- backend の責務境界を是正し、runtime/stdlib の解決ロジックを emitter から除去する。
- `math/gif/png` 検出は「設計違反の検知ガード」として扱い、再発を CI で fail-fast にする。

対象:
- `src/backends/*/emitter/*.py`
- EAST3 の `runtime_call` / `resolved_runtime_call` 契約
- `tools/` の静的ガードと CI 導線

非対象:
- runtime 新機能の追加
- ベンチマーク値更新
- README の性能表更新

受け入れ基準:
- backend 側に runtime/stdlib モジュール名依存の分岐（`owner == ...`、`runtime_call == ...` 固定比較、専用 dispatch table）が存在しない。
- すべての runtime/stdlib 呼び出しは EAST3 解決済み属性（`runtime_call` / `resolved_runtime_call`）のみで描画される。
- unresolved な stdlib/runtime 呼び出しは emitter で fail-closed する。
- `rg -n "math|gif|png" src/backends` は 0 件、または「検査専用ファイルの許可箇所」のみに限定される。
- CI に責務境界ガードが追加され、違反時に fail する。

確認コマンド（予定）:
- `rg -n "math|gif|png" src/backends`
- `python3 tools/check_todo_priority.py`
- `python3 tools/run_local_ci.py`

## 分解

- [x] [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S1-01] 監査ヒットを backend 別に「境界違反タイプ（分岐/dispatch/runtime実装混在）」へ分類し、修正順序を確定する。
- [x] [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S1-02] EAST3 -> backend の解決済み呼び出し契約（call/attr/module/type）を明文化し、emitter API 制約を固定する。
- [ ] [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S2-01] `lua/scala/rs` の高密度違反箇所を先行是正し、runtime/stdlib 分岐を解決済み描画へ置換する。
- [ ] [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S2-02] `cs/php/go/nim/kotlin/js/cpp` の残件を同方針で是正する。
- [ ] [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S2-03] emitter 内のフォールバック経路を fail-closed 化し、未解決時の推測レンダリングを禁止する。
- [ ] [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S3-01] 責務境界ガード（禁止分岐/禁止文字列/禁止dispatch）を `tools/` に追加し、CI 必須導線へ統合する。
- [ ] [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S3-02] unit/smoke/parity 回帰を更新し、設計是正の非退行を固定する。

決定ログ:
- 2026-03-05: ユーザー指摘に基づき、目的を「文字列撤去」から「責務境界の設計是正」へ修正した。`math/gif/png` 検索は症状検知ガードとして再定義した。
- 2026-03-05: [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S1-01] 179件を `branch/dispatch/runtime実装混在` へ分類し、`lua -> scala -> rs` を先行是正順に確定した（分類CSVを `work/logs/backend_boundary_audit_classified_20260305_s1_01.csv` に固定）。
- 2026-03-05: [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S1-02] `docs/ja/spec/spec-east.md` に EAST3 -> backend の固定契約（`Call/Attribute` の解決済み属性、優先順位、`resolved_runtime_source`、fail-closed、emitter API 制約）を追記し、再解決禁止を仕様化した。
- 2026-03-05: [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S2-01] `lua_native_emitter.py` から未使用の runtime 実装混在ブロック（`_emit_math_runtime_helpers` / `_emit_path_runtime_helpers` / `_emit_gif_runtime_helpers` / `_emit_png_runtime_helpers`）を削除。`math|gif|png` ヒットは `49 -> 8`、全 backend 合計は `179 -> 138` に縮退。`python3 test/unit/backends/lua/test_py2lua_smoke.py`（32件）で回帰 green を確認。
