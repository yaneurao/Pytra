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

### P0: Java `PyRuntime` から std/utils 実装を除去（SoT正本化）

文脈: [docs/ja/plans/p0-java-pyruntime-sot-extraction.md](../plans/p0-java-pyruntime-sot-extraction.md)

1. [ ] [ID: P0-JAVA-PYRUNTIME-SOT-01] Java runtime を `pytra-core` / `pytra-gen` 境界へ再収束させ、`PyRuntime.java` から SoT 由来実装を除去する。
2. [x] [ID: P0-JAVA-PYRUNTIME-SOT-01-S1-01] Java runtime の責務境界（`pytra-core`/`pytra-gen`）と禁止シンボルを仕様として固定する。
3. [x] [ID: P0-JAVA-PYRUNTIME-SOT-01-S1-02] `PyRuntime.java` 内の SoT 由来実装を棚卸しし、削除対象と移管先（`pytra-gen/std|utils`）を確定する。
4. [x] [ID: P0-JAVA-PYRUNTIME-SOT-01-S2-01] `src/pytra/std/{time,json,pathlib,math}.py` の Java 生成導線を整備し、`src/runtime/java/pytra-gen/std/*.java` を生成可能にする。
5. [x] [ID: P0-JAVA-PYRUNTIME-SOT-01-S2-02] Java runtime 配布導線（backend registry / runtime hook）を `pytra-core + pytra-gen/std + pytra-gen/utils` 前提へ更新する。
6. [ ] [ID: P0-JAVA-PYRUNTIME-SOT-01-S3-01] Java emitter からライブラリ固有 `PyRuntime.*` 直書き分岐を撤去し、解決済み IR 駆動へ移行する。
7. [x] [ID: P0-JAVA-PYRUNTIME-SOT-01-S3-02] Java emitter の回帰テスト（json/pathlib/time/png/gif）を追加し、直書き再混入を防止する。
8. [ ] [ID: P0-JAVA-PYRUNTIME-SOT-01-S4-01] `PyRuntime.java` から JSON/pathlib/time/math/image 実装を段階削除し、必要最小限の core API のみに縮退する。
9. [x] [ID: P0-JAVA-PYRUNTIME-SOT-01-S4-02] 静的ガード（`PyRuntime.java` 禁止シンボル検査）を `tools/run_local_ci.py` へ組み込み、再発を fail-fast 化する。
10. [x] [ID: P0-JAVA-PYRUNTIME-SOT-01-S4-03] Java smoke/parity（`sample/01,05,18`）を再実施し、artifact 含む一致を確認する。
- 進捗メモ: [ID: P0-JAVA-PYRUNTIME-SOT-01-S3-01] Java emitter の `write_rgb_png/save_gif/grayscale_palette/json.*` 直書き分岐を `runtime_call/resolved_runtime_call` 経路へ寄せたが、`json.*` 素通しは現行 `pytra-gen/std/json.java` 品質でコンパイル不成立のため一旦ロールバックし、継続課題として保持した。
- 進捗メモ: [ID: P0-JAVA-PYRUNTIME-SOT-01-S3-01] `resolved_runtime_call` の画像系（`write_rgb_png/save_gif/grayscale_palette`）は `PngHelper/GifHelper` へ直接描画するよう移行し、`PyRuntime.*` 経由を撤去した（Java smoke/parity green）。
- 進捗メモ: [ID: P0-JAVA-PYRUNTIME-SOT-01-S3-01] `resolved_runtime_call` の `json.loads/json.dumps` は `json.*` 直接描画へ移行し、Java emitter での `PyRuntime.pyJson*` 依存を撤去した（Path は継続）。
- 進捗メモ: [ID: P0-JAVA-PYRUNTIME-SOT-01-S3-02] `test_py2java_smoke.py` に emitter ソース検査を追加し、`json/png/gif` の `runtime_call == \"...\"` 直書き分岐再混入を回帰検知化した。
- 進捗メモ: [ID: P0-JAVA-PYRUNTIME-SOT-01-S4-01] `PyRuntime.java` から画像互換ラッパに加えて `pyPerfCounter` / `pyMath*` を除去し、`pytra-core/std/{time_impl.java,math_impl.java}`（`_impl`, `_m`）へ移管した。
- 進捗メモ: [ID: P0-JAVA-PYRUNTIME-SOT-01-S4-01] `PyRuntime.java` から `write_rgb_png/save_gif/grayscale_palette` 本体を削除し、`tools/check_java_pyruntime_boundary.py` で再混入禁止を fail-fast 化した（json/pathlib は残課題）。
- 進捗メモ: [ID: P0-JAVA-PYRUNTIME-SOT-01-S4-01] `PyRuntime.java` から `pyJsonDumps/pyJsonLoads/jsonStringify/jsonEscapeString/JsonParser` を除去し、境界ガードへ JSON 禁止シンボルを追加した（pathlib は残課題）。
- 進捗メモ: [ID: P0-JAVA-PYRUNTIME-SOT-01-S4-02] `tools/check_java_pyruntime_boundary.py` を `run_local_ci.py` へ組み込み済み。禁止シンボルは image 互換ラッパ + `pyPerfCounter` / `pyMath*` まで拡張した（json/pathlib は継続）。

### P0: 非C++ emitter のライブラリ関数名直書き再発防止（IR解決 + CIガード）

文脈: [docs/ja/plans/p0-emitter-runtimecall-guardrails.md](../plans/p0-emitter-runtimecall-guardrails.md)

1. [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01] 非C++ emitter における runtime/stdlib 関数名の直書き分岐を撤去し、IR解決 + CIガードで再発を防止する。
2. [x] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S1-01] 禁止/許可ルール（禁止文字列分岐・許可組み込み）を仕様化する。
3. [x] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S1-02] 既存違反を言語別に棚卸しし、移行対象を確定する。
4. [x] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S2-01] static check（`check_emitter_runtimecall_guardrails.py`）を追加して違反を fail 化する。
5. [x] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S2-02] guardrail をローカルCI/CI 必須導線へ組み込む。
6. [x] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-01] lower/IR の runtime API 解決経路を非C++ backend で共通利用できる形に整理する。
7. [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-02] Java emitter の直書き分岐を解決済み経路へ移行し、SoT 宣言名をそのまま描画する。
8. [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-02-R1] Java emitter からライブラリ依存 rename（wrapper 名生成・互換名変換）を撤去し、IR 解決シンボル素通し描画へ統一する。
9. [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-02-R2] `P0-JAVA-PYRUNTIME-SOT-01` と接続し、`PyRuntime.java` 依存の std/utils 呼び出し経路を排除した状態で Java smoke/parity を再固定する。
10. [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03] Java 以外の非C++ emitter（`cs/js/ts/go/rs/swift/kotlin/ruby/lua/scala/php/nim`）の直書き分岐を段階撤去する。
11. [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03-R1] Go/Kotlin/Swift を宣言駆動（`src/pytra/utils/png.py` / `gif.py` 正本）へ再移行し、emitter から backend 独自ラッパー名・runtime 実装シンボル直書きを撤去する。
12. [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03-R2] 残り非C++ emitter（`cs/js/ts/rs/ruby/lua/scala/php/nim`）へ同方針を展開し、`png.py/gif.py` 由来シンボルの IR 解決経路統一と禁止ガード allowlist 縮退を完了する。
13. [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-01] unit/smoke/parity 回帰を整備し、再発検知を固定する。
14. [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-02] docs（`spec`）へ責務境界を明文化する。
- 進捗メモ: [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03] Go emitter の `perf_counter/Path/json.*` と PNG/GIF runtime 呼び出しを `runtime_call/resolved_runtime_call` 経路へ移行し、guardrail baseline を `105 -> 95` へ縮退。
- 進捗メモ: [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03] Kotlin emitter の `perf_counter/json.*` と PNG/GIF runtime 呼び出しを `runtime_call/resolved_runtime_call` 経路へ移行し、guardrail baseline を `95 -> 87` へ縮退。
- 進捗メモ: [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03] Swift emitter の `perf_counter/json.*` と PNG/GIF runtime 呼び出しを `runtime_call/resolved_runtime_call` 経路へ移行し、guardrail baseline を `87 -> 79` へ縮退。
- 進捗メモ: [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03] emitter 内での `__pytra_write_rgb_png/__pytra_save_gif/__pytra_grayscale_palette` 混入を監視する `check_emitter_forbidden_runtime_symbols.py` を追加し、`run_local_ci.py` 経由で CI fail-fast 化（baseline 31件）した。
- 進捗メモ: [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03] 上記 Go/Kotlin/Swift の移行は runtime 実装シンボル直参照を残しており、完了条件未達として `S3-03-R1/R2` に再編してやり直す。
- 進捗メモ: [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03] `pyWriteRGBPNG` など公開wrapper名直書きへの置換案は採用せず、`png.py/gif.py` 宣言正本で解決する宣言駆動方針へ計画を更新した。

### P2: 多言語 runtime の C++ 同等化（再設計版: SoT厳守 + 生成優先）

文脈: [docs/ja/plans/p2-runtime-parity-with-cpp.md](../plans/p2-runtime-parity-with-cpp.md)

1. [ ] [ID: P2-RUNTIME-PARITY-CPP-02] 多言語 runtime 同等化を「SoT厳守・生成優先・責務分離」の前提で再設計し、再発不能な運用へ置換する。
2. [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S1-01] 旧P2（`P2-RUNTIME-PARITY-CPP-01`）を未完了一覧から削除し、新P2へ置換する。
3. [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S1-02] SoT/pytra-core/pytra-gen の責務境界と禁止事項を `docs/ja/spec` に明文化する。
4. [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S1-03] 対象モジュールの「生成必須 / core許可」分類表を作成する。
5. [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S2-01] `pytra-gen` の素通し命名違反を検知する静的チェックを追加する。
6. [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S2-02] marker（`source/generated-by`）・配置違反（core混在）監査を強化し、CIへ統合する。
7. [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S2-03] `pytra-core` 内の SoT 再実装痕跡を棚卸しし、`pytra-gen` 移管計画へ反映する。
8. [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S3-01] Java を先行対象として、emitter の直書き runtime 関数分岐を IR 解決経路へ移行する。
9. [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S3-02] Java 以外の非C++ backend（`cs/js/ts/go/rs/swift/kotlin/ruby/lua/scala/php/nim`）へ同方針を展開する。
10. [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S3-03] emitter でのライブラリ関数名直書き禁止を lint 化し、PR/CI で fail-fast 化する。
11. [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S4-01] 全対象言語で sample parity（artifact size+CRC32 含む）を再実施し、差分を固定する。
12. [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S4-02] 運用手順（ローカル/CI）を `docs/ja` / `docs/en` に反映する。

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
