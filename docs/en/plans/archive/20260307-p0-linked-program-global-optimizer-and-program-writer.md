<a href="../../../ja/plans/archive/20260307-p0-linked-program-global-optimizer-and-program-writer.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Linked-Program Global Optimizer and ProgramWriter

Last updated: 2026-03-07

Related TODO:
- `docs/ja/todo/index.md` `ID: P0-LINKED-PROGRAM-OPT-01`

Summary:
- Introduce a real linked-program unit that accepts multiple translation units instead of pretending that whole-program optimization can be performed from a single `Module`.
- Separate three responsibilities cleanly:
  - local `EAST3` optimization
  - whole-program / linked-program optimization
  - target-specific program writing and layout

Why this was needed:
- The previous `NonEscapeInterproceduralPass` was still rooted in a single input module and was only approximating cross-module reasoning.
- C++ multi-file output already had logic outside the emitter, but that logic was still backend-local instead of a shared `ProgramWriter` contract.
- To make `rc<>` ownership, `type_id`, cross-module summaries, and linked restart deterministic, Pytra needed a proper linked-program stage.

Target pipeline:

```text
Source(.py)
  -> EAST1
  -> EAST2
  -> EAST3 Module (per translation unit)
  -> LinkedProgramLoader
  -> LinkedProgramOptimizer / Linker
  -> BackendLower/Optimize (per module)
  -> ModuleEmitter
  -> ProgramWriter
```

Key design rules:
- Global correctness decisions belong to the linked-program optimizer, not to local `EAST3` passes.
- `ModuleEmitter` emits one module and may read global summaries, but must not recompute them.
- `ProgramWriter` owns layout, manifests, runtime copy, and packaging, but not language semantics.
- Single-file targets still conceptually have a `ProgramWriter`; theirs can be trivial.

Input direction:
- Introduce a `link-input.json` manifest that lists:
  - schema version
  - target
  - dispatch mode
  - entry modules
  - module paths
  - global options

Output direction:
- Do not collapse everything into one mega-IR.
- Emit:
  - `link-output.json`
  - optimized linked `EAST3` per module
  - program-wide summaries such as:
    - `type_id_table`
    - call graph / SCC
    - non-escape summary
    - container ownership hints

Implementation plan:
- Phase 1: define loader / manifest schema / validator
- Phase 2: add program-wide call graph and global summary materialization
- Phase 3: make `py2x` build in-memory linked programs
- Phase 4: add restart flow via `eastlink` / `ir2lang`
- Phase 5: remove import-closure fallback from the old single-module optimizer path
- Phase 6: extract C++ multi-file layout into an explicit `ProgramWriter`
- Phase 7: wire `pytra-cli` and manifest-driven build flow to the new route
- Phase 8: harden schema / determinism / regression tests

Acceptance:
- linked input / output schemas are fixed and validated
- the C++ multi-file route is driven by linked output and `ProgramWriter`
- `pytra-cli` can build and restart through the linked-program path
- old import-closure fallback is removed from the local optimizer path

Decision log:
- 2026-03-07: whole-program ownership and non-escape cannot be treated as “global optimization” if the optimizer still starts from a single `Module`. A linked-program input unit is required.
- 2026-03-07: `ProgramWriter` was separated from `ModuleEmitter` so that multi-file output stops bloating language emitters.
- 2026-03-07: linked-program output remains per-module `EAST3` plus a global manifest instead of becoming one monolithic IR file.
