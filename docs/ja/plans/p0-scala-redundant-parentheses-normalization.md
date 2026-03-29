<a href="../../en/plans/p0-scala-redundant-parentheses-normalization.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: Scala 出力の冗長括弧（`((...))` / 不要 `(...)`）削減

最終更新: 2026-03-02

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-SCALA-PAREN-NORM-01`

背景:
- `sample/scala/01_mandelbrot.scala` で、`if ((it >= max_iter)) {` や `var y2: Double = (y * y)` のような冗長括弧が残っている。
- 現行の Scala emitter は `BinOp` / `Compare` / `BoolOp` を広く括弧付きで描画しており、単純式でも `(...)` や `((...))` が過剰に出る。
- 可読性が低下し、C++ 出力と比較した品質差分の主要因になっている。

目的:
- Scala 出力で意味を変えずに冗長括弧を削減し、`sample/scala/01` の可読性を改善する。
- 優先対象は `if/while` 条件の二重括弧と、単純 `BinOp` 代入式の外側括弧。

対象:
- `src/hooks/scala/emitter/scala_native_emitter.py`
- `tools/unittest/test_py2scala_smoke.py`
- `tools/check/check_py2scala_transpile.py`（必要時）
- `sample/scala/01_mandelbrot.scala`（再生成確認）

非対象:
- EAST3 optimizer / lowering の意味変更
- Scala runtime の API 仕様変更
- 他 backend（cpp/rs/java/...）の括弧出力規則変更

受け入れ基準:
- `if ((...))` / `while ((...))` の二重括弧が `if (...)` / `while (...)` へ縮退する。
- `var y2: Double = (y * y)` のような単純式が `var y2: Double = y * y` へ縮退する。
- 優先順位が絡む式（例: `a * (b + c)`）は意味保持のため必要括弧を維持する。
- `check_py2scala_transpile.py` が通過し、`sample/scala/01` 再生成差分が期待どおりである。

確認コマンド（予定）:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2scala_smoke.py' -v`
- `python3 tools/check/check_py2scala_transpile.py`
- `python3 tools/gen/regenerate_samples.py --langs scala --stems 01_mandelbrot --force`

決定ログ:
- 2026-03-02: ユーザー指示により、実装着手せず計画のみを先行し、Scala の冗長括弧削減を `P0` で起票。
- 2026-03-02: `If/While/ForCore` 条件で `_strip_outer_parens` を通す経路を追加し、`while ((...))` を `while (...)` へ正規化。
- 2026-03-02: `BinOp` に単純オペランド fastpath（`Name/Constant/Attribute/Call/Subscript`）を追加し、不要な外側括弧のみ削減。複雑式は従来どおり括弧維持（fail-closed）。
- 2026-03-02: `test_py2scala_smoke.py` の runtime 分離後期待値を同期し、`check_py2scala_transpile` / `sample/scala/01` 再生成まで通過。

## 分解

- [x] [ID: P0-SCALA-PAREN-NORM-01-S1-01] 冗長括弧パターン（`BinOp` / `Compare` / `BoolOp` / 条件式）を棚卸しし、除去対象と保持対象を分類する。
- [x] [ID: P0-SCALA-PAREN-NORM-01-S1-02] 優先順位を壊さない最小括弧ルール（必要括弧判定）を仕様化する。
- [x] [ID: P0-SCALA-PAREN-NORM-01-S2-01] `Compare` / `BoolOp` の条件式レンダリングで二重括弧を削減する。
- [x] [ID: P0-SCALA-PAREN-NORM-01-S2-02] `BinOp` の単純式 fastpath を追加し、不要な外側括弧を削減する。
- [x] [ID: P0-SCALA-PAREN-NORM-01-S2-03] 優先順位が必要なケースでは括弧維持するガードを追加する（fail-closed）。
- [x] [ID: P0-SCALA-PAREN-NORM-01-S3-01] unit テストを更新し、冗長括弧再発を回帰検知できるようにする。
- [x] [ID: P0-SCALA-PAREN-NORM-01-S3-02] `sample/scala/01` 再生成と transpile チェックで非退行を確認する。
