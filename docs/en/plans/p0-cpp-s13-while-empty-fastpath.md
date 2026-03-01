# P0: `.empty()` Fast Path for sample/13 `while stack`

Last updated: 2026-03-01

Related TODO:
- `ID: P0-CPP-S13-WHILE-EMPTY-FASTPATH-01` in `docs/en/todo/index.md`

Background:
- In sample/13, `while stack:` expands to `while (py_len(stack) != 0)`.
- On paths where `stack` is confirmed as a typed list, `.empty()` is simpler and lower-cost.

Goal:
- Add a fast path that converts `while py_len(list) != 0` / `== 0` to `!list.empty()` / `list.empty()` on typed-list paths.

Scope:
- `src/hooks/cpp/emitter/cpp_emitter.py` / `stmt.py` (condition rendering)
- `test/unit/test_east3_cpp_bridge.py` / `test/unit/test_py2cpp_codegen_issues.py`

Out of scope:
- Condition-spec changes for object/Any paths
- Applying to containers other than list

Acceptance criteria:
- In sample/13, `while (py_len(stack) != 0)` is reduced to `while (!stack.empty())` equivalent.
- Unknown/object paths keep current fail-closed behavior.
- Transpile/unit checks pass.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`

Decision log:
- 2026-03-01: Opened an independent P0 item for reducing sample/13 `while stack` expression based on user request.
- 2026-03-01: Added typed-list truthy fast path (`!list.empty()`) to `render_cond`, pinning reduction of `while stack:` to `while (!(stack.empty()))`.
- 2026-03-01: Added `len(list) ==/!= 0` fast path to `_render_compare_expr`, now preferring `list.empty()` / `!(list.empty())` only for typed lists.
- 2026-03-01: Added sample/13 and `len(xs)==/!=0` regressions to `test_py2cpp_codegen_issues.py`, then passed `check_py2cpp_transpile` and unit tests.

## Breakdown

- [x] [ID: P0-CPP-S13-WHILE-EMPTY-FASTPATH-01-S1-01] Define fast-path applicability for typed-list conditions (`py_len(list) ==/!= 0`).
- [x] [ID: P0-CPP-S13-WHILE-EMPTY-FASTPATH-01-S2-01] Implement `.empty()` fast path in condition rendering.
- [x] [ID: P0-CPP-S13-WHILE-EMPTY-FASTPATH-01-S3-01] Add sample/13 regressions and pass transpile/check.
