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

### P0: 非C++ emitter のライブラリ関数名直書き再発防止（IR解決 + CIガード）

文脈: [docs/ja/plans/p0-emitter-runtimecall-guardrails.md](../plans/p0-emitter-runtimecall-guardrails.md)

1. [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01] 非C++ emitter における runtime/stdlib 関数名の直書き分岐を撤去し、IR解決 + CIガードで再発を防止する。
2. [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S1-01] 禁止/許可ルール（禁止文字列分岐・許可組み込み）を仕様化する。
3. [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S1-02] 既存違反を言語別に棚卸しし、移行対象を確定する。
4. [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S2-01] static check（`check_emitter_runtimecall_guardrails.py`）を追加して違反を fail 化する。
5. [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S2-02] guardrail をローカルCI/CI 必須導線へ組み込む。
6. [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-01] lower/IR の runtime API 解決経路を非C++ backend で共通利用できる形に整理する。
7. [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-02] Java emitter の直書き分岐を解決済み経路へ移行する。
8. [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03] Java 以外の非C++ emitter（`cs/js/ts/go/rs/swift/kotlin/ruby/lua/scala/php/nim`）の直書き分岐を段階撤去する。
9. [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-01] unit/smoke/parity 回帰を整備し、再発検知を固定する。
10. [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-02] docs（`spec`）へ責務境界を明文化する。

### P2: 多言語 runtime の C++ 同等化（API 契約・機能カバレッジ統一）

文脈: [docs/ja/plans/p2-runtime-parity-with-cpp.md](../plans/p2-runtime-parity-with-cpp.md)

1. [ ] [ID: P2-RUNTIME-PARITY-CPP-01] C++ runtime を基準に、他言語 runtime の API 契約と機能カバレッジを段階的に同等化する。
2. [x] [ID: P2-RUNTIME-PARITY-CPP-01-S1-01] C++ runtime の必須 API カタログ（module/function/契約）を抽出する。
3. [x] [ID: P2-RUNTIME-PARITY-CPP-01-S1-02] 各言語 runtime の実装有無マトリクスを作成し、欠落/互換/挙動差を分類する。
4. [x] [ID: P2-RUNTIME-PARITY-CPP-01-S1-03] 同等化対象を `Must/Should/Optional` で優先度付けする。
5. [x] [ID: P2-RUNTIME-PARITY-CPP-01-S2-01] Wave1（`go/java/kotlin/swift`）で `math/time/pathlib/json` 不足 API を実装する。
6. [x] [ID: P2-RUNTIME-PARITY-CPP-01-S2-01-S1-01] Wave1-Go: `json.loads/dumps` runtime API を追加し、Go emitter の `json.*` 呼び出しを runtime helper へ統一する。
7. [x] [ID: P2-RUNTIME-PARITY-CPP-01-S2-02] Wave1 の emitter 呼び出しを adapter 経由へ寄せ、API 名揺れを吸収する。
8. [x] [ID: P2-RUNTIME-PARITY-CPP-01-S2-03] Wave1 の parity 回帰を追加し、runtime 差由来 fail を固定する。
9. [x] [ID: P2-RUNTIME-PARITY-CPP-01-S3-01] Wave2（`ruby/lua/scala/php`）で不足 API を実装する。
10. [x] [ID: P2-RUNTIME-PARITY-CPP-01-S3-02] Wave2 の emitter 呼び出しを adapter 経由へ寄せる。
11. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S3-03] Wave2 の parity 回帰を追加し、runtime 差由来 fail を固定する。
12. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S4-01] Wave3（`js/ts/cs/rs`）で不足 API を補完し、契約差を解消する。
13. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S4-02] runtime API 欠落検知チェックを追加し、CI/ローカル回帰へ組み込む。
14. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S4-03] `docs/ja/spec` / `docs/en/spec` に runtime 同等化ポリシーと進捗表を反映する。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-01-S1-01] `docs/ja/spec/spec-runtime.md` に C++ runtime API 正本カタログ（Must/Should）を追加し、Wave 同等化の基準 API を固定。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-01-S1-02] `src/runtime/<lang>/pytra` 棚卸し結果を `native/mono/compat/missing` でマトリクス化し、主要欠落（json/pathlib/gif）を分類。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-01-S1-03] マトリクス差分を `Must/Should/Optional` へ優先度化し、Wave1/2/3 の着手順（json/pathlib/gif優先）を確定。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-01-S2-01-S1-01] Go runtime に `pyJsonLoads/pyJsonDumps` を追加し、Go emitter の `json.loads/json.dumps` を runtime helper へ統一。`test_py2go_smoke.py` と `check_py2go_transpile.py` で非退行確認。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-01-S2-01] Wave1-Java: `PyRuntime.pyJsonLoads/pyJsonDumps` を追加し、Java emitter の `json.loads/json.dumps` を runtime helper 経由へ統一。`test_py2java_smoke.py` と `check_py2java_transpile.py` で非退行確認。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-01-S2-01] Wave1-Kotlin: `py_runtime.kt` に `pyJsonLoads/pyJsonDumps` を追加し、Kotlin emitter の `json.loads/json.dumps` を helper 経由へ統一。`test_py2kotlin_smoke.py` と `check_py2kotlin_transpile.py` で非退行確認。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-01-S2-01] Wave1-Swift: `py_runtime.swift` に `pyJsonLoads/pyJsonDumps` を追加し、Swift emitter の `json.loads/json.dumps` を helper 経由へ統一。`test_py2swift_smoke.py` と `check_py2swift_transpile.py` で非退行確認。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-01-S2-01] Wave1-Java: `Path` runtime を `PyRuntime.Path`（`parent/name/stem` と `exists/read_text/write_text/mkdir/resolve`）として実装し、Java emitter の `Path` 型/ctor/isinstance を `PyRuntime.Path` へ統一。`test_py2java_smoke.py` と `check_py2java_transpile.py` で非退行確認。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-01-S2-01] Wave1-Kotlin/Swift: runtime に `Path` クラス（`parent/name/stem` + `exists/read_text/write_text/mkdir/resolve`）を追加し、`Path(...)` 呼び出し生成がそのままコンパイル可能であることを `test_py2{kotlin,swift}_smoke.py` と `check_py2{kotlin,swift}_transpile.py` で確認。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-01-S2-01] Wave1-Go: runtime に `Path` wrapper（`NewPath/__pytra_as_Path` + method群）を追加し、Go emitter で keyword 引数値を一般呼び出しへ反映するよう修正。`pathlib` の `mkdir(parents=True, exist_ok=True)` が `mkdir(true, true)` へ降りることを `test_py2go_smoke.py` と `check_py2go_transpile.py` で確認。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-01-S2-01] Wave1-Kotlin/Swift: runtime に `pyMath*` API（`sqrt/sin/cos/tan/exp/log/fabs/floor/ceil/pow/pi/e`）を追加し、emitter の `math.*` を runtime helper 経由へ統一。`test_py2{kotlin,swift}_smoke.py` と `check_py2{kotlin,swift}_transpile.py` で非退行確認。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-01-S2-01] Wave1 完了: `go/java/kotlin/swift` で `json/pathlib/math/time` の不足 API 実装と emitter 接続を完了し、`test_py2{go,java,kotlin,swift}_smoke.py` + `check_py2{go,java,kotlin,swift}_transpile.py` で green を確認。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-01-S2-02] Wave1 adapter 先行: Go/Java emitter の `math.*` を runtime helper (`pyMath*`) 経由へ統一し、Go emitter から `math` import 依存を撤去。`test_py2{go,java}_smoke.py` と `check_py2{go,java}_transpile.py` で非退行確認。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-01-S2-02] Java emitter の `perf_counter()` を `PyRuntime.pyPerfCounter()` adapter 経由へ統一。`test_py2java_smoke.py`（`perf_counter` ケース）と `check_py2java_transpile.py` で非退行確認。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-01-S2-02] Wave1 adapter 完了: `go/java/kotlin/swift` の `math/time/pathlib/json` 呼び出しを runtime helper / runtime wrapper 経由へ統一し、言語固有 API 名揺れを emitter 内部に閉じ込めた。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-01-S2-03] Wave1 parity を `go/java/kotlin/swift` で再実行し、初回ログ（`...s2_03.json`）の Kotlin 6件 run_failed を `pyMath*` 戻り型 `Double` 統一で解消。再計測ログ `work/logs/runtime_parity_wave1_go_java_kotlin_swift_20260304_s2_03_retry.json` で `case_pass=18/case_fail=0`（`ok:72`）を確認。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-01-S3-01] Wave2 先行（Ruby/PHP）として `pyMath*` / `pyJsonLoads|pyJsonDumps` / `Path` runtime API を `pytra-core` に追加し、`runtime_parity_check --targets ruby,php 01_mandelbrot` で artifact（size+CRC32）一致を確認。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-01-S3-01] Wave2 追加（Lua/Scala）として `pyMath*` / `Path` API を補完し、`runtime_parity_check --targets lua,scala 01_mandelbrot` で artifact（size+CRC32）一致を確認。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-01-S3-01] Scala runtime の `pyJsonLoads|pyJsonDumps` を parser/stringify 実装へ置換し、`check_py2{lua,php,scala}_transpile.py` を全通過。`runtime_parity_check --targets ruby,php,lua,scala 01_mandelbrot` で Wave2 4言語回帰を確認してクローズ。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-01-S3-02] Ruby/PHP/Scala emitter の `math/json/pathlib` 呼び出しを runtime adapter（`pyMath*` / `pyJson*` / `Path`）へ統一し、Lua emitter も `math/json/pathlib/time` import を runtime adapter 経由へ切替。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-01-S3-02] `check_py2{lua,php,scala}_transpile.py` と `runtime_parity_check --targets ruby,php,lua,scala 01_mandelbrot` を再実行し、adapter 化後の回帰が全通過（`ok:4`）であることを確認してクローズ。

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
