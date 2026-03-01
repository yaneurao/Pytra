# P0: Hoist `grid` Row Access in sample/13

Last updated: 2026-03-01

Related TODO:
- `ID: P0-CPP-S13-GRID-ROW-HOIST-01` in `docs/en/todo/index.md`

Background:
- In sample/13, around `grid[y][x]` / `grid[ny][nx]`, `py_at(grid, ... )` is repeatedly evaluated within the same loop.
- Without row-level temporaries for 2D access, redundant object-access sequences increase.

Goal:
- Hoist row access into `row` temporaries and remove repeated `py_at(grid, y)` for the same index.

Scope:
- `src/hooks/cpp/emitter/stmt.py` / `expr.py` (subscript expansion)
- `src/hooks/cpp/optimizer/passes/*` if needed
- `test/unit/test_py2cpp_codegen_issues.py`

Out of scope:
- Bulk CSE optimization for all samples
- Runtime list/dict API changes

Acceptance criteria:
- Row access is hoisted in sample/13 `capture` / main loop.
- Duplicate `object(py_at(grid, ...))` decreases.
- Regression tests and transpile check pass.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`

Decision log:
- 2026-03-01: Opened an independent P0 item for sample/13 row hoist based on user request.
- 2026-03-01: After concrete typed-list expansion, sample/13 `grid` access had already reduced to direct `grid[y][x]`, and `py_at(grid, ...)` / `object(py_at(grid, ...))` had disappeared, so no dedicated hoist implementation was added and behavior was pinned by regression tests.

## Breakdown

- [x] [ID: P0-CPP-S13-GRID-ROW-HOIST-01-S1-01] Define row-hoist target pattern (reaccessing `grid` at the same index).
- [x] [ID: P0-CPP-S13-GRID-ROW-HOIST-01-S2-01] Implement row hoist in emitter/optimizer and reduce sample/13 output.
- [x] [ID: P0-CPP-S13-GRID-ROW-HOIST-01-S3-01] Add regressions and pass transpile/check.
