# P1: sample/18 Rust 出力品質改善（可読性 + ホットパス縮退）

最終更新: 2026-03-02

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-RS-S18-QUALITY-01`

背景:
- `sample/rs/18_mini_language_interpreter.rs` には、意味互換優先の汎用経路が残り、
  `clone` 過多、負添字正規化式、`String` ベース文字走査、`to_string/format!` 連鎖が混在している。
- 同一ケースの C++ 出力と比較しても、Rust 側は「型既知なのに汎用式へ落ちる」箇所が目立つ。

目的:
- `sample/18` の Rust 出力で、型既知経路を優先する縮退を進め、可読性と実行効率を改善する。
- まずは再現性の高い局所改善（borrow化/添字fastpath/文字走査/文字列生成）を優先する。

対象:
- `src/hooks/rust/` 配下の emitter 実装（式/文/型/補助関数描画）
- `test/unit` の Rust codegen 回帰
- `sample/rs/18_mini_language_interpreter.rs`（再生成確認）

非対象:
- 言語仕様変更（演算意味、例外契約、整数除算仕様）
- Rust runtime API の大規模再設計
- sample 全件への即時横展開（まずは sample/18 先行）

受け入れ基準:
- `sample/rs/18` で次を満たす:
  - 不要 `clone` が削減される（参照で読める箇所は borrow 化）
  - 非負が確定する添字で負index正規化式が出力されない
  - tokenize ホットパスの文字走査が軽量化される
  - `to_string/format!` 連鎖の冗長断片が削減される
- `check_py2rs_transpile.py`、Rust smoke、`runtime_parity_check --targets rs` が非退行で通る。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2rs_transpile.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2rs*' -v`
- `python3 tools/regenerate_samples.py --langs rs --stems 18_mini_language_interpreter --force`
- `python3 tools/runtime_parity_check.py --case-root sample --targets rs --case 18_mini_language_interpreter`

決定ログ:
- 2026-03-02: ユーザー指示により、sample/18 Rust 出力改善を P1 として起票。

## 分解

- [ ] [ID: P1-RS-S18-QUALITY-01-S1-01] sample/18 Rust 出力の冗長断片（clone/添字/走査/format）を棚卸しし、改善対象を固定する。
- [ ] [ID: P1-RS-S18-QUALITY-01-S1-02] 期待効果とリスクで実装順を確定し、fail-closed 適用境界を定義する。
- [ ] [ID: P1-RS-S18-QUALITY-01-S2-01] `current_token/previous_token/eval_expr` で borrow 優先経路を追加し、不要 `clone` を削減する。
- [ ] [ID: P1-RS-S18-QUALITY-01-S2-02] 非負添字が確定する経路で index 正規化式を省略する fastpath を追加する。
- [ ] [ID: P1-RS-S18-QUALITY-01-S2-03] tokenize の文字走査を `String` 汎用経路から軽量経路（bytes/chars）へ縮退する。
- [ ] [ID: P1-RS-S18-QUALITY-01-S2-04] 小規模固定 token 判定で map 依存を減らし、分岐/lookup を簡素化する。
- [ ] [ID: P1-RS-S18-QUALITY-01-S2-05] `to_string/format!` 連鎖を簡約し、同値な直接生成へ寄せる。
- [ ] [ID: P1-RS-S18-QUALITY-01-S2-06] `&Vec<T>` 受けを `&[T]` に縮退できる経路を実装する。
- [ ] [ID: P1-RS-S18-QUALITY-01-S2-07] `BTreeMap` 利用箇所の必要性を再評価し、順序不要経路を軽量mapへ切替える。
- [ ] [ID: P1-RS-S18-QUALITY-01-S3-01] unit/golden 回帰を追加し、冗長出力パターンの再発を検知可能にする。
- [ ] [ID: P1-RS-S18-QUALITY-01-S3-02] `sample/rs/18` 再生成と transpile/smoke/parity で非退行を確認する。
