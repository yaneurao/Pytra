# P1: sample/kotlin/01 品質改善（C++品質との差分縮小）

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-KOTLIN-SAMPLE01-QUALITY-01`

背景:
- `sample/kotlin/01_mandelbrot.kt` は `sample/cpp/01_mandelbrot.cpp` と比べて品質差が大きい。
- 主な差分は以下。
  - 画像出力が `__pytra_noop(...)` へ退化し、生成コードが機能欠落。
  - 数値式に `__pytra_float` / `__pytra_int` の同型ラッパーが多重挿入され、可読性と実行効率を悪化。
  - 単純ループが `__step_*` 付き `while` へ lower され冗長。
  - `MutableList<Any?>` 退化が多く、typed container 最適化が効いていない。

目的:
- Kotlin backend の `sample/01` 出力を native 品質へ引き上げ、C++ 出力との差分を縮小する。

対象:
- `src/hooks/kotlin/emitter/*`
- `src/runtime/kotlin/pytra/*`（必要に応じて）
- `test/unit/test_py2kotlin_*`
- `sample/kotlin/01_mandelbrot.kt` の再生成

非対象:
- Kotlin backend 全ケースの一括最適化
- EAST3 仕様の大幅拡張
- C++/Go backend 側の同時改修

受け入れ基準:
- `sample/kotlin/01_mandelbrot.kt` で PNG 出力が no-op ではなく runtime の実関数呼び出しになる。
- 数値ホットパスの同型 `__pytra_float/__pytra_int` 連鎖が有意に減る。
- `range(stop)` / `range(start, stop, 1)` の単純ケースは canonical ループへ lower される。
- `pixels` 等のホットパスで `MutableList<Any?>` 退化を最小化し typed container を優先する。
- unit/transpile/parity が通る。

確認コマンド:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2kotlin*.py' -v`
- `python3 tools/check_py2kotlin_transpile.py`
- `python3 tools/regenerate_samples.py --langs kotlin --force`
- `python3 tools/runtime_parity_check.py --case-root sample --targets kotlin 01_mandelbrot`

分解:
- [x] [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S1-01] `sample/kotlin/01` の品質差分（冗長 cast / loop / no-op / any退化）を棚卸しし、改善優先順を固定する。
- [x] [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S2-01] Kotlin emitter の数値演算出力で同型変換連鎖を削減し、typed 経路を優先する。
- [x] [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S2-02] 単純 `range` ループを canonical loop へ lower する fastpath を追加する。
- [x] [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S2-03] `write_rgb_png` 経路を no-op から native runtime 呼び出しへ接続し、未解決時は fail-closed にする。
- [x] [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S2-04] `sample/01` の `pixels` 経路で typed container fastpath を追加し、`MutableList<Any?>` 退化を抑制する。
- [x] [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S3-01] 回帰テスト（コード断片 + parity）を追加し、`sample/kotlin/01` 再生成差分を固定する。

決定ログ:
- 2026-03-01: ユーザー指示により、`sample/kotlin/01` 品質改善を P1 として計画化し、TODO へ積む方針を確定した。
- 2026-03-02: [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S1-01] `sample/kotlin/01_mandelbrot.kt` を棚卸しし、主要ボトルネックを `__pytra_float` 78回 / `__pytra_int` 41回 / `__pytra_noop(write_rgb_png)` 1回 / `while ((...))` 3箇所 / `pixels` 再ラップ3箇所と確定。優先順は `S2-03(write_rgb_png) -> S2-01(cast縮退) -> S2-02(canonical loop) -> S2-04(append typed fastpath)` とした。
- 2026-03-02: [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S2-01] Kotlin emitter に runtime cast 正規化（同型二重ラップ除去）と `_needs_cast` 判定を導入し、代入/return/算術で不要な `__pytra_float/__pytra_int` を抑制した。
- 2026-03-02: [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S2-02] `ForCore(StaticRangeForPlan)` に `step==1` fastpath を追加し、`while ((...))` 形式を `while (i < stop)` へ canonical 化した。
- 2026-03-02: [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S2-03] `write_rgb_png` を emitter 側で `__pytra_write_rgb_png(...)` へ直結し、`src/runtime/kotlin/pytra/py_runtime.kt` に `BufferedImage`/`ImageIO` ベース実装を追加して no-op を撤去した。
- 2026-03-02: [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S2-04] `append` 出力で `MutableList<Any?>` 型既知時の fastpath を追加し、`pixels = __pytra_as_list(...); pixels.add(...)` を `pixels.add(...)` に縮退した。
- 2026-03-02: [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S3-01] 回帰テストを追加し、`test_py2kotlin_smoke`(14件)・`check_py2kotlin_transpile`(131件)・`runtime_parity_check(sample/01,kotlin)` をすべて通過。`sample/kotlin/01` は `__pytra_float` 78→10, `__pytra_int` 41→17, `__pytra_noop` 1→0 に縮退した。
