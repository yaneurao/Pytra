# P0: CSE/hoist for sample/13 `candidates` selection expression

Last updated: 2026-03-01

Related TODO:
- `ID: P0-CPP-S13-CANDIDATE-CSE-01` in `docs/en/todo/index.md`

Background:
- In `sel` extraction for sample/13, `(x * 17 + y * 29 + len(stack) * 13) % len(candidates)` and `py_at(candidates, idx)` are repeated per element.
- Repeated expansion of identical expressions hurts readability and execution efficiency.

Goal:
- Hoist identical index calculation and identical element access into temporary variables so `sel` expansion references them only once.

Scope:
- `src/hooks/cpp/emitter/stmt.py` / EAST3 optimizer pass if needed
- `test/unit/test_py2cpp_codegen_issues.py`

Out of scope:
- Full introduction of generic CSE
- Comprehensive optimization guarantees beyond sample/13

Acceptance criteria:
- In sample/13, index calculation is reduced to one occurrence, and duplicate `candidates[...]` / `py_at(candidates, ...)` decreases.
- `sel` expansion becomes `get<0..3>` from single retrieval.
- Existing regressions are not broken.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`

Decision log:
- 2026-03-01: Opened an independent P0 item for duplicate `candidates` selection expressions in sample/13 based on user request.
- 2026-03-01: After applying the immediately prior typed-list expansion, `sel` in sample/13 had already reduced to a single `candidates[idx]` retrieval, so no dedicated CSE implementation was added and behavior was pinned by regression tests.

## Breakdown

- [x] [ID: P0-CPP-S13-CANDIDATE-CSE-01-S1-01] Define duplicate-expression patterns around `sel` and applicability conditions (fail-closed).
- [x] [ID: P0-CPP-S13-CANDIDATE-CSE-01-S2-01] Implement hoist for index/element retrieval and reduce duplicate output.
- [x] [ID: P0-CPP-S13-CANDIDATE-CSE-01-S3-01] Add sample/13 regressions and pass transpile/check.
