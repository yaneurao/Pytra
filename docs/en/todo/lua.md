<a href="../../en/todo/lua.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — Lua backend

> Domain-specific TODO. See [index.md](./index.md) for the full index.

Last updated: 2026-04-02 (Lua fixture 144/144, stdlib 16/16, sample partially re-measured)

## Operating Rules

- **The old toolchain1 (`src/toolchain/emit/lua/`) must not be modified.** All new development and fixes go in `src/toolchain2/emit/lua/` ([spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1).
- Each task requires an `ID` and a context file (`docs/ja/plans/*.md`).
- Work in priority order (lower P numbers first).
- Progress notes and commit messages must always include the same `ID`.
- **When a task is complete, change `[ ]` to `[x]` and append a completion note, then commit.**
- Completed tasks are periodically moved to `docs/ja/todo/archive/`.
- **Completion criteria for parity tests: "emit + compile + run + stdout match".**
- **You must read the [emitter implementation guide](../spec/spec-emitter-guide.md).** It covers the parity check tool, prohibited patterns, and how to use mapping.json.

## References

- Old toolchain1 Lua emitter: `src/toolchain/emit/lua/`
- toolchain2 TS emitter (reference implementation): `src/toolchain2/emit/ts/`
- Existing Lua runtime: `src/runtime/lua/`
- Emitter implementation guide: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json spec: `docs/ja/spec/spec-runtime-mapping.md`

## Incomplete Tasks

### P0-LUA-TYPE-ID-CLEANUP: Remove __pytra_isinstance from the Lua runtime

Spec: [docs/ja/spec/spec-adt.md](../spec/spec-adt.md) §6

Lua has a native `type()`, so `__pytra_isinstance` is unnecessary.

1. [x] [ID: P0-LUA-TYPEID-CLN-S1] Remove `__pytra_isinstance` from `src/runtime/lua/built_in/py_runtime.lua` (2026-04-02) — metatable/type-id determination helpers moved to emitter-generated `pytra_isinstance(...)`
2. [ ] [ID: P0-LUA-TYPEID-CLN-S2] Confirm no regressions in fixture + sample parity

### P1-LUA-EMITTER: Implement a new Lua emitter in toolchain2

Context: [docs/ja/plans/p1-lua-emitter.md](../plans/p1-lua-emitter.md)

1. [x] [ID: P1-LUA-EMITTER-S1] Implement a new Lua emitter in `src/toolchain2/emit/lua/` — CommonRenderer + override structure. Reference the old `src/toolchain/emit/lua/` and the TS emitter. Only override Lua-specific features (1-based index, nil, metatables, etc.) (2026-04-01)
2. [x] [ID: P1-LUA-EMITTER-S2] Create `src/runtime/lua/mapping.json` — define `calls`, `types`, `env.target`, `builtin_prefix`, `implicit_promotions` (2026-04-01)
3. [x] [ID: P1-LUA-EMITTER-S3] Confirm Lua emit success for all fixtures (2026-04-01) — `_transpile_in_memory(..., target='lua')` gives fixture 136/136 emit success
4. [x] [ID: P1-LUA-EMITTER-S4] Align the Lua runtime with toolchain2 emit output (2026-04-01) — Aligned Path/json/sys/png/glob/deque/ArgumentParser, class inheritance, list/bytearray/string methods, and linked `pytra_isinstance`
5. [ ] [ID: P1-LUA-EMITTER-S5] Pass fixture + sample Lua run parity (`lua5.4`) — As of 2026-04-03: `fixture 144/144 pass`, `stdlib 16/16 pass`. Fixed pure-Python generated helper loading per emitter guide, connected `pytra.utils.png/gif` via `dofile()`. Added `bytearray.extend` and `dict.clear()` to runtime/emitter, reconfirmed full fixture `144/144 pass` including new fixtures. Further reverted `static_cast` to `__pytra_int/__pytra_float/...` to resolve `02_raytrace_spheres` / `04_orbit_trap_julia` artifact mismatches, and directly connected `bytearray.extend(bytes_slice)` to `__pytra_bytearray_extend_slice(...)` for GIF hot path. Confirmed PASS for at least: `01_mandelbrot`, `02_raytrace_spheres`, `03_julia_set`, `04_orbit_trap_julia`, `05_mandelbrot_zoom`, `06_julia_parameter_sweep`, `07_game_of_life_loop`, `08_langtons_ant`, `17_monte_carlo_pi`, `18_mini_language_interpreter`. `06/07/08` confirmed PASS with `--cmd-timeout-sec 14400`. Full sample PASS count is not yet finalized
6. [x] [ID: P1-LUA-EMITTER-S6] Pass stdlib Lua parity (`--case-root stdlib`) (2026-04-01) — `runtime_parity_check_fast.py --targets lua --case-root stdlib` confirms `16/16 pass`

### P2-LUA-LINT-FIX: Fix hardcode violations in the Lua emitter

1. [x] [ID: P2-LUA-LINT-S1] Confirm 0 Lua violations in `check_emitter_hardcode_lint.py` (2026-04-01) — 0 violations

### P3-COPY-ELISION: Add copy elision metadata to EAST3 and optimize bytes copies in Lua

Context: [docs/ja/plans/p3-copy-elision-east-meta.md](../plans/p3-copy-elision-east-meta.md)

`bytes(bytearray)` copies are in the hot path of GIF samples. Omitting copies based solely on the emitter's own judgment violates semantics (rolled back). Linker analysis results will be placed in EAST3 meta as `copy_elision_safe_v1`, and the emitter will only omit copies when it sees that flag.

1. [x] [ID: P3-COPY-ELISION-S1] Define the `copy_elision_safe_v1` schema in spec-east.md (2026-04-02) — `Call.meta.copy_elision_safe_v1` defined as canonical linker metadata
2. [x] [ID: P3-COPY-ELISION-S2] Implement copy elision determination via def-use / non-escape analysis in the linker (2026-04-02) — v1 is narrow/fail-closed: only annotate when `return bytes(local_bytearray)` flows exclusively to a readonly `list[bytes]`
3. [x] [ID: P3-COPY-ELISION-S3] Implement copy omission in the Lua emitter by checking `copy_elision_safe_v1` (2026-04-02) — introduced `__pytra_bytes_alias()` and alias only `bytes(bytearray)` calls that have the metadata
4. [ ] [ID: P3-COPY-ELISION-S4] Confirm `07_game_of_life_loop` Lua parity PASS + performance improvement — `03_julia_set` is PASS with no regression. `07_game_of_life_loop` still times out even with `--cmd-timeout-sec 600` after copy elision

### P20-LUA-SELFHOST: Convert toolchain2 to Lua via the Lua emitter and run it

1. [ ] [ID: P20-LUA-SELFHOST-S0] Complete type annotation for selfhost target code (shared with other languages)
2. [ ] [ID: P20-LUA-SELFHOST-S1] Emit all toolchain2 .py files to Lua and confirm they can run
3. [ ] [ID: P20-LUA-SELFHOST-S2] Place Lua selfhost golden files
4. [ ] [ID: P20-LUA-SELFHOST-S3] Confirm fixture parity PASS with `run_selfhost_parity.py --selfhost-lang lua --emit-target lua --case-root fixture`
5. [ ] [ID: P20-LUA-SELFHOST-S4] Confirm sample parity PASS with `run_selfhost_parity.py --selfhost-lang lua --emit-target lua --case-root sample`
