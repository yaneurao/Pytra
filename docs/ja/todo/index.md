# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-04

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

### P0: sample artifact CRC 一致化（Kotlin gate撤去 + Swift再検証 + fail群修復）

文脈: [docs/ja/plans/p0-multilang-artifact-crc-align.md](../plans/p0-multilang-artifact-crc-align.md)

1. [ ] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01] `sample` の artifact parity（size+CRC32）を `cpp,rs,cs,js,ts,go,java,swift,kotlin` で一致させる。
2. [x] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S1-01] Kotlin artifact gate 撤去後 baseline を固定し、失敗カテゴリを言語別にロックする。
3. [x] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S1-02] Swift toolchain 導入後の `--targets swift --all-samples` を完走して失敗カテゴリをロックする。
4. [x] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-01] Kotlin `save_gif` no-op 経路を除去し、runtime GIF writer 実装で artifact_missing を解消する。
5. [x] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-02] Kotlin PNG writer を Python準拠バイナリに揃え、01..04 の mismatch を解消する。
6. [x] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-03] Java image call を runtime 実装へ接続し、artifact_missing を解消する。
7. [ ] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-04] Java compile fail（`RuntimeError` / dict.get-default / 型）を修正して sample 実行を完走可能にする。
8. [ ] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-05] Go `__pytra_bytes([]byte)` と typed演算戻り値（`ifexp/min/max`）を修正して run_failed を解消する。
9. [ ] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-06] Go sample/18 `TokenLike` フィールドアクセス崩れを修正する。
10. [ ] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-07] Swift 引数ラベル整合（定義/呼び出し）を修正して sample 実行を成立させる。
11. [ ] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-08] JS/TS PNG/GIF writer を Python準拠バイナリへ揃えて mismatch を解消する。
12. [ ] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-09] C# image系 CRC mismatch を切り分け・修正する。
13. [ ] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-10] C++ sample/07,16 compile fail と 06/12/14 CRC mismatch を修正する。
14. [ ] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S3-01] 9言語全件で artifact parity を再実行し、`mismatch/run_failed/toolchain_missing=0` を確認する。
15. [ ] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S3-02] 回帰テストと仕様書へ CRC32 parity 運用ルールを反映する。
- 進捗メモ: [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-01] Kotlin emitter の `save_gif/grayscale_palette` を runtime 接続へ切替え、`src/runtime/kotlin/pytra/py_runtime.kt` に GIF writer を追加。`--targets kotlin --all-samples` 再実行で `artifact_missing=0` を確認（`work/logs/runtime_parity_sample_kotlin_crc_20260304_after_gif.json`）。
- 進捗メモ: [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-02] Kotlin PNG writer を Python runtime と同じ stored-block zlib/chunk 仕様へ変更し、`01..04` の size/CRC mismatch を解消（`work/logs/runtime_parity_sample_kotlin_crc_20260304_after_png_store.json`）。残件は GIF 系 `artifact_crc32_mismatch` 8件。
- 進捗メモ: [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S1-02] `runtime_parity_check.py` に `--cmd-timeout-sec` を追加して `--targets swift --all-samples` を完走化。`work/logs/runtime_parity_sample_swift_crc_20260304_all_timeout90.json` で `run_failed=17/artifact_missing=1` を固定。
- 進捗メモ: [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S1-01] 既存 `cpp..kotlin` baseline と更新版 Kotlin/Swift ログを合成し、言語別カテゴリを `work/logs/runtime_parity_sample_baseline_lock_20260304.json` へ固定。
- 進捗メモ: [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-03] Java emitter の `save_gif/write_rgb_png/grayscale_palette` を runtime 実装へ接続し、`--targets java --all-samples` 再実行で `artifact_missing=0` を確認（`work/logs/runtime_parity_sample_java_crc_20260304_after_image_connect.json`）。

### P0: sample/13 PHP parity 不一致（frames 147→2）原因調査

文脈: [docs/ja/plans/p0-php-s13-parity-investigation.md](../plans/p0-php-s13-parity-investigation.md)

1. [ ] [ID: P0-PHP-S13-PARITY-INVEST-01] `sample/13` の PHP 出力が `frames: 2` になる根本原因を特定し、修正方針を確定する。
2. [ ] [ID: P0-PHP-S13-PARITY-INVEST-01-S1-01] parity 失敗を単独再現し、実行ログと artifact 情報を採取する。
3. [ ] [ID: P0-PHP-S13-PARITY-INVEST-01-S1-02] Python と PHP の `frames` 算出経路を比較し、最初の乖離点を特定する。
4. [ ] [ID: P0-PHP-S13-PARITY-INVEST-01-S2-01] 乖離を生む層（EAST3 / lower / emitter / runtime）を 1 箇所に特定する。
5. [ ] [ID: P0-PHP-S13-PARITY-INVEST-01-S2-02] 最小再現ケース案を作成し、回帰テスト化粒度を確定する。
6. [ ] [ID: P0-PHP-S13-PARITY-INVEST-01-S3-01] 修正方針を文脈へ記録し、次段の修正タスクを起票する。

### P1: `py2x` 一本化の再開（legacy `py2*.py` wrapper 完全撤去）

文脈: [docs/ja/plans/p1-py2x-wrapper-final-removal-reopen.md](../plans/p1-py2x-wrapper-final-removal-reopen.md)

1. [ ] [ID: P1-PY2X-WRAPPER-REMOVE-REOPEN-01] archive 済みの `py2x` 統一タスクを再開し、残存する legacy wrapper（`py2rs.py`, `py2cs.py`, ...）を完全撤去する。
2. [ ] [ID: P1-PY2X-WRAPPER-REMOVE-REOPEN-01-S1-01] wrapper 参照の残存箇所を `tools/test/docs/selfhost` で再棚卸しし、置換順を確定する。
3. [ ] [ID: P1-PY2X-WRAPPER-REMOVE-REOPEN-01-S2-01] `tools/` の wrapper 直参照を `py2x` / backend module 参照へ置換する。
4. [ ] [ID: P1-PY2X-WRAPPER-REMOVE-REOPEN-01-S2-02] `test/unit` の wrapper ファイル依存テストを `py2x` 基準または backend module 基準へ置換する。
5. [ ] [ID: P1-PY2X-WRAPPER-REMOVE-REOPEN-01-S2-03] `docs/ja` / `docs/en` の wrapper 名記述を `py2x` 正規入口へ更新する。
6. [ ] [ID: P1-PY2X-WRAPPER-REMOVE-REOPEN-01-S3-01] `src/py2*.py` wrapper 群と `toolchain/compiler/py2x_wrapper.py` を削除する（`py2x.py` / `py2x-selfhost.py` は除外）。
7. [ ] [ID: P1-PY2X-WRAPPER-REMOVE-REOPEN-01-S3-02] wrapper 再流入を検知する静的ガードを更新し、削除後構成を固定する。
8. [ ] [ID: P1-PY2X-WRAPPER-REMOVE-REOPEN-01-S3-03] transpile/smoke 回帰を実行し、wrapper 撤去後の非退行を確認する。
- 進捗メモ: [ID: P1-PY2X-WRAPPER-REMOVE-REOPEN-01] archive からの差し戻し。`src/py2*.py` 実ファイルと wrapper 依存（`tools/check_multilang_selfhost_stage1.py`, `tools/check_noncpp_east3_contract.py`, `test/unit/test_py2*_smoke.py`）残存を確認し、完了判定を再オープンした。

### P1: `py2x` 共通 smoke テスト統合（全言語）

文脈: [docs/ja/plans/p1-py2x-unified-smoke-suite.md](../plans/p1-py2x-unified-smoke-suite.md)

1. [ ] [ID: P1-PY2X-SMOKE-UNIFY-01] `test_py2*_smoke.py` の共通観点を `py2x` ベースの共通 smoke へ統合し、全言語を1つの枠組みで検証できるようにする。
2. [ ] [ID: P1-PY2X-SMOKE-UNIFY-01-S1-01] `test_py2*_smoke.py` の共通観点と言語固有観点を棚卸しし、共通化対象を確定する。
3. [ ] [ID: P1-PY2X-SMOKE-UNIFY-01-S2-01] `py2x` target パラメタライズの共通 smoke テスト（新規）を追加する。
4. [ ] [ID: P1-PY2X-SMOKE-UNIFY-01-S2-02] 各言語 smoke から共通化済みケースを削減し、言語固有検証のみを残す。
5. [ ] [ID: P1-PY2X-SMOKE-UNIFY-01-S2-03] 共通 smoke と言語固有 smoke の責務境界をテストコード内コメントと計画書へ明記する。
6. [ ] [ID: P1-PY2X-SMOKE-UNIFY-01-S3-01] unit/transpile 回帰を実行し、統合後の非退行を確認する。
7. [ ] [ID: P1-PY2X-SMOKE-UNIFY-01-S3-02] `docs/ja/spec`（必要なら `docs/en/spec`）へ smoke テスト運用ルールを反映する。

### P1: `test/unit` レイアウト再編と未使用テスト整理

文脈: [docs/ja/plans/p1-test-unit-layout-and-pruning.md](../plans/p1-test-unit-layout-and-pruning.md)

1. [ ] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01] `test/unit` を責務別フォルダへ再編し、未使用テストを根拠付きで整理する。
2. [ ] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S1-01] `test/unit` の現行テストを責務分類（common/backends/ir/tooling/selfhost）で棚卸しし、移動マップを確定する。
3. [ ] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S1-02] 目標ディレクトリ規約を定義し、命名・配置ルールを決定する。
4. [ ] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S2-01] テストファイルを新ディレクトリへ移動し、`tools/` / `docs/` の参照パスを一括更新する。
5. [ ] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S2-02] `unittest discover` と個別実行導線が新構成で通るように CI/ローカルスクリプトを更新する。
6. [ ] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S3-01] 未使用テスト候補を抽出し、`削除/統合/維持` を判定する監査メモを作成する。
7. [ ] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S3-02] 判定済みの未使用テストを削除または統合し、再発防止チェック（必要なら新規）を追加する。
8. [ ] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S4-01] 主要 unit/transpile/selfhost 回帰を実行し、再編・整理後の非退行を確認する。
9. [ ] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S4-02] `docs/ja/spec`（必要なら `docs/en/spec`）へ新しいテスト配置規約と運用手順を反映する。

### P2: 多言語 runtime の C++ 同等化（API 契約・機能カバレッジ統一）

文脈: [docs/ja/plans/p2-runtime-parity-with-cpp.md](../plans/p2-runtime-parity-with-cpp.md)

1. [ ] [ID: P2-RUNTIME-PARITY-CPP-01] C++ runtime を基準に、他言語 runtime の API 契約と機能カバレッジを段階的に同等化する。
2. [x] [ID: P2-RUNTIME-PARITY-CPP-01-S1-01] C++ runtime の必須 API カタログ（module/function/契約）を抽出する。
3. [x] [ID: P2-RUNTIME-PARITY-CPP-01-S1-02] 各言語 runtime の実装有無マトリクスを作成し、欠落/互換/挙動差を分類する。
4. [x] [ID: P2-RUNTIME-PARITY-CPP-01-S1-03] 同等化対象を `Must/Should/Optional` で優先度付けする。
5. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S2-01] Wave1（`go/java/kotlin/swift`）で `math/time/pathlib/json` 不足 API を実装する。
6. [x] [ID: P2-RUNTIME-PARITY-CPP-01-S2-01-S1-01] Wave1-Go: `json.loads/dumps` runtime API を追加し、Go emitter の `json.*` 呼び出しを runtime helper へ統一する。
7. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S2-02] Wave1 の emitter 呼び出しを adapter 経由へ寄せ、API 名揺れを吸収する。
8. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S2-03] Wave1 の parity 回帰を追加し、runtime 差由来 fail を固定する。
9. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S3-01] Wave2（`ruby/lua/scala/php`）で不足 API を実装する。
10. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S3-02] Wave2 の emitter 呼び出しを adapter 経由へ寄せる。
11. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S3-03] Wave2 の parity 回帰を追加し、runtime 差由来 fail を固定する。
12. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S4-01] Wave3（`js/ts/cs/rs`）で不足 API を補完し、契約差を解消する。
13. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S4-02] runtime API 欠落検知チェックを追加し、CI/ローカル回帰へ組み込む。
14. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S4-03] `docs/ja/spec` / `docs/en/spec` に runtime 同等化ポリシーと進捗表を反映する。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-01-S1-01] `docs/ja/spec/spec-runtime.md` に C++ runtime API 正本カタログ（Must/Should）を追加し、Wave 同等化の基準 API を固定。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-01-S1-02] `src/runtime/<lang>/pytra` 棚卸し結果を `native/mono/compat/missing` でマトリクス化し、主要欠落（json/pathlib/gif）を分類。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-01-S1-03] マトリクス差分を `Must/Should/Optional` へ優先度化し、Wave1/2/3 の着手順（json/pathlib/gif優先）を確定。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-01-S2-01-S1-01] Go runtime に `pyJsonLoads/pyJsonDumps` を追加し、Go emitter の `json.loads/json.dumps` を runtime helper へ統一。`test_py2go_smoke.py` と `check_py2go_transpile.py` で非退行確認。

### P4: 全言語 selfhost 完全化（低低優先）

文脈: [docs/ja/plans/p4-multilang-selfhost-full-rollout.md](../plans/p4-multilang-selfhost-full-rollout.md)

1. [ ] [ID: P4-MULTILANG-SH-01] `cpp/rs/cs/js/ts/go/java/swift/kotlin/ruby/lua/scala` の selfhost を段階的に成立させ、全言語の multistage 監視を通過可能にする。
2. [ ] [ID: P4-MULTILANG-SH-01-S2-03] JS selfhost の stage2 依存 transpile 失敗を解消し、multistage を通す。
3. [ ] [ID: P4-MULTILANG-SH-01-S3-01] TypeScript の preview-only 状態を解消し、selfhost 実行可能な生成モードへ移行する。
4. [ ] [ID: P4-MULTILANG-SH-01-S3-02] Go/Java/Swift/Kotlin の native backend 化タスクと接続し、selfhost 実行チェーンを有効化する。
5. [ ] [ID: P4-MULTILANG-SH-01-S3-03] Ruby/Lua/Scala3 を selfhost multistage 監視対象へ追加し、runner 未定義状態を解消する。
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
