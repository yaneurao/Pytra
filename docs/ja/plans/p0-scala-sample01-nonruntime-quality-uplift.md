# P0: sample/01 Scala品質改善（runtime外出し除く）

最終更新: 2026-03-02

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01`

背景:
- `sample/scala/01_mandelbrot.scala` は C++ 版と比べて、runtime 埋め込み以外にも冗長要素（`Any` 退化、過剰 cast、boundary ラベル多用）が残っている。
- runtime 外出しは別タスク（`P0-RUNTIME-EXT-SCALA-LUA-01`）で扱うため、本計画では生成コード品質そのものの改善に集中する。
- 目的は「runtime 分離前でも読める/追える Scala 出力」を先に作り、後続の runtime 分離で差分が崩れない状態にすること。

目的:
- `sample/scala/01` で runtime 以外の冗長を縮退し、C++ 版に近い可読性と型明瞭性を確保する。
- 改善を sample 専用ハックにせず、Scala emitter の一般規則として再利用可能にする。

対象:
- `src/hooks/scala/emitter/scala_native_emitter.py`
- `src/hooks/code_emitter.py`（Scala 共通規則の利用範囲のみ）
- `tools/check_py2scala_transpile.py`
- `sample/scala/01_mandelbrot.scala`（再生成で反映）

非対象:
- runtime helper 外出し（`P0-RUNTIME-EXT-SCALA-LUA-01` で実施）
- Scala runtime API の新規追加/削除
- Scala 以外 backend の同時最適化

受け入れ基準:
- `sample/scala/01_mandelbrot.scala` のホットパスで `mutable.ArrayBuffer[Any]` が typed container に置換される。
- 単純 while/for 相当経路で不要な `boundary.Label` が出力されない。
- 同型変換連鎖（`__pytra_int(0L)` など）が削減され、型既知経路は直接式で出力される。
- `tools/check_py2scala_transpile.py` と sample parity（`01_mandelbrot`）が非退行で通る。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2scala_transpile.py`
- `python3 tools/regenerate_samples.py --langs scala --force`
- `python3 tools/runtime_parity_check.py --case-root sample --targets scala 01_mandelbrot --ignore-unstable-stdout`

分解:
- [ ] [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S1-01] `sample/cpp/01` と `sample/scala/01` を比較し、runtime外の品質差分（型退化/冗長cast/制御構文）を断片で固定する。
- [ ] [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S1-02] runtime外タスク境界（本計画で扱う改善 / runtime外出しへ委譲する改善）を明文化する。
- [ ] [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S2-01] `pixels` などホットパスで `Any` 退化を抑制する typed container 出力規則を実装する。
- [ ] [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S2-02] break/continue を含まない単純ループで `boundary` 出力を省略する fastpath を実装する。
- [ ] [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S2-03] 型既知経路の identity cast（`__pytra_int(0L)` 等）を削減する emit 規則を実装する。
- [ ] [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S2-04] `color_map` 相当の小戻り値経路で `ArrayBuffer[Any]` 依存を縮小する戻り値表現最適化を実装する。
- [ ] [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S3-01] 回帰テスト（コード断片）を追加し、`sample/scala/01` の品質指標を固定する。
- [ ] [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S3-02] Scala transpile/smoke/parity を実行し、非退行を確認する。

決定ログ:
- 2026-03-02: ユーザー指示により、runtime外出しとは独立した `sample/01` Scala品質改善を P0 として起票。
