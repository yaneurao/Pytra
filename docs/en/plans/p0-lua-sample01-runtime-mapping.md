# P0: Correct runtime mapping for sample/lua/01 (highest priority)

Last updated: 2026-03-01

Related TODO:
- `ID: P0-LUA-SAMPLE01-RUNTIME-01` in `docs/ja/todo/index.md`

Background:
- `sample/lua/01_mandelbrot.lua` is generated with functional gaps because import mapping is not implemented.
- Specifically:
  - `from time import perf_counter` is converted into a `not yet mapped` comment.
  - `pytra.runtime.png` degrades into a no-op stub (`write_rgb_png = function(...) end`).
- In this state, correct I/O behavior for `sample/lua/01` cannot be guaranteed, and benchmark/parity preconditions are not satisfied.

Goal:
- Connect import mapping for `perf_counter` and PNG writer in the Lua backend to real functionality, and remove no-op degradation.

Scope:
- `src/hooks/lua/emitter/lua_native_emitter.py`
- `src/runtime/lua/*` (additions as needed)
- `test/unit/test_py2lua_smoke.py` (or Lua-specific tests)
- Regeneration result of `sample/lua/01_mandelbrot.lua`

Out of scope:
- Whole-backend performance optimization for Lua
- Cleanup of redundant expressions outside `sample/lua/01` (handled in another P1)
- Simultaneous changes to other language backends

Acceptance criteria:
- `not yet mapped` comments do not remain in `sample/lua/01_mandelbrot.lua`.
- `png.write_rgb_png` is not no-op and calls a real runtime implementation.
- `perf_counter` resolves through Lua runtime.
- Unresolved imports are not implicitly no-op and can be detected fail-closed.
- Transpile/smoke/parity pipelines pass.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2lua*.py' -v`
- `python3 tools/check_py2lua_transpile.py`
- `python3 tools/regenerate_samples.py --langs lua --force`
- `python3 tools/runtime_parity_check.py --case-root sample --targets lua 01_mandelbrot`

Breakdown:
- [x] [ID: P0-LUA-SAMPLE01-RUNTIME-01-S1-01] Implement Lua runtime mapping for `time.perf_counter` and ban `not yet mapped` comment generation.
- [x] [ID: P0-LUA-SAMPLE01-RUNTIME-01-S2-01] Connect `pytra.runtime.png` / `pytra.utils.png` to real runtime calls instead of no-op stubs.
- [x] [ID: P0-LUA-SAMPLE01-RUNTIME-01-S2-02] Remove no-op fallback for unresolved imports and switch to fail-closed (explicit errors).
- [x] [ID: P0-LUA-SAMPLE01-RUNTIME-01-S3-01] Add regression tests and lock non-regression with `sample/lua/01` regeneration + parity.

Decision log:
- 2026-03-01: By user instruction, fixed policy to prioritize correcting runtime feature gaps in `sample/lua/01` (time/png no-op) under `P0`.
- 2026-03-01: In `src/hooks/lua/emitter/lua_native_emitter.py`, connected `time.perf_counter` to `__pytra_perf_counter`, connected `pytra.runtime.png` / `pytra.utils.png` to `__pytra_write_rgb_png`-based implementation rather than no-op stubs, and changed unresolved `pytra.*` (especially `gif`) to fail-closed (`RuntimeError`).
- 2026-03-01: Confirmed `output_mismatch` caused by Lua default print separators (tabs), and introduced `__pytra_print` helper to unify output with Python-compatible space-separated formatting.
- 2026-03-01: Updated regression coverage in `test/unit/test_py2lua_smoke.py` and confirmed `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2lua_smoke.py' -v` (18 tests, OK).
- 2026-03-01: Verified execution with `python3 src/py2lua.py sample/py/01_mandelbrot.py -o sample/lua/01_mandelbrot.lua && lua sample/lua/01_mandelbrot.lua`, and confirmed `python3 tools/runtime_parity_check.py --case-root sample --targets lua --ignore-unstable-stdout 01_mandelbrot` as PASS (`cases=1 pass=1 fail=0`).
