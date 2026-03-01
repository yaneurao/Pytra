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
- [ ] [ID: P1-LUA-SAMPLE01-QUALITY-01-S1-01] Lock redundant points in `sample/lua/01` (implicit runtime dependency / `nil` initialization / loop forms) with code fragments.
- [ ] [ID: P1-LUA-SAMPLE01-QUALITY-01-S2-01] Make runtime-dependent output explicit for `int/float/bytearray` etc. and improve self-contained readability.
- [ ] [ID: P1-LUA-SAMPLE01-QUALITY-01-S2-02] Reduce unnecessary `nil` initialization of `r/g/b` on typed paths.
- [ ] [ID: P1-LUA-SAMPLE01-QUALITY-01-S2-03] Add fastpath that simplifies step/parenthesis output for simple `range` loops.
- [ ] [ID: P1-LUA-SAMPLE01-QUALITY-01-S3-01] Add regression tests and lock regenerated diffs of `sample/lua/01`.

Decision Log:
- 2026-03-01: Per user instruction, readability/redundancy improvements for `sample/lua/01` were planned as P1.
