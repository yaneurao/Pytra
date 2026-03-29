<a href="../../ja/plans/p0-scala-redundant-parentheses-normalization.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Reduce Redundant Parentheses in Scala Output (`((...))` / unnecessary `(...)`)

Last updated: 2026-03-02

Related TODO:
- `ID: P0-SCALA-PAREN-NORM-01` in `docs/ja/todo/index.md`

Background:
- `sample/scala/01_mandelbrot.scala` still contains redundant parentheses such as `if ((it >= max_iter)) {` and `var y2: Double = (y * y)`.
- The current Scala emitter broadly parenthesizes `BinOp` / `Compare` / `BoolOp`, so even simple expressions produce excessive `(...)` or `((...))`.
- This reduces readability and is a major contributor to quality gaps compared with C++ output.

Goal:
- Reduce redundant parentheses in Scala output without changing meaning, and improve readability in `sample/scala/01`.
- Priority targets are double parentheses in `if/while` conditions and outer parentheses around simple `BinOp` assignment expressions.

In scope:
- `src/hooks/scala/emitter/scala_native_emitter.py`
- `tools/unittest/test_py2scala_smoke.py`
- `tools/check/check_py2scala_transpile.py` (if needed)
- `sample/scala/01_mandelbrot.scala` (regeneration check)

Out of scope:
- Semantic changes in EAST3 optimizer / lowering
- Scala runtime API spec changes
- Parenthesis emission rule changes in other backends (`cpp/rs/java/...`)

Acceptance criteria:
- Double parentheses in `if ((...))` / `while ((...))` are reduced to `if (...)` / `while (...)`.
- Simple expressions like `var y2: Double = (y * y)` are reduced to `var y2: Double = y * y`.
- Expressions requiring precedence preservation (example: `a * (b + c)`) keep required parentheses.
- `check_py2scala_transpile.py` passes, and regenerated diffs for `sample/scala/01` match expectations.

Verification commands (planned):
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2scala_smoke.py' -v`
- `python3 tools/check/check_py2scala_transpile.py`
- `python3 tools/gen/regenerate_samples.py --langs scala --stems 01_mandelbrot --force`

Decision log:
- 2026-03-02: Per user instruction, created a P0 ticket for Scala redundant-parentheses reduction as a planning-first task without immediate implementation.
- 2026-03-02: Added a path that passes `If/While/ForCore` conditions through `_strip_outer_parens` to normalize `while ((...))` to `while (...)`.
- 2026-03-02: Added a simple-operand fastpath (`Name/Constant/Attribute/Call/Subscript`) for `BinOp` to remove only unnecessary outer parentheses; complex expressions keep existing parentheses (fail-closed).
- 2026-03-02: Synced post-runtime-separation expected values in `test_py2scala_smoke.py` and passed through `check_py2scala_transpile` and `sample/scala/01` regeneration.

## Breakdown

- [x] [ID: P0-SCALA-PAREN-NORM-01-S1-01] Inventory redundant-parentheses patterns (`BinOp` / `Compare` / `BoolOp` / conditional expressions) and classify removable vs keep-required cases.
- [x] [ID: P0-SCALA-PAREN-NORM-01-S1-02] Specify minimal parenthesis rules (required-parenthesis decisions) that preserve precedence.
- [x] [ID: P0-SCALA-PAREN-NORM-01-S2-01] Reduce double parentheses in conditional rendering for `Compare` / `BoolOp`.
- [x] [ID: P0-SCALA-PAREN-NORM-01-S2-02] Add a simple-expression fastpath for `BinOp` to reduce unnecessary outer parentheses.
- [x] [ID: P0-SCALA-PAREN-NORM-01-S2-03] Add guards to keep parentheses when needed by precedence (fail-closed).
- [x] [ID: P0-SCALA-PAREN-NORM-01-S3-01] Update unit tests so regression detection can catch redundant-parentheses reintroduction.
- [x] [ID: P0-SCALA-PAREN-NORM-01-S3-02] Confirm no regression via `sample/scala/01` regeneration and transpile checks.
