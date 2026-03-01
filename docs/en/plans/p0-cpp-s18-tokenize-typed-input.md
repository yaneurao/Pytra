# P0: Type sample/18 `tokenize` input (remove `object` degradation)

Last updated: 2026-03-01

Related TODO:
- `ID: P0-CPP-S18-TOKENIZE-TYPED-IN-01` in `docs/ja/todo/index.md`

Background:
- In current generated C++ for `sample/18`, the function is `tokenize(object lines)` and begins by going through `py_to_str_list_from_object(lines)`.
- The source type is already known as `lines: list[str]`, so converting to `object` here causes both copy/cast overhead and readability loss.

Goal:
- Preserve the `list[str]` type at the `tokenize` boundary, removing degradation to `object` and reconversion.

Scope:
- `src/hooks/cpp/emitter/*` (function signature/type bridging/caller consistency)
- `test/unit/test_py2cpp_codegen_issues.py`
- `sample/cpp/18_mini_language_interpreter.cpp` (regeneration check)

Out of scope:
- Mini-language grammar changes
- Full runtime API redesign

Acceptance criteria:
- `tokenize` in `sample/18` no longer takes an `object` argument and receives `list<str>` directly.
- `py_to_str_list_from_object(lines)` is not emitted inside `tokenize`.
- Generated output, unit tests, and transpile checks pass with no regression.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 src/py2cpp.py sample/py/18_mini_language_interpreter.py -o sample/cpp/18_mini_language_interpreter.cpp`

Decision log:
- 2026-03-01: Filed as P0 for additional sample/18 optimization to remove `object` degradation at the `tokenize` boundary.
- 2026-03-01: Added typed signature emission (`const list<str>&`) for `pyobj + list[str]` arguments in `emit_function`, and changed `tokenize` arguments from `object` to `list<str>`.
- 2026-03-01: In typed enumerate restoration for `ForCore`, fixed the condition to prefer `py_enumerate(lines)` when a typed `list[str]` parameter name is present, and removed `py_to_str_list_from_object(lines)` from inside the function.
- 2026-03-01: Added `list[str]`-specific `py_to_str_list_from_object(...)` conversion in callsite coercion, and fixed policy to safely connect `pyobj`-derived `object` variables (`demo_lines`/`source_lines`) to typed `tokenize`.
- 2026-03-01: Confirmed non-regression via `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v` (80 tests), `python3 tools/check_py2cpp_transpile.py` (`checked=134 ok=134 fail=0 skipped=6`), and `python3 tools/runtime_parity_check.py --case-root sample --targets cpp 18_mini_language_interpreter --ignore-unstable-stdout` (PASS).

## Breakdown

- [x] [ID: P0-CPP-S18-TOKENIZE-TYPED-IN-01] Remove `object` degradation from `tokenize` arguments and preserve `list[str]` across the boundary.
- [x] [ID: P0-CPP-S18-TOKENIZE-TYPED-IN-01-S1-01] Inventory current type-decision paths that fall to `object` (function definition/call), and lock fail-closed conditions.
- [x] [ID: P0-CPP-S18-TOKENIZE-TYPED-IN-01-S2-01] Update type bridging in the C++ emitter so `tokenize(lines)` is emitted with a typed signature.
- [x] [ID: P0-CPP-S18-TOKENIZE-TYPED-IN-01-S2-02] Add sample/18 regression coverage and lock non-emission of `py_to_str_list_from_object(lines)`.
- [x] [ID: P0-CPP-S18-TOKENIZE-TYPED-IN-01-S3-01] Run transpile/unit/sample regeneration and confirm non-regression.
