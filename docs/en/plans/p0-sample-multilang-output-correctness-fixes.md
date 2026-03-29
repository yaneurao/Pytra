<a href="../../ja/plans/p0-sample-multilang-output-correctness-fixes.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Correctness Fixes for Multilingual Sample Output (Scala/C#)

Last updated: 2026-03-02

Related TODO:
- `ID: P0-SAMPLE-OUTPUT-CORRECTNESS-01` in `docs/ja/todo/index.md`

Background:
- Cross-checking generated code in `sample/` found outputs that can affect correctness, not just readability.
- In Scala, some expressions break operator precedence and change evaluation order from the original Python expression (example: `255.0 * (1.0 - t)` becomes `255.0 * 1.0 - t`).
- In C#, the typed path contains expressions such as `double t = iter_count / max_iter;` that go through integer division and can embed precision loss in future reuse.

Goal:
- First fix outputs in generated samples that do produce or could produce semantic differences, to build a safe baseline for subsequent quality improvements.

In scope:
- `src/hooks/scala/emitter/*.py`
- `src/hooks/cs/emitter/*.py`
- `sample/scala/01_mandelbrot.scala`
- `sample/cs/01_mandelbrot.cs`
- Related unit/golden tests

Out of scope:
- Performance optimization (hot path optimization is handled in P1)
- Readability-only adjustments (redundant parentheses / temporary variable reduction handled in P2)

Acceptance criteria:
- In Scala output, formulas in `sample/01` are emitted with precedence equivalent to Python.
- In C# output, typed numeric division runs through floating-point paths, removing integer-division dependency.
- Added regression tests can detect the same precedence breakage (Scala) and typed-division regressions (C#).
- Scala/C# parity for `sample/01` passes.

Verification commands:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2scala*' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cs*' -v`
- `python3 tools/gen/regenerate_samples.py --langs scala,cs --stems 01_mandelbrot --force`
- `python3 tools/check/runtime_parity_check.py --case-root sample --targets scala,cs --ignore-unstable-stdout 01_mandelbrot`

Breakdown:
- [x] [ID: P0-SAMPLE-OUTPUT-CORRECTNESS-01-S1-01] Fix arithmetic-precedence preservation in the Scala emitter and remove broken expressions in `sample/scala/01`.
- [x] [ID: P0-SAMPLE-OUTPUT-CORRECTNESS-01-S1-02] Fix typed-division output in the C# emitter and remove integer-division paths.
- [x] [ID: P0-SAMPLE-OUTPUT-CORRECTNESS-01-S2-01] Add Scala/C# regression tests and lock in detection for this class of regression.
- [x] [ID: P0-SAMPLE-OUTPUT-CORRECTNESS-01-S2-02] Regenerate `sample/01` and confirm no regression via parity.

Decision log:
- 2026-03-02: During multilingual sample code quality investigation, separated correctness-impacting fixes (Scala precedence / C# division) into P0.
- 2026-03-02: [ID: P0-SAMPLE-OUTPUT-CORRECTNESS-01-S1-01] Introduced binop precedence handling (`_binop_precedence` / `_wrap_binop_operand`) in `scala_native_emitter.py` so parentheses are preserved for `255.0 * (1.0 - t)`.
- 2026-03-02: [ID: P0-SAMPLE-OUTPUT-CORRECTNESS-01-S1-02] Unified `Div` output in `cs_emitter.py` to `System.Convert.ToDouble(lhs) / System.Convert.ToDouble(rhs)` and removed integer division in typed paths.
- 2026-03-02: [ID: P0-SAMPLE-OUTPUT-CORRECTNESS-01-S2-01] Added regression tests to `test_py2scala_smoke.py` / `test_py2cs_smoke.py` to lock in precedence and typed-division behavior.
- 2026-03-02: [ID: P0-SAMPLE-OUTPUT-CORRECTNESS-01-S2-02] Regenerated `sample/{scala,cs}/01_mandelbrot` with `regenerate_samples` and confirmed parity pass in `runtime_parity_check` (`targets=scala,cs`, `cases=1/fail=0`).
