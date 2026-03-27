<a href="../../en/plans/p1-ruby-sample01-quality-uplift.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1: sample/ruby/01 品質改善（C++品質との差分縮小）

最終更新: 2026-03-02

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-RUBY-SAMPLE01-QUALITY-01`

背景:
- `sample/ruby/01_mandelbrot.rb` は `sample/cpp/01_mandelbrot.cpp` と比較して品質差が大きい。
- 主な差分は以下。
  - 単純ループが `__step_*` 付き `while` lower に退化し、可読性と最適化余地を損ねる。
  - 数値式に `__pytra_int` / `__pytra_float` / `__pytra_div` の同型ラッパーが多重挿入される。
  - `__pytra_truthy` が比較式にも過剰挿入され、Ruby ネイティブ表現を阻害する。
  - `r/g/b` の `nil` 初期化など、型既知経路で不要な一時初期化が残る。

目的:
- Ruby backend の `sample/01` 出力を native 品質へ引き上げ、C++ 出力との差分を縮小する。

対象:
- `src/hooks/ruby/emitter/*`
- `src/hooks/common/*`（必要に応じて）
- `src/runtime/ruby/py_runtime.rb`（必要に応じて）
- `test/unit/test_py2ruby_*`
- `sample/ruby/01_mandelbrot.rb` の再生成

非対象:
- Ruby backend 全ケースの一括最適化
- EAST3 仕様の大規模変更
- C++/Go/Kotlin/Swift backend 側の同時改修

受け入れ基準:
- `sample/ruby/01_mandelbrot.rb` の単純 `range` ループが canonical ループへ lower される。
- 数値ホットパスの同型 `__pytra_int/__pytra_float/__pytra_div` 連鎖が有意に減る。
- 比較式周辺の `__pytra_truthy` 過剰挿入を抑制し、Ruby ネイティブ条件式を優先する。
- `r/g/b` の不要な `nil` 初期化など、typed 経路で不要な一時初期化を削減する。
- unit/transpile/parity が通る。

確認コマンド:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2ruby*.py' -v`
- `python3 tools/check_py2ruby_transpile.py`
- `python3 tools/regenerate_samples.py --langs ruby --force`
- `python3 tools/runtime_parity_check.py --case-root sample --targets ruby 01_mandelbrot`

分解:
- [x] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S1-01] `sample/ruby/01` の品質差分（冗長 cast / loop / truthy / 一時初期化）を棚卸しし、改善優先順を固定する。
- [x] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S2-01] Ruby emitter の数値演算出力で同型変換連鎖を削減し、typed 経路を優先する。
- [x] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S2-02] 単純 `range` ループを canonical loop へ lower する fastpath を追加する。
- [x] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S2-03] 比較式/論理式の `__pytra_truthy` 挿入条件を最適化し、Ruby ネイティブ条件式を優先する。
- [x] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S2-04] `sample/01` の `r/g/b` 等で不要な `nil` 初期化を削減する typed 代入 fastpath を追加する。
- [x] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S3-01] 回帰テスト（コード断片 + parity）を追加し、`sample/ruby/01` 再生成差分を固定する。

決定ログ:
- 2026-03-01: ユーザー指示により、`sample/ruby/01` 品質改善を P1 として計画化し、TODO へ積む方針を確定した。
- 2026-03-02: [ID: P1-RUBY-SAMPLE01-QUALITY-01-S1-01] `sample/ruby/01` と `sample/cpp/01` の棚卸しを実施し、改善優先順を固定。
- 2026-03-02: [ID: P1-RUBY-SAMPLE01-QUALITY-01-S2-02] `ForCore(StaticRange)` に `step=1/-1` canonical while fastpath を追加し、`sample/ruby/01` の `__step_*` を 12 -> 0 へ削減。
- 2026-03-02: [ID: P1-RUBY-SAMPLE01-QUALITY-01-S2-01] 型既知の `int/float/bool` 変換を省略する cast helper を Ruby emitter に追加し、`sample/ruby/01` の loop 初期化/境界で `__pytra_int` 連鎖を削減（`while y < height` などへ縮退）。
- 2026-03-02: [ID: P1-RUBY-SAMPLE01-QUALITY-01-S2-03] bool確定ノードの条件式で `__pytra_truthy` を抑制し、`if (it >= max_iter)` など Ruby ネイティブ条件へ縮退。
- 2026-03-02: [ID: P1-RUBY-SAMPLE01-QUALITY-01-S2-04] `declare=true` かつ `decl_type` が scalar の `AnnAssign(value=None)` は `nil` 初期化を出力せず、`sample/ruby/01` の `r/g/b = nil` を撤去。
- 2026-03-02: [ID: P1-RUBY-SAMPLE01-QUALITY-01-S3-01] `test_py2rb_smoke.py` の `sample01` 断片検証を拡張し（loop/cast/truthy/nil 初期化）、`runtime_parity_check --targets ruby 01_mandelbrot` pass で回帰固定を完了。

## S1-01 棚卸し結果

計測断片（`sample/01`）:

- Ruby 出力: `__pytra_int` 18箇所 / `__pytra_float` 3箇所 / `__pytra_div` 4箇所 / `__pytra_truthy` 3箇所 / `__step_*` 12箇所。
- C++ 出力: `py_to<float64>` 5箇所、`py_div` 0箇所、`py_truthy` 0箇所、単純 `for` に縮退済み。

差分カテゴリと優先順:

1. ループ形状: Ruby は `__step_* + while` へ退化（`for i in range(...)` の可読性低下が最も大きい）。
2. 数値演算ラッパ: `__pytra_int/__pytra_div` の同型変換連鎖がホットパスに残存。
3. 一時初期化: `r/g/b = nil` が typed 分岐前に残る。
4. truthy 過剰: 比較式でも `__pytra_truthy(...)` を経由する経路がある。

実装順:

1. `S2-02`（loop canonicalization）
2. `S2-01`（同型数値 cast 削減）
3. `S2-04`（typed 初期化縮退）
4. `S2-03`（truthy 挿入条件最適化）
