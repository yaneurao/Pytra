# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-02

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

### P0: Nim toolchain 導入 + py2nim 実装 + test 通過

文脈: [docs/ja/plans/p0-nim-toolchain-py2nim-testpass.md](../plans/p0-nim-toolchain-py2nim-testpass.md)

1. [x] [ID: P0-NIM-TOOLCHAIN-PY2NIM-01] この環境に Nim コンパイラを導入し、`py2nim.py` の実装と Nim 対象 `test/` 通過までを完了する。
2. [x] [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S1-01] Nim コンパイラ導入方式（パッケージマネージャ/バージョン固定）を決定し、この環境へ導入する。
3. [x] [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S1-02] `nim --version` と最小 compile 実行で toolchain 稼働を確認し、再現手順を残す。
4. [x] [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S2-01] Nim backend の実装配置を `src/backends/nim/emitter/` 基準へ整理し、`src/hooks/nim` 依存を解消する。
5. [x] [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S2-02] `src/py2nim.py` を実装し、EAST3 only・runtime 分離コピー・fail-closed を満たす CLI 導線を作る。
6. [x] [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S2-03] Nim native emitter の最小対応（関数/分岐/ループ/主要式）を整備し、既知 fixture を変換可能にする。
7. [x] [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S2-04] `src/runtime/nim/pytra/py_runtime.nim` を整備し、生成コードからの参照契約を固定する。
8. [x] [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S3-01] `test/unit/test_py2nim_smoke.py` と必要 fixture を整備し、Nim 導線の最小回帰を固定する。
9. [x] [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S3-02] `tools/check_py2nim_transpile.py` を整備して transpile 一括回帰を追加する。
10. [x] [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S3-03] Nim 対象 test/check を実行して pass を確認し、結果を記録する。
11. [x] [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S3-04] 既存主要チェック（`check_py2cpp_transpile` など）で非退行を確認する。
- 進捗メモ: [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S1-01] Nim 1.6.10 を `apt-get install -y nim` で導入し、`nim` コマンドを有効化。
- 進捗メモ: [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S2-01] `src/backends/nim/emitter` を新設し、`src/hooks/nim` 依存を撤去（旧 `src/hooks/nim` は削除）。
- 進捗メモ: [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S2-02] `src/py2nim.py`（EAST3 only / runtime 分離）を実装し、`--east-stage 2` を明示拒否。
- 進捗メモ: [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S3-03] `check_py2nim_transpile` と `test_py2nim_smoke` を pass、`py2nim -> nim c` の最小 compile 成功を確認。
- 進捗メモ: [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S3-04] `python3 tools/check_py2cpp_transpile.py` は `checked=140 ok=140 fail=0 skipped=6` で非退行を確認。

### P0: C++ backend ディレクトリ再整列（5フォルダ -> `lower/optimizer/emitter`）

文脈: [docs/ja/plans/p0-cpp-backend-dir-realign.md](../plans/p0-cpp-backend-dir-realign.md)

1. [ ] [ID: P0-CPP-DIR-REALIGN-01] `src/backends/cpp/` 直下の `hooks/header/multifile/profile/runtime_emit` を責務境界に沿って再配置し、構成を `lower/optimizer/emitter` 中心へ整理する。
2. [x] [ID: P0-CPP-DIR-REALIGN-01-S1-01] 現行 5 フォルダの責務と参照元を棚卸しし、移設先を確定する。
3. [x] [ID: P0-CPP-DIR-REALIGN-01-S1-02] 新配置の命名規約と import 境界を文書化する。
4. [x] [ID: P0-CPP-DIR-REALIGN-01-S2-01] `profile` を `emitter` 配下へ移設し、`py2cpp`/`CppEmitter` の参照を更新する。
5. [x] [ID: P0-CPP-DIR-REALIGN-01-S2-02] `hooks` を `emitter` 配下へ移設し、hook factory 導線を更新する。
6. [x] [ID: P0-CPP-DIR-REALIGN-01-S2-03] `runtime_emit` を `emitter` 配下へ移設し、runtime path/include 解決を更新する。
7. [ ] [ID: P0-CPP-DIR-REALIGN-01-S2-04] `header` を `emitter` 配下へ移設し、header 生成導線を更新する。
8. [ ] [ID: P0-CPP-DIR-REALIGN-01-S2-05] `multifile` を `emitter` 配下へ移設し、multi-file 出力導線を更新する。
9. [ ] [ID: P0-CPP-DIR-REALIGN-01-S2-06] 旧 5 フォルダを削除し、旧 import を全面撤去する。
10. [ ] [ID: P0-CPP-DIR-REALIGN-01-S3-01] 旧 import 再発防止チェックを追加する。
11. [ ] [ID: P0-CPP-DIR-REALIGN-01-S3-02] unit/transpile/sample 回帰で非退行を確認する。
- 進捗メモ: [ID: P0-CPP-DIR-REALIGN-01-S1-01] 5 フォルダの責務/参照元を棚卸しし、移設先を `emitter` 配下へ確定。
- 進捗メモ: [ID: P0-CPP-DIR-REALIGN-01-S1-02] `src/backends/cpp/` 直下を `lower/optimizer/emitter` 限定とする命名・import 規約を文書化。
- 進捗メモ: [ID: P0-CPP-DIR-REALIGN-01-S2-01] `profile` 実体を `emitter/profile_loader.py` へ移設し、`py2cpp`/`CppEmitter` 側 import を新パスへ切り替え。
- 進捗メモ: [ID: P0-CPP-DIR-REALIGN-01-S2-02] `hooks` 実体を `emitter/hooks_registry.py` へ移設し、hook factory 参照（`py2cpp`/profile/profile.json）を更新。
- 進捗メモ: [ID: P0-CPP-DIR-REALIGN-01-S2-03] `runtime_emit` 実体を `emitter/runtime_paths.py` へ移設し、`py2cpp`/`CppModuleEmitter` の runtime path/include 解決参照を更新。

### P1: sample/18 PHP コード生成改善（実行可能化 + 品質向上）

文脈: [docs/ja/plans/p1-php-s18-codegen-quality-uplift.md](../plans/p1-php-s18-codegen-quality-uplift.md)

1. [ ] [ID: P1-PHP-S18-CODEGEN-QUALITY-01] `sample/php/18_mini_language_interpreter.php` のコード生成品質を改善し、実行可能性と意味互換を回復する。
2. [ ] [ID: P1-PHP-S18-CODEGEN-QUALITY-01-S1-01] `sample/18` の失敗断片（dict literal / membership / ctor / entrypoint）を棚卸しし、改善境界を固定する。
3. [ ] [ID: P1-PHP-S18-CODEGEN-QUALITY-01-S2-01] PHP emitter の dict literal 出力を修正し、キー付き連想配列を正しく生成する。
4. [ ] [ID: P1-PHP-S18-CODEGEN-QUALITY-01-S2-02] `in` / `not in` の lower を型別に修正し、dict membership を `array_key_exists` 系へ統一する。
5. [ ] [ID: P1-PHP-S18-CODEGEN-QUALITY-01-S2-03] dataclass 由来クラス（`Token/ExprNode/StmtNode`）のフィールド/コンストラクタ出力を整合させる。
6. [ ] [ID: P1-PHP-S18-CODEGEN-QUALITY-01-S2-04] `main_guard` 出力の entrypoint 名衝突回避を一般化し、`sample/18` で衝突しないことを保証する。
7. [ ] [ID: P1-PHP-S18-CODEGEN-QUALITY-01-S3-01] unit/smoke 回帰を追加し、同種崩れ（dict/in/ctor/entrypoint）の再発検知を固定する。
8. [ ] [ID: P1-PHP-S18-CODEGEN-QUALITY-01-S3-02] `sample/php/18` 再生成と parity 実行で非退行を確認する。

### P1: 非C++ backend 3層再整列（`Lower` / `Optimizer` / `Emitter`）

文脈: [docs/ja/plans/p1-multilang-backend-3layer-realign.md](../plans/p1-multilang-backend-3layer-realign.md)

1. [ ] [ID: P1-MULTILANG-BACKEND-3LAYER-01] 非C++ backend を順次 `Lower -> Optimizer -> Emitter` の3層へ再整列し、責務境界を統一する。
2. [ ] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S1-01] 非C++ backend の現状責務（意味決定/正規化/描画）の棚卸しを作成する。
3. [ ] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S1-02] 3層契約（LangIR最小契約・fail-closed・層別禁止事項）を定義する。
4. [ ] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S1-03] ディレクトリ/命名/import 規約を文書化する。
5. [ ] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S2-01] Wave1: `rs` に `lower/optimizer` 骨格を導入し、`py2rs` を3層配線へ切り替える。
6. [ ] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S2-02] Wave1: `scala` に `lower/optimizer` 骨格を導入し、`py2scala` を3層配線へ切り替える。
7. [ ] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S2-03] Wave1 回帰（unit/transpile/sample）を固定し、移行テンプレートを確定する。
8. [ ] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S3-01] Wave2: `js/ts/cs` に同テンプレートを展開する。
9. [ ] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S3-02] Wave3: `go/java/kotlin/swift` に同テンプレートを展開する。
10. [ ] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S3-03] Wave4: `ruby/lua/php` に同テンプレートを展開する。
11. [ ] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S4-01] 旧構成再発防止チェック（旧 import / emitter責務逆流）を追加する。
12. [ ] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S4-02] `docs/ja/spec` / `docs/en/spec` に3層標準構成を反映する。

### P2: `py2x.py` 一本化 frontend 導入（層別 option pass-through）

文脈: [docs/ja/plans/p2-py2x-unified-frontend-rollout.md](../plans/p2-py2x-unified-frontend-rollout.md)

1. [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01] `py2x.py` を共通 frontend として導入し、言語別 `py2*.py` の重複責務を backend registry + 層別 option へ再編する。
2. [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S1-01] 現行 `py2*.py` の CLI 差分と runtime 配置差分を棚卸しし、共通 frontend 化で残す差分を確定する。
3. [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S1-02] `py2x` 共通 CLI 仕様を策定する（`--target`, 層別 option, 互換オプション, fail-fast 規約）。
4. [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S1-03] backend registry 契約（entrypoint, default options, option schema, runtime packaging hook）を定義する。
5. [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S2-01] `py2x.py` を実装し、共通入力処理（`.py/.json -> EAST3`）と target dispatch を導入する。
6. [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S2-02] 層別 option parser（`--lower-option`, `--optimizer-option`, `--emitter-option`）と schema 検証を実装する。
7. [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S2-03] 既存 `py2*.py` を thin wrapper 化し、互換 CLI を `py2x` 呼び出しへ委譲する。
8. [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S2-04] runtime/packaging 差分を backend extensions hook へ移し、frontend 側分岐を削減する。
9. [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S3-01] CLI 単体テストを追加し、target dispatch と層別 option 伝搬を固定する。
10. [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S3-02] 既存 transpile check 群を `py2x` 経由でも通し、言語横断で非退行を確認する。
11. [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S3-03] `docs/ja` / `docs/en` の使い方・仕様を更新し、移行手順（互換ラッパ期間を含む）を明文化する。

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
