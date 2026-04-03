# P3-COPY-ELISION: Add copy elision metadata to EAST3 / linker

Last updated: 2026-04-02

## Background

In the Lua GIF sample (`07_game_of_life_loop`), copying with `bytes(bytearray)` has become a hot path. The Lua contributor attempted an optimization that eliminates the copy in `__pytra_bytes(table)` and returns `v` directly, but this violates the semantics of Python's `bytes(bytearray)`, which creates a copy.

If an emitter elides a copy on its own judgment, the `bytes` object would change if the original `bytearray` is modified afterward, corrupting the output. Optimizations are only legal when based on information from EAST / linker.

## Required information

Conditions under which copy elision is safe:
1. The copy source (`bytearray`) is not mutated after the copy (non-mutate after copy)
2. The copy result (`bytes`) is used only in a read-only manner (`borrow_kind: readonly_ref`)

These cannot be determined from single-module `borrow_kind` alone (see spec-east.md §5); whole-program analysis is required.

## Existing framework

Existing metadata in EAST3 / linker that is relevant:
- `borrow_kind`: `value | readonly_ref | mutable_ref` (spec-east.md §5)
- `meta.linked_program_v1.non_escape_summary`: non-escape analysis at the linker stage
- `meta.linked_program_v1.container_ownership_hints_v1`: container ownership hints

These will be extended to carry the copy elision determination.

## Approach

1. Extend the linker's non-escape / def-use analysis to determine whether "the copy source is not mutated after the copy"
2. Attach the determination result as `meta.copy_elision_safe_v1` on the Call node
3. Emitters may elide a copy only when `copy_elision_safe_v1` is present
4. If `copy_elision_safe_v1` is absent, generate the copy (fail-closed)

## Target

- `src/toolchain2/link/` — Extend linker analysis
- `docs/ja/spec/spec-east.md` — Define the `copy_elision_safe_v1` schema
- `src/toolchain2/emit/lua/` — Add copy elision support (first consumer)
- All emitters — In the future, the same metadata can be referenced for optimization

## Out of scope

- Copy elision based on the emitter's own judgment (prohibited; EAST metadata is the source of truth)
- Introducing `borrow_kind=move` (a candidate for future extension but out of scope for this task)

## Subtasks

1. [ ] [ID: P3-COPY-ELISION-S1] Formalize the conditions under which `bytes(bytearray)` copy elision is safe, and define the `copy_elision_safe_v1` schema in spec-east.md
2. [ ] [ID: P3-COPY-ELISION-S2] Implement copy elision determination in the linker's def-use / non-escape analysis
3. [ ] [ID: P3-COPY-ELISION-S3] Implement copy elision in the Lua emitter using `copy_elision_safe_v1`
4. [ ] [ID: P3-COPY-ELISION-S4] Confirm that `07_game_of_life_loop` Lua parity PASSes and performance improves

## Decision Log

- 2026-04-02: The Lua contributor performed `__pytra_bytes` copy elision based on their own emitter judgment → rolled back as a semantics violation. Filed as a path that attaches metadata to EAST / linker.
- 2026-04-02: Added `Call.meta.copy_elision_safe_v1` to `docs/ja/spec/spec-east.md`. v1 is dedicated to `bytes(bytearray)`; backends may optimize to an alias / borrow only when the linker has attached the metadata.
- 2026-04-02: Implemented a narrow/fail-closed v1 analysis in the linker. Currently annotates only cases where `return bytes(local_bytearray)` flows into a readonly `list[bytes]` within the same module.
- 2026-04-02: Implemented `copy_elision_safe_v1` support in the Lua emitter/runtime. `03_julia_set` passes with no regression. `07_game_of_life_loop` improved but still times out at `--cmd-timeout-sec 600`.
