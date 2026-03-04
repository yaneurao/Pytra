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
- [x] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03] 残り非C++ emitter（`cs/js/ts/go/rs/swift/kotlin/ruby/lua/scala/php/nim`）の直書き分岐を段階撤去する。
- [x] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03-R1] Go/Kotlin/Swift を宣言駆動（`png.py/gif.py` 正本）へ再移行し、emitter から backend 独自ラッパー名・runtime 実装シンボルの直書きを撤去する。
- [x] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03-R2] 残り非C++ emitter（`cs/js/ts/rs/ruby/lua/scala/php/nim`）へ同方針を展開し、`png.py/gif.py` 由来シンボルを IR 解決経由へ統一、禁止ガード allowlist を継続縮退する。
- [x] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-01] unit/smoke/parity 回帰を整備し、再発検知を固定する。
- [x] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-02] `docs/ja/spec` / `docs/en/spec` に責務境界（IR解決 vs emitter描画）を明文化する。
- [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-03] `runtime_call/resolved_runtime_call` 未解決時は fail-closed（黙ってフォールバックしない）を non-C++ emitter 共通で強制する。
- [x] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-04] Java emitter から stdlib 専用解決ロジック（例: `_java_math_runtime_call`, `owner == "math"`, `owner_type == "Path"`）を撤去し、EAST3 解決情報のみで描画する。
- [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-05] emitter API を「解決済み Call IR 描画専用」に制限し、生 `callee/owner/attr` 分岐を書けない境界へ段階移行する（Java 先行）。
- [x] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-06] guardrail を「分岐以外（dispatch table/context literal）」も検知する形へ拡張し、strict backend（Java）では allowlist 例外を禁止する。
- [x] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-07] EAST3 固定入力（`test/ir/*.json`）から backend-only 回帰を追加し、`math/Path` を含む解決済み runtime 呼び出しが emitter 直書きなしで通ることを固定する。
- [x] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-08] Emitter変更の Stop-Ship（必須3コマンド + FAIL時コミット禁止）を運用ルールへ固定し、レビュー checklist 化する。

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
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03`] Go/Swift/Kotlin emitter で `owner == "math"` 分岐を撤去し、`resolved_runtime_call=math.*` 優先の経路へ移行した。既存 `pyMath*` runtime への接続は維持しつつ、各言語 smoke に source-level 再発防止アサートを追加した。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-07`] 固定入力 `test/ir/java_math_path_runtime.east3.json` を追加し、`test_py2java_smoke.py::test_java_native_emitter_backend_only_ir_fixture_resolves_math_and_path` で backend-only 回帰を導入した。IR 側では module-attr call の戻り型推論を補強し、`math.sin(math.pi)` が `double` 経路で描画されることを固定した。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-08`] `docs/ja/spec/spec-tools.md` / `docs/en/spec/spec-tools.md` に Stop-Ship チェックリストを追加し、必須3コマンド・FAIL時コミット禁止・レビュー確認項目を明文化した。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03-R1`] Swift/Kotlin emitter の `runtime_call == "write_rgb_png|save_gif|grayscale_palette|json.loads|json.dumps|perf_counter|Path"` 分岐を撤去し、`resolved_runtime_call` と `semantic_tag` から runtime シンボルを導出する経路へ置換した。`test_py2swift_smoke.py`（12件）/`test_py2kotlin_smoke.py`（14件）と guardrail 3本を再通過し、allowlist を runtimecall `114->106`・forbidden symbol `28->22` へ更新した。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03-R1`] Go emitter でも `runtime_call` 直書き分岐を撤去し、`resolved_runtime_call` + `semantic_tag` から runtime シンボルを導出する経路へ統一した。`save_gif` の既定引数補完は semantic-tag（`stdlib.symbol.save_gif`）で維持し、`test_py2go_smoke.py`（14件）と guardrail 3本を再通過した。allowlist は runtimecall `114->99` まで縮退した。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-02`] `docs/ja/spec/spec-east.md` / `docs/en/spec/spec-east.md` の `runtime_call/resolved_runtime_call` 責務境界節へ CI 強制コマンド（`check_emitter_runtimecall_guardrails.py` / `check_emitter_forbidden_runtime_symbols.py` / `check_noncpp_east3_contract.py`）を追記し、禁止事項と運用導線を同一仕様上で固定した。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-01`] Go/Swift/Kotlin smoke に backend-only IR fixture（`test/ir/java_math_path_runtime.east3.json`）回帰を追加し、Java と同様に `math.sin/math.pi` と `Path.parent/name/stem` が emitter 直書きなしで描画されることを固定した。3言語 smoke（Go 15件 / Swift 13件 / Kotlin 15件）と guardrail 3本を再通過した。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03-R2`] JS emitter の `runtime_map` から `pytra.std.time` / `pytra.std.pathlib` / `pytra.utils.png` / `pytra.utils.gif` 直書きエントリを撤去し、既存の汎用 `module_id -> ./...` 解決へ統一した。`test_py2js_smoke.py`（21件）と guardrail 3本を再通過し、runtimecall allowlist を `99->95` へ縮退した。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03-R2`] Nim emitter の `save_gif` / `write_rgb_png` 直書き分岐を撤去し、`semantic_tag=stdlib.symbol.save_gif` と `resolved_runtime_call(module_attr)` を使う描画へ置換した。`test_py2nim_smoke.py`（2件）と guardrail 3本を再通過し、runtimecall allowlist を `95->93` へ縮退した。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03-R2`] PHP emitter の `resolved_runtime_call` 描画を汎用規則へ寄せ、`save_gif` の keyword 引数順序（`delay_cs/loop`）と `grayscale_palette` の 0 引数呼び出しを直書き分岐なしで維持した。`test_py2php_smoke.py`（9件）+ guardrail 3本（runtimecall/forbidden/noncpp）を再通過し、forbidden-symbol allowlist を `22->20` に縮退した。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03-R2`] Ruby emitter に `runtime_call/resolved_runtime_call` 優先描画を追加し、`perf_counter/Path` と `png/gif/json/math` の call/attribute 直書き分岐を段階撤去した。`test_py2rb_smoke.py`（20件）+ guardrail 3本を再通過し、runtimecall allowlist を `83->72` へ縮退した。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03-R2`] C# emitter で import 解決情報（`_resolve_imported_symbol`）を使った `pytra.utils.*` 呼び出しルーティングを導入し、`save_gif/write_rgb_png/grayscale_palette` の Name-call 直書きを撤去した。併せて `json.loads/dumps` の属性専用分岐を汎用属性描画へ置換し、`render_expr(Attribute)` は `runtime_call=path_parent/path_name/path_stem` を優先描画して `owner_type == "Path"` 直書き依存を縮退した。`test_py2cs_smoke.py`（43件）+ guardrail 3本を再通過し、runtimecall allowlist を `72->66` へ更新した。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03-R2`] C# emitter の残件だった `Path/perf_counter/py_assert_*` 固定分岐を、import解決（`_resolve_imported_symbol`）と `py_assert_` 接頭辞処理へ統合した。`_module_alias_target` の `pytra.std.pathlib + Path` 固定判定も `*.pathlib` + Uppercase symbol の一般化へ置換し、guardrail 直書き検知をさらに縮退した。`test_py2cs_smoke.py`（43件）+ guardrail 3本を再通過し、runtimecall allowlist を `66->58` に更新した。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03-R2`] Rust emitter の import/use 生成で `pytra.utils.assertions` 直書き判定を helper（suffix 判定）へ置換し、`_render_call` の `py_assert_stdout` 専用分岐を `py_assert_` 接頭辞処理へ吸収した。挙動は維持したまま guardrail の直書き文字列を縮退し、`test_py2rs_smoke.py`（29件）+ guardrail 3本を再通過、runtimecall allowlist を `58->54` へ更新した。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03-R2`] Rust emitter の `save_gif/write_rgb_png` 直比較を撤去し、`pytra.utils.(gif|png)` 判定 + 引数個数ベース共通参照化（`_apply_image_runtime_ref_args`）へ置換した。Name-call と Attribute-call の両経路で同一ロジックを共有し、`pytra.utils.gif/png`・`save_gif/write_rgb_png` 文字列直書きを大幅縮退した。`test_py2rs_smoke.py`（29件）+ guardrail 3本を再通過し、runtimecall allowlist を `54->42` に更新した。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03-R2`] Lua emitter の import 解決節を `module_name/symbol` 依存の固定比較から `mod/sym` ベースへ再編し、`pytra.utils.*` は leaf 由来の汎用 module/symbol 解決へ統合した。合わせて `_render_call` の `save_gif` keyword 専用分岐を廃止し、汎用 keyword 位置引数連結へ変更して call/attribute 両経路の直書きを削減した。`test_py2lua_smoke.py`（31件）+ guardrail 3本を再通過し、runtimecall allowlist を `42->17`（残り Scala のみ）、forbidden-symbol allowlist を `20->16` へ更新した。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03-R2`] Scala emitter を `runtime_call/resolved_runtime_call` 優先へ移行し、`Path/perf_counter/png/gif` の Name/Attribute 直書きを撤去した。`Path` は `String` 値経路へ統一し、`path_parent/name/stem` と `mkdir/exists/write_text/read_text` は `__pytra_path_*` helper 描画へ集約した。`test_py2scala_smoke.py`（15件）+ guardrail 3本を再通過し、runtimecall allowlist を `17->0`、forbidden-symbol allowlist を `16->10` へ縮退した。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-03`] Scala emitter で fail-closed を先行導入し、`semantic_tag=stdlib.*` なのに `runtime_call/resolved_runtime_call` が空の Call/Attribute は即 `RuntimeError` とした。`test_py2scala_smoke.py` に未解決 stdlib call の負例を追加して回帰固定した（16件 green）。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-03`] Go emitter にも同じ fail-closed を展開し、`semantic_tag=stdlib.*` かつ `runtime_call/resolved_runtime_call` 未解決の Call/Attribute を即 `RuntimeError` とした。`test_py2go_smoke.py` に未解決 stdlib call の負例を追加し、Go smoke 16件 green を確認した。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-03`] Kotlin emitter にも fail-closed を展開し、`semantic_tag=stdlib.*` かつ `runtime_call/resolved_runtime_call` 未解決の Call/Attribute を即 `RuntimeError` とした。`test_py2kotlin_smoke.py` に未解決 stdlib call の負例を追加し、Kotlin smoke 16件 green を確認した。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-03`] Swift emitter にも fail-closed を展開し、`semantic_tag=stdlib.*` かつ `runtime_call/resolved_runtime_call` 未解決の Call/Attribute を即 `RuntimeError` とした。`test_py2swift_smoke.py` に未解決 stdlib call の負例を追加し、Swift smoke 14件 green を確認した。
- 2026-03-05: [ID: `P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-03`] Ruby emitter にも fail-closed を展開し、`semantic_tag=stdlib.*` かつ `runtime_call/resolved_runtime_call` 未解決の Call/Attribute を即 `RuntimeError` とした。`test_py2rb_smoke.py` に未解決 stdlib call の負例を追加し、Ruby smoke 21件 green を確認した。
