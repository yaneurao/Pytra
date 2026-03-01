# P0: EAST3 cross-module non-escape analysis (including imported module bodies)

Last updated: 2026-02-28

Related TODO:
- `ID: P0-EAST3-XMOD-NONESCAPE-01` in `docs/ja/todo/index.md`

Background:
- The current `NonEscapeInterproceduralPass` analyzes only `FunctionDef/ClassDef` within the same module.
- Therefore imported functions such as `save_gif(...)` become unresolved calls, and under default policy (fail-closed) their arguments are treated as escaped.
- As a result, on the C++ emitter side there are still cases where `frames: list[bytes]` cannot be judged as non-escape and degrades to `object`.

Goal:
- Extend EAST3 non-escape analysis across modules (import closure), and compute summaries on a call graph that includes imported function bodies.
- Do not introduce handwritten `escape contract` definitions; decide only from actual source bodies.

Scope:
- `src/pytra/compiler/east_parts/east3_opt_passes/non_escape_call_graph.py`
- `src/pytra/compiler/east_parts/east3_opt_passes/non_escape_interprocedural_pass.py`
- Import-resolution area (as needed: `core.py` / `transpile_cli.py` / EAST3 doc meta)
- `src/hooks/cpp/emitter/cpp_emitter.py` (collapse fixed safe-call judgment)
- `test/unit/test_east3_non_escape_*`
- `test/unit/test_py2cpp_*` and `tools/check_py2cpp_transpile.py`
- Regeneration check for `sample/cpp/05_mandelbrot_zoom.cpp`

Out of scope:
- New handwritten `escape contract` registry
- Applying escape optimization to other backends (Rust/Java/Go, etc.)
- Advanced alias analysis or points-to analysis

Acceptance criteria:
- A call graph including imported functions is built, and `non_escape_summary` converges across modules.
- On the `sample/05` path calling `save_gif`, `frames` is judged non-escape, and C++ output can preserve `list<bytes>` (or equivalent value type).
- Even with unresolved imports or circular imports, fail-closed behavior is preserved and convergence is deterministic without crashes.
- Existing `east3 optimizer` / `py2cpp` regressions pass with no regression.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_non_escape_*.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_optimizer*.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_*.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/regenerate_samples.py --langs cpp --force`
- `rg -n "frames|save_gif|list<bytes>|object frames" sample/cpp/05_mandelbrot_zoom.cpp`

Decision log:
- 2026-02-28: By user instruction, the `escape contract` approach was rejected and policy was fixed to a cross-module call-graph-based non-escape judgment.
- 2026-02-28: Registered `NonEscapeInterproceduralPass` in the default `EAST3` pass sequence so `non_escape_callsite` annotations are added in normal `py2cpp` conversion paths.
- 2026-02-28: Introduced a policy that builds import-only fallback docs when self-host parsing of imported modules fails (including relative imports), and resolves re-export paths (e.g. `pytra.runtime.gif -> pytra.utils.gif`) by `module_id::symbol` alias tracking.
- 2026-02-28: Fixed self-host parser handling of hex integer literals (`0x..`), resolving the `ValueError` that blocked EAST conversion of `pytra.utils.gif`.

## Breakdown

- [x] [ID: P0-EAST3-XMOD-NONESCAPE-01-S1-01] Finalize import-closure collection spec (target module range, behavior on cycles, fail-closed on unresolved).
- [x] [ID: P0-EAST3-XMOD-NONESCAPE-01-S1-02] Uniquely key function symbols by `module_id::symbol` and implement cross-module call-target resolution.
- [x] [ID: P0-EAST3-XMOD-NONESCAPE-01-S2-01] Extend `NonEscapeInterproceduralPass` to cross-module summary computation while keeping SCC fixed-point deterministic.
- [x] [ID: P0-EAST3-XMOD-NONESCAPE-01-S2-02] Update callsite `meta.non_escape_callsite` / module `meta.non_escape_summary` with cross-analysis results.
- [x] [ID: P0-EAST3-XMOD-NONESCAPE-01-S3-01] Collapse C++ emitter dependence on fixed safe-call whitelist and prioritize `non_escape_callsite` annotation for stack-list judgment.
- [x] [ID: P0-EAST3-XMOD-NONESCAPE-01-S3-02] Verify in `sample/05` that `frames` does not degrade to `object`, and reduce implicit conversion at `save_gif` calls.
- [x] [ID: P0-EAST3-XMOD-NONESCAPE-01-S4-01] Add regression tests for module-cross / unresolved-import / recursive-import cases and lock fail-closed behavior and determinism.
- [x] [ID: P0-EAST3-XMOD-NONESCAPE-01-S4-02] Run `check_py2cpp_transpile` and C++ regressions to confirm non-regression.

## S1-01 Collection spec (finalized)

- Analysis starts from one current EAST3 module. Build import closure from dependency-module candidates in `meta.import_bindings`.
- Modules in closure are those obtained by BFS over `module_id` for `binding_kind in {module,symbol,wildcard}`; expand each `module_id` only once.
- Resolve `module_id -> source_path` by prioritizing existing import-resolution results. If unresolved, do not add that module to closure (fail-closed).
- If module loading fails (missing file, parse failure, EAST3 generation failure), treat callsites targeting that module as unresolved and apply unknown-call escape policy.
- Stop circular imports with `visited(module_id)`. SCC is handled in the call-graph layer; import-closure collection does not recurse further.
- For determinism, fix queue insertion order and module processing order to ascending `module_id`.
- Standardize summary `symbol` keys to `module_id::function`, allowing same-name function collisions.
- Default policy is fail-closed. Write only functions analyzable within closure into `meta.non_escape_summary`; unresolved functions keep callsite `resolved=false`.
