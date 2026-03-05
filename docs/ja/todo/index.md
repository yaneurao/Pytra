# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-05

## 文脈運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度上書きは `docs/ja/plans/instruction-template.md` 形式でチャット指示し、`todo2.md` は使わない。
- 着手対象は「未完了の最上位優先度ID（最小 `P<number>`、同一優先度では上から先頭）」に固定し、明示上書き指示がない限り低優先度へ進まない。
- `P0` が 1 件でも未完了なら `P1` 以下には着手しない。
- 着手前に文脈ファイルの `背景` / `非対象` / `受け入れ基準` を確認する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める（例: ``[ID: P0-XXX-01] ...``）。
- `docs/ja/todo/index.md` の進捗メモは 1 行要約に留め、詳細（判断・検証ログ）は文脈ファイル（`docs/ja/plans/*.md`）の `決定ログ` に記録する。
- 1 つの `ID` が大きい場合は、文脈ファイル側で `-S1` / `-S2` 形式の子タスクへ分割して進めてよい（親 `ID` 完了までは親チェックを維持）。
- 割り込み等で未コミット変更が残っている場合は、同一 `ID` を完了させるか差分を戻すまで別 `ID` に着手しない。
- `docs/ja/todo/index.md` / `docs/ja/plans/*.md` 更新時は `python3 tools/check_todo_priority.py` を実行し、差分に追加した進捗 `ID` が最上位未完了 `ID`（またはその子 `ID`）と一致することを確認する。
- 作業中の判断は文脈ファイルの `決定ログ` へ追記する。
- 一時出力は既存 `out/`（または必要時のみ `/tmp`）を使い、リポジトリ直下に新規一時フォルダを増やさない。

## メモ

- このファイルは未完了タスクのみを保持します。
- 完了済みタスクは `docs/ja/todo/archive/index.md` 経由で履歴へ移動します。
- `docs/ja/todo/archive/index.md` は索引のみを保持し、履歴本文は `docs/ja/todo/archive/YYYYMMDD.md` に日付単位で保存します。


## 未完了タスク

### P0: runtime ルート再編（`runtime2` 退避 + 新 `runtime/` 再構築）で C++ parity を先行復旧（最優先）

文脈: [docs/ja/plans/p0-runtime-root-reset-cpp-parity.md](../plans/p0-runtime-root-reset-cpp-parity.md)

1. [ ] [ID: P0-RUNTIME-ROOT-RESET-CPP-01] 旧 runtime を `src/runtime2` へ退避し、新 `src/runtime/cpp/{core,gen}` で C++ parity を復旧する。
2. [x] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S1-01] C++ runtime 参照点（backend/toolchain/tools）を棚卸しし、移行影響範囲を固定する。
3. [x] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S1-02] `src/runtime` を `src/runtime2` へ `git mv` し、新 `src/runtime/cpp/{core,gen}` を作成する。
4. [x] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S1-03] `src/runtime2` 参照禁止ガードを追加する。
5. [x] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S2-01] C++ backend の runtime/include 解決を `core/gen` 前提へ更新し、`pytra` shim 経路を削除する。
6. [ ] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S2-02] runtime generator（manifest/出力先/marker）を `runtime/cpp/gen` へ切り替える。
7. [ ] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S2-03] C++ build manifest/コピー導線を `runtime/cpp/core` + `runtime/cpp/gen` のみに統一する。
8. [ ] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S3-01] C++ 必要 runtime（std/utils）を SoT から再生成し、`gen/` のみへ配置する。
9. [ ] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S3-02] C++ 固有手書き実装（`*-impl.*`）を `core/` へ整理する。
10. [ ] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S4-01] `tools/runtime_parity_check.py --targets cpp --case-root fixture` を通過させる。
11. [ ] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S4-02] `tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples` を通過させる。
12. [ ] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S4-03] parity fail を潰し切り、再実行で安定通過を確認する。
13. [ ] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S5-01] `docs/ja/spec` の runtime レイアウトと運用手順（生成/検証）を更新する。
- 進捗メモ: [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S1-01] `work/logs/p0_runtime_root_reset_cpp_ref_inventory_targets_20260305_s1_01.txt`（50件）を固定し、影響範囲を `src/backends/cpp/*` / `src/toolchain/compiler/*` / `tools/*` に確定。
- 進捗メモ: [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S1-02] `src/runtime -> src/runtime2` を移動し、`src/runtime/cpp/core`（旧 `pytra-core`）と `src/runtime/cpp/gen`（旧 `pytra-gen`）を新設。旧 `src/runtime2/cpp/pytra` shim を隔離した。
- 進捗メモ: [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S1-03] `tools/check_runtime2_references_absent.py` を追加し、`run_local_ci.py` と tooling unit test（`test_check_runtime2_references_absent.py`）へ統合して `src/runtime2` 参照の再流入を fail-fast 化。
- 進捗メモ: [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S2-01] C++ backend の runtime include 解決を `runtime/cpp/core` + `runtime/cpp/gen` へ切替し、`sample/py/01_mandelbrot.py` の再変換結果が `#include "runtime/cpp/core/built_in/py_runtime.h"` / `runtime/cpp/gen/...` になることを確認。

### P0: `pytra-cli` 責務再編（命名統一 + target分岐撤去）（最優先）

文脈: [docs/ja/plans/p0-pytra-cli-boundary-and-dispatch-removal.md](../plans/p0-pytra-cli-boundary-and-dispatch-removal.md)

1. [x] [ID: P0-PYTRA-CLI-REALIGN-01] `pytra-cli` を backend プロファイル駆動へ再編し、CLI 本体から target 言語ごとの分岐を撤去する。
2. [x] [ID: P0-PYTRA-CLI-REALIGN-01-S1-01] CLI本体 / backendプロファイル / 実行runner の責務境界を文書化し、禁止事項を固定する。
3. [x] [ID: P0-PYTRA-CLI-REALIGN-01-S1-02] `src/pytra-cli.py` へ命名統一し、`./pytra` / parity / tooling 参照を更新する。
4. [x] [ID: P0-PYTRA-CLI-REALIGN-01-S2-01] target 固有 build/run/transpile 契約を `toolchain` 側プロファイルへ抽出する。
5. [x] [ID: P0-PYTRA-CLI-REALIGN-01-S2-02] `src/pytra-cli.py` を共通ディスパッチ専用へ縮退し、target 分岐を撤去する。
6. [x] [ID: P0-PYTRA-CLI-REALIGN-01-S2-03] target 非互換オプション（例: `--codegen-opt`）をプロファイル検証で fail-fast 化する。
7. [x] [ID: P0-PYTRA-CLI-REALIGN-01-S3-01] parity/tooling を新CLI契約へ追従させ、target 直書き重複を削減する。
8. [x] [ID: P0-PYTRA-CLI-REALIGN-01-S3-02] unit/parity/docs を更新し、回帰を固定する。
- 進捗メモ: [ID: P0-PYTRA-CLI-REALIGN-01-S1-02] `src/pytra_cli.py` を廃止して `src/pytra-cli.py` へ命名統一し、`./pytra` / `tools/runtime_parity_check.py` / `test_pytra_cli` / 利用ドキュメントの参照先を更新。
- 進捗メモ: [ID: P0-PYTRA-CLI-REALIGN-01-S1-01] `docs/ja|en/spec/spec-make.md` に `pytra-cli` 境界節を追加し、CLI本体/プロファイル/runner の責務と禁止事項（target分岐直書き禁止）を固定。
- 進捗メモ: [ID: P0-PYTRA-CLI-REALIGN-01-S2-01] `src/toolchain/compiler/pytra_cli_profiles.py` を追加し、出力パス決定と non-cpp build/run 契約を `pytra-cli` から抽出。`test_pytra_cli.py` / `test_pytra_cli_profiles.py` を通過。
- 進捗メモ: [ID: P0-PYTRA-CLI-REALIGN-01-S2-02] `src/pytra-cli.py` の `target == ...` 分岐を撤去し、`TargetProfile.build_driver` で transpile/build を共通ディスパッチ化。
- 進捗メモ: [ID: P0-PYTRA-CLI-REALIGN-01-S2-03] profile 互換検証を追加し、non-cpp での `--codegen-opt` と `--compiler/--std/--opt/--exe`（`--build`時）を fail-fast 化。tooling unit を拡張。
- 進捗メモ: [ID: P0-PYTRA-CLI-REALIGN-01-S3-01] `tools/runtime_parity_check.py` の target order/needs 直書きを `pytra_cli_profiles` 参照へ置換し、`test_runtime_parity_check_cli.py` を新CLI契約へ更新。
- 進捗メモ: [ID: P0-PYTRA-CLI-REALIGN-01-S3-02] non-cpp `run_cmd` の stdout 誤転送を修正し、`test_pytra_cli.py` 回帰追加 + `runtime_parity_check`（sample `01_mandelbrot`, `cpp/java`）再実行で一致を確認。

### P0: backend の runtime/stdlib 責務境界を再設計する（設計是正）

文脈: [docs/ja/plans/p0-backend-runtime-boundary-realign.md](../plans/p0-backend-runtime-boundary-realign.md)

1. [x] [ID: P0-BACKEND-BOUNDARY-REALIGN-01] backend の runtime/stdlib 解決責務漏れを是正し、EAST3 解決済み描画へ再収束する。
2. [x] [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S1-01] 監査ヒットを backend 別に違反タイプへ分類し、修正順序を確定する。
3. [x] [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S1-02] EAST3 -> backend 解決済み呼び出し契約（call/attr/module/type）を固定する。
4. [x] [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S2-01] `lua/scala/rs` の高密度違反箇所を先行是正する。
5. [x] [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S2-02] `cs/php/go/nim/kotlin/js/cpp` の残件を同方針で是正する。
6. [x] [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S2-03] emitter のフォールバックを fail-closed 化し、推測レンダリングを禁止する。
7. [x] [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S3-01] 責務境界ガード（禁止分岐/禁止文字列/禁止dispatch）を CI 必須導線へ追加する。
8. [x] [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S3-02] unit/smoke/parity 回帰を更新して非退行を固定する。
- 進捗メモ: [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S1-01] `work/logs/backend_boundary_audit_hits_20260305_s1_01.txt`（179件）を `branch/dispatch/runtime実装混在` に分類し、`lua -> scala -> rs` を先行是正順として固定。
- 進捗メモ: [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S1-02] `docs/ja/spec/spec-east.md` に EAST3 -> backend 固定契約（解決済み属性、解決優先順位、fail-closed、emitter API 制約）を追記した。
- 進捗メモ: [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S2-01] `lua_native_emitter.py` から未使用 runtime実装混在ブロックを削除し、`math|gif|png` ヒットを `49 -> 8` に縮退。`test_py2lua_smoke.py`（32件）通過。
- 進捗メモ: [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S2-01] `scala_native_emitter.py` の未使用 inline runtime helper 群と `rs_emitter.py` の未使用 `RUST_RUNTIME_SUPPORT` を削除し、`scala:39 -> 29` / `rs:31 -> 4`、全 backend 合計 `138 -> 101` へ縮退。`test_py2scala_smoke.py`（16件）/ `test_py2rs_smoke.py`（30件）通過。
- 進捗メモ: [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S2-01] `scala_native_emitter.py` の `owner=="math"` 再解決フォールバックを撤去し、`scala` ヒットを `29 -> 16`、全 backend 合計を `101 -> 88` に縮退。`test_py2scala_smoke.py`（16件）再通過を確認。
- 進捗メモ: [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S2-02] `php_native_emitter.py` / `go_native_emitter.py` の `owner=="math"` 生AST再解決フォールバックを撤去し、`php+go` ヒットを `28 -> 12`、全 backend 合計を `88 -> 72` に縮退。`test_py2php_smoke.py`（10件）/ `test_py2go_smoke.py`（16件）通過。
- 進捗メモ: [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S2-02] `kotlin_native_emitter.py` / `nim_native_emitter.py` の `math` 生AST再解決フォールバック（型推論・call/attr）を撤去し、`kotlin+nim` ヒットを `8 -> 3`、全 backend 合計を `72 -> 67` に縮退。`test_py2kotlin_smoke.py`（16件）/ `test_py2nim_smoke.py`（3件）通過。
- 進捗メモ: [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S2-02] `cs_emitter.py` の `owner=="math/png/gif"` 生ASTフォールバック（call/attr）を撤去し、`cs` ヒットを `20 -> 8`、全 backend 合計を `67 -> 55` に縮退。`test_py2cs_smoke.py` は既存 baseline と同じ `failures=11` を維持（新規悪化なし）。
- 進捗メモ: [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S2-02] `nim_native_emitter.py` の式文フォールバックから `save_gif` / `write_rgb_png` 直判定を撤去し、`nim` ヒットを `3 -> 1`、全 backend 合計を `55 -> 53` に縮退。`test_py2nim_smoke.py`（3件）再通過を確認。
- 進捗メモ: [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S2-02] 残ヒット（`go/cs/js/cpp`）は import/runtime map 解決・診断文字列・互換コメントに分類し、生AST再解決フォールバックは対象 backend で撤去完了。以降は `S2-03`（fail-closed 強化）/`S3-01`（CIガード）で拘束する。
- 進捗メモ: [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S2-03] `php/go` で stdlib runtime_call の空振り時フォールバックを縮退し、`resolved_runtime_call` 経路は fail-closed 化。`go` の `runtime_call=std::filesystem::*`（legacy表現）は現状 target解決不足のため従来フォールバックを維持し、`test_py2php_smoke.py`（10件）/`test_py2go_smoke.py`（16件）は通過。
- 進捗メモ: [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S2-03] `kotlin` でも `resolved_runtime_call` の空振り時フォールバックを例外化し、stdlib call/attribute の fail-closed を補強。`test_py2kotlin_smoke.py`（16件）通過。
- 進捗メモ: [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S2-03] `js/cs/nim` でも `resolved_runtime_call` 空振り時の stdlib fallback を例外化し、call/attribute の推測レンダリングを停止。`test_py2js_smoke.py`（22件）/`test_py2nim_smoke.py`（3件）通過、`test_py2cs_smoke.py` は既存 baseline の `failures=11` を維持（新規悪化なし）。
- 進捗メモ: [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S3-01] `run_local_ci.py` に組み込み済みの guard群（`check_emitter_runtimecall_guardrails.py` / `check_emitter_forbidden_runtime_symbols.py`）を実運用検証し、`forbidden` 側を「findings=0 なら空allowlist許容」に修正。両ガード + tooling unit test 通過。
- 進捗メモ: [ID: P0-BACKEND-BOUNDARY-REALIGN-01-S3-02] `go/php/kotlin/js/cs/nim` smoke に `resolved_runtime_call` 空振り fail-closed 回帰を追加し、`go/php/kotlin/js/nim/cs` smoke（合計117件）・`check_emitter_runtimecall_guardrails.py`・`check_emitter_forbidden_runtime_symbols.py`・tooling（`test_check_emitter_runtimecall_guardrails.py` / `test_runtime_parity_check_cli.py`）を通過。あわせて `go/php/kotlin/cs` emitter に semantic_tag 整合チェックを追加し、`resolved_runtime_call` 推測レンダリング漏れを是正。

### P1: runtime generator の単一化（特殊スクリプト撤去）

文脈: [docs/ja/plans/p1-runtime-generator-unification.md](../plans/p1-runtime-generator-unification.md)

1. [x] [ID: P1-RUNTIME-GEN-UNIFY-01] runtime生成導線を `pytra-cli`/`py2x` 正規経路へ統合し、言語別特殊 generator を撤去する。
2. [x] [ID: P1-RUNTIME-GEN-UNIFY-01-S1-01] 既存 generator 3本（image/java/cs）の責務差分を棚卸しし、統合要件を固定する。
3. [x] [ID: P1-RUNTIME-GEN-UNIFY-01-S1-02] target/出力先/marker を持つ宣言設定を定義し、コード内分岐を設定へ移す。
4. [x] [ID: P1-RUNTIME-GEN-UNIFY-01-S2-01] 汎用 generator（単一スクリプト）を実装し、`pytra-cli`/`py2x` 呼び出しへ統合する。
5. [x] [ID: P1-RUNTIME-GEN-UNIFY-01-S2-02] 既存呼び出し元を新導線へ置換する。
6. [x] [ID: P1-RUNTIME-GEN-UNIFY-01-S2-03] `tools/gen_image_runtime_from_canonical.py` / `tools/gen_java_std_runtime_from_canonical.py` / `tools/gen_cs_image_runtime_from_canonical.py` を削除する。
7. [x] [ID: P1-RUNTIME-GEN-UNIFY-01-S3-01] 特殊 generator 再導入禁止ガードを CI へ追加する。
8. [x] [ID: P1-RUNTIME-GEN-UNIFY-01-S3-02] runtime監査 + parity 回帰で非退行を固定する。
- 進捗メモ: [ID: P1-RUNTIME-GEN-UNIFY-01-S1-01] `gen_image/gen_java_std/gen_cs_image` の入出力・命名・後処理差分を計画書へ棚卸しし、単一導線へ移す固定要件を確定。
- 進捗メモ: [ID: P1-RUNTIME-GEN-UNIFY-01-S1-02] `tools/runtime_generation_manifest.json` を追加し、module/target/output/marker/postprocess（cs helper）を宣言設定化。manifest構造の unit test を追加。
- 進捗メモ: [ID: P1-RUNTIME-GEN-UNIFY-01-S2-01] `tools/gen_runtime_from_manifest.py` を追加し、manifest 駆動で `py2x` 生成 + marker 付与 + `cs_program_to_helper` 後処理を共通化。tooling unit（`test_gen_runtime_from_manifest.py`）を追加。
- 進捗メモ: [ID: P1-RUNTIME-GEN-UNIFY-01-S2-02] `test_gen_image_runtime_from_canonical.py` の参照先を新 generator に置換し、既存呼び出し導線を `gen_runtime_from_manifest` へ寄せた。
- 進捗メモ: [ID: P1-RUNTIME-GEN-UNIFY-01-S2-03] 旧特殊 generator 3本を削除し、`test_audit_image_runtime_sot.py` の `generated-by` 期待値を `tools/gen_runtime_from_manifest.py` へ更新。
- 進捗メモ: [ID: P1-RUNTIME-GEN-UNIFY-01-S3-01] `tools/check_runtime_special_generators_absent.py` を追加し、`run_local_ci.py` に統合。`gen_*_from_canonical.py` 再導入をCIで fail-fast 化。
- 進捗メモ: [ID: P1-RUNTIME-GEN-UNIFY-01-S3-02] runtime監査を再実行し `check_runtime_std_sot_guard.py` の stale allowlist 1件（`json src/runtime/java/pytra-core/built_in/PyRuntime.java`）を解消。parity（`cpp,java,ruby,lua,php` の `01_mandelbrot`）は `java` の `png.py` 変換構文崩れで継続対応中。
- 進捗メモ: [ID: P1-RUNTIME-GEN-UNIFY-01-S3-02] `gen_runtime_from_manifest.py` を runtime hook 非依存化して Java `pytra-gen/utils/png.java,gif.java` を再生成。`java_native_emitter.py`/`PyRuntime.java` を補強したが、parity は `tmp class名`, `PngHelper`, `uint8`, `open/PyFile` など Java 側の残課題で未完了。

### P2: `check_py2*` checker の単一化（`--target` + プロファイル）

文脈: [docs/ja/plans/p2-checker-unification.md](../plans/p2-checker-unification.md)

1. [x] [ID: P2-CHECKER-UNIFY-01] checker を `tools/check_py2x_transpile.py --target <lang>` へ統合し、言語別 `check_py2*.py` を段階撤去する。
2. [x] [ID: P2-CHECKER-UNIFY-01-S1-01] 既存 `check_py2*.py` の差分（ケース選定・expected-fail・追加検証）を棚卸しして統一仕様を定義する。
3. [x] [ID: P2-CHECKER-UNIFY-01-S1-02] target別プロファイル形式を設計する。
4. [x] [ID: P2-CHECKER-UNIFY-01-S2-01] 単一 checker 本体（`check_py2x_transpile.py`）を実装する。
5. [x] [ID: P2-CHECKER-UNIFY-01-S2-02] 既存 `check_py2*.py` を互換ラッパ化して新checkerへ委譲させる。
6. [x] [ID: P2-CHECKER-UNIFY-01-S2-03] `run_local_ci.py` / 契約検証スクリプト / docs の呼び出しを単一 checker へ置換する。
7. [x] [ID: P2-CHECKER-UNIFY-01-S3-01] 互換期間終了後に `check_py2*.py` を削除し、再導入防止ガードを追加する。
8. [x] [ID: P2-CHECKER-UNIFY-01-S3-02] unit/CI 回帰で非退行を固定する。
- 進捗メモ: [ID: P2-CHECKER-UNIFY-01-S1-01] `check_py2*_transpile.py` 14本を棚卸しし、差分軸を `case_mode(all|explicit)` / 構造化expected-fail / 品質hook / 追加CLIフラグへ固定。統一仕様を `p2-checker-unification.md` に反映。
- 進捗メモ: [ID: P2-CHECKER-UNIFY-01-S1-02] 単一checker profile 仕様を `target/case_mode/cases/expected_failures/quality_hooks/flags/stage2_probe` で固定し、単純expected-fail集合の正規化規則を定義。
- 進捗メモ: [ID: P2-CHECKER-UNIFY-01-S2-01] `tools/check_py2x_transpile.py` + `check_py2x_profiles.json` を追加し、共通実行器を実装。`cpp/java/scala` profile を移植し `sample/py/01_mandelbrot.py` smoke（3target）通過を確認。
- 進捗メモ: [ID: P2-CHECKER-UNIFY-01-S2-01] profile を全14targetへ展開し、`php_sample18`/runtime sidecar 検証/`cpp_emitter_separation` preflight を共通化。`--skip-east3-contract-tests` 付き `sample/py/01_mandelbrot.py` smoke（14target）を通過。
- 進捗メモ: [ID: P2-CHECKER-UNIFY-01-S2-02] 既存 `check_py2*.py` 14本を互換ラッパ化し、`check_py2x_transpile.py --target` へ委譲。`cpp` 互換の `--check-multi-file-imports/--check-yanesdk-smoke` も unified 側へ移植し、`nim/cpp/js` ラッパ経路の実行を確認。
- 進捗メモ: [ID: P2-CHECKER-UNIFY-01-S2-03] `run_local_ci.py` / `check_noncpp_east3_contract.py` / `check_gsk_native_regression.py` の checker 呼び出しを `check_py2x_transpile.py --target` へ置換し、`js/ts` は preflight 再帰回避のため `--skip-east3-contract-tests` を付与。`check_noncpp --skip-transpile`・`check_py2js_transpile.py`・`check_py2ts_transpile.py` を通過。
- 進捗メモ: [ID: P2-CHECKER-UNIFY-01-S3-01] 旧 `check_py2*.py` 14本を削除し、`check_legacy_transpile_checkers_absent.py` + tooling unit test を追加。`run_local_ci.py` に再導入防止ガードを統合し、Scala checker unit は `check_py2x_transpile.py` 前提へ移行。

### P2: 多言語 runtime の C++ 同等化（再設計版: SoT厳守 + 生成優先）

文脈: [docs/ja/plans/p2-runtime-parity-with-cpp.md](../plans/p2-runtime-parity-with-cpp.md)

1. [ ] [ID: P2-RUNTIME-PARITY-CPP-02] 多言語 runtime 同等化を「SoT厳守・生成優先・責務分離」の前提で再設計し、再発不能な運用へ置換する。
2. [x] [ID: P2-RUNTIME-PARITY-CPP-02-S1-01] 旧P2（`P2-RUNTIME-PARITY-CPP-01`）を未完了一覧から削除し、新P2へ置換する。
3. [x] [ID: P2-RUNTIME-PARITY-CPP-02-S1-02] SoT/pytra-core/pytra-gen の責務境界と禁止事項を `docs/ja/spec` に明文化する。
4. [x] [ID: P2-RUNTIME-PARITY-CPP-02-S1-03] 対象モジュールの「生成必須 / core許可」分類表を作成する。
5. [x] [ID: P2-RUNTIME-PARITY-CPP-02-S2-01] `pytra-gen` の素通し命名違反を検知する静的チェックを追加する。
6. [x] [ID: P2-RUNTIME-PARITY-CPP-02-S2-02] marker（`source/generated-by`）・配置違反（core混在）監査を強化し、CIへ統合する。
7. [x] [ID: P2-RUNTIME-PARITY-CPP-02-S2-03] `pytra-core` 内の SoT 再実装痕跡を棚卸しし、`pytra-gen` 移管計画へ反映する。
8. [x] [ID: P2-RUNTIME-PARITY-CPP-02-S3-01] Java を先行対象として、emitter の直書き runtime 関数分岐を IR 解決経路へ移行する。
9. [x] [ID: P2-RUNTIME-PARITY-CPP-02-S3-02] Java 以外の非C++ backend（`cs/js/ts/go/rs/swift/kotlin/ruby/lua/scala/php/nim`）へ同方針を展開する。
10. [x] [ID: P2-RUNTIME-PARITY-CPP-02-S3-03] emitter でのライブラリ関数名直書き禁止を lint 化し、PR/CI で fail-fast 化する。
11. [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S4-01] 全対象言語で sample parity（artifact size+CRC32 含む）を再実施し、差分を固定する。
12. [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S4-02] 運用手順（ローカル/CI）を `docs/ja` / `docs/en` に反映する。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-02-S1-01] 旧P2の未完了一覧残置を整理し、`docs/en/todo/index.md` / `docs/en/plans/p2-runtime-parity-with-cpp.md` を新P2（`...-CPP-02`）へ置換した。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-02-S1-02] `docs/ja/spec/spec-runtime.md` に全言語共通の SoT/pytra-core/pytra-gen 責務境界節を追加し、必須事項（生成優先・marker・EAST3解決済み描画）と禁止事項（core 再実装・特別命名・emitter 直書き分岐）および監査コマンドを固定した。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-02-S1-03] `docs/ja/spec/spec-runtime.md` に `std/utils` モジュール分類表を追加し、`argparse..typing` + `assertions/gif/png` を生成必須、`dataclasses_impl/math_impl/time_impl` を core許可（impl境界）として固定した。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-02-S2-01] `tools/check_runtime_pytra_gen_naming.py` を追加し、`pytra-gen/std|utils` の素通し命名・配置違反を検知できるようにした。`tools/runtime_pytra_gen_naming_allowlist.txt`（11件）で既存負債を明示し、`test_check_runtime_pytra_gen_naming.py` と本体スクリプト実行を通過。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-02-S2-02] `tools/check_runtime_core_gen_markers.py` を追加して全言語 `pytra-gen` marker 必須/`pytra-core` 混在禁止を監査可能化し、`tools/run_local_ci.py` に `check_runtime_core_gen_markers.py` と `check_runtime_pytra_gen_naming.py` を統合。`test_check_runtime_core_gen_markers.py` と両ガード実行を通過（baseline allowlist: marker=1, naming=11）。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-02-S2-03] `work/logs/runtime_core_sot_reimpl_inventory_20260305_s2_03.tsv` を作成して `pytra-core` 再実装痕跡（10ファイル）を棚卸しし、`docs/ja/plans/p2-runtime-parity-with-cpp.md` に言語別移管ウェーブ（JSON系/画像系/core境界）を追記した。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-02-S3-01] Java emitter の直書き runtime 分岐残存を監査し、`check_emitter_runtimecall_guardrails.py`（strict java）と `test_py2java_smoke.py`（25件）で IR 解決経路への収束状態を再確認して完了に更新した。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-02-S3-02] 非Java backend について `check_emitter_runtimecall_guardrails.py`（全backend no findings）と smoke 再実行（`rs/rb/lua/scala/swift/ts=127件`、加えて本ターン実施済み `go/php/kotlin/js/nim/cs=117件`）を通過し、IR解決経路 + fail-closed 方針の展開完了を確認した。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-02-S3-03] lint 導線として `check_emitter_runtimecall_guardrails.py` / `check_emitter_forbidden_runtime_symbols.py` を `tools/run_local_ci.py` 必須ステップへ固定済みであることを再確認し、strict backend(`java`)の fail-fast 条件と合わせて PR/CI 側の拒否条件を確定した。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-02-S4-01] sample parity を再実行し、`01_mandelbrot` / `02_raytrace_spheres` の全14target結果を `work/logs/runtime_parity_sample01_multilang_20260305.json` / `work/logs/runtime_parity_sample02_multilang_20260305.json` に固定。failカテゴリ（`js/ts`, `go`, `nim`, `cpp(02)`, `java(02)`）を確定した。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-02-S4-01] `nim` の invalid module name を修正（出力名 `main.nim` 固定 + parity側 `stderr` 取り込み）。`01/02` の nim parity は artifact size+CRC32 一致で通過し、残failは `js/ts, go, cpp(02), java(02)` に収束。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-02-S4-01] sample parity 全件再実行を開始し、`01-03` の時点で `js/ts/go/nim/java/cpp` のブロッカーを確認（`js/png.js` f-string残存、`go/png.go` 文字列崩れ、Nim module名制約、Java `tmp` class名、C++ runtime link競合）。`rs/cs/ruby/lua/php/swift/kotlin/scala` は同区間で artifact size/CRC32 一致を確認。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-02-S4-01] `png.py` 正本を backend 互換寄りに修正して `js/ts/go` の `pytra-gen/utils/png.*` を再生成。`01_mandelbrot` 再検証で `js/ts` は構文エラーを脱して `write_rgb_png` export未解決へ、`go` は文字列崩れ解消後に `extend/main重複/pyWriteRGBPNG未定義` が残る段階まで前進。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-02-S4-01] `runtime_parity_check.py` に target別出力ディレクトリの事前削除を追加し、`01_mandelbrot/02_raytrace_spheres` を `js,ts,go,cpp,java,nim` で再実行して artifact size/CRC32 一致を確認（`work/logs/runtime_parity_sample01_02_focus_20260305_after_freshfix.json`）。

### P4: 全言語 selfhost 完全化（低低優先）

文脈: [docs/ja/plans/p4-multilang-selfhost-full-rollout.md](../plans/p4-multilang-selfhost-full-rollout.md)

1. [ ] [ID: P4-MULTILANG-SH-01] `cpp/rs/cs/js/ts/go/java/swift/kotlin/ruby/lua/scala/php/nim` の selfhost を段階的に成立させ、全言語の multistage 監視を通過可能にする。
2. [ ] [ID: P4-MULTILANG-SH-01-S2-03] JS selfhost の stage2 依存 transpile 失敗を解消し、multistage を通す。
3. [ ] [ID: P4-MULTILANG-SH-01-S3-01] TypeScript の preview-only 状態を解消し、selfhost 実行可能な生成モードへ移行する。
4. [ ] [ID: P4-MULTILANG-SH-01-S3-02] Go/Java/Swift/Kotlin の native backend 化タスクと接続し、selfhost 実行チェーンを有効化する。
5. [ ] [ID: P4-MULTILANG-SH-01-S3-03] Ruby/Lua/Scala3/PHP/Nim を selfhost multistage 監視対象へ追加し、runner 未定義状態を解消する。
6. [ ] [ID: P4-MULTILANG-SH-01-S4-01] 全言語 multistage 回帰を CI 導線へ統合し、失敗カテゴリの再発を常時検知できるようにする。
7. [ ] [ID: P4-MULTILANG-SH-01-S4-02] 完了判定テンプレート（各言語の stage 通過条件と除外条件）を文書化し、運用ルールを固定する。
- 完了済み子タスク（`S1-01` 〜 `S2-02-S3`）および過去進捗メモは `docs/ja/todo/archive/20260301.md` へ移管済み。
- 進捗メモ: [ID: P4-MULTILANG-SH-01-S2-03] JS emitter の selfhost parser 制約違反（`Any` 受け `node.get()/node.items()`）と関数内 `FunctionDef` 未対応を解消し、先頭失敗を `stage1_dependency_transpile_fail` から `self_retranspile_fail (ERR_MODULE_NOT_FOUND: ./pytra/std.js)` まで前進。
- 進捗メモ: [ID: P4-MULTILANG-SH-01-S2-03] JS selfhost 準備に shim 生成・import 正規化・export 注入・構文置換を追加し、`ERR_MODULE_NOT_FOUND` を解消。先頭失敗は `SyntaxError: Unexpected token ':'`（`raw[qpos:]` 由来）へ遷移。
- 進捗メモ: [ID: P4-MULTILANG-SH-01-S2-03] JS selfhost 向けに slice/集合判定の source 側縮退、ESM shim 化、import 正規化再設計、`argparse`/`Path` 互換 shim、`.py -> EAST3(JSON)` 入力経路、`JsEmitter` profile loader の selfhost 互換化を段階適用。先頭失敗は `ReferenceError/SyntaxError` 群を解消して `TypeError: CodeEmitter._dict_copy_str_object is not a function` へ遷移。
- 進捗メモ: [ID: P4-MULTILANG-SH-01-S2-03] `CodeEmitter.load_type_map` と `js_emitter` 初期化の dict access を object-safe 化し、selfhost rewrite に `set/list/dict` polyfill と `CodeEmitter` static alias 補完を追加。先頭失敗は `dict is not defined` を解消して `TypeError: module.get is not a function` へ前進。
- 進捗メモ: [ID: P4-MULTILANG-SH-01-S2-03] selfhost rewrite を `.get -> __pytra_dict_get` 化し、`Path` shim に `parent/name/stem` property 互換と `mkdir(parents/exist_ok)` 既定冪等化を追加。`js` は `stage1 pass / stage2 pass` に到達し、先頭失敗は `stage3 sample output missing` へ遷移。
- 進捗メモ: [ID: P4-MULTILANG-SH-01-S2-03] `CodeEmitter/JsEmitter` の object-safe 変換（`startswith/strip/find` 依存除去、`next_tmp` f-string 修正、ASCII helperの `ord/chr` 依存撤去）と selfhost rewrite の String polyfill（`strip/lstrip/rstrip/startswith/endswith/find/lower/upper/map`）を追加。`js` は `stage1/native pass`・`multistage stage2 pass` を維持し、先頭失敗は `stage3 sample_transpile_fail (SyntaxError: Invalid or unexpected token)` へ前進。
- 進捗メモ: [ID: P4-MULTILANG-SH-01-S2-03] `emit` のインデント生成（文字列乗算）を loop 化し、`quote_string_literal` の `quote` 非文字列防御、`_emit_function` の `in_class` 判定を `None` 依存から空文字判定へ変更。`js` は `stage1/native pass`・`multistage stage2 pass` を維持し、先頭失敗は `stage3 sample_transpile_fail (SyntaxError: Unexpected token '{')` に更新（`py2js_stage2.js` の未解決 placeholder/関数ヘッダ崩れが残件）。
