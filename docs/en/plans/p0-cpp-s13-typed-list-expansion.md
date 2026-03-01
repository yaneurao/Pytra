# P0: Expand Typed-List Handling for `cpp_list_model=pyobj` in sample/13

Last updated: 2026-03-01

Related TODO:
- `ID: P0-CPP-S13-TYPED-LIST-EXPAND-01` in `docs/en/todo/index.md`

Background:
- In `sample/13`, `grid/stack/dirs/frames` fall back to `object` paths, increasing multi-step access through `py_at/py_set_at/py_to`.
- Current typed exceptions for pyobj lists are limited and cannot sufficiently restore types like `list[list[int64]]` or `list[tuple[...]]` back to value/list types.

Goal:
- Even with `cpp_list_model=pyobj`, treat lists with concrete element types that include no `Any/unknown` as typed lists, reducing object degradation in sample/13.

Scope:
- `src/hooks/cpp/emitter/type_bridge.py` (pyobj list decision)
- `src/hooks/cpp/emitter/stmt.py` / `collection_expr.py` (typed list generation/iteration)
- `test/unit/test_py2cpp_codegen_issues.py`

Out of scope:
- Design changes that fully migrate lists to PyObj-based model
- Spec changes to `cpp_list_model=value`

Acceptance criteria:
- In sample/13, `grid/stack/dirs/frames` move toward typed-list output.
- Dependence on `object(py_at(grid, ...))` decreases from main paths.
- `check_py2cpp_transpile` and unit tests pass.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/regenerate_samples.py --langs cpp --force`

Decision log:
- 2026-03-01: Opened this P0 item for pyobj-list typed expansion to improve redundancy in sample/13 based on user request.
- 2026-03-01: Added decision rules that treat concrete `list[T]` as typed-list candidates even in `pyobj` (element types must exclude `Any/unknown/None`), moving `grid/stack/dirs/frames/candidates` in sample/13 toward value-model output. Passed `test_py2cpp_codegen_issues` (84), `test_east3_cpp_bridge` (90), `check_py2cpp_transpile` (134/134), and sample/13 parity (cpp).

## Breakdown

- [x] [ID: P0-CPP-S13-TYPED-LIST-EXPAND-01-S1-01] Specify typed-list decision expansion conditions for `cpp_list_model=pyobj` (concrete element types).
- [x] [ID: P0-CPP-S13-TYPED-LIST-EXPAND-01-S2-01] Update emitter implementation and move `grid/stack/dirs/frames` in sample/13 toward typed lists.
- [x] [ID: P0-CPP-S13-TYPED-LIST-EXPAND-01-S3-01] Add sample/13 fragment regressions and pass transpile/check.
