<a href="../../ja/plans/p0-backend-runtime-boundary-realign.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p0-backend-runtime-boundary-realign.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p0-backend-runtime-boundary-realign.md`

# P0: backend の runtime/stdlib 責務境界を再設計する（設計是正）

最終更新: 2026-03-05

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-BACKEND-BOUNDARY-REALIGN-01`

背景:
- `audit-runtime` 監査で、`src/toolchain/emit/` に `math` / `gif` / `png` が多数出現した。
- これは「文字列を消すこと」が本質ではなく、runtime/stdlib 解決責務が emitter 側へ漏れている設計不整合の症状である。
- 正しい責務境界は、EAST3 までで module/call/attr/type を解決し、backend は解決済み情報を描画するだけに限定すること。

監査結果（2026-03-05）:
- 検出ファイル（11件）
  - `src/toolchain/emit/cpp/emitter/cpp_emitter.py`
  - `src/toolchain/emit/cpp/emitter/module.py`
  - `src/toolchain/emit/cs/emitter/cs_emitter.py`
  - `src/toolchain/emit/go/emitter/go_native_emitter.py`
  - `src/toolchain/emit/js/emitter/js_emitter.py`
  - `src/toolchain/emit/kotlin/emitter/kotlin_native_emitter.py`
  - `src/toolchain/emit/lua/emitter/lua_native_emitter.py`
  - `src/toolchain/emit/nim/emitter/nim_native_emitter.py`
  - `src/toolchain/emit/php/emitter/php_native_emitter.py`
  - `src/toolchain/emit/rs/emitter/rs_emitter.py`
  - `src/toolchain/emit/scala/emitter/scala_native_emitter.py`

S1-01 分類結果（違反タイプ別）:
- 監査生ログ: `work/logs/backend_boundary_audit_hits_20260305_s1_01.txt`（179件）
- 分類CSV: `work/logs/backend_boundary_audit_classified_20260305_s1_01.csv`

| backend file | branch | dispatch | runtime実装混在 | total |
| --- | ---: | ---: | ---: | ---: |
| `src/toolchain/emit/lua/emitter/lua_native_emitter.py` | 4 | 25 | 20 | 49 |
| `src/toolchain/emit/scala/emitter/scala_native_emitter.py` | 12 | 16 | 11 | 39 |
| `src/toolchain/emit/rs/emitter/rs_emitter.py` | 2 | 15 | 14 | 31 |
| `src/toolchain/emit/cs/emitter/cs_emitter.py` | 11 | 9 | 0 | 20 |
| `src/toolchain/emit/php/emitter/php_native_emitter.py` | 3 | 15 | 0 | 18 |
| `src/toolchain/emit/go/emitter/go_native_emitter.py` | 2 | 8 | 0 | 10 |
| `src/toolchain/emit/nim/emitter/nim_native_emitter.py` | 5 | 0 | 1 | 6 |
| `src/toolchain/emit/js/emitter/js_emitter.py` | 0 | 0 | 2 | 2 |
| `src/toolchain/emit/kotlin/emitter/kotlin_native_emitter.py` | 1 | 0 | 1 | 2 |
| `src/toolchain/emit/cpp/emitter/cpp_emitter.py` | 1 | 0 | 0 | 1 |
| `src/toolchain/emit/cpp/emitter/module.py` | 0 | 1 | 0 | 1 |

修正順序（S1-01 確定）:
1. `lua -> scala -> rs`（`runtime実装混在` が高密度）
2. `cs -> php -> go`（分岐/dispatch の比率が高い）
3. `nim -> js -> kotlin -> cpp`（低密度残件）

目的:
- backend の責務境界を是正し、runtime/stdlib の解決ロジックを emitter から除去する。
- `math/gif/png` 検出は「設計違反の検知ガード」として扱い、再発を CI で fail-fast にする。

対象:
- `src/toolchain/emit/*/emitter/*.py`
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
- [x] [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S2-01] `lua/scala/rs` の高密度違反箇所を先行是正し、runtime/stdlib 分岐を解決済み描画へ置換する。
- [x] [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S2-02] `cs/php/go/nim/kotlin/js/cpp` の残件を同方針で是正する。
- [x] [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S2-03] emitter 内のフォールバック経路を fail-closed 化し、未解決時の推測レンダリングを禁止する。
- [x] [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S3-01] 責務境界ガード（禁止分岐/禁止文字列/禁止dispatch）を `tools/` に追加し、CI 必須導線へ統合する。
- [x] [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S3-02] unit/smoke/parity 回帰を更新し、設計是正の非退行を固定する。

決定ログ:
- 2026-03-05: ユーザー指摘に基づき、目的を「文字列撤去」から「責務境界の設計是正」へ修正した。`math/gif/png` 検索は症状検知ガードとして再定義した。
- 2026-03-05: [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S1-01] 179件を `branch/dispatch/runtime実装混在` へ分類し、`lua -> scala -> rs` を先行是正順に確定した（分類CSVを `work/logs/backend_boundary_audit_classified_20260305_s1_01.csv` に固定）。
- 2026-03-05: [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S1-02] `docs/ja/spec/spec-east.md` に EAST3 -> backend の固定契約（`Call/Attribute` の解決済み属性、優先順位、`resolved_runtime_source`、fail-closed、emitter API 制約）を追記し、再解決禁止を仕様化した。
- 2026-03-05: [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S2-01] `lua_native_emitter.py` から未使用の runtime 実装混在ブロック（`_emit_math_runtime_helpers` / `_emit_path_runtime_helpers` / `_emit_gif_runtime_helpers` / `_emit_png_runtime_helpers`）を削除。`math|gif|png` ヒットは `49 -> 8`、全 backend 合計は `179 -> 138` に縮退。`python3 test/unit/toolchain/emit/lua/test_py2lua_smoke.py`（32件）で回帰 green を確認。
- 2026-03-05: [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S2-01] `scala_native_emitter.py` に残留していた未使用 inline runtime helper 群（`_emit_runtime_helpers` / `_emit_runtime_helpers_minimal` など）を削除し、`rs_emitter.py` の未使用 `RUST_RUNTIME_SUPPORT` を撤去。`math|gif|png` ヒットは `scala: 39 -> 29`、`rs: 31 -> 4`、全 backend 合計は `138 -> 101` に縮退。`python3 test/unit/toolchain/emit/scala/test_py2scala_smoke.py`（16件）と `python3 test/unit/toolchain/emit/rs/test_py2rs_smoke.py`（30件）で回帰 green を確認。
- 2026-03-05: [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S2-01] `scala_native_emitter.py` から `owner=="math"` による生AST再解決フォールバック（attribute/call/type推論）を撤去し、解決済み runtime_call 経路へ統一。`math|gif|png` ヒットは `scala: 29 -> 16`、全 backend 合計は `101 -> 88` に縮退し、`test_py2scala_smoke.py`（16件）再通過を確認。
- 2026-03-05: [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S2-02] `php_native_emitter.py` / `go_native_emitter.py` から `owner=="math"` 生AST再解決フォールバック（call/attribute/type推論）を撤去。`math|gif|png` ヒットは `php+go: 28 -> 12`、全 backend 合計は `88 -> 72` に縮退。`test_py2php_smoke.py`（10件）と `test_py2go_smoke.py`（16件）で回帰 green を確認。
- 2026-03-05: [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S2-02] `kotlin_native_emitter.py` / `nim_native_emitter.py` の `math` 生AST再解決フォールバック（型推論・call/attr）を撤去。`math|gif|png` ヒットは `kotlin+nim: 8 -> 3`、全 backend 合計は `72 -> 67` に縮退。`test_py2kotlin_smoke.py`（16件）と `test_py2nim_smoke.py`（3件）で回帰 green を確認。
- 2026-03-05: [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S2-02] `cs_emitter.py` の `owner=="math/png/gif"` 生ASTフォールバック（call/attr）を撤去し、import alias / resolved 経路へ統一。`math|gif|png` ヒットは `cs: 20 -> 8`、全 backend 合計は `67 -> 55` に縮退。`test_py2cs_smoke.py` は既存 baseline（`failures=11`）のままで、新規悪化は確認されなかった。
- 2026-03-05: [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S2-02] `nim_native_emitter.py` の式文フォールバックから `save_gif` / `write_rgb_png` 文字列直判定を撤去し、解決済み型ベース判定へ統一。`math|gif|png` ヒットは `nim: 3 -> 1`、全 backend 合計は `55 -> 53` に縮退。`test_py2nim_smoke.py`（3件）再通過を確認。
- 2026-03-05: [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S2-02] 対象 backend（`cs/php/go/nim/kotlin/js/cpp`）の生AST再解決フォールバック撤去を完了。残ヒットは import/runtime map 解決・診断文字列・互換コメントに分類し、fail-closed 強化（`S2-03`）と CI ガード（`S3-01`）で拘束する方針を確定。
- 2026-03-05: [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S2-03] `php/go` に fail-closed 補強を追加し、`runtime_call` が存在しても描画不能な `resolved_runtime_call` 経路は例外化した。`go` は `runtime_call=std::filesystem::*`（legacy表現）で target固有 symbol へ還元できないケースがあるため、`runtime_source=runtime_call` は従来フォールバックを暫定維持。`test_py2php_smoke.py`（10件）/ `test_py2go_smoke.py`（16件）は通過。
- 2026-03-05: [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S2-03] `kotlin` でも `resolved_runtime_call` 空振り時の stdlib fallback を例外化し、call/attribute 両方で fail-closed を補強。`test_py2kotlin_smoke.py`（16件）回帰 green を確認。
- 2026-03-05: [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S2-03] `js/cs/nim` でも `resolved_runtime_call` 空振り時の stdlib fallback を例外化し、call/attribute 推測レンダリングを停止。`js`/`nim` smoke は green、`cs` は既存 baseline（`failures=11`）維持で新規悪化なし。これにより fail-closed 適用対象を `go/php/kotlin/js/cs/nim` へ拡大し、`S2-03` を完了。
- 2026-03-05: [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S3-01] CI導線（`tools/run_local_ci.py`）上の guard 実行を再検証し、`check_emitter_forbidden_runtime_symbols.py` を「findings=0 のとき空allowlist許容」に修正。`check_emitter_runtimecall_guardrails.py` / `check_emitter_forbidden_runtime_symbols.py` / `test_check_emitter_runtimecall_guardrails.py` の3系統を通過確認し、ガードを常時実行可能状態へ固定。
- 2026-03-05: [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S3-02] `go/php/kotlin/js/cs/nim` smoke へ `resolved_runtime_call` 空振り fail-closed 回帰を追加。追加テストで露見した `go/php/kotlin/cs` の推測レンダリング漏れを修正（`semantic_tag` tail と `resolved_runtime_call` の整合チェックを導入）し、`test_py2{go,php,kotlin,js,nim,cs}_smoke.py`（合計117件）を全通過。あわせて `check_emitter_runtimecall_guardrails.py` / `check_emitter_forbidden_runtime_symbols.py` / `test_check_emitter_runtimecall_guardrails.py` / `test_runtime_parity_check_cli.py` を再実行して非退行を固定。
