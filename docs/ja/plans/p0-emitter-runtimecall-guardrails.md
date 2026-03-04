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

## 分解

- [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S1-01] 非C++ emitter の禁止/許可ルール（禁止文字列分岐、許可組み込み）を仕様化する。
- [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S1-02] 既存 emitter の違反棚卸し（言語別・関数別）を作成する。
- [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S2-01] `tools/check_emitter_runtimecall_guardrails.py` を追加し、違反を fail 化する。
- [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S2-02] guardrail チェックを `run_local_ci` と CI 必須ジョブへ組み込む。
- [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-01] lower/IR 側の runtime API 解決経路（`runtime_call` 系）を非C++ backend 共通で利用できる形に整理する。
- [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-02] Java emitter の直書き分岐（`write_rgb_png/save_gif/grayscale_palette/json.*` 等）を解決済み経路へ移行する。
- [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S3-03] 残り非C++ emitter（`cs/js/ts/go/rs/swift/kotlin/ruby/lua/scala/php/nim`）の直書き分岐を段階撤去する。
- [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-01] unit/smoke/parity 回帰を整備し、再発検知を固定する。
- [ ] [ID: P0-EMITTER-RUNTIMECALL-GUARDRAILS-01-S4-02] `docs/ja/spec` / `docs/en/spec` に責務境界（IR解決 vs emitter描画）を明文化する。

決定ログ:
- 2026-03-05: ユーザー指示（5回目再発）に基づき、非C++ emitter のライブラリ関数名直書きを防ぐ P0 計画を起票。
