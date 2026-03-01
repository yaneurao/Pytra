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
- [x] [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S1-01] `sample/cpp/01` と `sample/scala/01` を比較し、runtime外の品質差分（型退化/冗長cast/制御構文）を断片で固定する。
- [x] [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S1-02] runtime外タスク境界（本計画で扱う改善 / runtime外出しへ委譲する改善）を明文化する。
- [x] [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S2-01] `pixels` などホットパスで `Any` 退化を抑制する typed container 出力規則を実装する。
- [x] [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S2-02] break/continue を含まない単純ループで `boundary` 出力を省略する fastpath を実装する。
- [x] [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S2-03] 型既知経路の identity cast（`__pytra_int(0L)` 等）を削減する emit 規則を実装する。
- [x] [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S2-04] `color_map` 相当の小戻り値経路で `ArrayBuffer[Any]` 依存を縮小する戻り値表現最適化を実装する。
- [x] [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S3-01] 回帰テスト（コード断片）を追加し、`sample/scala/01` の品質指標を固定する。
- [x] [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S3-02] Scala transpile/smoke/parity を実行し、非退行を確認する。

決定ログ:
- 2026-03-02: ユーザー指示により、runtime外出しとは独立した `sample/01` Scala品質改善を P0 として起票。
- 2026-03-02: [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S1-01] `sample/cpp/01` 比較で「typed container不足」「boundary過多」「identity cast残存」を優先改善差分として固定した。
- 2026-03-02: [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S1-02] runtime本体定義/配置は P0-RUNTIME-EXT-SCALA-LUA-01 側へ委譲し、本計画は `// 01:` 以降の生成本体品質のみを対象に確定した。
- 2026-03-02: [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S2-01] `bytearray/list[int] -> mutable.ArrayBuffer[Long]` を導入し、`sample/01` の `pixels` を `Any` から typed container へ縮退した。
- 2026-03-02: [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S2-02] ループ本体に `break/continue` が存在しない場合、`ForCore/While` で `boundary` 生成を省略する fastpath を追加した。
- 2026-03-02: [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S2-03] `int/float` の型既知引数と `StaticRange` の start/stop/step に対して identity cast を省略し、`sample/01` の冗長 `__pytra_int(...)` を削減した。
- 2026-03-02: [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S2-04] `tuple[int,int,int]` を `mutable.ArrayBuffer[Long]` へ縮退し、`color_map` の戻り値経路から `ArrayBuffer[Any]` 依存を縮小した。
- 2026-03-02: [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S3-01] `check_py2scala_transpile.py` に `sample/01` の品質断片チェック（`boundary`/identity cast 再発検知）を追加した。
- 2026-03-02: [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S3-02] `check_py2scala_transpile.py`（135件）と sample parity（`--targets scala 01_mandelbrot`）を実行し、非退行を確認した。

## S1実施結果（2026-03-02）

### S1-01: `sample/cpp/01` vs `sample/scala/01` 品質差分固定

- 差分A: container 型退化
  - Scala: `color_map(...): mutable.ArrayBuffer[Any]` / `pixels: mutable.ArrayBuffer[Any]`
  - C++: `std::tuple<int64,int64,int64>` / `bytearray`
  - 影響: 画素ループが `Any` ベースになり、型情報と可読性が低下。
- 差分B: 制御構文の冗長化
  - Scala: `while` ごとに `boundary` + `Label` が多重に挿入される。
  - C++: `for/while` が素直な構文で出力される。
  - 影響: `break/continue` 非使用のホットループでもノイズが増える。
- 差分C: identity cast / helper 連鎖
  - Scala: `__pytra_int(0L)`, `y < __pytra_int(height)`, `__pytra_int(escape_count(...))`
  - C++: `int64` 既知経路では直接式（`0`, `y < height`, `escape_count(...)`）。
  - 影響: 同型変換で式が長くなり、レビュー時の追跡コストが増える。

### S1-02: runtime外タスク境界の明文化

- 本計画で扱う:
  - `// 01:` コメント以降の関数本体出力（`escape_count/color_map/render_mandelbrot/run_mandelbrot`）。
  - emitter の typed container / cast / loop fastpath 規則。
- 本計画で扱わない:
  - `def __pytra_*` runtime helper 実装そのもの。
  - runtime ファイル配置・読み込み導線・parity 実行時の runtime 同梱規約。
  - これらは P0-RUNTIME-EXT-SCALA-LUA-01 の責務として維持する。
