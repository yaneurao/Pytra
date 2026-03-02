# P1: sample/ruby/03 出力品質改善（Julia hot path）

最終更新: 2026-03-02

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-RUBY-S03-QUALITY-01`

背景:
- `sample/ruby/03_julia_set.rb` は動作互換を満たしているが、ホットパスに汎用 helper が残り、可読性と実行効率を下げている。
- 代表例として、内側ループでの `__pytra_div` 呼び出し、`pixels.append` 3 連呼、過剰な括弧、同型変換 helper が観測される。

目的:
- `sample/ruby/03` の生成コードを「型既知経路を優先する」形へ寄せ、冗長出力を削減する。
- parity を壊さずに、ホットパスの helper 依存を段階的に減らす。

対象:
- `src/hooks/ruby/emitter/`（式/文/演算描画）
- `test/unit` の Ruby codegen 回帰
- `sample/ruby/03_julia_set.rb`（再生成確認）

非対象:
- Ruby runtime API の全面再設計
- 他 sample / 他 backend への一括横展開
- 画質や演算意味（整数除算・ゼロ除算契約）の変更

受け入れ基準:
- `sample/ruby/03` で次を満たす:
  - 型既知 `float/int` 経路で不要 `__pytra_div` が削減される。
  - `r/g/b` 初期化の冗長代入が削減される。
  - 過剰括弧と同型変換 helper の冗長出力が削減される。
  - ピクセル書き込み周辺の冗長呼び出しが縮退する。
- `check_py2rb_transpile.py` と `runtime_parity_check --targets ruby --case 03_julia_set` が通る。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2rb_transpile.py`
- `python3 tools/regenerate_samples.py --langs ruby --stems 03_julia_set --force`
- `python3 tools/runtime_parity_check.py --case-root sample --targets ruby --case 03_julia_set --ignore-unstable-stdout`

決定ログ:
- 2026-03-02: ユーザー指示により、`sample/ruby/03` の改善項目を P1 計画として起票。

## 分解

- [ ] [ID: P1-RUBY-S03-QUALITY-01-S1-01] `sample/ruby/03` の冗長断片（`__pytra_div` / append / 初期化 / 括弧 / cast）を棚卸しし、優先順を固定する。
- [ ] [ID: P1-RUBY-S03-QUALITY-01-S1-02] fail-closed 適用境界（型既知条件、演算意味維持条件）を仕様化する。
- [ ] [ID: P1-RUBY-S03-QUALITY-01-S2-01] 型既知の割り算経路で `__pytra_div` 依存を削減する emitter fastpath を追加する。
- [ ] [ID: P1-RUBY-S03-QUALITY-01-S2-02] `pixels.append` 周辺の冗長呼び出しを削減する出力規則を追加する。
- [ ] [ID: P1-RUBY-S03-QUALITY-01-S2-03] `r/g/b` 初期化の冗長代入を削減する分岐出力へ更新する。
- [ ] [ID: P1-RUBY-S03-QUALITY-01-S2-04] Ruby 出力の過剰括弧を削減する正規化規則を追加する。
- [ ] [ID: P1-RUBY-S03-QUALITY-01-S2-05] 同型変換 helper（`__pytra_float/__pytra_int`）の不要呼び出しを抑制する。
- [ ] [ID: P1-RUBY-S03-QUALITY-01-S3-01] unit/golden 回帰を追加し、冗長パターンの再発を検知可能にする。
- [ ] [ID: P1-RUBY-S03-QUALITY-01-S3-02] `sample/ruby/03` 再生成と transpile/parity で非退行を確認する。
