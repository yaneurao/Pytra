# P0: Add Lua backend (highest priority)

Last updated: 2026-02-28

Related TODO:
- `ID: P0-LUA-BACKEND-01` in `docs/ja/todo/index.md`

Background:
- By user instruction, policy was fixed to add Lua as a new target language for Pytra.
- Currently `py2lua.py` and `src/hooks/lua/` do not exist, and the Lua backend is unimplemented.
- As with existing backends, if responsibility boundaries (EAST3 input, fail-closed, runtime boundary) are not fixed first, implementation bloat and compatibility breakage risk are high.

Goal:
- Add a direct generation path `EAST3 -> Lua native` with `py2lua.py` as the entrypoint, so key cases from `sample/py` can run on Lua.

Scope:
- `src/py2lua.py`
- `src/hooks/lua/emitter/`
- `src/runtime/lua/pytra/` (minimum necessary)
- `tools/check_py2lua_transpile.py` / `test/unit/test_py2lua_smoke.py` / parity pipeline
- `sample/lua` and related docs

Out of scope:
- Simultaneous addition of PHP backend
- Advanced optimization for Lua backend (prioritize correctness and regression pipeline first)
- Large design changes in existing backends (`cpp/rs/cs/js/ts/go/java/swift/kotlin/ruby`)

Acceptance criteria:
- Lua code can be generated from EAST3 via `py2lua.py`.
- Minimal fixtures (`add` / `if_else` / `for_range`) transpile and run.
- `tools/check_py2lua_transpile.py` and smoke/parity regression pipelines are prepared.
- `sample/lua` and usage/capability docs in `docs/ja` are synced.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2lua_transpile.py`
- `python3 -m unittest discover -s test/unit -p 'test_py2lua_smoke.py' -v`
- `python3 tools/runtime_parity_check.py --case-root sample --targets lua --all-samples --ignore-unstable-stdout`

Decision log:
- 2026-02-28: By user instruction, policy was fixed to start Lua backend addition as highest priority (P0).
- 2026-02-28: [ID: `P0-LUA-BACKEND-01-S1-01`] Added `docs/ja/spec/spec-lua-native-backend.md`, fixing input responsibilities (EAST3 only), fail-closed, runtime boundary, and out-of-scope items as contract.
- 2026-02-28: [ID: `P0-LUA-BACKEND-01-S1-02`] Added `src/py2lua.py` and `src/hooks/lua/emitter/lua_native_emitter.py`, and implemented a minimal native path for `add/if_else/for_range`. Added `test/unit/test_py2lua_smoke.py` (9 tests) to lock CLI/EAST3 loading/minimal fixture transpilation.
- 2026-02-28: [ID: `P0-LUA-BACKEND-01-S2-01`] Added to Lua emitter: `Assign(target/targets)`, `While`, `Dict/Subscript/IfExp/JoinedStr/Attribute/Box/Unbox`, and Attribute Call lowering. Expanded `test_py2lua_smoke.py` to 12 tests and passed. In cross-fixture runs, improved `ok 22 -> 57`; remaining issues converged to S2-02 areas such as `ClassDef/ListComp/Lambda`.
- 2026-02-28: [ID: `P0-LUA-BACKEND-01-S2-02`] Added `ClassDef`/constructor/method dispatch/`IsInstance`/import lowering (`math` and `pytra.utils png/gif` stubs). Expanded `test_py2lua_smoke.py` to 15 tests and passed. In cross-fixture runs, improved `ok 57 -> 81`; remaining issues converged to non-class areas such as `ListComp/Lambda/ObjStr`.
- 2026-02-28: [ID: `P0-LUA-BACKEND-01-S3-01`] Added `tools/check_py2lua_transpile.py` and confirmed `checked=86 ok=86 fail=0 skipped=53`. Added `runtime_parity_check --targets lua` pipeline and confirmed PASS (exit 0) on `17_monte_carlo_pi` with `toolchain_missing`.
- 2026-02-28: [ID: `P0-LUA-BACKEND-01-S3-02`] Added `lua` config to `tools/regenerate_samples.py` and regenerated `sample/lua` for `02/03/04/17` (`summary: total=4 skip=0 regen=4 fail=0`). Synced Lua pipeline and current coverage in `docs/ja/how-to-use.md` / `docs/ja/spec/spec-user.md` / `docs/ja/spec/spec-import.md` / `sample/readme-ja.md`.

## Breakdown

- [x] [ID: P0-LUA-BACKEND-01-S1-01] Document Lua backend contract (input EAST3, fail-closed, runtime boundary, out-of-scope) in `docs/ja/spec`.
- [x] [ID: P0-LUA-BACKEND-01-S1-02] Add skeletons for `src/py2lua.py` and `src/hooks/lua/emitter/`, and pass minimal fixtures.
- [x] [ID: P0-LUA-BACKEND-01-S2-01] Implement basic expression/statement lowering (assignment, branching, loop, call, minimal builtins).
- [x] [ID: P0-LUA-BACKEND-01-S2-02] Implement phased support for class/instance/isinstance/import (including `math` and image runtime).
- [x] [ID: P0-LUA-BACKEND-01-S3-01] Add `check_py2lua_transpile` and smoke/parity regression pipelines.
- [x] [ID: P0-LUA-BACKEND-01-S3-02] Regenerate `sample/lua` and sync README/How-to-use.
