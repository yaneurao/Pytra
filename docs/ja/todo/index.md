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

### P0: `backends/common` 基盤導入（`CodeEmitter` + profiles 集約）

文脈: [docs/ja/plans/p0-backends-common-foundation.md](../plans/p0-backends-common-foundation.md)

1. [x] [ID: P0-BACKENDS-COMMON-FOUNDATION-01] `src/backends/common` を導入し、`CodeEmitter` / profiles の共通基盤を `backends` 配下へ統一する。
2. [x] [ID: P0-BACKENDS-COMMON-FOUNDATION-01-S1-01] 共通資産（`CodeEmitter` / hooks / profile loader / profile JSON）の現行配置と参照点を棚卸しする。
3. [x] [ID: P0-BACKENDS-COMMON-FOUNDATION-01-S1-02] `backends/common` と `backends/<lang>/profiles` の配置規約・依存方向を定義する。
4. [x] [ID: P0-BACKENDS-COMMON-FOUNDATION-01-S2-01] `src/backends/common` を新設し、`CodeEmitter` / `EmitterHooks` を移設する。
5. [x] [ID: P0-BACKENDS-COMMON-FOUNDATION-01-S2-02] `src/profiles/common/*` を `src/backends/common/profiles/*` へ移設する。
6. [x] [ID: P0-BACKENDS-COMMON-FOUNDATION-01-S2-03] `src/profiles/<lang>/*` を `src/backends/<lang>/profiles/*` へ移設し、参照更新する。
7. [x] [ID: P0-BACKENDS-COMMON-FOUNDATION-01-S2-04] 旧 import 経路に対する互換 shim（必要最小限）を導入し、段階移行の破断を防ぐ。
8. [x] [ID: P0-BACKENDS-COMMON-FOUNDATION-01-S3-01] `rg` 監査で `src/profiles/` 直参照と旧 `code_emitter` 参照の残存を解消する。
9. [x] [ID: P0-BACKENDS-COMMON-FOUNDATION-01-S3-02] 主要 transpile チェックを通し、改修起因の非退行を確認する。
10. [x] [ID: P0-BACKENDS-COMMON-FOUNDATION-01-S3-03] `docs/ja/spec`（必要なら `docs/en/spec`）へ責務境界とフォルダ規約を反映する。

### P0: `py2x` エントリ分離（通常 `py2x.py` / selfhost `py2x-selfhost.py`）

文脈: [docs/ja/plans/p0-py2x-dual-entrypoints-host-selfhost.md](../plans/p0-py2x-dual-entrypoints-host-selfhost.md)

1. [ ] [ID: P0-PY2X-DUAL-ENTRYPOINT-01] `py2x.py`（通常）と `py2x-selfhost.py`（selfhost）を分離し、通常は lazy import・selfhost は static import を固定する。
2. [x] [ID: P0-PY2X-DUAL-ENTRYPOINT-01-S1-01] 現行 `py2x` 導線（通常実行/selfhost実行）の import 制約と責務境界を棚卸しする。
3. [x] [ID: P0-PY2X-DUAL-ENTRYPOINT-01-S1-02] `py2x.py`（host）と `py2x-selfhost.py`（selfhost）の契約（許可/禁止事項）を定義する。
4. [ ] [ID: P0-PY2X-DUAL-ENTRYPOINT-01-S2-01] `py2x.py` を host-lazy 専用実装へ整理する（selfhost 条件分岐を排除）。
5. [ ] [ID: P0-PY2X-DUAL-ENTRYPOINT-01-S2-02] `py2x-selfhost.py` を新設し、static eager import のみで同等CLIを提供する。
6. [ ] [ID: P0-PY2X-DUAL-ENTRYPOINT-01-S2-03] backend registry 依存を host/selfhost で分離し、境界違反を検知できる形にする。
7. [ ] [ID: P0-PY2X-DUAL-ENTRYPOINT-01-S3-01] unit/transpile 回帰を実行し、通常導線の非退行を確認する。
8. [ ] [ID: P0-PY2X-DUAL-ENTRYPOINT-01-S3-02] selfhost 用導線の smoke/最小回帰を実行し、動的 import 非依存を確認する。
9. [ ] [ID: P0-PY2X-DUAL-ENTRYPOINT-01-S3-03] docs に使い分けと移行手順を追記する。

### P0: `src/pytra` 3層分離ブートストラップ（`frontends` / `ir` / `backend`）

文脈: [docs/ja/plans/p0-pytra-src-3layer-bootstrap.md](../plans/p0-pytra-src-3layer-bootstrap.md)

1. [ ] [ID: P0-PYTRA-SRC-3LAYER-01] `src/pytra` 名前空間を維持しつつ `frontends` / `ir` を導入し、`compiler` 混在責務を段階的に分離する。
2. [ ] [ID: P0-PYTRA-SRC-3LAYER-01-S1-01] `src/pytra/compiler` 配下を棚卸しし、`frontends` / `ir` / 互換層に分類する。
3. [ ] [ID: P0-PYTRA-SRC-3LAYER-01-S1-02] `src/pytra` 名前空間維持前提のディレクトリ規約と import 境界（依存方向）を定義する。
4. [ ] [ID: P0-PYTRA-SRC-3LAYER-01-S2-01] `src/pytra/frontends` / `src/pytra/ir` を新設し、最小 bootstrap モジュールを配置する。
5. [ ] [ID: P0-PYTRA-SRC-3LAYER-01-S2-02] Python入力〜EAST1 生成の frontends 相当モジュールを `src/pytra/frontends` へ移設する。
6. [ ] [ID: P0-PYTRA-SRC-3LAYER-01-S2-03] EAST1/2/3・lower/optimizer/analysis の IR 相当モジュールを `src/pytra/ir` へ移設する。
7. [ ] [ID: P0-PYTRA-SRC-3LAYER-01-S2-04] `src/pytra/compiler` を互換 shim 化し、既存 import を壊さない re-export 導線を整備する。
8. [ ] [ID: P0-PYTRA-SRC-3LAYER-01-S3-01] 境界ガード（禁止 import / 逆流依存）を追加し、再発防止を固定する。
9. [ ] [ID: P0-PYTRA-SRC-3LAYER-01-S3-02] 主要 unit/transpile 回帰を実行して非退行を確認する。
10. [ ] [ID: P0-PYTRA-SRC-3LAYER-01-S3-03] `docs/ja/spec`（必要なら `docs/en/spec`）へ新責務境界と移行方針を反映する。

### P1: `ir2lang.py` 導入（EAST3 JSON 直入力 + target lazy import）

文脈: [docs/ja/plans/p1-ir2lang-lazy-backend-from-east3.md](../plans/p1-ir2lang-lazy-backend-from-east3.md)

1. [ ] [ID: P1-IR2LANG-LAZY-EMIT-01] `test/ir` / `sample/ir` の EAST3(JSON) から target 言語へ直接変換する `ir2lang.py` を導入する（selfhost は非対象）。
2. [ ] [ID: P1-IR2LANG-LAZY-EMIT-01-S1-01] `test/ir` / `sample/ir` の入力形式（JSON schema / stage marker / 必須メタ）を棚卸しし、受理契約を確定する。
3. [ ] [ID: P1-IR2LANG-LAZY-EMIT-01-S1-02] `ir2lang.py` CLI 仕様（必須引数、出力先、層別 option、fail-fast 条件）を定義する。
4. [ ] [ID: P1-IR2LANG-LAZY-EMIT-01-S2-01] `src/ir2lang.py` を実装し、EAST3 JSON 読み込みと target dispatch を導入する。
5. [ ] [ID: P1-IR2LANG-LAZY-EMIT-01-S2-02] backend registry 経由の target lazy import を実装し、非指定 backend import を回避する。
6. [ ] [ID: P1-IR2LANG-LAZY-EMIT-01-S2-03] `--lower/--optimizer/--emitter-option` の層別 pass-through を実装する。
7. [ ] [ID: P1-IR2LANG-LAZY-EMIT-01-S2-04] EAST2/不正IR入力の fail-fast エラー整備とメッセージ標準化を行う。
8. [ ] [ID: P1-IR2LANG-LAZY-EMIT-01-S3-01] 主要 target で `sample/ir` / `test/ir` 変換スモークを追加し、backend 単体回帰導線を固定する。
9. [ ] [ID: P1-IR2LANG-LAZY-EMIT-01-S3-02] `docs/ja/how-to-use.md`（必要なら `docs/en/how-to-use.md`）へ手順を追記する。

### P2: `py2x.py` 一本化 frontend 導入（層別 option pass-through）

文脈: [docs/ja/plans/p2-py2x-unified-frontend-rollout.md](../plans/p2-py2x-unified-frontend-rollout.md)

1. [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01] `py2x.py` を共通 frontend として導入し、言語別 `py2*.py` の重複責務を backend registry + 層別 option へ再編する。
2. [x] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S1-01] 現行 `py2*.py` の CLI 差分と runtime 配置差分を棚卸しし、共通 frontend 化で残す差分を確定する。
3. [x] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S1-02] `py2x` 共通 CLI 仕様を策定する（`--target`, 層別 option, 互換オプション, fail-fast 規約）。
4. [x] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S1-03] backend registry 契約（entrypoint, default options, option schema, runtime packaging hook）を定義する。
5. [x] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S2-01] `py2x.py` を実装し、共通入力処理（`.py/.json -> EAST3`）と target dispatch を導入する。
6. [x] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S2-02] 層別 option parser（`--lower-option`, `--optimizer-option`, `--emitter-option`）と schema 検証を実装する。
7. [x] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S2-03] 既存 `py2*.py` を thin wrapper 化し、互換 CLI を `py2x` 呼び出しへ委譲する。
8. [x] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S2-04] runtime/packaging 差分を backend extensions hook へ移し、frontend 側分岐を削減する。
9. [x] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S3-01] CLI 単体テストを追加し、target dispatch と層別 option 伝搬を固定する。
10. [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S3-02] 既存 transpile check 群を `py2x` 経由でも通し、言語横断で非退行を確認する。
11. [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S3-03] `docs/ja` / `docs/en` の使い方・仕様を更新し、移行手順（互換ラッパ期間を含む）を明文化する。
- 進捗メモ: [ID: P2-PY2X-UNIFIED-FRONTEND-01-S1-01] `py2*.py` の CLI/runtime 配置差分を棚卸しし、共通 frontend 化後に残す差分を `runtime_packaging_hook`・backend post-process・`py2cpp.py` 互換ラッパ維持の3分類で確定。
- 進捗メモ: [ID: P2-PY2X-UNIFIED-FRONTEND-01-S1-02] `py2x` の共通 CLI（`--target`, 共通 optimizer option, 層別 pass-through）と互換方針、fail-fast 規約（stage2禁止・schema検証）を計画書に確定。
- 進捗メモ: [ID: P2-PY2X-UNIFIED-FRONTEND-01-S1-03] backend registry の必須契約（entrypoint, default options, schema, runtime hook, compat wrapper）を定義し、S2 実装インタフェースを固定。
- 進捗メモ: [ID: P2-PY2X-UNIFIED-FRONTEND-01-S2-01] `src/py2x.py` と `src/pytra/compiler/backend_registry.py` を追加し、14 target の共通 EAST3 入力 + dispatch + runtime hook の初版を実装（`--help` と複数 target 変換を確認）。
- 進捗メモ: [ID: P2-PY2X-UNIFIED-FRONTEND-01-S2-02] `--lower/--optimizer/--emitter-option key=value` の抽出と schema 検証を実装し、`cpp.emitter` で有効値反映・未知 key の fail-fast（exit=2）を確認。
- 進捗メモ: [ID: P2-PY2X-UNIFIED-FRONTEND-01-S2-03] `py2{rs,cs,js,ts,go,java,kotlin,swift,rb,lua,php,scala,nim}.py` を `run_py2x_for_target` 薄ラッパへ切替し、`check_noncpp_east3_contract --skip-transpile`・`test_east2_to_east3_lowering`・各 transpile check（php runtime `std/time.php` 補完含む）で非退行を確認。
- 進捗メモ: [ID: P2-PY2X-UNIFIED-FRONTEND-01-S2-04] runtime/packaging 差分を `backend_registry.runtime_hook` に統一し、`check_noncpp_east3_contract` へ「wrapperで旧 runtime copy 呼び出し禁止」静的ガードを追加して frontend 側分岐の再流入を防止。
- 進捗メモ: [ID: P2-PY2X-UNIFIED-FRONTEND-01-S3-01] `test/unit/test_py2x_cli.py` を追加し、`--target` 必須/`--east-stage 2` fail-fast と層別 option（`--lower/--optimizer/--emitter-option`）の `resolve_layer_options` 伝搬・dispatch 経路を unit で固定。

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
