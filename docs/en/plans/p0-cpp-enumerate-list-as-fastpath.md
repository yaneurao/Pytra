# P0: Introduce C++ `py_enumerate_list_as<T>()` (remove intermediate copy from `py_to_str_list_from_object`)

Last updated: 2026-03-01

Related TODO:
- `ID: P0-CPP-ENUM-LIST-AS-01` in `docs/en/todo/index.md`

Background:
- When restoring `enumerate(lines)` (`lines: list[str]`) to a typed loop under `cpp_list_model=pyobj`, current output is `py_enumerate(py_to_str_list_from_object(lines))`.
- `py_to_str_list_from_object()` rescans list elements inside `object` with `obj_to_str` and builds a new `list<str>`, causing an unnecessary intermediate copy.
- The tokenize loop in sample/18 goes through this path, so this is wasted work on a hot path.

Goal:
- Add `py_enumerate_list_as<T>(const object&)` (+ `start` overload) to runtime, and introduce a fast path that directly enumerates `object(list<object>)` and returns `list<tuple<int64, T>>`.
- Replace the typed-enumerate restoration path in the C++ emitter from `py_to_str_list_from_object(...)` to `py_enumerate_list_as<str>(...)` and remove intermediate `list<str>` construction.

Scope:
- `src/runtime/cpp/pytra-core/built_in/py_runtime.h` (add `py_enumerate_list_as<T>`)
- `src/hooks/cpp/emitter/stmt.py` (change typed enumerate fast-path output)
- `test/unit/test_py2cpp_codegen_issues.py` (update fixed string for sample/18)
- Runtime regressions such as `test/unit/test_cpp_runtime_boxing.py` when needed

Out of scope:
- Contract changes to existing API `py_enumerate(object)`
- Introducing generic `py_enumerate_as<T>` for `str` / `dict` / `set`
- Changes to `cpp_list_model=value` path

Acceptance criteria:
- In `sample/18` output for `cpp_list_model=pyobj`, `py_enumerate(py_to_str_list_from_object(lines))` disappears and `py_enumerate_list_as<str>(lines)` is used.
- The start-specified path with `py_enumerate_list_as<str>(..., start)` is also correctly emitted and works.
- `check_py2cpp_transpile` and related unit tests pass.
- Existing fail-closed behavior is preserved (safe behavior for non-list/object mismatch).

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/regenerate_samples.py --langs cpp --force`

Decision log:
- 2026-03-01: By user instruction, opened this P0 task to introduce `py_enumerate_list_as<T>()` to avoid intermediate list construction by `py_to_str_list_from_object`.
- 2026-03-01: Adopted `py_enumerate_list_as<T>` as the API name to make it explicit that it is list-specific; generic `py_enumerate_as<T>` was made out of scope.
- 2026-03-01: Decided to add `py_enumerate_list_as<T>(const object&, int64)` / `py_enumerate_list_as<T>(const object&)` to runtime and generate typed tuple lists via direct `obj_to_list_ptr` enumeration + `py_to<T>` conversion.
- 2026-03-01: Replaced `py_to_str_list_from_object(...)` with `py_enumerate_list_as<str>(...)` in typed enumerate restoration in `stmt.py`, removing intermediate `list<str>` reconstruction.
- 2026-03-01: Added regression for pyobj runtime list conditions in `test_east3_cpp_bridge.py` and pinned `py_enumerate_list_as<str>(lines)` output. `check_py2cpp_transpile` and unit tests passed.

## Breakdown

- [x] [ID: P0-CPP-ENUM-LIST-AS-01-S1-01] Add `py_enumerate_list_as<T>(object[, start])` to runtime and generate typed tuple enumeration from `object(list<object>)`.
- [x] [ID: P0-CPP-ENUM-LIST-AS-01-S2-01] Switch typed enumerate fast path in `stmt.py` to `py_enumerate_list_as<str>(...)` output.
- [x] [ID: P0-CPP-ENUM-LIST-AS-01-S2-02] Update expected values in sample/18 regression tests and pin non-dependence on `py_to_str_list_from_object`.
- [x] [ID: P0-CPP-ENUM-LIST-AS-01-S3-01] Run unit/transpile/sample regeneration and verify non-regression.
