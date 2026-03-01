# P0: Collapse EAST3 identity `py_to<T>` (highest priority)

Last updated: 2026-03-01

Related TODO:
- `ID: P0-EAST3-PYTO-IDENTITY-01` in `docs/ja/todo/index.md`

Background:
- In C++ output, there are paths where conversions like `py_to<float64>(x)` remain even though the input is already confirmed as `float64`.
- Semantically this is a no-op, but it lowers generated-code readability and adds noise that looks like unnecessary runtime conversion calls.
- Existing omission of identity casts on the C++ side is local/fragmented, and a consistent collapse convention in the previous stage (EAST3) is missing.

Goal:
- Remove identity `py_to<T>` in the EAST3 optimization layer first, collapsing redundant conversions in a backend-independent way.
- Keep only a fail-closed final guard in the C++ emitter, and organize responsibilities as "EAST3 first + emitter safety net".

Scope:
- `src/pytra/compiler/east_parts/east3_opt_passes/*` (identity-conversion collapse pass)
- `src/pytra/compiler/east_parts/east3_optimizer.py` (pass order/enabling)
- `src/hooks/cpp/emitter/*` (minimize final guards/prevent reintroduction)
- `test/unit/test_east3_optimizer.py` / `test/unit/test_east3_cpp_bridge.py` / `tools/check_py2cpp_transpile.py`

Out of scope:
- Conversion-spec changes for dynamic paths such as `object`/`Any`/`unknown`
- Contract changes to the `py_to` runtime API itself
- Code-formatting improvements for non-C++ backends

Acceptance criteria:
- EAST3 removes `py_to<T>`-equivalent casts where source/target identity types are confirmed, within semantics-preserving scope.
- Casts are preserved on `object`/`Any`/`unknown` paths, keeping fail-closed behavior.
- The C++ emitter can suppress identity casts as a final guard against reintroduction.
- `check_py2cpp_transpile` and related units pass with no regression.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_optimizer.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/regenerate_samples.py --langs cpp --force`

Decision log:
- 2026-02-28: By user instruction, policy was fixed to make identity-conversion reduction such as `py_to<float64>(x)` primarily handled by the EAST3 optimization layer, with C++ emitter as safety net.
- 2026-03-01: Added `IdentityPyToElisionPass` and implemented EAST3-side collapse rules for identity conversions of `py_to_string/py_to_bool/py_to_int64/py_to_float64/static_cast` and `Unbox/CastOrRaise` (excluding `object/Any/unknown`).
- 2026-03-01: Added the new pass to `build_default_passes()`, and added pass enable/disable tests plus `py_to_string` / `Unbox` collapse regressions in `test_east3_optimizer.py`.
- 2026-03-01: Confirmed non-regression by running `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_optimizer.py' -v`, `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -v`, `python3 tools/check_py2cpp_transpile.py`, and `python3 tools/regenerate_samples.py --langs cpp --force`.

## Breakdown

- [x] [ID: P0-EAST3-PYTO-IDENTITY-01-S1-01] Fix identity `py_to<T>` collapse rules (applicability/exclusions) as EAST3 pass spec.
- [x] [ID: P0-EAST3-PYTO-IDENTITY-01-S2-01] Implement identity-cast collapse pass in EAST3 optimizer and integrate it into existing pass order.
- [x] [ID: P0-EAST3-PYTO-IDENTITY-01-S2-02] Organize C++ emitter identity-cast suppression as a final guard, preserving fail-closed behavior even when EAST3 pass is not applied.
- [x] [ID: P0-EAST3-PYTO-IDENTITY-01-S3-01] Lock regressions via unit/transpile checks/sample regeneration.
