<a href="../../docs-ja/plans/p1-runtime-layout-unification.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# TASK GROUP: TG-P1-RUNTIME-LAYOUT

Last updated: 2026-02-22

Related TODO:
- `docs-ja/todo.md` `ID: P1-RUNTIME-01` to `P1-RUNTIME-06`

Background:
- Runtime placement conventions are fragmented by language, blurring maintenance responsibilities and lookup rules.

Objective:
- Unify runtime placement under `src/runtime/<lang>/pytra/` and align responsibility boundaries for runtime assets.

In scope:
- Rust: migration from `src/rs_module/` to `src/runtime/rs/pytra/`
- Other languages: migration plan for runtime-dependent assets from `src/*_module/` to `src/runtime/<lang>/pytra/`
- Unified runtime resolution paths in `py2*` / hooks

Out of scope:
- Adding runtime features themselves for each language

Acceptance criteria:
- Runtime references are unified to `src/runtime/<lang>/pytra/`
- New runtime additions directly under `src/*_module/` stop

Validation commands:
- `python3 tools/check_py2cpp_transpile.py`
- Language smoke tests (`test/unit/test_py2*_smoke.py`)

`P1-RUNTIME-04` migration plan (non-Rust):

1. Gradually migrate current assets (`src/*_module/`) to the following destinations.
   - C#: `src/cs_module/{py_runtime.cs,pathlib.cs,png_helper.cs,gif_helper.cs,time.cs}` -> `src/runtime/cs/pytra/{built_in,std,utils}/...`
   - JS: `src/js_module/{py_runtime.js,pathlib.js,png_helper.js,gif_helper.js,math.js,time.js}` -> `src/runtime/js/pytra/{built_in,std,utils}/...`
   - TS: `src/ts_module/{py_runtime.ts,pathlib.ts,png_helper.ts,gif_helper.ts,math.ts,time.ts}` -> `src/runtime/ts/pytra/{built_in,std,utils}/...`
   - Go: `src/go_module/py_runtime.go` -> `src/runtime/go/pytra/built_in/py_runtime.go`
   - Java: `src/java_module/PyRuntime.java` -> `src/runtime/java/pytra/built_in/PyRuntime.java`
   - Swift: `src/swift_module/py_runtime.swift` -> `src/runtime/swift/pytra/built_in/py_runtime.swift`
   - Kotlin: `src/kotlin_module/py_runtime.kt` -> `src/runtime/kotlin/pytra/built_in/py_runtime.kt`
2. Migration steps:
   - Step A: create `src/runtime/<lang>/pytra/` skeletons, place copied files with minimal-diff updates that preserve import/namespace behavior.
   - Step B: switch runtime resolution in each `py2<lang>.py` / hook to prefer the new layout (old layout remains compatibility fallback).
   - Step C: pass language-level smoke checks (`tools/check_py2<lang>_transpile.py`, `test/unit/test_py2<lang>_smoke.py`) and remove old-layout references gradually.
   - Step D: after compatibility window, remove runtime bodies from `src/*_module/`, keeping relocation guidance only if needed.
3. Completion conditions:
   - Runtime bodies for non-Rust languages are also under `src/runtime/<lang>/pytra/`.
   - Runtime resolution in `py2*` / hooks works against new layout, with no body dependency on old `src/*_module/`.

`P1-RUNTIME-06` operational rules:

1. Add new runtime implementations (`py_runtime.*`, `pathlib.*`, `png/gif helper`, etc.) only under `src/runtime/<lang>/pytra/`.
2. Treat `src/*_module/` as compatibility layers only; do not add new runtime body files there.
3. Treat compatibility layers as temporary assets intended for removal after migration, and always link them to removal tasks in TODO.
4. If exceptions are required, record reason and planned removal deadline in `docs-ja/todo.md` within the same turn.

Decision log:
- 2026-02-22: Initial draft.
- 2026-02-22: Added `P1-RUNTIME-04` migration plan for non-Rust languages (`C#/JS/TS/Go/Java/Swift/Kotlin`) from `src/*_module/` to `src/runtime/<lang>/pytra/`.
- 2026-02-22: Added `P1-RUNTIME-06` operational rule: no new runtime bodies under `src/*_module/`.
