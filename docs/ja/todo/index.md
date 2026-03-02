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

### P0: `src/hooks` -> `src/backends` 一括改名（最優先の最優先）

文脈: [docs/ja/plans/p0-hooks-to-backends-oneshot-rename.md](../plans/p0-hooks-to-backends-oneshot-rename.md)

1. [x] [ID: P0-HOOKS-TO-BACKENDS-RENAME-01] backend 実装ルートを `src/hooks` から `src/backends` へ一括改名し、import/ドキュメント/検証導線を同時収束させる。
2. [x] [ID: P0-HOOKS-TO-BACKENDS-RENAME-01-S1-01] `src/hooks/**` の現行構成を棚卸しし、`src/backends/**` への 1:1 移動マップを確定する。
3. [x] [ID: P0-HOOKS-TO-BACKENDS-RENAME-01-S1-02] 改名時に影響する import 参照点（`src/`, `tools/`, `test/`）を全列挙し、更新順序を固定する。
4. [x] [ID: P0-HOOKS-TO-BACKENDS-RENAME-01-S2-01] `src/hooks` を `src/backends` へ一括移動し、パッケージ初期化ファイルを維持する。
5. [x] [ID: P0-HOOKS-TO-BACKENDS-RENAME-01-S2-02] `src/py2*.py` と compiler/utility 側 import を `hooks.*` から `backends.*` へ一括更新する。
6. [x] [ID: P0-HOOKS-TO-BACKENDS-RENAME-01-S2-03] `tools/**` / `test/**` の import を `backends.*` へ一括更新し、テスト実行導線を復旧する。
7. [x] [ID: P0-HOOKS-TO-BACKENDS-RENAME-01-S2-04] 必要最小限の互換層（`src/hooks` re-export）を設置し、当面の外部参照破断を防ぐ（不要なら設置しない）。
8. [x] [ID: P0-HOOKS-TO-BACKENDS-RENAME-01-S3-01] `docs/ja` / `docs/en` の仕様・手順書で `src/hooks` 表記を `src/backends` へ更新する。
9. [x] [ID: P0-HOOKS-TO-BACKENDS-RENAME-01-S3-02] `spec-folder` / `spec-dev` の責務記述を `backends` 名へ更新し、`hooks` を互換・退役扱いへ明記する。
10. [x] [ID: P0-HOOKS-TO-BACKENDS-RENAME-01-S4-01] 全 target の transpile チェックを再実行し、改名起因の import 崩れがないことを確認する。
11. [x] [ID: P0-HOOKS-TO-BACKENDS-RENAME-01-S4-02] `rg` による残存 `hooks.*` 参照監査を実施し、残存理由を明示して収束させる。
- 進捗メモ: [ID: P0-HOOKS-TO-BACKENDS-RENAME-01] `src/hooks` を `src/backends` へ移動し、`src/test/tools` の import を `backends.*` へ更新。`check_py2cpp_transpile`/`check_py2rs_transpile` は通過、`check_py2cs_transpile` は既知2件失敗（`yield_generator_min.py`, `tuple_assign.py`）を確認。

### P0: C++ 3段構成移行（案1: `CppLower` / `CppIrOptimizer` / `CppEmitter`）

文脈: [docs/ja/plans/p0-cpp-lower-pipeline-rollout.md](../plans/p0-cpp-lower-pipeline-rollout.md)

1. [ ] [ID: P0-CPP-LOWER-PIPELINE-01] C++ backend を `EAST3 -> CppLower -> CppIrOptimizer -> CppEmitter` 構成へ移行し、責務境界を固定する。
2. [x] [ID: P0-CPP-LOWER-PIPELINE-01-S1-01] C++ IR の最小ノード集合（Stmt/Expr/Type/Decl）と fail-closed 契約を定義する。
3. [x] [ID: P0-CPP-LOWER-PIPELINE-01-S1-02] 案1のファイル責務（`cpp_lower.py` / `cpp_ir_optimizer.py` / `cpp_emitter.py`）と公開 API を固定する。
4. [x] [ID: P0-CPP-LOWER-PIPELINE-01-S2-01] `cpp_lower.py` を新設し、EAST3 Module から C++ IR Module へ lower する骨格を実装する。
5. [x] [ID: P0-CPP-LOWER-PIPELINE-01-S2-02] `cpp_ir_optimizer.py` を新設し、既存 optimizer pass の移設/再配線方針を実装する。
6. [x] [ID: P0-CPP-LOWER-PIPELINE-01-S2-03] `py2cpp` から新パイプラインを呼び出す配線と dump/trace 入口を追加する。
7. [ ] [ID: P0-CPP-LOWER-PIPELINE-01-S3-01] 文単位の構造決定（loop/if/tuple unpack など）を emitter から lower/optimizer 側へ移設する。
8. [ ] [ID: P0-CPP-LOWER-PIPELINE-01-S3-02] 式単位の正規化（cast/compare/binop の冗長除去）を emitter から lower/optimizer 側へ移設する。
9. [ ] [ID: P0-CPP-LOWER-PIPELINE-01-S3-03] `CppEmitter` の EAST3 直接分岐を削減し、C++ IR レンダラ責務へ縮退する。
10. [x] [ID: P0-CPP-LOWER-PIPELINE-01-S4-01] lower/optimizer/emitter 境界を検証する unit テストを追加し、回帰を固定する。
11. [x] [ID: P0-CPP-LOWER-PIPELINE-01-S4-02] C++ transpile/sample/parity を実施し、非退行を確認する。
- 進捗メモ: [ID: P0-CPP-LOWER-PIPELINE-01] `CppLower` / `CppIrOptimizer` を新設し、`emit_cpp_from_east` を `lower -> optimizer -> emitter` へ配線。`test_cpp_optimizer*` と `check_py2cpp_transpile`（136/136, skip6）を通過。
- 進捗メモ: [ID: P0-CPP-LOWER-PIPELINE-01] `CppBraceOmitHintPass` を追加して `If/ForCore` の brace 省略判定を optimizer 側へ移し、emitter は `cpp_omit_braces_v1` ヒント優先で描画するように更新。
- 進捗メモ: [ID: P0-CPP-LOWER-PIPELINE-01] `sample/cpp` の `01/08/18` を再生成し、`runtime_parity_check`（target=cpp）で 3/3 pass を確認した。
- 進捗メモ: [ID: P0-CPP-LOWER-PIPELINE-01] `CppForIterModeHintPass` で legacy `For` の iter_mode 決定を optimizer へ移し、`cpp_iter_mode_v1` を emitter 側で優先利用するように更新。
- 進捗メモ: [ID: P0-CPP-LOWER-PIPELINE-01] `CppCastCallNormalizePass` を追加し、`py_to_*` 入れ子と `static_cast` 重複の式正規化を optimizer 側へ移設した。
- 進捗メモ: [ID: P0-CPP-LOWER-PIPELINE-01] `CppCompareNormalizePass` を追加し、bool 比較（`== True/False`, `!= True/False`）の冗長形を optimizer 側で正規化した。

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
