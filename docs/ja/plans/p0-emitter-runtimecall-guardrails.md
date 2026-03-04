# P0: 非C++ emitter の runtime 関数名直書き禁止（IR解決 + CIガード）

最終更新: 2026-03-05

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01`

背景:
- 非C++ backend の emitter に、`callee_name == "..."` / `attr_name == "..."` で runtime/stdlib 関数名を直書きする分岐が残っている。
- 同種の再発が継続しており、運用ルールだけでは防げていない。
- 本来、`pytra.std.*` / `pytra.utils.*` の解決は IR 側で確定し、emitter は解決済みノードを描画するだけに限定すべき。

目的:
- 非C++ emitter からライブラリ関数名直書き分岐を撤去する。
- runtime API 解決責務を lower/IR 側へ寄せ、emitter は `runtime_call` 系ノード描画に限定する。
- 禁止事項を静的チェックで fail-fast 化し、再発を CI で防止する。

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
- [x] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-02] Java emitter の直書き分岐（`write_rgb_png/save_gif/grayscale_palette/json.*` 等）を解決済み経路へ移行する。
- [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03] 残り非C++ emitter（`cs/js/ts/go/rs/swift/kotlin/ruby/lua/scala/php/nim`）の直書き分岐を段階撤去する。
- [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-01] unit/smoke/parity 回帰を整備し、再発検知を固定する。
- [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-02] `docs/ja/spec` / `docs/en/spec` に責務境界（IR解決 vs emitter描画）を明文化する。

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
