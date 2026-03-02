# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-03

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

### P0: Nim runtime 整備で `sample/` parity 全件通過

文脈: [docs/ja/plans/p0-nim-sample-parity-runtime-hardening.md](../plans/p0-nim-sample-parity-runtime-hardening.md)

1. [x] [ID: P0-NIM-SAMPLE-PARITY-RUNTIME-01] Nim runtime を整備し、`sample/` の Nim parity を全件通過させる。
2. [x] [ID: P0-NIM-SAMPLE-PARITY-RUNTIME-01-S1-01] `sample` 全件の Nim parity ベースラインを取得し、失敗ケース一覧と失敗カテゴリを確定する。
3. [x] [ID: P0-NIM-SAMPLE-PARITY-RUNTIME-01-S1-02] 失敗ケースを runtime API 不足・契約不整合・emitter 側問題に切り分け、修正優先順を確定する。
4. [x] [ID: P0-NIM-SAMPLE-PARITY-RUNTIME-01-S2-01] `py_runtime.nim` の不足 API を fail-closed で補完する。
5. [x] [ID: P0-NIM-SAMPLE-PARITY-RUNTIME-01-S2-02] emitter と runtime の呼び出し契約を整合し、必要な出力修正を実施する。
6. [x] [ID: P0-NIM-SAMPLE-PARITY-RUNTIME-01-S2-03] case 固有崩れを最小修正で解消する。
7. [x] [ID: P0-NIM-SAMPLE-PARITY-RUNTIME-01-S3-01] `sample/nim` を再生成し、transpile/compile/runtime エラーを全件解消する。
8. [x] [ID: P0-NIM-SAMPLE-PARITY-RUNTIME-01-S3-02] `runtime_parity_check --targets nim --ignore-unstable-stdout` 全件 pass を確認する。
9. [x] [ID: P0-NIM-SAMPLE-PARITY-RUNTIME-01-S3-03] `check_py2nim_transpile` と関連回帰で非退行を確認する。
- 進捗メモ: [ID: P0-NIM-SAMPLE-PARITY-RUNTIME-01-S3-03] `sample/nim`（18ケース + `py_runtime.nim`）を再生成し、`runtime_parity_check --case-root sample --targets nim --ignore-unstable-stdout` は `cases=18 pass=18 fail=0`、`check_py2nim_transpile` は `checked=7 ok=7 fail=0` を確認。

### P1: 非C++ backend 3層再整列（`Lower` / `Optimizer` / `Emitter`）

文脈: [docs/ja/plans/p1-multilang-backend-3layer-realign.md](../plans/p1-multilang-backend-3layer-realign.md)

1. [x] [ID: P1-MULTILANG-BACKEND-3LAYER-01] 非C++ backend を順次 `Lower -> Optimizer -> Emitter` の3層へ再整列し、責務境界を統一する。
2. [x] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S1-01] 非C++ backend の現状責務（意味決定/正規化/描画）の棚卸しを作成する。
3. [x] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S1-02] 3層契約（LangIR最小契約・fail-closed・層別禁止事項）を定義する。
4. [x] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S1-03] ディレクトリ/命名/import 規約を文書化する。
5. [x] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S2-01] Wave1: `rs` に `lower/optimizer` 骨格を導入し、`py2rs` を3層配線へ切り替える。
6. [x] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S2-02] Wave1: `scala` に `lower/optimizer` 骨格を導入し、`py2scala` を3層配線へ切り替える。
7. [x] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S2-03] Wave1 回帰（unit/transpile/sample）を固定し、移行テンプレートを確定する。
8. [x] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S3-01] Wave2: `js/ts/cs` に同テンプレートを展開する。
9. [x] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S3-02] Wave3: `go/java/kotlin/swift` に同テンプレートを展開する。
10. [x] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S3-03] Wave4: `ruby/lua/php` に同テンプレートを展開する。
11. [x] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S4-01] 旧構成再発防止チェック（旧 import / emitter責務逆流）を追加する。
12. [x] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S4-02] `docs/ja/spec` / `docs/en/spec` に3層標準構成を反映する。
- 進捗メモ: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S1-01] `src/backends/{rs,cs,js,ts,go,java,kotlin,swift,ruby,lua,scala,php,nim}` の責務棚卸しを完了し、全backendで意味決定/正規化/描画が emitter 側へ混在している事実を整理。
- 進捗メモ: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S1-02] Lower/Optimizer/Emitter の入出力契約・禁止事項・fail-closed ルールを計画書へ明文化。
- 進捗メモ: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S1-03] `lower/optimizer/emitter` の命名規約と import 規約（`py2<lang>.py` は3層配線のみ）を確定。
- 進捗メモ: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S2-01] `backends/rs/lower`・`backends/rs/optimizer` を追加し、`py2rs.py` を `lower -> optimizer -> emitter` 配線へ切替。1ケース smoke と `check_py2rs_transpile` pass で非退行を確認。
- 進捗メモ: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S2-02] `backends/scala/lower`・`backends/scala/optimizer` を追加し、`py2scala.py` を `lower -> optimizer -> emitter` 配線へ切替。`check_py2scala_transpile` は `checked=141 ok=141 fail=0` で通過。
- 進捗メモ: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S2-03] `scala` の `bytearray/bytes` 戻り型と `ForCore` 条件式フォールバックを修正し、Wave1 回帰（`check_py2{rs,scala}_transpile` と `runtime_parity_check --case-root sample --targets rs,scala --ignore-unstable-stdout`）を全通過。
- 進捗メモ: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S3-01] `js/ts/cs` へ `lower/optimizer` 骨格を追加し `py2{js,ts,cs}` を3層配線へ切替。`check_py2{js,ts,cs}_transpile` は全通過（各 `checked=133 ok=133 fail=0 skipped=8`）。
- 進捗メモ: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S3-02] `go/java/kotlin/swift` へ `lower/optimizer` 骨格を追加し `py2{go,java,kotlin,swift}` を3層配線へ切替。`check_py2{go,java,kotlin,swift}_transpile` は全通過（各 `checked=131 ok=131 fail=0 skipped=10`）。
- 進捗メモ: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S3-03] `ruby/lua/php` へ `lower/optimizer` 骨格を追加し `py2{rb,lua,php}` を3層配線へ切替。`check_py2{rb,lua,php}_transpile` は全通過（`rb:132/132`, `lua:89/89`, `php:10/10`）。
- 進捗メモ: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S4-01] `check_noncpp_east3_contract.py` を 12 backend（`rs/cs/js/ts/go/java/kotlin/swift/ruby/lua/php/scala`）対応へ拡張し、3層配線必須パターンと layer逆流 import 禁止の静的ガードを追加。transpile 回帰（12本）も全通過。
- 進捗メモ: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S4-02] `docs/ja/spec/{spec-dev,spec-folder}.md` と `docs/en/spec/{spec-dev,spec-folder}.md` に3層標準構成（適用 backend、層責務、逆流禁止、検査コマンド）を反映し、P1 を完了化。

### P2: `py2x.py` 一本化 frontend 導入（層別 option pass-through）

文脈: [docs/ja/plans/p2-py2x-unified-frontend-rollout.md](../plans/p2-py2x-unified-frontend-rollout.md)

1. [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01] `py2x.py` を共通 frontend として導入し、言語別 `py2*.py` の重複責務を backend registry + 層別 option へ再編する。
2. [x] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S1-01] 現行 `py2*.py` の CLI 差分と runtime 配置差分を棚卸しし、共通 frontend 化で残す差分を確定する。
3. [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S1-02] `py2x` 共通 CLI 仕様を策定する（`--target`, 層別 option, 互換オプション, fail-fast 規約）。
4. [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S1-03] backend registry 契約（entrypoint, default options, option schema, runtime packaging hook）を定義する。
5. [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S2-01] `py2x.py` を実装し、共通入力処理（`.py/.json -> EAST3`）と target dispatch を導入する。
6. [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S2-02] 層別 option parser（`--lower-option`, `--optimizer-option`, `--emitter-option`）と schema 検証を実装する。
7. [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S2-03] 既存 `py2*.py` を thin wrapper 化し、互換 CLI を `py2x` 呼び出しへ委譲する。
8. [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S2-04] runtime/packaging 差分を backend extensions hook へ移し、frontend 側分岐を削減する。
9. [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S3-01] CLI 単体テストを追加し、target dispatch と層別 option 伝搬を固定する。
10. [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S3-02] 既存 transpile check 群を `py2x` 経由でも通し、言語横断で非退行を確認する。
11. [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S3-03] `docs/ja` / `docs/en` の使い方・仕様を更新し、移行手順（互換ラッパ期間を含む）を明文化する。
- 進捗メモ: [ID: P2-PY2X-UNIFIED-FRONTEND-01-S1-01] `py2*.py` の CLI/runtime 配置差分を棚卸しし、共通 frontend 化後に残す差分を `runtime_packaging_hook`・backend post-process・`py2cpp.py` 互換ラッパ維持の3分類で確定。

### P2: 多言語 runtime の C++ 同等化（API 契約・機能カバレッジ統一）

文脈: [docs/ja/plans/p2-runtime-parity-with-cpp.md](../plans/p2-runtime-parity-with-cpp.md)

1. [ ] [ID: P2-RUNTIME-PARITY-CPP-01] C++ runtime を基準に、他言語 runtime の API 契約と機能カバレッジを段階的に同等化する。
2. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S1-01] C++ runtime の必須 API カタログ（module/function/契約）を抽出する。
3. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S1-02] 各言語 runtime の実装有無マトリクスを作成し、欠落/互換/挙動差を分類する。
4. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S1-03] 同等化対象を `Must/Should/Optional` で優先度付けする。
5. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S2-01] Wave1（`go/java/kotlin/swift`）で `math/time/pathlib/json` 不足 API を実装する。
6. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S2-02] Wave1 の emitter 呼び出しを adapter 経由へ寄せ、API 名揺れを吸収する。
7. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S2-03] Wave1 の parity 回帰を追加し、runtime 差由来 fail を固定する。
8. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S3-01] Wave2（`ruby/lua/scala/php`）で不足 API を実装する。
9. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S3-02] Wave2 の emitter 呼び出しを adapter 経由へ寄せる。
10. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S3-03] Wave2 の parity 回帰を追加し、runtime 差由来 fail を固定する。
11. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S4-01] Wave3（`js/ts/cs/rs`）で不足 API を補完し、契約差を解消する。
12. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S4-02] runtime API 欠落検知チェックを追加し、CI/ローカル回帰へ組み込む。
13. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S4-03] `docs/ja/spec` / `docs/en/spec` に runtime 同等化ポリシーと進捗表を反映する。

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
