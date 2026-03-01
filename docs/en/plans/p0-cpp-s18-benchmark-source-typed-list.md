# P0: Convert sample/18 benchmark source construction to a typed list (`object + py_append` collapse)

Last updated: 2026-03-01

Related TODO:
- `ID: P0-CPP-S18-BENCH-TYPED-LIST-01` in `docs/ja/todo/index.md`

Background:
- In sample/18 `build_benchmark_source` / `run_demo` / `run_benchmark`, an `object` list and `py_append` remain, which hurts readability and runtime efficiency.
- `list[str]` is valid in this path, so it can be shifted to a typed list.

Goal:
- Move benchmark source construction to a typed-list (`list<str>`) centered flow, and reduce `object` boxing and append-helper dependency.

Scope:
- `src/hooks/cpp/emitter/*` (list initialization/append/return type consistency)
- `test/unit/test_east3_cpp_bridge.py`
- `test/unit/test_py2cpp_codegen_issues.py`
- `sample/cpp/18_mini_language_interpreter.cpp`

Out of scope:
- Logic changes to benchmark scenarios
- Broad one-shot optimization of other samples

Acceptance criteria:
- `object lines = make_object(list<object>{})` is not emitted in sample/18 `build_benchmark_source`.
- `run_demo`/`run_benchmark` are also connected with `list[str]` consistency, with no extra `object` reconversion.
- Non-regression is confirmed via transpile/unit/parity checks.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/runtime_parity_check.py --case-root sample --targets cpp 18_mini_language_interpreter --ignore-unstable-stdout`

Decision log:
- 2026-03-01: Filed as P0 for additional sample/18 optimization to convert benchmark source construction to a typed list.
- 2026-03-01: Added `list[str]` value-model tracking (function return / AnnAssign local / call coercion), and removed `object + py_append + py_to_str_list_from_object` from `build_benchmark_source`/`run_demo`/`run_benchmark`. Confirmed non-regression by passing `test_east3_cpp_bridge` (90), `test_py2cpp_codegen_issues` (83), `check_py2cpp_transpile` (134/134), and sample/18 parity (cpp).

## Breakdown

- [x] [ID: P0-CPP-S18-BENCH-TYPED-LIST-01] Shift `build_benchmark_source` and downstream calls to typed lists and collapse `object + py_append`.
- [x] [ID: P0-CPP-S18-BENCH-TYPED-LIST-01-S1-01] Inventory type boundaries from `build_benchmark_source` to `tokenize`/`parse_program` and lock conditions for preserving `list[str]`.
- [x] [ID: P0-CPP-S18-BENCH-TYPED-LIST-01-S2-01] Update the emitter to emit list initialization/append/return on typed paths.
- [x] [ID: P0-CPP-S18-BENCH-TYPED-LIST-01-S2-02] Add sample/18 regression coverage to prevent reintroduction of `object lines` and `py_append(lines, ...)`.
- [x] [ID: P0-CPP-S18-BENCH-TYPED-LIST-01-S3-01] Re-run transpile/unit/parity and confirm non-regression.
