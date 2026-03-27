<a href="../../en/plans/p1-rs-s18-quality-uplift.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

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
- 2026-03-02: sample/18 の棚卸しで、優先度を `clone削減 -> 添字fastpath -> 走査軽量化 -> 文字列生成簡約 -> API型縮退(&Vec->&[T]) -> map見直し` の順に固定。
- 2026-03-02: fail-closed 境界を「型既知 + 値境界不変 + 失敗時は現行出力維持」に確定。`unknown/object/union` と順序依存経路は最適化非適用に固定。
- 2026-03-02: Rust emitter の借用引数型解決を拡張し、`list[T]` の参照引数を `&Vec<T>` から `&[T]` へ縮退（S2-06）。
- 2026-03-02: `sample/rs/18` で `tokenize/eval_expr/execute` の slice 署名を確認し、`check_py2rs_transpile` と parity（case18）を通過。
- 2026-03-02: `AnnAssign` の list 添字初期化で borrow 優先経路を実装し、`eval_expr` 冒頭の `ExprNode` 取得を clone から `&ExprNode` 参照へ縮退（S2-01）。
- 2026-03-02: `if` then 節に限定した符号ヒントを導入し、`single_tag > 0` 配下の添字で負index正規化式を省略（S2-02）。
- 2026-03-02: `str` 添字の非負確定経路を `py_str_at_nonneg` へ分岐し、tokenize の文字取得を軽量化（S2-03）。
- 2026-03-02: 小規模固定 `dict[str, const]` の `get` を `match` へ縮退し、token 判定 lookup の map 依存を削減（S2-04）。
- 2026-03-02: cast 無し `str` Add 連鎖を平坦化して `format!` 1回へ統合し、nested `format!` を削減（S2-05）。
- 2026-03-02: sample/18 向け回帰検知を追加（`single_tag` 添字 fastpath / `py_str_at_nonneg` / nested `format!` 非出力）し、再生成 + transpile/smoke/parity を再通過（S3-01/S3-02）。
- 2026-03-02: 順序依存解析（`items/keys/values`・dict反復・外部不明呼び出し）を追加し、順序不要な `dict[str,int64]` 経路を `HashMap` へ縮退（S2-07）。

## 分解

- [x] [ID: P1-RS-S18-QUALITY-01-S1-01] sample/18 Rust 出力の冗長断片（clone/添字/走査/format）を棚卸しし、改善対象を固定する。
- [x] [ID: P1-RS-S18-QUALITY-01-S1-02] 期待効果とリスクで実装順を確定し、fail-closed 適用境界を定義する。
- [x] [ID: P1-RS-S18-QUALITY-01-S2-01] `current_token/previous_token/eval_expr` で borrow 優先経路を追加し、不要 `clone` を削減する。
- [x] [ID: P1-RS-S18-QUALITY-01-S2-02] 非負添字が確定する経路で index 正規化式を省略する fastpath を追加する。
- [x] [ID: P1-RS-S18-QUALITY-01-S2-03] tokenize の文字走査を `String` 汎用経路から軽量経路（bytes/chars）へ縮退する。
- [x] [ID: P1-RS-S18-QUALITY-01-S2-04] 小規模固定 token 判定で map 依存を減らし、分岐/lookup を簡素化する。
- [x] [ID: P1-RS-S18-QUALITY-01-S2-05] `to_string/format!` 連鎖を簡約し、同値な直接生成へ寄せる。
- [x] [ID: P1-RS-S18-QUALITY-01-S2-06] `&Vec<T>` 受けを `&[T]` に縮退できる経路を実装する。
- [x] [ID: P1-RS-S18-QUALITY-01-S2-07] `BTreeMap` 利用箇所の必要性を再評価し、順序不要経路を軽量mapへ切替える。
- [x] [ID: P1-RS-S18-QUALITY-01-S3-01] unit/golden 回帰を追加し、冗長出力パターンの再発を検知可能にする。
- [x] [ID: P1-RS-S18-QUALITY-01-S3-02] `sample/rs/18` 再生成と transpile/smoke/parity で非退行を確認する。

## 棚卸し結果（S1-01）

- `clone` 過多:
  - `current_token/previous_token` が `Token` を clone 返却（`clone()` + index 正規化式）。
  - `eval_expr` 冒頭で `ExprNode` を clone 取得。
  - `Parser::new((tokens).clone())` の呼び出し側 clone。
- 添字正規化式:
  - `vec[((if idx < 0 { len + idx } else { idx }) as usize)]` 形が多数（`expr_nodes/tokens`）。
  - 非負が保証される `pos/expr_index` でも同式が残存。
- 走査/lookup:
  - `tokenize` の `ch` が毎回 `String` 化（`py_str_at(...).to_string()`）。
  - 単文字 token 判定で `BTreeMap<String, i64>` lookup を毎回実施。
- 文字列生成:
  - `format!("{}{}", format!("{}{}", ...))` 連鎖で深いネスト。
  - `to_string()` が短命値にも広く付与される。
- API 形状:
  - 関数引数が `&Vec<T>` 固定で `&[T]` へ縮退できる箇所が残る。

## 実装順・境界（S1-02）

- 実装順（期待効果/安全性）:
  1. `S2-01` borrow 優先（clone 削減、意味保持しやすい）
  2. `S2-02` 非負添字 fastpath（境界明確）
  3. `S2-06` `&Vec<T> -> &[T]`（低リスク）
  4. `S2-05` 文字列生成簡約
  5. `S2-03` tokenize 走査軽量化
  6. `S2-04` token 判定 map 見直し
  7. `S2-07` map 構造再評価（影響範囲大）
- fail-closed ルール:
  - 型/境界が判定できない場合は最適化しない。
  - index fastpath は `idx >= 0` が構文上確定するケースのみ。
  - borrow 化は mutable alias が発生しない箇所のみ。
  - lookup 構造変更は出力順序依存がないことを確認できる箇所のみ。
