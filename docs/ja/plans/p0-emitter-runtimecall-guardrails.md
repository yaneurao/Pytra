# P0: 非C++ emitter の runtime 関数名直書き禁止（IR解決 + CIガード）

最終更新: 2026-03-05

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01`
- `docs/ja/todo/index.md` の `ID: P0-JAVA-PYRUNTIME-SOT-01`

背景:
- 非C++ backend の emitter に、`callee_name == "..."` / `attr_name == "..."` で runtime/stdlib 関数名を直書きする分岐が残っている。
- 同種の再発が継続しており、運用ルールだけでは防げていない。
- 本来、`pytra.std.*` / `pytra.utils.*` の解決は IR 側で確定し、emitter は解決済みノードを描画するだけに限定すべき。
- 既存の「Java は移行完了」判定は早すぎた。`PyRuntime.java`（`pytra-core`）に std/utils 実装が残る状態では、emitter 側の解決責務分離が未達である。

目的:
- 非C++ emitter からライブラリ関数名直書き分岐を撤去する。
- runtime API 解決責務を lower/IR 側へ寄せ、emitter は `runtime_call` 系ノード描画に限定する。
- 禁止事項を静的チェックで fail-fast 化し、再発を CI で防止する。
- `src/pytra/std/*.py` / `src/pytra/utils/*.py` の宣言を正本とし、emitter 側の補正ロジック（wrapper 名生成・互換名フォールバック）を撤去する。

対象:
- `src/backends/*/emitter/*.py`（非C++）
- EAST3 lower / backend lower の runtime API 解決経路
- `tools/` の静的チェック・CI導線・回帰テスト

非対象:
- C++ emitter の全面改修
- runtime 実装本体の機能追加
- sample/README の性能更新

受け入れ基準:
- 非C++ emitter に `pytra.std.*` / `pytra.utils.*` 由来関数名の文字列比較分岐が存在しない。
- runtime/stdlib 呼び出しは lower 済みの解決情報（`runtime_call` 等）経由で emit される。
- `math` を含む stdlib 呼び出しで、emitter 側に `owner == "math"` / `attr == "sqrt"` のようなモジュール専用解決分岐を持たない。
- `Path` 属性アクセス（`parent/name/stem`）で、emitter 側に `owner_type == "Path"` の型分岐を持たず、IR の解決済み属性ノード（`runtime_call=path_*`）を描画する。
- `src/pytra/utils/png.py` / `src/pytra/utils/gif.py` の関数宣言（`write_rgb_png` / `save_gif` / `grayscale_palette`）を正本として解決し、emitter に backend 独自ラッパー名（例: `pyWriteRGBPNG`）や runtime 実装シンボル（例: `__pytra_write_rgb_png`）を直書きしない。
- `resolved_runtime_call` は正本宣言名をそのまま使用し、emitter で `json.loads -> pyJsonLoads` のようなライブラリ依存 rename を行わない。
- `pytra-core`（例: Java `PyRuntime.java`）には std/utils 実装本体を残さず、`pytra-gen` 生成物へ配置されている。
- 例外許可は `len/print/isinstance/range` 等の言語組み込み橋渡しに限定され、許可リストで管理される。
- 静的チェックが CI/ローカル必須導線に統合され、違反時は fail する。
- 代表 backend 群で transpile/smoke/parity 回帰が green。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_emitter_runtimecall_guardrails.py`
- `python3 tools/run_local_ci.py`
- `python3 tools/runtime_parity_check.py 01_mandelbrot --case-root sample --targets cs,js,ts,go,java,ruby,lua,scala,php,nim`

## S1-01 仕様（禁止/許可）

禁止（non-C++ emitter で `if/elif` による文字列分岐を置かない）:
- runtime 関数名: `write_rgb_png` / `save_gif` / `grayscale_palette` / `perf_counter`
- assertion 関数名: `py_assert_stdout` / `py_assert_eq` / `py_assert_true` / `py_assert_all`
- module/symbol 名（runtime 側責務）: `pytra.utils.png` / `pytra.utils.gif` / `pytra.utils.assertions` / `pytra.std.test` / `pytra.std.pathlib`
- `json.loads` / `json.dumps` / `Path` の direct lower（文字列分岐）

許可（言語組み込みブリッジの最小集合）:
- `len` / `print` / `isinstance` / `range`
- `int` / `float` / `bool` / `str`
- `min` / `max` / `enumerate` / `abs`
- `list` / `dict` / `set` / `tuple` / `bytes` / `bytearray`

運用:
- 既存負債は `tools/emitter_runtimecall_guardrails_allowlist.txt` で明示管理する。
- 新規追加は `tools/check_emitter_runtimecall_guardrails.py` で fail させる。
- 実際の解決責務は lower/IR 側へ寄せ、emitter は解決済みノード描画へ限定する。

## S1-02 棚卸し結果（2026-03-05）

non-C++ emitter の direct-branch 棚卸し結果（合計 `115` 件）:

| backend | 件数 |
| --- | ---: |
| cs | 11 |
| go | 12 |
| java | 10 |
| kotlin | 8 |
| lua | 24 |
| nim | 1 |
| php | 10 |
| rs | 6 |
| ruby | 11 |
| scala | 14 |
| swift | 8 |

シンボル別上位:
- `save_gif`: 21
- `write_rgb_png`: 20
- `Path`: 12
- `grayscale_palette`: 11
- `perf_counter`: 9
- `loads` / `dumps`: 各 7
- `pytra.utils.assertions`: 7

移行順（実装優先度）:
1. Java（`S3-02` で先行移行）
2. 残り non-C++ emitter（`S3-03`）
3. `loads/dumps/Path/perf_counter` を runtime_call 解決経路へ統合

## 分解

- [x] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S1-01] 非C++ emitter の禁止/許可ルール（禁止文字列分岐、許可組み込み）を仕様化する。
- [x] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S1-02] 既存 emitter の違反棚卸し（言語別・関数別）を作成する。
- [x] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S2-01] `tools/check_emitter_runtimecall_guardrails.py` を追加し、違反を fail 化する。
- [x] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S2-02] guardrail チェックを `run_local_ci` と CI 必須ジョブへ組み込む。
- [x] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-01] lower/IR 側の runtime API 解決経路（`runtime_call` 系）を非C++ backend 共通で利用できる形に整理する。
- [x] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-02] Java emitter の直書き分岐（`write_rgb_png/save_gif/grayscale_palette/json.*` 等）を解決済み経路へ移行し、SoT 宣言名をそのまま描画する。
- [x] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-02-R1] Java emitter からライブラリ依存 rename（wrapper 名生成・互換名変換）を撤去し、IR 解決シンボル素通し描画へ統一する。
- [x] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-02-R2] Java runtime cleanup と接続し、`PyRuntime.java` 依存の std/utils 呼び出し経路を排除した状態で Java smoke/parity を再固定する。
- [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03] 残り非C++ emitter（`cs/js/ts/go/rs/swift/kotlin/ruby/lua/scala/php/nim`）の直書き分岐を段階撤去する。
- [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03-R1] Go/Kotlin/Swift を宣言駆動（`png.py/gif.py` 正本）へ再移行し、emitter から backend 独自ラッパー名・runtime 実装シンボルの直書きを撤去する。
- [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03-R2] 残り非C++ emitter（`cs/js/ts/rs/ruby/lua/scala/php/nim`）へ同方針を展開し、`png.py/gif.py` 由来シンボルを IR 解決経由へ統一、禁止ガード allowlist を継続縮退する。
- [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-01] unit/smoke/parity 回帰を整備し、再発検知を固定する。
- [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-02] `docs/ja/spec` / `docs/en/spec` に責務境界（IR解決 vs emitter描画）を明文化する。
- [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-03] `runtime_call/resolved_runtime_call` 未解決時は fail-closed（黙ってフォールバックしない）を non-C++ emitter 共通で強制する。
- [x] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-04] Java emitter から stdlib 専用解決ロジック（例: `_java_math_runtime_call`, `owner == "math"`, `owner_type == "Path"`）を撤去し、EAST3 解決情報のみで描画する。
- [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-05] emitter API を「解決済み Call IR 描画専用」に制限し、生 `callee/owner/attr` 分岐を書けない境界へ段階移行する（Java 先行）。
- [x] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-06] guardrail を「分岐以外（dispatch table/context literal）」も検知する形へ拡張し、strict backend（Java）では allowlist 例外を禁止する。
- [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-07] EAST3 固定入力（`test/ir/*.json`）から backend-only 回帰を追加し、`math/Path` を含む解決済み runtime 呼び出しが emitter 直書きなしで通ることを固定する。
- [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-08] Emitter変更の Stop-Ship（必須3コマンド + FAIL時コミット禁止）を運用ルールへ固定し、レビュー checklist 化する。

決定ログ:
- 2026-03-05: ユーザー指示（5回目再発）に基づき、非C++ emitter のライブラリ関数名直書きを防ぐ P0 計画を起票。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S1-01`] 禁止/許可ルールを明文化し、監視対象シンボルと許可組み込みの境界を固定した。既存負債は allowlist 管理、増分のみ fail-fast とする運用方針を確定した。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S1-02`] non-C++ emitter の direct-branch を棚卸しし、言語別件数（最大は `lua=24`）とシンボル上位（`save_gif/write_rgb_png/Path`）を固定した。移行優先順を `java -> その他` に確定した。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S2-01`] `tools/check_emitter_runtimecall_guardrails.py` を追加し、non-C++ emitter の禁止シンボル direct-branch 増分を fail-fast 化した。`tools/emitter_runtimecall_guardrails_allowlist.txt`（115件）を baseline として固定し、`python3 tools/check_emitter_runtimecall_guardrails.py` が通過することを確認した。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S2-02`] `tools/run_local_ci.py` に `check_emitter_runtimecall_guardrails.py` を必須ステップとして追加し、運用ドキュメント（`docs/ja/spec/spec-tools.md` / `docs/en/spec/spec-tools.md`）へ反映した。ローカル CI 導線で常時実行される状態に固定した。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-01`] IR へ non-C++ 向け `resolved_runtime_call` 注釈経路を追加した（`lookup_noncpp_*` + `core.py` で import symbol/module attr 解決）。既存 `runtime_call`/`BuiltinCall` 契約は維持し、C++ 経路を壊さずに段階移行できる形へ整理した。`test_stdlib_signature_registry.py` と `test_east_core.py::test_noncpp_runtime_call_annotations_for_import_symbol_and_module_attr` で回帰固定を確認した。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-02`] Java emitter の `perf_counter/Path/json.loads/json.dumps/write_rgb_png/save_gif/grayscale_palette` 直書き分岐を `runtime_call + resolved_runtime_call` 解決経路へ集約した。`test_py2java_smoke.py`（22件）を再通過し、guardrail allowlist を `115 -> 105` へ更新して直書き削減を固定した。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03`] Go emitter の同種分岐（`perf_counter/Path/json.loads/json.dumps/write_rgb_png/save_gif/grayscale_palette`）を `runtime_call + resolved_runtime_call` 経路へ移行した。`test_py2go_smoke.py`（13件）を通過し、guardrail allowlist を `105 -> 95` へ更新した。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03`] Kotlin emitter の同種分岐（`perf_counter/json.loads/json.dumps/write_rgb_png/save_gif/grayscale_palette`）を `runtime_call + resolved_runtime_call` 経路へ移行した。`test_py2kotlin_smoke.py`（13件）を通過し、guardrail allowlist を `95 -> 87` へ更新した。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03`] Swift emitter の同種分岐（`perf_counter/json.loads/json.dumps/write_rgb_png/save_gif/grayscale_palette`）を `runtime_call + resolved_runtime_call` 経路へ移行した。`test_py2swift_smoke.py`（11件）を通過し、guardrail allowlist を `87 -> 79` へ更新した。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03`] `tools/check_emitter_forbidden_runtime_symbols.py` を追加し、`src/backends/*/emitter/*.py` における `__pytra_write_rgb_png/__pytra_save_gif/__pytra_grayscale_palette` の混入増分を CI fail 化した。`tools/run_local_ci.py` と `docs/ja|en/spec/spec-tools.md` へ導線を追加し、baseline allowlist（31件）を固定した。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03`] タスク見直しの結果、Go/Kotlin/Swift の上記移行は runtime 実装シンボル（`__pytra_*`）直参照を emitter 側に残しており完了条件未達と判断。`S3-03-R1/R2` を追加して未完了として再実施する方針に戻した。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03`] 「公開wrapper名（例: `pyWriteRGBPNG`）へ置換する」案は、`png.py/gif.py` 宣言を正本にした解決責務分離に反するため却下。途中差分は破棄し、`S3-03-R1/R2` を宣言駆動移行として再定義した。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-02`] Java emitter の `Path/json/png/gif` を `resolved_runtime_call` 宣言名マップへ統一し、`PyRuntime.*` 依存を撤去した（`pathlib.Path` 直描画化を含む）。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-02-R1`] Java emitter のライブラリ依存 rename（`json.loads -> pyJsonLoads` 等）を削除し、未マップ `resolved_runtime_call` は描画しない fail-closed 方針へ更新した。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-02-R2`] Java runtime cleanup 後の `PyRuntime.java`（std/utils 残置なし）で smoke/parity（`01/05/18`）を再固定する段取りを明文化した。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03-R1`] Go emitter の PNG/GIF 呼び出しを `__pytra_*` 直参照から `pyWriteRGBPNG/pySaveGIF/pyGrayscalePalette`（宣言駆動）へ移行し、`test_py2go_smoke.py` と sample parity（`01/05`）の再通過を確認した（Kotlin/Swift は未着手）。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-06`] `check_emitter_runtimecall_guardrails.py` を branch 以外（dispatch table/context literal）も検知するよう拡張し、strict backend（Java）は allowlist 例外なしの 0 件必須に固定した。回帰用に `test_check_emitter_runtimecall_guardrails.py` を追加し、`run_local_ci.py` へ組み込んだ。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-04`] `Path.parent/name/stem` の解決を Java emitter の `owner_type == "Path"` 分岐から IR 側（`BuiltinAttr + runtime_call=path_parent/path_name/path_stem`）へ移し、Java emitter の型分岐を撤去した。`test_east_core.py` と `test_py2java_smoke.py` に回帰を追加した。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-04`] Java emitter の `_java_math_runtime_call` と `owner == "math"` 分岐を撤去し、`math.*` 呼び出しは通常の属性経路（特例なし）で描画するよう更新した。`test_py2java_smoke.py` に再発防止アサート（`owner == "math"` / `_java_math_runtime_call` 禁止）を追加し、`check_emitter_runtimecall_guardrails.py` を再通過した。
