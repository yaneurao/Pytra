<a href="../../ja/plans/p1-lua-sample01-quality-uplift.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: `sample/lua/01` Quality Uplift (Readability and Redundancy Reduction)

Last updated: 2026-03-01

Related TODO:
- `ID: P1-LUA-SAMPLE01-QUALITY-01` in `docs/ja/todo/index.md`

Background:
- Aside from functional aspects, `sample/lua/01_mandelbrot.lua` has a large readability/redundancy quality gap compared with C++ output.
- Major gaps are:
  - Runtime dependencies such as `int/float/bytearray` are implicit, lowering stand-alone readability.
  - Unnecessary temporary initialization like `r/g/b = nil` remains.
  - Many `for ... , 1 do` and excessive parentheses hurt readability.

Objective:
- Improve readability of `sample/lua/01` output and reduce redundant code.

Scope:
- `src/hooks/lua/emitter/lua_native_emitter.py`
- `src/runtime/lua/*` (as needed)
- `test/unit/test_py2lua_smoke.py` (code-fragment regressions)
- Regenerate `sample/lua/01_mandelbrot.lua`

Out of scope:
- Fixing runtime functional gaps (time/png no-op) (handled earlier in P0)
- Bulk application across the whole Lua backend
- Large EAST3 specification changes

Acceptance Criteria:
- Make runtime-dependent expressions explicit in `sample/lua/01_mandelbrot.lua` and reduce implicit dependencies.
- Remove unnecessary `nil` initialization on typed paths such as `r/g/b`.
- Reduce unnecessary step/parenthesis expressions in simple `range`-origin loops.
- Existing transpile/smoke/parity checks pass without regression.

Validation Commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2lua*.py' -v`
- `python3 tools/check_py2lua_transpile.py`
- `python3 tools/regenerate_samples.py --langs lua --force`

Breakdown:
- [x] [ID: P1-LUA-SAMPLE01-QUALITY-01-S1-01] Lock redundant points in `sample/lua/01` (implicit runtime dependency / `nil` initialization / loop forms) with code fragments.
- [x] [ID: P1-LUA-SAMPLE01-QUALITY-01-S2-01] Make runtime-dependent output explicit for `int/float/bytearray` etc. and improve self-contained readability.
- [x] [ID: P1-LUA-SAMPLE01-QUALITY-01-S2-02] Reduce unnecessary `nil` initialization of `r/g/b` on typed paths.
- [x] [ID: P1-LUA-SAMPLE01-QUALITY-01-S2-03] Add fastpath that simplifies step/parenthesis output for simple `range` loops.
- [x] [ID: P1-LUA-SAMPLE01-QUALITY-01-S3-01] Add regression tests and lock regenerated diffs of `sample/lua/01`.

Decision Log:
- 2026-03-01: Per user instruction, readability/redundancy improvements for `sample/lua/01` were planned as P1.
- 2026-03-02: [ID: P1-LUA-SAMPLE01-QUALITY-01-S1-01] Fixed current redundant fragments in `sample/lua/01_mandelbrot.lua`, and locked implementation priority as `explicit runtime dependency -> reduce nil initialization -> simplify loops`.
- 2026-03-02: [ID: P1-LUA-SAMPLE01-QUALITY-01-S2-01] Unified `int/float/bytearray/bytes` output from inline expansion to `__pytra_*` runtime-helper calls, updating `sample/lua/01` to explicit helper dependency via runtime files.
- 2026-03-02: [ID: P1-LUA-SAMPLE01-QUALITY-01-S2-02] Reduced scalar `AnnAssign(value=None)` to `local name` output and removed `local r/g/b = nil` from `sample/lua/01`.
- 2026-03-02: [ID: P1-LUA-SAMPLE01-QUALITY-01-S2-03] Omitted `step=1` in simple `range` loops, simplified simple bounds to `n - 1`, and stopped emitting `::__pytra_continue_*::` on loops that do not use `continue`.
- 2026-03-02: [ID: P1-LUA-SAMPLE01-QUALITY-01-S3-01] Added `sample01` quality regression fragments to `test_py2lua_smoke.py` (runtime-helper usage / nil removal / loop simplification), and confirmed pass on `check_py2lua_transpile` and `runtime_parity_check --targets lua 01_mandelbrot`.

## S1-01 Audit Results

Locked fragments (`sample/lua/01_mandelbrot.lua`):

- Implicit runtime dependency:
  - `local perf_counter = __pytra_perf_counter`
  - `local png = __pytra_png_module()`
  - `png.write_rgb_png(out_path, width, height, pixels)`
  - Runtime-helper groups are expanded directly at the top of generated output (low self-descriptiveness).
- Unnecessary `nil` initialization:
  - `local r = nil`
  - `local g = nil`
  - `local b = nil`
- Loop redundancy:
  - `for y = 0, (height) - 1, 1 do`
  - `for x = 0, (width) - 1, 1 do`
  - `for i = 0, (max_iter) - 1, 1 do`
  - `::__pytra_continue_2::` / `::__pytra_continue_3::` are emitted even on simple loops.

Implementation priority:

1. `S2-01`: make runtime dependency APIs explicit (improve self-contained call-site readability)
2. `S2-02`: remove `nil` initialization on typed paths
3. `S2-03`: simplify `, 1` / excess parentheses / unnecessary continue labels in loops
