# P5: C++ `py_runtime.h` residual thin seam shrink

Last updated: 2026-03-12

Related TODO:
- `ID: P5-CPP-PYRUNTIME-RESIDUAL-THIN-SEAM-SHRINK-01` in `docs/en/todo/index.md`

Background:
- `src/runtime/cpp/native/core/py_runtime.h` has already been reduced significantly, and the typed collection compatibility plus generic `type_id` compatibility buckets are now empty in the header-surface inventory.
- However, the current header still keeps the object-bridge mutation seam `py_append(object& ...)` and the shared `type_id` thin seam (`py_runtime_value_type_id`, `py_runtime_value_isinstance`, `py_runtime_object_type_id`, `py_runtime_object_isinstance`, `py_runtime_type_id_is_subtype`, `py_runtime_type_id_issubclass`).
- These are not removable through header cleanup alone; they require an explicit decision about how the C++ / Rust / C# emitters and runtimes will reduce their shared contract first.
- Therefore this task is a later-stage `P5` planning task, not an immediate implementation of the final shrink itself.

Goal:
- Split the remaining `py_runtime.h` thin seams into intentional residuals and seams that can eventually move back into backend-local contracts.
- Fix the reduction order for the object-bridge mutation seam and the shared `type_id` seam so a future header-shrink task can proceed bundle by bundle.
- Document the representative C++ / Rust / C# emitter and runtime contracts and prevent silent re-expansion.

In scope:
- Inventory of the remaining thin seams in `py_runtime.h`
- C++ emitter ownership review for object-bridge and shared `type_id` callers
- Rust / C# emitter and runtime ownership review for shared `type_id` seams
- Minimization policy for `py_append(object&)` as an object-only seam
- Handoff docs / tooling / regressions for final thin-seam removal

Out of scope:
- Actually deleting those seams from `py_runtime.h` in this task
- Full redesign of nominal ADT or type-predicate contracts
- Large ABI redesigns for the Rust/C# runtimes
- New collection support such as `deque`

Acceptance criteria:
- The remaining seams in `py_runtime.h` are classified into object-bridge mutation and shared `type_id` thin seams, and their reduction order is fixed in docs/tooling.
- Residual callers in the C++ / Rust / C# emitters are organized by bucket.
- The blockers and handoff criteria for the eventual final shrink are documented.
- `python3 tools/check_todo_priority.py` and `git diff --check` pass.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_cpp_pyruntime_header_surface.py`
- `python3 tools/check_cpp_pyruntime_contract_inventory.py`
- `python3 tools/check_crossruntime_pyruntime_emitter_inventory.py`
- `python3 tools/check_cpp_pyruntime_residual_thin_seam_contract.py`
- `python3 tools/check_cpp_pyruntime_residual_thin_seam_handoff_contract.py`
- `git diff --check`

Decision log:
- 2026-03-12: Immediate `py_runtime.h` cleanup is largely complete, so the remaining work depends on cross-runtime contract cleanup and is placed at `P5`.
- 2026-03-12: The representative residual baseline is `py_append(object&)` plus the shared `type_id` thin seams, while the typed compatibility bucket is already empty.
- 2026-03-12: Future shrink order will treat the object-bridge mutation seam and the shared `type_id` seam separately, reducing C++ / Rust / C# emitter+runtime contracts bundle by bundle.
- 2026-03-12: The follow-up and handoff references inside `check_cpp_pyruntime_header_surface.py` and `check_crossruntime_pyruntime_emitter_inventory.py` are pinned to the active `P5-CPP-PYRUNTIME-RESIDUAL-THIN-SEAM-SHRINK-01` task instead of archived `P0/P4` tasks, so this task itself guards the current residual baseline.
- 2026-03-12: In the source-wide contract inventory, only the C# bytearray compat seam (`py_append/py_pop`) plus the `gif/png` utility runtime remain in `object_bridge_required`, while the shared runtime contract keeps only the `type_id` thin seam and the native compiler `py_runtime_object_isinstance` bridge.
- 2026-03-12: The shared `type_id` thin seam classification is fixed by the `P5-...-S2-02` guard in `check_crossruntime_pyruntime_emitter_inventory.py`; C++ keeps only `py_runtime_value_type_id` as future-reducible, while Rust/C# treat all remaining residual callers as must-remain-until-runtime-task.
- 2026-03-12: Final handoff criteria are centralized in `check_cpp_pyruntime_residual_thin_seam_handoff_contract.py`, which pins the bundle order plus the header-surface, source-wide contract, and crossruntime emitter guards as the archive preconditions for this `P5` task.

## Breakdown

- [x] [ID: P5-CPP-PYRUNTIME-RESIDUAL-THIN-SEAM-SHRINK-01-S1-01] Lock the current header surface and cross-runtime residual caller baseline in docs, tooling, and inventory.
- [x] [ID: P5-CPP-PYRUNTIME-RESIDUAL-THIN-SEAM-SHRINK-01-S2-01] Classify ownership for the object-bridge mutation seam and identify lanes that can move back to backend-local lowering.
- [x] [ID: P5-CPP-PYRUNTIME-RESIDUAL-THIN-SEAM-SHRINK-01-S2-02] Classify the shared `type_id` thin seam contracts across C++ / Rust / C# and separate must-remain from future-reducible callers.
- [x] [ID: P5-CPP-PYRUNTIME-RESIDUAL-THIN-SEAM-SHRINK-01-S3-01] Sync final-shrink handoff criteria, bundle order, and representative regressions into docs, tooling, and archive flow.
