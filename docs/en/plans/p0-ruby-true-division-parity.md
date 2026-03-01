# P0: Fix Ruby `/` Operator True-Division Compatibility

Last updated: 2026-02-27

Related TODO:
- `ID: P0-RUBY-DIV-SEMANTICS-01` in `docs/ja/todo/index.md`

Background:
- In Ruby-backend generated code, `int / int` is evaluated as Ruby integer division, creating semantic differences from Python `/` (true division).
- Because of this, behavior diverges in cases with floating-point coordinate math such as `sample/06_julia_parameter_sweep`, breaking parity and the validity of runtime comparison.

Goal:
- Align `/` semantics in the Ruby backend to Python compatibility (always true division) and remove semantic differences in known cases including at least `sample/06`.

In scope:
- Binary operation lowering for `/` in Ruby emitter
- Unit/smoke regressions for Ruby
- Regeneration of `sample/ruby` and parity verification procedure

Out of scope:
- Spec extensions for `//` (floor division) or `%`
- Whole-Ruby optimization (performance tuning)
- Division-spec changes in other language backends

Acceptance criteria:
- Python `/` is evaluated as true division in Ruby-generated code.
- Ruby execution results match Python on regression cases including `sample/06` (following existing unstable-line exclusion rules).
- Tests are added (unit or smoke) to prevent recurrence of `/` semantic differences and make detection possible in CI paths.

Verification commands:
- `python3 -m unittest discover -s test/unit -p 'test_py2rb_smoke.py' -v`
- `python3 tools/check_py2rb_transpile.py`
- `python3 tools/runtime_parity_check.py --case-root sample --targets ruby --all-samples --ignore-unstable-stdout`

Decision log:
- 2026-02-27: During analysis of `sample/05` slowdown factors, we confirmed `int/int` division semantic differences in Ruby-generated `sample/06`; opened this as a P0 fix task.
- 2026-02-28: [ID: P0-RUBY-DIV-SEMANTICS-01-S1-01] Added `/` regressions to `test_py2rb_smoke.py` (`test_true_division_binop_uses_pytra_div_helper` / `test_sample06_uses_true_division_helper`) so code generation via true-division helper is detectable in `sample/06`-related cases.
- 2026-02-28: [ID: P0-RUBY-DIV-SEMANTICS-01-S1-02] Changed Ruby emitter `Div` lowering to `__pytra_div(lhs, rhs)`, and added runtime helper `__pytra_div` (based on `__pytra_float`, raising `ZeroDivisionError` on divide-by-zero), eliminating `int/int` integer-division differences.
- 2026-02-28: [ID: P0-RUBY-DIV-SEMANTICS-01-S1-03] Regenerated all 18 `sample/ruby` outputs and ran `runtime_parity_check --targets ruby --all-samples`, confirming `pass=18 fail=0`. Also passed `check_py2rb_transpile.py` (`checked=133 ok=133 fail=0 skipped=6`).

## Breakdown

- [x] [ID: P0-RUBY-DIV-SEMANTICS-01-S1-01] Pin reproducible cases including `sample/06` and add regression tests that detect `/` semantic differences.
- [x] [ID: P0-RUBY-DIV-SEMANTICS-01-S1-02] Fix `/` lowering in Ruby emitter to true-division semantics and validate compatibility with existing conversions.
- [x] [ID: P0-RUBY-DIV-SEMANTICS-01-S1-03] Regenerate `sample/ruby`, then update runtime parity and measurement re-run verification procedures in README.
