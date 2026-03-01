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
- [ ] [ID: P0-SCALA-SAMPLE01-QUALITY-01-S1-01] `sample/scala/01` と `sample/cpp/01` を比較し、冗長項目（cast/loop/runtime埋込/typed退化）を断片で固定する。
- [ ] [ID: P0-SCALA-SAMPLE01-QUALITY-01-S1-02] Scala emitter 改善の優先順（可読性インパクト × 実装難易度）を確定する。
- [ ] [ID: P0-SCALA-SAMPLE01-QUALITY-01-S2-01] 数値演算出力の同型 cast 連鎖を削減し、typed 経路を優先する。
- [ ] [ID: P0-SCALA-SAMPLE01-QUALITY-01-S2-02] `range(stop)` / `range(start, stop, 1)` を canonical loop へ lower する fastpath を追加する。
- [ ] [ID: P0-SCALA-SAMPLE01-QUALITY-01-S2-03] `pixels` append ホットパスで `mutable.ArrayBuffer[Any]` typed 経路を優先し、再ラップを削減する。
- [ ] [ID: P0-SCALA-SAMPLE01-QUALITY-01-S2-04] runtime/helper 埋め込みの縮退方針（外出しまたは最小埋込）を実装し、`sample/01` の見通しを改善する。
- [ ] [ID: P0-SCALA-SAMPLE01-QUALITY-01-S3-01] 回帰テスト（コード断片）を追加し、`sample/scala/01` 差分を固定する。
- [ ] [ID: P0-SCALA-SAMPLE01-QUALITY-01-S3-02] `sample/scala` 再生成 + smoke/parity を実行して非退行を確認する。

決定ログ:
- 2026-03-02: ユーザー指示により、`sample/scala/01` の品質改善を P0 として計画化し、TODO へ細分化登録する方針を確定した。
