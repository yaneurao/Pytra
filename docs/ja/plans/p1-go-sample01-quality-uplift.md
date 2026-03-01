# P1: sample/go/01 品質改善（C++品質との差分縮小）

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-GO-SAMPLE01-QUALITY-01`

背景:
- `sample/go/01_mandelbrot.go` は `sample/cpp/01_mandelbrot.cpp` と比較して、生成コード品質が低い。
- 主な差分は以下。
  - 数値演算に `__pytra_float` / `__pytra_int` が多重挿入され、可読性と実行効率が悪化。
  - 単純な正方向ループにも汎用 step 付き lower が適用され冗長。
  - 画像出力が `__pytra_noop(...)` で失効しており、生成コードとして機能欠落。
  - `[]any` 退化が多く、型情報を使った最適化が効いていない。

目的:
- Go backend の `sample/01` 出力を「実用可能な native 品質」に引き上げ、C++ 出力との差を縮小する。

対象:
- `src/hooks/go/emitter/*`
- `src/runtime/go/pytra/*`（必要に応じて）
- `test/unit/test_py2go_*`
- `sample/go/01_mandelbrot.go` の再生成

非対象:
- Go backend 全ケースの一括最適化
- EAST3 最適化仕様の大幅追加
- C++/Rust backend 側の調整

受け入れ基準:
- `sample/go/01_mandelbrot.go` で PNG 出力が no-op ではなく実関数呼び出しになる。
- 数値ホットパスで同型 `__pytra_float/__pytra_int` 連鎖が有意に減る。
- `for i := 0; i < n; i++` 相当へ lower 可能な箇所は canonical loop を優先する。
- `sample/go/01_mandelbrot.go` の `pixels` 等で typed container を優先し、`[]any` 退化を最小化する。
- unit/transpile チェックと sample parity が通る。

確認コマンド:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2go*.py' -v`
- `python3 tools/check_py2go_transpile.py`
- `python3 tools/regenerate_samples.py --langs go --force`
- `python3 tools/runtime_parity_check.py --case-root sample --targets go 01_mandelbrot`

分解:
- [ ] [ID: P1-GO-SAMPLE01-QUALITY-01-S1-01] `sample/go/01` の品質差分（冗長 cast / loop / no-op / any退化）を棚卸しし、改善優先順を固定する。
- [ ] [ID: P1-GO-SAMPLE01-QUALITY-01-S2-01] Go emitter の数値演算出力で同型変換連鎖を削減し、typed 経路を優先する。
- [ ] [ID: P1-GO-SAMPLE01-QUALITY-01-S2-02] `range(stop)` / `range(start, stop, 1)` 系を canonical `for` へ lower する fastpath を追加する。
- [ ] [ID: P1-GO-SAMPLE01-QUALITY-01-S2-03] `write_rgb_png` 経路を no-op から native runtime 呼び出しへ接続し、未解決時は fail-closed にする。
- [ ] [ID: P1-GO-SAMPLE01-QUALITY-01-S2-04] `sample/01` の `pixels` ホットパスで `[]any` 退化を抑制する typed container fastpath を追加する。
- [ ] [ID: P1-GO-SAMPLE01-QUALITY-01-S3-01] 回帰テスト（コード断片 + parity）を追加し、`sample/go/01` 再生成差分を固定する。

決定ログ:
- 2026-03-01: ユーザー指示により、`sample/go/01` 品質改善を P1 として計画化し、TODO へ積む方針を確定した。
