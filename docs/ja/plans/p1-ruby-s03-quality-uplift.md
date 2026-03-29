<a href="../../en/plans/p1-ruby-s03-quality-uplift.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

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
- `python3 tools/check/check_todo_priority.py`
- `python3 tools/check/check_py2rb_transpile.py`
- `python3 tools/gen/regenerate_samples.py --langs ruby --stems 03_julia_set --force`
- `python3 tools/check/runtime_parity_check.py --case-root sample --targets ruby --case 03_julia_set --ignore-unstable-stdout`

決定ログ:
- 2026-03-02: ユーザー指示により、`sample/ruby/03` の改善項目を P1 計画として起票。
- 2026-03-02: `sample/ruby/03_julia_set.rb` の棚卸しで、優先度を `1) hot path 除算 helper 2) 画素 append 3連 3) r/g/b 初期化 4) 過剰括弧 5) 同型 cast helper` の順に固定。
- 2026-03-02: fail-closed 境界を「型既知 numeric（`int/float/bool`）かつ副作用なし式のみ fastpath 適用、`Any/object/union/呼び出し副作用` は既存 helper 経路維持」に確定。
- 2026-03-02: Ruby emitter に `_strip_outer_parens` と `BinOp` 単純式 fastpath を追加し、`if/while` 条件と `zx2 = zx * zx` 系の冗長括弧を削減。
- 2026-03-02: `BinOp` fastpath は precedence guard（`Add/Sub` と `Mult/Div/...`）を追加し、`255.0 * (1.0 - t)` のような右オペランド grouping を保持する fail-closed 実装に固定。
- 2026-03-02: `test_py2rb_smoke.py` を更新し、`sample/01` と `sample/03` の括弧品質回帰を追加。`runtime_parity_check --case-root sample --targets ruby --ignore-unstable-stdout 03_julia_set` を通過。
- 2026-03-02: 連続 `append` の peephole を追加し、同一 owner + 安全引数（Name/Constant/Attribute/Subscript）2件以上を `owner.concat([..])` へ縮退。
- 2026-03-02: `sample/ruby/01` / `sample/ruby/03` で `pixels.concat([r, g, b])` を確認。`test_py2rb_smoke` と `03_julia_set` parity を再通過。
- 2026-03-02: `test_sample03_reduces_redundant_parentheses_in_binop_and_conditions` を追加し、括弧縮退 + `concat` 縮退の回帰検知を固定（S3-01）。
- 2026-03-02: `tools/gen/regenerate_samples.py --langs ruby --stems 01_mandelbrot,03_julia_set --force` と `runtime_parity_check ... 03_julia_set` を再実行し、S3-02 を完了。
- 2026-03-02: `Div` で「右辺が非ゼロ数値定数」のみ direct `/` fastpath を追加し、ゼロ除算契約を壊さない境界で `__pytra_div` 依存を削減（S2-01）。
- 2026-03-02: `sample/ruby/06` の `t = __pytra_div((i - 1), 254.0)` が `(__pytra_float(i - 1)) / 254.0` へ縮退。`03/06` parity 通過を確認。
- 2026-03-02: `_render_float_cast` の数値定数 fastpath（`int -> <n>.0`, `float -> literal`）を追加し、同型 cast helper 呼び出しを抑制（S2-05）。
- 2026-03-02: `Assign*` 連鎖 + `If` の保守的 peephole を追加し、`if` 真分岐が pre-init と同値な場合のみ pre-init を削除（S2-03）。

## 分解

- [x] [ID: P1-RUBY-S03-QUALITY-01-S1-01] `sample/ruby/03` の冗長断片（`__pytra_div` / append / 初期化 / 括弧 / cast）を棚卸しし、優先順を固定する。
- [x] [ID: P1-RUBY-S03-QUALITY-01-S1-02] fail-closed 適用境界（型既知条件、演算意味維持条件）を仕様化する。
- [x] [ID: P1-RUBY-S03-QUALITY-01-S2-01] 型既知の割り算経路で `__pytra_div` 依存を削減する emitter fastpath を追加する。
- [x] [ID: P1-RUBY-S03-QUALITY-01-S2-02] `pixels.append` 周辺の冗長呼び出しを削減する出力規則を追加する。
- [x] [ID: P1-RUBY-S03-QUALITY-01-S2-03] `r/g/b` 初期化の冗長代入を削減する分岐出力へ更新する。
- [x] [ID: P1-RUBY-S03-QUALITY-01-S2-04] Ruby 出力の過剰括弧を削減する正規化規則を追加する。
- [x] [ID: P1-RUBY-S03-QUALITY-01-S2-05] 同型変換 helper（`__pytra_float/__pytra_int`）の不要呼び出しを抑制する。
- [x] [ID: P1-RUBY-S03-QUALITY-01-S3-01] unit/golden 回帰を追加し、冗長パターンの再発を検知可能にする。
- [x] [ID: P1-RUBY-S03-QUALITY-01-S3-02] `sample/ruby/03` 再生成と transpile/parity で非退行を確認する。

## 棚卸し結果（S1-01）

- `__pytra_div` hot path: `zy0/zx/t` 計算で `__pytra_div(y, __hoisted_cast_1)` / `__pytra_div(x, __hoisted_cast_2)` / `__pytra_div(i, __hoisted_cast_3)` が残る。
- append 3 連: `pixels.append(r); pixels.append(g); pixels.append(b);` が各画素ごとに 3 call 発生。
- 初期化冗長: `r=g=b=0` 相当を `r=0; g=0; b=0;` + `if` 内で再代入している。
- 過剰括弧: `if (i >= max_iter)`, `zx2 = (zx * zx)`, `zy = (((2.0 * zx) * zy) + cy)` 等で括弧が過多。
- 同型 cast helper: `__pytra_float((height - 1))` や `__pytra_int((255.0 * ...))` で明らかな同型/単純式 helper が残る。

## 適用境界（S1-02）

- 数値演算 fastpath は `resolved_type` が `int/int64/float/float64/bool` のみ適用。
- `Any/object/union/unknown` を含む式は helper 維持（`__pytra_div`, `__pytra_float`, `__pytra_int`）。
- function call/attribute call を含む式は副作用順序を壊さないため括弧・helper 縮退を抑制。
- 除算は `Div` のみ対象。`FloorDiv`/`Mod` は Python 互換優先で既存 helper 維持。
- append 縮退は bytearray/list の要素型が確定するケースだけ適用し、未確定時は従来経路を維持。
