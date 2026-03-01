# P0: Direct typed unpack for sample/18 `enumerate(lines)`

Last updated: 2026-03-01

Related TODO:
- `ID: P0-CPP-S18-ENUM-DIRECT-TYPED-01` in `docs/ja/todo/index.md`

Background:
- In current generated C++ for `sample/18`, there is still a path that goes through `for (object __itobj ... )` + `py_at(__itobj, i)`.
- Since `enumerate(lines)` is statically known to be `tuple<int64, str>`, it can be lowered to direct unpack.

Goal:
- Standardize `enumerate(lines)` to a direct typed loop (`const auto& [idx, source]`) and eliminate `object` relay.

Scope:
- `src/hooks/cpp/emitter/stmt.py`
- `src/hooks/cpp/emitter/expr.py` (if needed)
- `test/unit/test_east3_cpp_bridge.py`
- `test/unit/test_py2cpp_codegen_issues.py`
- `sample/cpp/18_mini_language_interpreter.cpp`

Out of scope:
- Full type-coverage expansion for enumerate runtime (sample/18 prioritized)
- Broad EAST3 IR spec changes

Acceptance criteria:
- The `tokenize` loop in sample/18 does not use `object` iteration + `py_at`.
- `line_index/source` are directly unpacked in the loop header.
- Unit/transpile checks pass with no regression.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`

Decision log:
- 2026-03-01: Filed as P0 for additional sample/18 optimization to lock direct unpack for `enumerate(lines)`.
- 2026-03-01: In typed enumerate restoration for `ForCore`, fixed the condition to prefer `py_enumerate(lines)` when the typed `list[str]` parameter name is available, avoiding fallback to the `object __itobj` + `py_at` path.
- 2026-03-01: Updated sample/18 regression expectations in `test_py2cpp_codegen_issues.py` to `for (const auto& [line_index, source] : py_enumerate(lines))`, and fixed non-emission of `object __itobj` and `py_at(__itobj, ...)`.
- 2026-03-01: Confirmed non-regression with `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v` (80 tests) and `python3 tools/check_py2cpp_transpile.py` (`checked=134 ok=134 fail=0 skipped=6`).

## Breakdown

- [x] [ID: P0-CPP-S18-ENUM-DIRECT-TYPED-01] Standardize `enumerate(lines)` to direct typed unpack without object relay.
- [x] [ID: P0-CPP-S18-ENUM-DIRECT-TYPED-01-S1-01] Organize `For` lowering conditions (iterable/list/tuple type known) and lock fail-closed behavior outside applicability.
- [x] [ID: P0-CPP-S18-ENUM-DIRECT-TYPED-01-S2-01] Update `for` header emission to prioritize direct structured binding.
- [x] [ID: P0-CPP-S18-ENUM-DIRECT-TYPED-01-S2-02] Add sample/18 regression coverage and lock non-emission of `object __itobj` + `py_at`.
- [x] [ID: P0-CPP-S18-ENUM-DIRECT-TYPED-01-S3-01] Confirm non-regression via transpile/unit/sample regeneration.
