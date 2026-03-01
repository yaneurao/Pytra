# P0: Fix Keyword-Argument Type Propagation for C++ Module Import Functions (remove redundant `int64(py_to<int64>(...))`)

Last updated: 2026-03-01

Related TODO:
- `ID: P0-CPP-MODULE-KW-COERCE-01` in `docs/en/todo/index.md`

Background:
- In C++ output for sample/15, `save_gif(..., delay_cs=4, loop=0)` becomes redundant conversion like `int64(py_to<int64>(4))`.
- Root cause: when merging keyword arguments into positional arguments for module-import function calls, value nodes (`kw_nodes`) are not passed to type-coercion logic and are treated as `unknown`.
- As a result, `_coerce_args_for_module_function()` adds runtime casts in fail-closed mode, leaving redundant casts even for literals.

Goal:
- After argument merge for module-import functions, keep "argument strings" and "corresponding AST nodes" in the same order and use them correctly in coercion.
- Avoid generating redundant `int64(py_to<int64>(...))` for known `int64` literals such as `save_gif(..., delay_cs=4, loop=0)`.

Scope:
- `src/hooks/cpp/emitter/call.py` (args/kw merge and node propagation for import-function path)
- `src/hooks/cpp/emitter/module.py` (module-function coercion)
- `test/unit/test_py2cpp_codegen_issues.py` (sample/15 fragment regression)
- `test/unit/test_east3_cpp_bridge.py` / `tools/check_py2cpp_transpile.py` as needed

Out of scope:
- Changes to keyword merge behavior for class methods / local function calls
- Design changes to module function signature extractor (`extract_function_signatures_from_python_source`)
- Runtime API changes

Acceptance criteria:
- For `save_gif` call in sample/15, output is `..., 4, 0)` and `int64(py_to<int64>(4))` / `int64(py_to<int64>(0))` disappear.
- Even with keyword order swapped (`loop=0, delay_cs=4`), argument order and types remain correct.
- `check_py2cpp_transpile` and related unit tests pass.
- Existing fail-closed behavior remains for `unknown/Any` paths.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/regenerate_samples.py --langs cpp --force`

Decision log:
- 2026-03-01: Based on user report (`int64(py_to<int64>(4))` in sample/15), identified the cause as missing AST-node propagation for keyword arguments in module-import functions and opened this as a P0 task.
- 2026-03-01: Confirmed policy to fix args/kw node alignment at callsite first, and split auxiliary string-literal inference into follow-up optimization.
- 2026-03-01: Unified module-function path to merge not only `args/kw` but also `arg_nodes/kw_nodes` in the same order, and updated `_coerce_args_for_module_function()` to receive merged nodes.
- 2026-03-01: Added `arg_names` to module-signature extraction and adopted reordering to `save_gif(..., delay_cs, loop)` order even when keyword order is swapped (`loop=0, delay_cs=4`).
- 2026-03-01: Added sample/15 regression and keyword-order swap case to `test_py2cpp_codegen_issues.py`; passed `check_py2cpp_transpile` and unit tests (`py2cpp_codegen_issues`, `east3_cpp_bridge`).

## Breakdown

- [x] [ID: P0-CPP-MODULE-KW-COERCE-01-S1-01] When merging `args` and `kw` for module-import function calls, also merge `arg_nodes` and `kw_nodes` in the same order.
- [x] [ID: P0-CPP-MODULE-KW-COERCE-01-S2-01] Pass correct merged nodes to `_coerce_args_for_module_function()` and suppress redundant casts on type-known keyword-literal paths.
- [x] [ID: P0-CPP-MODULE-KW-COERCE-01-S2-02] Add regression tests for sample/15 and keyword-order swap case, pinning `..., 4, 0)` form.
- [x] [ID: P0-CPP-MODULE-KW-COERCE-01-S3-01] Verify non-regression with transpile check / unit / sample regeneration.
