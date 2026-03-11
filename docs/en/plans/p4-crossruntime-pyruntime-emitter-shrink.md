# P4 Crossruntime PyRuntime Emitter Shrink

Last updated: 2026-03-12

Purpose:
- Prepare the next `py_runtime.h` shrink by cleaning up the remaining emitter-side `py_runtime` dependencies in C++, Rust, and C#.
- Make the split between typed lanes and object-bridge lanes explicit in emitters so more surface can be removed from the C++ header.
- Align the cross-runtime `type_id` / `isinstance` / `issubclass` contract onto thin seams and narrow the reasons shared contract surface still remains.

Background:
- [py_runtime.h](/workspace/Pytra/src/runtime/cpp/native/core/py_runtime.h) has already been reduced to 1310 lines, but it still carries `object_bridge_compat` and `shared_type_id_contract` seams.
- The C++ emitter has already upstreamed most typed-lane behavior, but object fallbacks and compatibility seams still remain.
- The Rust and C# emitters also still lower some `isinstance` / `issubclass` / mutation paths against the current C++ runtime contract, so the header cannot be safely reduced in isolation.
- This is not a header-only cleanup task. It is a cross-runtime emitter contract realignment, so it is tracked separately as a later `P4`.

Out of scope:
- Immediate deletion or large rewrites inside `py_runtime.h`.
- Full runtime rewrites for Rust or C#.
- Introducing a new object system or ADT model.

Acceptance criteria:
- The C++ / Rust / C# emitter dependencies relevant to `py_runtime.h` shrink are inventoried in the plan.
- Helpers that can leave typed lanes are clearly separated from helpers that intentionally remain object-bridge-only.
- Lowering contracts for `isinstance` / `issubclass` / `type_id` are split into cross-runtime thin seams and backend-specific residuals.
- Representative regression / inventory / source-guard strategy is defined.
- The `docs/en/` mirror follows the Japanese source plan.

## Child tasks

- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01-S1-01] Inventory the `py_runtime` dependencies in the C++ / Rust / C# emitters and classify them into typed lanes, object bridge, and shared type_id seams.
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01-S2-01] Re-audit the C++ emitter to separate object-bridge-only helpers from already-upstreamed typed lanes and define header-shrink regressions.
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01-S2-02] Fix the plan for Rust / C# mutation and `isinstance` / `issubclass` lowering so they target thin seams instead of the current shared contract directly.
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01-S3-01] Define representative inventory, smoke, and source-guard lanes so post-shrink contract re-entry fails closed.
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01-S4-01] Connect the removable `py_runtime.h` surface and the final residual seam to the follow-up shrink task.

## Decision log

- 2026-03-12: This task is a prerequisite for later `py_runtime.h` shrink, but it should not block current higher-priority parser/compiler work, so it is tracked as `P4`.
- 2026-03-12: The order is inventory and emitter-contract realignment first, then header shrink handoff, not header deletion first.
