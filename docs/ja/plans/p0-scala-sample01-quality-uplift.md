# P0: sample/scala/01 品質改善（C++品質との差分縮小）

最終更新: 2026-03-02

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-SCALA-SAMPLE01-QUALITY-01`

背景:
- `sample/scala/01_mandelbrot.scala` は同ケースの C++ 出力と比べて、可読性と型特化度の差が大きい。
- 主な差分は以下。
  - runtime/helper が単一生成ファイルへ大量埋め込みされ、コード本体の視認性が低い。
  - `Any` / `mutable.ArrayBuffer[Any]` 退化と `__pytra_*` 変換連鎖が多く、型既知経路でも冗長になる。
  - 単純 `range` でも汎用 step 分岐ループが出力され、canonical loop へ縮退していない。
  - `pixels` append のホットパスで `__pytra_as_list` の再ラップが残る。

目的:
- `sample/scala/01` の生成品質を改善し、C++ 出力に近い「読みやすい typed/native 形」へ寄せる。

対象:
- `src/hooks/scala/emitter/scala_native_emitter.py`
- （必要に応じて）Scala runtime helper 出力方式
- `test/unit/test_py2scala_smoke.py`
- `sample/scala/01_mandelbrot.scala` の再生成

非対象:
- Scala backend 全ケースの完全最適化
- Scala 言語機能の網羅対応拡大
- C++/Go/Rust backend の同時調整

受け入れ基準:
- `sample/scala/01_mandelbrot.scala` で `__pytra_float(__pytra_float(...))` / `__pytra_int(__pytra_int(...))` の同型連鎖が解消される。
- `for i in range(...)` 由来の `step==1` ループは canonical ループへ縮退する。
- `pixels` append ホットパスで `__pytra_as_list(pixels)` の再ラップを削減する。
- Scala runtime helper の埋め込み方式について方針を固定し、少なくとも `sample/01` で視認性改善が確認できる。
- `test_py2scala_smoke` と Scala sample parity（最低 `01_mandelbrot`）が非退行で通る。

確認コマンド（予定）:
- `python3 tools/regenerate_samples.py --langs scala --force`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2scala_smoke.py' -v`
- `python3 tools/runtime_parity_check.py --case-root sample --targets scala 01_mandelbrot`

分解:
- [x] [ID: P0-SCALA-SAMPLE01-QUALITY-01-S1-01] `sample/scala/01` と `sample/cpp/01` を比較し、冗長項目（cast/loop/runtime埋込/typed退化）を断片で固定する。
- [x] [ID: P0-SCALA-SAMPLE01-QUALITY-01-S1-02] Scala emitter 改善の優先順（可読性インパクト × 実装難易度）を確定する。
- [x] [ID: P0-SCALA-SAMPLE01-QUALITY-01-S2-01] 数値演算出力の同型 cast 連鎖を削減し、typed 経路を優先する。
- [x] [ID: P0-SCALA-SAMPLE01-QUALITY-01-S2-02] `range(stop)` / `range(start, stop, 1)` を canonical loop へ lower する fastpath を追加する。
- [x] [ID: P0-SCALA-SAMPLE01-QUALITY-01-S2-03] `pixels` append ホットパスで `mutable.ArrayBuffer[Any]` typed 経路を優先し、再ラップを削減する。
- [ ] [ID: P0-SCALA-SAMPLE01-QUALITY-01-S2-04] runtime/helper 埋め込みの縮退方針（外出しまたは最小埋込）を実装し、`sample/01` の見通しを改善する。
- [x] [ID: P0-SCALA-SAMPLE01-QUALITY-01-S3-01] 回帰テスト（コード断片）を追加し、`sample/scala/01` 差分を固定する。
- [x] [ID: P0-SCALA-SAMPLE01-QUALITY-01-S3-02] `sample/scala` 再生成 + smoke/parity を実行して非退行を確認する。

S1 棚卸し（2026-03-02）:
- 規模差分: `sample/scala/01_mandelbrot.scala` は 706 行、`sample/cpp/01_mandelbrot.cpp` は 91 行で、主因は runtime/helper の単一ファイル埋め込み。
- cast 連鎖（同型）:
```scala
var __hoisted_cast_3: Double = __pytra_float(__pytra_float(max_iter))
r = __pytra_int(__pytra_int((__pytra_float(255.0) * __pytra_float((__pytra_float(t) * __pytra_float(t))))))
```
- loop 退化（step 汎用分岐）:
```scala
val __step_2 = __pytra_int(1L)
while ((__step_2 >= 0L && y < __pytra_int(height)) || (__step_2 < 0L && y > __pytra_int(height))) {
```
- append ホットパス再ラップ:
```scala
pixels = __pytra_as_list(pixels); pixels.append(r)
pixels = __pytra_as_list(pixels); pixels.append(g)
pixels = __pytra_as_list(pixels); pixels.append(b)
```

S1 優先順（可読性インパクト × 実装難易度）:
1. `S2-01` cast 同型連鎖削減（高インパクト / 低〜中難易度）
2. `S2-03` append ホットパス typed fastpath（高インパクト / 中難易度）
3. `S2-02` canonical loop fastpath（中インパクト / 中難易度）
4. `S2-04` runtime/helper 縮退（高インパクト / 高難易度）

決定ログ:
- 2026-03-02: ユーザー指示により、`sample/scala/01` の品質改善を P0 として計画化し、TODO へ細分化登録する方針を確定した。
- 2026-03-02: [ID: P0-SCALA-SAMPLE01-QUALITY-01-S1-01] `sample/scala/01` と `sample/cpp/01` を比較し、冗長断片（cast 連鎖 / step 汎用 loop / append 再ラップ / runtime 埋め込み）を固定した。
- 2026-03-02: [ID: P0-SCALA-SAMPLE01-QUALITY-01-S1-02] 実装優先順を `cast -> append -> loop -> runtime 縮退` に確定した。
- 2026-03-02: [ID: P0-SCALA-SAMPLE01-QUALITY-01-S2-01] `scala_native_emitter` に同型 wrapper 正規化（`_to_*`）と型既知 operand fastpath を追加し、`sample/scala/01` から `__pytra_float(__pytra_float(` / `__pytra_int(__pytra_int(` を除去した。
- 2026-03-02: [ID: P0-SCALA-SAMPLE01-QUALITY-01-S2-02] `ForCore(StaticRangeForPlan)` で `step==1` の canonical while fastpath（`while (i < stop)`）を追加し、`__step` 分岐ループを縮退した。
- 2026-03-02: [ID: P0-SCALA-SAMPLE01-QUALITY-01-S2-03] `append` 文で typed local（`mutable.ArrayBuffer[Any]`）を検出した場合、`__pytra_as_list` 再ラップなしで `pixels.append(...)` を直接出力する fastpath を追加した。
- 2026-03-02: [ID: P0-SCALA-SAMPLE01-QUALITY-01-S3-01] `test_py2scala_smoke.py` に `test_sample_01_quality_fastpaths_reduce_redundant_wrappers` を追加し、cast/loop/append の断片を回帰固定した。
- 2026-03-02: [ID: P0-SCALA-SAMPLE01-QUALITY-01-S3-02] `sample/py/*.py -> sample/scala/*.scala` を全件再生成し、`test_py2scala_smoke`（17件）と `runtime_parity_check --all-samples --targets scala`（18/18 pass）を確認した。`tools/regenerate_samples.py --langs scala` は未対応（`unknown language(s): scala`）のため別 P0 で継続管理。
