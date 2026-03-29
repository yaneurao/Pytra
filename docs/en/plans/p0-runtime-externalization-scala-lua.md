<a href="../../ja/plans/p0-runtime-externalization-scala-lua.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Scala/Lua Runtime Externalization (Remove Inline Helpers)

Last updated: 2026-03-02

Related TODO:
- `ID: P0-RUNTIME-EXT-SCALA-LUA-01` in `docs/ja/todo/index.md`

Background:
- `sample/scala/*.scala` currently inlines runtime helpers directly in generated code instead of referencing a separate file like `py_runtime.scala`.
- `sample/lua/*.lua` does the same by expanding `__pytra_*` helpers at the top, so the runtime source of truth is not managed separately.
- Existing backends such as Go/Java/Kotlin/Swift/Ruby/Rust already use separated runtime files, so only Scala/Lua remain operationally inconsistent.

Goal:
- Remove runtime helper implementations from Scala/Lua generated sources and standardize on separate runtime file references.
- Keep runtime source-of-truth implementations under `src/runtime/<lang>/pytra/` and place them in the same output directory during transpilation.

In scope:
- `src/hooks/scala/emitter/scala_native_emitter.py`
- `src/hooks/lua/emitter/lua_native_emitter.py`
- `src/py2scala.py`
- `src/py2lua.py`
- `src/runtime/scala/pytra/*` (new)
- `src/runtime/lua/pytra/*` (new)
- `tools/check/check_py2scala_transpile.py`
- `tools/check/check_py2lua_transpile.py`
- `tools/check/runtime_parity_check.py` (if needed)

Out of scope:
- Full runtime API redesign
- Scala/Lua backend performance optimization (cast/loop reductions, etc.)
- Runtime redesign for other language backends

Acceptance criteria:
- Runtime helper implementations (for example, `__pytra_int`) are no longer emitted inline in `sample/scala/*.scala` and `sample/lua/*.lua`.
- Running `py2scala` / `py2lua` places runtime files in the output destination.
- Scala/Lua transpile checks can verify the runtime-separation contract (inline forbidden + runtime file exists).
- Sample parity checks (at minimum `01_mandelbrot`) confirm no regression.

Verification commands:
- `python3 tools/check/check_todo_priority.py`
- `python3 tools/check/check_py2scala_transpile.py`
- `python3 tools/check/check_py2lua_transpile.py`
- `python3 tools/gen/regenerate_samples.py --langs scala,lua --force`
- `python3 tools/check/runtime_parity_check.py --case-root sample --targets scala,lua 01_mandelbrot --ignore-unstable-stdout`

Breakdown:
- [x] [ID: P0-RUNTIME-EXT-SCALA-LUA-01-S1-01] Inventory Scala/Lua inline helper emission points and runtime API dependencies, and finalize the externalization boundary.
- [x] [ID: P0-RUNTIME-EXT-SCALA-LUA-01-S1-02] Specify runtime file placement rules (path/file names/loading method).
- [x] [ID: P0-RUNTIME-EXT-SCALA-LUA-01-S2-01] Build the Scala runtime source of truth (`src/runtime/scala/pytra/py_runtime.scala`).
- [x] [ID: P0-RUNTIME-EXT-SCALA-LUA-01-S2-02] Remove inline helper emission from the Scala emitter and implement runtime placement in `py2scala.py`.
- [x] [ID: P0-RUNTIME-EXT-SCALA-LUA-01-S2-03] Build the Lua runtime source of truth (`src/runtime/lua/pytra/py_runtime.lua`).
- [x] [ID: P0-RUNTIME-EXT-SCALA-LUA-01-S2-04] Remove inline helper emission from the Lua emitter and implement runtime placement and loading in `py2lua.py`.
- [x] [ID: P0-RUNTIME-EXT-SCALA-LUA-01-S3-01] Update transpile checks/smoke/parity and lock in regression detection for runtime separation.

## S1 Implementation Results (2026-03-02)

### S1-01: Inline Helper Inventory and Externalization Boundary

- Scala:
  - The inline runtime implementation is concentrated in `_emit_runtime_helpers()` in `scala_native_emitter.py` (`__pytra_*` 54 functions).
  - In `transpile_to_scala_native()`, `_emit_runtime_helpers_minimal(...)` injects required helpers into generated code.
  - Externalization boundary: move the full helper set returned by `_emit_runtime_helpers*` into `py_runtime.scala`; emitter side only imports/uses it.
- Lua:
  - Inline runtime is emitted progressively from `_emit_imports()` through `_emit_*_helper` / `_emit_*_runtime_helpers`.
  - Main emission groups are `print/repeat/truthy/contains/string predicates/perf_counter/math/path/gif/png/isinstance` (11 groups total).
  - Externalization boundary: move helper implementations currently generated directly by `_emit_imports()` into `py_runtime.lua`; emitter side only references the runtime module.
- CLI:
  - `py2scala.py` / `py2lua.py` currently write generated code only and have no runtime placement step.
  - A runtime copy path must be added to the CLIs during externalization.

### S1-02: Runtime File Placement Rules

- Source-of-truth placement:
  - Scala: `src/runtime/scala/pytra/py_runtime.scala`
  - Lua: `src/runtime/lua/pytra/py_runtime.lua`
- Generated output placement:
  - `py2scala.py` copies runtime to `output_path.parent / "py_runtime.scala"`.
  - `py2lua.py` copies runtime to `output_path.parent / "py_runtime.lua"`.
  - Align with existing Go/Kotlin/Swift/Ruby/Rust "adjacent to output file" convention.
- fail-closed:
  - If the runtime source-of-truth file is missing, raise `RuntimeError` in CLI and do not treat generation as success.
- Emitter contract:
  - Do not emit helper implementation strings.
  - Only reference function-name contracts (`__pytra_*`) provided by runtime files.

Decision log:
- 2026-03-02: Per user instruction, opened a new P0 ticket prioritizing Scala/Lua runtime separation.
- 2026-03-02: [ID: P0-RUNTIME-EXT-SCALA-LUA-01-S1-01] Inventoried Scala/Lua inline helper emission points and runtime API dependencies, and fixed the boundary as "move helper implementations to runtime source-of-truth + emitter is reference-only".
- 2026-03-02: [ID: P0-RUNTIME-EXT-SCALA-LUA-01-S1-02] Fixed runtime placement rules as "source of truth at `src/runtime/<lang>/pytra/py_runtime.*` + copy to `output_path.parent/py_runtime.*`".
- 2026-03-02: [ID: P0-RUNTIME-EXT-SCALA-LUA-01-S2-01] Added `src/runtime/scala/pytra/py_runtime.scala` and extracted the current `_emit_runtime_helpers()` helper set into a source-of-truth file.
- 2026-03-02: [ID: P0-RUNTIME-EXT-SCALA-LUA-01-S2-02] Removed runtime inline injection from the Scala emitter and switched to a contract where `py2scala.py` places `py_runtime.scala` in the output destination.
- 2026-03-02: [ID: P0-RUNTIME-EXT-SCALA-LUA-01-S2-03] Added `src/runtime/lua/pytra/py_runtime.lua` and extracted Lua helper implementations (11 groups) into a source-of-truth file.
- 2026-03-02: [ID: P0-RUNTIME-EXT-SCALA-LUA-01-S2-04] Removed direct helper expansion from the Lua emitter and migrated to `dofile(.../py_runtime.lua)` loading + runtime placement in `py2lua.py`.
- 2026-03-02: [ID: P0-RUNTIME-EXT-SCALA-LUA-01-S3-01] Updated `check_py2scala_transpile.py` / `check_py2lua_transpile.py` / `runtime_parity_check.py` and fixed the runtime-separation contract (runtime generation + inline forbidden + runtime co-loading during Scala execution).
