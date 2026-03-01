# P0: Emit Direct `/` for Division Between C++ `float64` Values Instead of `py_div`

Last updated: 2026-02-28

Related TODO:
- `ID: P0-CPP-DIV-FLOAT-FASTPATH-01` in `docs/en/todo/index.md`

Background:
- The current C++ emitter lowers almost all `Div` (`/`) to `py_div(lhs, rhs)`.
- `py_div` is needed for Python-compatible true-division paths, but for `float64`-to-`float64` operations it is effectively the same as `lhs / rhs` and hurts generated-code readability.
- In `sample/cpp/01_mandelbrot.cpp`, expressions between `float64` values also become `py_div(...)`.

Goal:
- For `Div` where both sides are confirmed as `float64` (or `float32`), emit direct `lhs / rhs` in C++ output.
- Also move paths that are promoted to float after casts (including `int/int` and `float/int`) to direct `/` output.
- Keep `py_div` on type-uncertain paths (`unknown`/`object`, etc.) to preserve fail-closed behavior.

Scope:
- `src/hooks/cpp/emitter/operator.py` (`Div` lower decision)
- `src/hooks/cpp/optimizer/passes/*` if needed (downstream support)
- `test/unit/test_py2cpp_smoke.py` / `test/unit/test_east3_cpp_bridge.py` / `tools/check_py2cpp_transpile.py`
- Regenerated `sample/cpp` outputs (especially `01_mandelbrot.cpp`)

Out of scope:
- Semantic spec changes for `FloorDiv` / `Mod`
- Migration to EAST3 common optimization layer
- Div-lowering changes for Rust/Java/other backends

Acceptance criteria:
- For type-confirmed `Div` on `float64/float64` (including `float32` when needed), `/` is emitted instead of `py_div`.
- `Div` expressions that become float-float after casts (including `int/int`, `float/int`) are also reduced to `/`.
- On `unknown/object` paths, `py_div` is kept and Python compatibility is not broken.
- `check_py2cpp_transpile` and C++ smoke tests pass without regression.
- Target lines in `sample/cpp/01_mandelbrot.cpp` (`t` computation) change to `/` notation.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_smoke.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/regenerate_samples.py --langs cpp --force`
- `rg -n "py_div\\(| / " sample/cpp/01_mandelbrot.cpp`

Decision log:
- 2026-02-28: By user instruction, opened a P0 item for C++ output optimization to avoid `py_div` for `Div` between `float64` values.
- 2026-02-28: Chosen policy is to determine effective type for `Div` using both `get_expr_type()` and `casts` (`on=left/right`, `to=float64/float32`), and reduce cast-promoted paths to `/`.
- 2026-02-28: Kept `py_div` on `unknown/object` paths as before, preserving fail-closed behavior when fast path is not applicable.

## Breakdown

- [x] [ID: P0-CPP-DIV-FLOAT-FASTPATH-01-S1-01] Document type conditions for `Div` lowering (`float64/float64` first, keep `py_div` for Any/object/int).
- [x] [ID: P0-CPP-DIV-FLOAT-FASTPATH-01-S2-01] Implement typed fast path (direct `/` output) in the `Div` branch of `operator.py`.
- [x] [ID: P0-CPP-DIV-FLOAT-FASTPATH-01-S2-02] Pin boundary cases (`float32`, mixed float, int, Any/object`) with regression tests.
- [x] [ID: P0-CPP-DIV-FLOAT-FASTPATH-01-S3-01] Run `check_py2cpp_transpile` / C++ smoke and verify non-regression.
- [x] [ID: P0-CPP-DIV-FLOAT-FASTPATH-01-S3-02] Regenerate `sample/cpp` and confirm `py_div` reduction in `01_mandelbrot.cpp`.
