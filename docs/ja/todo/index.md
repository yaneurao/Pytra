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

### P2: 多言語 runtime の C++ 同等化（再設計版: SoT厳守 + 生成優先）

文脈: [docs/ja/plans/p2-runtime-parity-with-cpp.md](../plans/p2-runtime-parity-with-cpp.md)

1. [ ] [ID: P2-RUNTIME-PARITY-CPP-02] 多言語 runtime 同等化を「SoT厳守・生成優先・責務分離」の前提で再設計し、再発不能な運用へ置換する。
2. [x] [ID: P2-RUNTIME-PARITY-CPP-02-S1-01] 旧P2（`P2-RUNTIME-PARITY-CPP-01`）を未完了一覧から削除し、新P2へ置換する。
3. [x] [ID: P2-RUNTIME-PARITY-CPP-02-S1-02] SoT/pytra-core/pytra-gen の責務境界と禁止事項を `docs/ja/spec` に明文化する。
4. [x] [ID: P2-RUNTIME-PARITY-CPP-02-S1-03] 対象モジュールの「生成必須 / core許可」分類表を作成する。
5. [x] [ID: P2-RUNTIME-PARITY-CPP-02-S2-01] `pytra-gen` の素通し命名違反を検知する静的チェックを追加する。
6. [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S2-02] marker（`source/generated-by`）・配置違反（core混在）監査を強化し、CIへ統合する。
7. [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S2-03] `pytra-core` 内の SoT 再実装痕跡を棚卸しし、`pytra-gen` 移管計画へ反映する。
8. [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S3-01] Java を先行対象として、emitter の直書き runtime 関数分岐を IR 解決経路へ移行する。
9. [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S3-02] Java 以外の非C++ backend（`cs/js/ts/go/rs/swift/kotlin/ruby/lua/scala/php/nim`）へ同方針を展開する。
10. [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S3-03] emitter でのライブラリ関数名直書き禁止を lint 化し、PR/CI で fail-fast 化する。
11. [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S4-01] 全対象言語で sample parity（artifact size+CRC32 含む）を再実施し、差分を固定する。
12. [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S4-02] 運用手順（ローカル/CI）を `docs/ja` / `docs/en` に反映する。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-02-S1-01] 旧P2の未完了一覧残置を整理し、`docs/en/todo/index.md` / `docs/en/plans/p2-runtime-parity-with-cpp.md` を新P2（`...-CPP-02`）へ置換した。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-02-S1-02] `docs/ja/spec/spec-runtime.md` に全言語共通の SoT/pytra-core/pytra-gen 責務境界節を追加し、必須事項（生成優先・marker・EAST3解決済み描画）と禁止事項（core 再実装・特別命名・emitter 直書き分岐）および監査コマンドを固定した。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-02-S1-03] `docs/ja/spec/spec-runtime.md` に `std/utils` モジュール分類表を追加し、`argparse..typing` + `assertions/gif/png` を生成必須、`dataclasses_impl/math_impl/time_impl` を core許可（impl境界）として固定した。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-02-S2-01] `tools/check_runtime_pytra_gen_naming.py` を追加し、`pytra-gen/std|utils` の素通し命名・配置違反を検知できるようにした。`tools/runtime_pytra_gen_naming_allowlist.txt`（11件）で既存負債を明示し、`test_check_runtime_pytra_gen_naming.py` と本体スクリプト実行を通過。

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
