# P0: Reduce Same-Type Cast Chains in sample/13

Last updated: 2026-03-01

Related TODO:
- `ID: P0-CPP-S13-SAMECAST-CUT-01` in `docs/en/todo/index.md`

Background:
- Same-type cast chains such as `int64(py_to<int64>(...))` remain in C++ output for sample/13.
- Even on known-type paths, dynamic-cast strings remain and reduce readability.

Goal:
- Remove `int64(py_to<int64>(...))` and similar same-type no-op casts on type-known paths, preferring direct use.

Scope:
- `src/pytra/compiler/east_parts/east3_opt_passes/*` (cast-reduction pass if needed)
- `src/hooks/cpp/emitter/expr.py` / `type_bridge.py` (final guard)
- `test/unit/test_py2cpp_codegen_issues.py`

Out of scope:
- Cast contract changes on `object/Any/unknown` paths
- Runtime `py_to` API spec changes

Acceptance criteria:
- Same-type cast chains in sample/13 are reduced.
- Unknown paths remain fail-closed.
- `check_py2cpp_transpile` and unit tests pass.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`

Decision log:
- 2026-03-01: Opened an independent P0 item for same-type cast reduction in sample/13 based on user request.
- 2026-03-01: After concrete typed-list expansion, same-type cast chains `int64(py_to<int64>(...))` / `float64(py_to<float64>(...))` had disappeared in sample/13, so no additional pass was implemented and behavior was pinned by regression tests.

## Breakdown

- [x] [ID: P0-CPP-S13-SAMECAST-CUT-01-S1-01] Pin sample/13 same-type cast patterns and reduction applicability conditions.
- [x] [ID: P0-CPP-S13-SAMECAST-CUT-01-S2-01] Implement same-type cast reduction in EAST3 or C++ emitter.
- [x] [ID: P0-CPP-S13-SAMECAST-CUT-01-S3-01] Add regressions and pass transpile/check.
