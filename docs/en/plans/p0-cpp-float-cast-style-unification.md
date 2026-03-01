# P0: Unify C++ `float64` Cast Style (`static_cast<float64>` -> `float64(...)`)

Last updated: 2026-02-28

Related TODO:
- `ID: P0-CPP-FLOAT-CAST-STYLE-01` in `docs/en/todo/index.md`

Background:
- `sample/cpp` output still has `float64` conversions such as `float64 __hoisted_cast_4 = static_cast<float64>(width);`.
- `float64` is an alias of `double` in runtime, and from a readability perspective this should be moved to function-style cast `float64(width)`.
- Existing implementation uses `static_cast<...>` in multiple places (`apply_cast`/emit), without separating style policy by type.

Goal:
- Unify numeric cast style to `float64(expr)` for casts to `float64` in the C++ backend (including `float32` if needed), reducing output of `static_cast<float64>(expr)`.
- Prioritize semantic preservation, and keep existing fail-closed behavior for `object/Any/unknown` boundaries and non-floating-point casts.

Scope:
- `src/hooks/cpp/emitter/expr.py` (`apply_cast`)
- Direct `static_cast<float64>` emission points in `src/hooks/cpp/emitter/stmt.py` / `src/hooks/cpp/emitter/call.py` / `src/hooks/cpp/emitter/*`
- `test/unit/test_east3_cpp_bridge.py` / `test/unit/test_py2cpp_codegen_issues.py` / `tools/check_py2cpp_transpile.py`
- Verify regenerated `sample/cpp` (especially `16_glass_sculpture_chaos.cpp`)

Out of scope:
- Cast-style changes for types other than `float64` (`int64` / `uint8` / enum, etc.)
- Changes to EAST3 type inference spec
- Changes to runtime definition `using float64 = double;`

Acceptance criteria:
- Cast style to `float64` is unified to `float64(expr)`, and `static_cast<float64>(...)` is no longer newly emitted.
- Safe conversions at `object/Any/unknown` boundaries (`py_to<float64>`, etc.) remain intact.
- `check_py2cpp_transpile` and related unit tests pass.
- Hoisted cast examples in `sample/cpp/16_glass_sculpture_chaos.cpp` change to `float64(width)` form.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/regenerate_samples.py --langs cpp --force`

Decision log:
- 2026-02-28: By user instruction, opened this P0 task to unify output style from `static_cast<float64>(x)` to `float64(x)`.
- 2026-02-28: Confirmed that the scope is style unification; conversion itself (`int64 -> float64`) stays unchanged.
- 2026-03-01: Unified `float64` cast output to `float64(...)` in `call.py` (Builtin `static_cast`), `expr.py` (`min/max` pre-cast), `stmt.py` (AugAssign Any->float), and `cpp_emitter.py` (dict.get float path).
- 2026-03-01: Kept `py_to_float64` / `py_to<float64>` at Any/object boundaries and pinned regressions in `test_float_cast_on_any_like_keeps_runtime_conversion`.
- 2026-03-01: Added sample/16 regression and pinned non-emission of `static_cast<float64>`, plus `float64(width)` / `::std::max<float64>(float64(...), float64(...))`. Unit/transpile checks passed.

## Breakdown

- [x] [ID: P0-CPP-FLOAT-CAST-STYLE-01-S1-01] Inventory `float64` cast emission points in the C++ emitter and pin unified/excluded targets.
- [x] [ID: P0-CPP-FLOAT-CAST-STYLE-01-S2-01] Change `apply_cast` and direct-emission points to prefer `float64(expr)`, eliminating `static_cast<float64>`.
- [x] [ID: P0-CPP-FLOAT-CAST-STYLE-01-S2-02] Add regression tests to verify `py_to<float64>` remains on `object/Any/unknown` paths.
- [x] [ID: P0-CPP-FLOAT-CAST-STYLE-01-S3-01] Verify non-regression with transpile check / unit / sample regeneration and pin corresponding output diff in sample/16.
