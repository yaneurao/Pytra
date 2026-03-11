# P4 Crossruntime PyRuntime Residual Caller Shrink

Last updated: 2026-03-12

Purpose:
- Prepare the next `py_runtime.h` shrink by cleaning up the remaining non-emitter `py_runtime` callers.
- Inventory the residual callers in native compiler wrappers, generated C++ runtime code, and Rust/C# runtime builtins, then narrow the reasons `object_bridge_compat` and `shared_type_id_contract` still remain.
- Separate the residual caller seams that must survive until the final header shrink from the seams that should be moved onto thin helpers first.

Background:
- The existing [p4-crossruntime-pyruntime-emitter-shrink.md](./p4-crossruntime-pyruntime-emitter-shrink.md) covers C++ / Rust / C# emitter dependencies, but emitter cleanup alone does not remove the residual callers that still keep `py_runtime.h` large.
- The remaining callers are concentrated in native compiler wrappers (`transpile_cli.cpp`, `backend_registry_static.cpp`), generated C++ runtime modules (`type_id.cpp`, `json.cpp`, `iter_ops.cpp`, and related files), and Rust/C# runtime builtins.
- Even after emitter-side cleanup, these callers would still force `py_runtime.h` to keep `object_bridge_compat` and `shared_type_id_contract` surface, so they need a separate caller-side inventory and handoff.
- This is not the final header deletion step. It is a cross-runtime residual caller contract cleanup, so it is tracked as a later `P4`.

Out of scope:
- Immediate deletion or large rewrites inside `py_runtime.h`.
- Re-doing the emitter-side residual dependency cleanup.
- Introducing a new runtime object model or type system.

Acceptance criteria:
- Residual `py_runtime.h` callers in native compiler wrappers, generated C++ runtime code, and Rust/C# runtime builtins are inventoried in the plan.
- The residual callers are classified into `object_bridge_compat` and `shared_type_id_contract`, with a clear handoff for which ones should move onto thin helpers first.
- Representative source-guard / inventory / smoke lanes are defined so caller re-entry fails closed.
- The residual seam needed for the later header shrink handoff is explicitly documented.
- The English mirror stays aligned with the Japanese source plan.

## Child tasks

- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-RESIDUAL-CALLER-SHRINK-01-S1-01] Inventory residual `py_runtime` callers in native compiler wrappers, generated C++ runtime code, and Rust/C# runtime builtins, then classify them into `object_bridge_compat` and `shared_type_id_contract`.
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-RESIDUAL-CALLER-SHRINK-01-S2-01] Move native compiler-wrapper `type_id` / object-bridge callers toward thin helper seams and define representative regressions.
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-RESIDUAL-CALLER-SHRINK-01-S2-02] Re-classify residual callers in the generated C++ runtime and separate callers that must remain from callers that can be re-delegated before header shrink.
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-RESIDUAL-CALLER-SHRINK-01-S2-03] Inventory Rust/C# runtime builtin dependencies on the shared seams and define the final cross-runtime residual contract shape.
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-RESIDUAL-CALLER-SHRINK-01-S3-01] Add residual-caller inventory tooling, source guards, and smoke coverage, then connect the final residual seam to the later header-shrink handoff.

## Emitter Handoff Snapshot

- The preceding [20260312-p4-crossruntime-pyruntime-emitter-shrink.md](./archive/20260312-p4-crossruntime-pyruntime-emitter-shrink.md) task already reduced the emitter-driven `typed_collection_compat` and `shared_type_id_compat` buckets to empty.
- The only header residual bucket handed to this task is `object_bridge_mutation`, and the header surface source of truth remains [check_cpp_pyruntime_header_surface.py](/workspace/Pytra/tools/check_cpp_pyruntime_header_surface.py).
- This task therefore focuses on non-emitter callers that still keep `object_bridge_mutation` alive, while the preceding emitter inventory tool keeps watching for emitter-side re-entry.

## Decision log

- 2026-03-12: Emitter-side cleanup alone is not enough to reduce the remaining `py_runtime.h` surface, so a separate `P4` was added for native/generated/runtime-builtin callers.
- 2026-03-12: This task is a residual caller inventory and thin-seam cleanup step, not the final header deletion step, so it remains a `P4`.
- 2026-03-12: The emitter-shrink handoff is fixed as `typed_collection_compat = empty`, `shared_type_id_compat = empty`, and `object_bridge_mutation = residual caller owned`, so this task now owns the last non-emitter header blocker.
