# P1: sample/ruby/01 品質改善（C++品質との差分縮小）

最終更新: 2026-03-01

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
- [ ] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S1-01] `sample/ruby/01` の品質差分（冗長 cast / loop / truthy / 一時初期化）を棚卸しし、改善優先順を固定する。
- [ ] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S2-01] Ruby emitter の数値演算出力で同型変換連鎖を削減し、typed 経路を優先する。
- [ ] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S2-02] 単純 `range` ループを canonical loop へ lower する fastpath を追加する。
- [ ] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S2-03] 比較式/論理式の `__pytra_truthy` 挿入条件を最適化し、Ruby ネイティブ条件式を優先する。
- [ ] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S2-04] `sample/01` の `r/g/b` 等で不要な `nil` 初期化を削減する typed 代入 fastpath を追加する。
- [ ] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S3-01] 回帰テスト（コード断片 + parity）を追加し、`sample/ruby/01` 再生成差分を固定する。

決定ログ:
- 2026-03-01: ユーザー指示により、`sample/ruby/01` 品質改善を P1 として計画化し、TODO へ積む方針を確定した。
