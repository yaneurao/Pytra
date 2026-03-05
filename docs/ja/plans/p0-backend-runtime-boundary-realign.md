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

- [ ] [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S1-01] 監査ヒットを backend 別に「境界違反タイプ（分岐/dispatch/runtime実装混在）」へ分類し、修正順序を確定する。
- [ ] [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S1-02] EAST3 -> backend の解決済み呼び出し契約（call/attr/module/type）を明文化し、emitter API 制約を固定する。
- [ ] [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S2-01] `lua/scala/rs` の高密度違反箇所を先行是正し、runtime/stdlib 分岐を解決済み描画へ置換する。
- [ ] [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S2-02] `cs/php/go/nim/kotlin/js/cpp` の残件を同方針で是正する。
- [ ] [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S2-03] emitter 内のフォールバック経路を fail-closed 化し、未解決時の推測レンダリングを禁止する。
- [ ] [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S3-01] 責務境界ガード（禁止分岐/禁止文字列/禁止dispatch）を `tools/` に追加し、CI 必須導線へ統合する。
- [ ] [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S3-02] unit/smoke/parity 回帰を更新し、設計是正の非退行を固定する。

決定ログ:
- 2026-03-05: ユーザー指摘に基づき、目的を「文字列撤去」から「責務境界の設計是正」へ修正した。`math/gif/png` 検索は症状検知ガードとして再定義した。
