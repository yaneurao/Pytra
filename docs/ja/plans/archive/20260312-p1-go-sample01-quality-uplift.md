# P1: sample/go/01 品質改善（C++品質との差分縮小）

最終更新: 2026-03-02

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
- [x] [ID: P1-GO-SAMPLE01-QUALITY-01-S1-01] `sample/go/01` の品質差分（冗長 cast / loop / no-op / any退化）を棚卸しし、改善優先順を固定する。
- [x] [ID: P1-GO-SAMPLE01-QUALITY-01-S2-01] Go emitter の数値演算出力で同型変換連鎖を削減し、typed 経路を優先する。
- [x] [ID: P1-GO-SAMPLE01-QUALITY-01-S2-02] `range(stop)` / `range(start, stop, 1)` 系を canonical `for` へ lower する fastpath を追加する。
- [x] [ID: P1-GO-SAMPLE01-QUALITY-01-S2-03] `write_rgb_png` 経路を no-op から native runtime 呼び出しへ接続し、未解決時は fail-closed にする。
- [x] [ID: P1-GO-SAMPLE01-QUALITY-01-S2-04] `sample/01` の `pixels` ホットパスで `[]any` 退化を抑制する typed container fastpath を追加する。
- [x] [ID: P1-GO-SAMPLE01-QUALITY-01-S3-01] 回帰テスト（コード断片 + parity）を追加し、`sample/go/01` 再生成差分を固定する。

決定ログ:
- 2026-03-01: ユーザー指示により、`sample/go/01` 品質改善を P1 として計画化し、TODO へ積む方針を確定した。
- 2026-03-01: `sample/go/01_mandelbrot.go` と `sample/cpp/01_mandelbrot.cpp` を比較し、以下を優先順で固定した。
  - P1: `write_rgb_png` が `__pytra_noop(...)` へ落ちる機能欠落（実行品質の本丸）。
  - P2: `pixels` が `[]any` 退化し append ごとに `__pytra_as_list` を挟むホットパス劣化。
  - P3: `__pytra_float/__pytra_int` の同型 cast 連鎖（`__pytra_float(float64(...))` など）による冗長化。
  - P4: `range(..., step=1)` でも汎用 step 分岐ループ（`(__step>=0 && ...) || ...`）を生成する冗長 lower。
- 2026-03-02: `S2-01` として、型既知の numeric cast fastpath（`_render_binop_expr` / `_render_compare_expr` / math 呼び出し / 代入 cast）を導入し、二重 `__pytra_float/__pytra_int` を削減した。`sample/go/01_mandelbrot.go` 再生成で `var x2 float64 = (x * x)` 等の縮退を確認。`PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2go_smoke.py' -v` は pass。`python3 tools/check_py2go_transpile.py` の fail 4件（Try/Yield/Swap 未対応）は既知カテゴリで本タスク外と記録した。
- 2026-03-02: `S2-02` として `StaticRangeForPlan` に step 定数 fastpath を追加し、`step==1` を `for i := start; i < stop; i += 1`、`step==-1` を `for i := start; i > stop; i -= 1` へ lower するよう変更した。`sample/go/01_mandelbrot.go` 再生成で `for i := int64(0); i < max_iter; i += 1` と `for y/x := ...; ...; ... += 1` を確認。`test_py2go_smoke` は pass、`check_py2go_transpile` fail 4件は既知未対応カテゴリ（Try/Yield/Swap）で不変。
- 2026-03-02: `S2-03` として画像 API の no-op 経路を撤去し、`write_rgb_png/save_gif/grayscale_palette` を Go runtime hook（`__pytra_write_rgb_png/__pytra_save_gif/__pytra_grayscale_palette`）へ接続した。`save_gif` は keyword（`delay_cs`, `loop`）を取り込み、未対応 keyword は fail-closed。`python3 tools/regenerate_samples.py --langs go --force` で `sample/go` を再生成し、`sample/go/01` が `__pytra_write_rgb_png(...)`、`sample/go/05` が `__pytra_save_gif(..., int64(5), int64(0))` へ更新されたことを確認。`runtime_parity_check` では `01_mandelbrot` が `artifact_size_mismatch`（`python:5761703`, `go:5761708`）で残るため、最終 parity 収束は `S3-01` 側で扱う。
- 2026-03-02: `S2-04` として `append/pop` に `[]any` owner の typed fastpath を追加し、`append(__pytra_as_list(pixels), ...)` を `append(pixels, ...)` へ縮退させた。`sample/go/01` 再生成で `pixels = append(pixels, r/g/b)` を確認。`test_py2go_smoke` は pass、`check_py2go_transpile` fail 4件（Try/Yield/Swap）は不変。
- 2026-03-02: `S3-01` として `test_py2go_smoke` に回帰断片（numeric cast / canonical loop / image runtime hook / pixels append fastpath）を追加し、`python3 tools/runtime_parity_check.py --case-root sample --targets go 01_mandelbrot` を pass (`cases=1 pass=1 fail=0`) へ収束させた。PNG runtime は Python 実装と同じ stored-deflate 生成へ合わせた。`tools/check_py2go_transpile.py` は他 backend と同じ既知負例（`finally/try_raise/yield_generator_min/tuple_assign`）を expected-fail に揃え、`checked=131 ok=131 fail=0 skipped=10` を確認した。
