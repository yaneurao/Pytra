<a href="../../ja/plans/p1-lua-emitter.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-2563EB?style=flat-square">
</a>

# P1-LUA-EMITTER: Implement a new Lua emitter in toolchain2

Last updated: 2026-04-02
Status: In progress

## Background

A Lua emitter and runtime exist in the old toolchain1, but they need to be migrated to the new toolchain2 pipeline.

## Design

- Implemented in `src/toolchain2/emit/lua/` using CommonRenderer + override structure
- Reference the old `src/toolchain/emit/lua/` and TS emitter (`src/toolchain2/emit/ts/`)
- Define `calls`, `types`, `env.target`, `builtin_prefix`, `implicit_promotions` in `src/runtime/lua/mapping.json`
- parity check: three-stage verification (fixture + sample + stdlib) via `runtime_parity_check_fast.py --targets lua`

## Decision Log

- 2026-03-31: Lua backend role established. Approach: implement toolchain2 emitter following the emitter guide.
- 2026-04-01: Confirmed implementation of `src/toolchain2/emit/lua/` and `src/runtime/lua/mapping.json`. Fixture emit: 136/136 success.
- 2026-04-01: Reduced `check_emitter_hardcode_lint.py --lang lua -v --no-write` to 0 findings.
- 2026-04-01: parity incomplete. Representative remaining gaps: `add`, `deque_basic`, `class_instance`, `json_*`, `sys_extended`, `argparse_extended`, `pathlib_extended`.
- 2026-04-01: stdlib parity recovered to `16/16 pass`. Implemented Path/json/sys/png/glob/deque/ArgumentParser, class inheritance, list/bytearray/string methods, and linked `pytra_isinstance` in Lua runtime/emitter.
- 2026-04-01: fixture parity improved to `119/137 pass`. Added `StaticRangeForPlan`, staticmethod dispatch, varargs restoration, list concat, zip/sum, and table repr.
- 2026-04-01: sample parity `1/18 pass`. Remaining issues: image artifacts, loop/continue, missing helper functions, sample-specific lowered patterns.
- 2026-04-01: Changed Lua profile to `exception_style=union_return` per `docs/ja/spec/spec-exception.md`. Implemented `ErrorReturn` / `ErrorCheck` / `ErrorCatch` in the emitter; modified `pytra.built_in.error` to emit/load as a pure Python exception class. Exception fixture 5 cases recovered to pass.
- 2026-04-01: Added `dict.get/items` owner completion, `continue` lowering absorption, `import math` shim, `ArgumentParser.add_argument` keyword reflection, dataclass default constructor generation, `sys.set_argv/set_path`, and `re.sub(count=0)` runtime alignment. stdlib recovered to `16/16 pass`; fixture improved to `115/137 pass`.
- 2026-04-01: Continued Lua emitter/runtime fixes. Fixed `type(v).__name__`, bare re-raise, truthiness, property getter, tuple-return unpack, dict/set comprehension, single-argument `range()`, union-via-dict dispatch, `deque`/container `len()`. fixture improved to `131/137 pass`, stdlib maintained `16/16 pass`. Remaining gaps: `class_tuple_assign`, `reversed_enumerate`, `ok_fstring_format_spec`, `ok_lambda_default`, `object_container_access`, `str_repr_containers`.
- 2026-04-01: Added class field `decl_type` retrieval, Lambda `args[].default` support, statically-typed emit for `str([])/str({})`, and conditional branching for float repr. fixture: `137/137 pass`, stdlib: `16/16 pass`. sample: `1/18 pass`; remaining issues are syntax errors, row/base nil, and missing artifacts.
- 2026-04-02: Fixed pure-Python generated module loading per the emitter guide. Changed `pytra.utils.png/gif` to connect via `dofile()` instead of escaping to a Lua runtime shim; also changed module alias imports to be loaded by `runtime_module_id` base. Resolved syntax errors by wrapping `continue` labels in inner `do ... end`.
- 2026-04-02: Aligned `__pytra_bytearray_append` to Python `bytearray.append(int(...))` by converting to integer; changed the hot path from `table.insert()` to direct append. `03_julia_set` passes with `--cmd-timeout-sec 600`; PNG helper unit test also matches at the byte level. Remaining sample differences are mostly performance issues; `07_game_of_life_loop` and `18_mini_language_interpreter` confirmed within 600s timeout.
- 2026-04-02: As a pre-step for sample optimization, added `dict in` specialization, `len(str/list/tuple/bytearray)` fast path, and lightweight truthiness/ifexp to the Lua emitter. Also added checked access helpers for list/string/tuple/bytearray subscript on assign RHS; confirmed full fixture including additional fixtures at `140/140 pass`. Unresolved timeouts for `07_game_of_life_loop` and `18_mini_language_interpreter` remain.
- 2026-04-02: Followed updates to `pytra.utils.png/gif` pure-Python helpers; added `bytearray.extend` and `dict.clear()` to Lua runtime/emitter. Updated full fixture to `144/144 pass`. Confirmed pass for samples `01_mandelbrot`, `03_julia_set`, `05_mandelbrot_zoom`, `17_monte_carlo_pi`, `18_mini_language_interpreter`. Unresolved: `02_raytrace_spheres` / `04_orbit_trap_julia` artifact CRC mismatch, and `06_julia_parameter_sweep` / `07_game_of_life_loop` / `08_langtons_ant` 600s timeout.
- 2026-04-02: Restored `static_cast` handling in the Lua emitter; `__CAST__` now falls through to `__pytra_int/__pytra_float/__pytra_to_string/__pytra_truthy` instead of being a plain passthrough. This resolves the artifact mismatch in `02_raytrace_spheres` and `04_orbit_trap_julia`.
- 2026-04-02: Added a dedicated path in emitter/runtime connecting `bytearray.extend(compressed[pos:pos + chunk_len])` directly to `__pytra_bytearray_extend_slice(...)` for GIF sample hot paths. Avoids intermediate array generation from `__pytra_slice(...)` to reduce timeout for `06_julia_parameter_sweep` / `07_game_of_life_loop` / `08_langtons_ant`.
- 2026-04-02: As `P0-LUA-TYPEID-CLN-S1`, removed `__pytra_isinstance` from the runtime and moved class/type-id check helpers to emitter-generated `pytra_isinstance(...)`. Confirmed full fixture `144/144 pass` and representative samples `02/04/17/18 pass`.
- 2026-04-03: Added micro-optimizations to the Lua runtime: chunked write for `open().write(bytes_table)`, 0..255 fast path for `bytearray.append/extend/extend_slice`, direct indexing for `bytes()/bytearray()` copy, integer fast path for checked subscript, and single-element fast path for `repeat_seq([x], n)`. No regression in targeted fixtures. `06_julia_parameter_sweep` passes at `789.5s`; `07_game_of_life_loop` and `08_langtons_ant` also pass with `--cmd-timeout-sec 14400`.
