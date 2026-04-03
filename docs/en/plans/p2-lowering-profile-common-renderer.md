<a href="../../en/plans/p2-lowering-profile-common-renderer.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P2-LOWERING-PROFILE: Lowering profile + CommonRenderer introduction

Last updated: 2026-03-28
Status: In progress

## Background

Currently each language emitter implements the full EAST3 node traversal logic independently, yet the vast majority is structurally identical (If/While/BinOp/Call/Return, etc.). The differences between languages are mainly syntax tokens and a few structural variations.

Additionally, because EAST3 lowering produces a single shape (e.g., expanding tuple unpack into Subscript), problems arise for languages like Go that have no tuple type. Lowering that adapts to each language's capabilities is needed.

## Design

### Lowering profile

Each language declares its capabilities in the CodeEmitter profile JSON. EAST3 lowering reads this and generates a shape appropriate for the language.

Key profile items:
- `tuple_unpack_style`: subscript / structured_binding / pattern_match / multi_return / individual_temps
- `container_covariance`: true / false
- `closure_style`: native_nested / closure_syntax
- `with_style`: raii / try_with_resources / using / defer / try_finally
- `property_style`: field_access / method_call
- `swap_style`: std_swap / multi_assign / mem_swap / temp_var

### CommonRenderer

A shared base class for EAST3 node traversal. It generates code by consulting the profile's syntax tables (type_map, operator_map, syntax). Each language emitter inherits from CommonRenderer and overrides only the language-specific nodes (FunctionDef, ClassDef, For, etc.).

See spec-language-profile.md §7–§8 for details.

## Subtasks

1. [ID: P2-LOWERING-PROFILE-S1] Finalize the lowering profile schema and create profile JSON for C++ and Go
2. [ID: P2-LOWERING-PROFILE-S2] Make EAST3 lowering read the lowering profile and expand tuple unpack according to `tuple_unpack_style`
3. [ID: P2-LOWERING-PROFILE-S3] Reflect `container_covariance` / `with_style` / `property_style` in lowering
4. [ID: P2-LOWERING-PROFILE-S4] Implement the CommonRenderer base class (shared node traversal for If/While/BinOp/Call/Return/Assign, etc.)
5. [ID: P2-LOWERING-PROFILE-S5] Migrate the C++ emitter to the CommonRenderer + override structure
6. [ID: P2-LOWERING-PROFILE-S6] Migrate the Go emitter to the CommonRenderer + override structure
7. [ID: P2-LOWERING-PROFILE-S7] Confirm that parity is maintained for all existing fixture + sample across all languages

## Progress notes

- 2026-03-28: [ID: P2-LOWERING-PROFILE-S1] Unified the canonical profile location to `src/toolchain2/emit/profiles/`, added `toolchain2.emit.common.profile_loader` referencing `core.json`, `cpp.json`, `go.json`, and focused unit tests. Fixed schema validation and core merge for `tuple_unpack_style` / `container_covariance` / `closure_style` / `with_style` / `property_style` / `swap_style`.
- 2026-03-28: [ID: P2-LOWERING-PROFILE-S2] Made `lower_east2_to_east3(..., target_language=...)` read the lowering profile and branch tuple unpack to `core=individual_temps`, `cpp=TupleUnpack`, `go=MultiAssign`. Also made the Go emitter minimally consume `multi_return[...]` function signatures / return / multi-assign, and fixed the per-target EAST3 and emit in focused unit tests.
- 2026-03-28: [ID: P2-LOWERING-PROFILE-S3] Reflected `container_covariance` / `with_style` / `property_style` in lowering. With `container_covariance=false`, generates `CovariantCopy`; with `with_style=try_finally`, lowers `With` to bind + `Try(finally close)`; with `property_style=field_access`, normalizes `attribute_access_kind="property_getter"` to field access. Added minimal `CovariantCopy` consumption to the C++ / Go emitters and fixed in focused unit tests.
- 2026-03-28: [ID: P3-COMMON-RENDERER-S1] Added `toolchain2.emit.common.common_renderer.CommonRenderer`, implementing shared expr/stmt walk reading `operators` / `syntax` / `lowering` from the profile JSON. `Constant/Name/BinOp/UnaryOp/Compare/BoolOp/Expr/Return/If/While` are handled in the base; `Call/Attribute/Assign` remain as hooks. Fixed C++ / Go profile syntax differences in dummy renderer unit tests.
- 2026-03-28: [ID: P3-COMMON-RENDERER-S4] On the C++ side, restored `If/While` condition hooks and `BinOp/UnaryOp/Compare/BoolOp` expr overrides via CommonRenderer while preserving C++-specific truthiness / numeric promotion / runtime call resolution. Regenerated runtime EAST for `pytra.utils.png/gif` via the toolchain2 path, removed `pytra.utils.` from `mapping.json` `skip_modules`, and fixed `png.write_rgb_png` to resolve to a native runtime symbol. Confirmed C++ parity pass for focused unit tests and sample parity for `01_mandelbrot`, `02_raytrace_spheres`, `13_maze_generation_steps`, `14_raymarching_light_cycle`.

## Acceptance Criteria

1. C++ / Go lowering profiles are declared in JSON.
2. Tuple unpack is lowered according to the language profile (Go: multi_return / individual_temps).
3. CommonRenderer handles shared nodes and C++ / Go emitters consist only of overrides.
4. Parity is maintained for existing fixture + sample.

## Decision Log

- 2026-03-28: Triggered by the tuple unpack problem in the Go emitter, discussed the design of language capability declarations (lowering profile) and a shared renderer. Added to spec-language-profile.md §7–§8.
