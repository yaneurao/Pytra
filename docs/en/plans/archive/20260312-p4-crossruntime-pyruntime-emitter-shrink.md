<a href="../../../ja/plans/archive/20260312-p4-crossruntime-pyruntime-emitter-shrink.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

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

- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01-S1-01] Inventory the `py_runtime` dependencies in the C++ / Rust / C# emitters and classify them into typed lanes, object bridge, and shared type_id seams.
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01-S2-01] Re-audit the C++ emitter to separate object-bridge-only helpers from already-upstreamed typed lanes and define header-shrink regressions.
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01-S2-02] Fix the plan for Rust / C# mutation and `isinstance` / `issubclass` lowering so they target thin seams instead of the current shared contract directly.
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01-S3-01] Define representative inventory, smoke, and source-guard lanes so post-shrink contract re-entry fails closed.
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01-S4-01] Connect the removable `py_runtime.h` surface and the final residual seam to the follow-up shrink task.

## Current Residual Inventory (2026-03-12)

- `cpp_emitter_object_bridge_residual`
  - `py_runtime_object_type_id` @ `src/backends/cpp/emitter/cpp_emitter.py`
  - `py_runtime_object_isinstance` @ `src/backends/cpp/emitter/runtime_expr.py`
  - `py_runtime_object_isinstance` @ `src/backends/cpp/emitter/stmt.py`
  - `py_append/extend/pop/clear/reverse/sort/set_at` @ `src/backends/cpp/emitter/call.py`
- `cpp_emitter_shared_type_id_residual`
  - `py_runtime_type_id_is_subtype`
  - `py_runtime_type_id_issubclass`
  - both under `src/backends/cpp/emitter/runtime_expr.py`
- `rs_emitter_shared_type_id_residual`
  - `py_runtime_value_type_id`
  - `py_runtime_value_isinstance`
  - `py_runtime_type_id_is_subtype`
  - `py_runtime_type_id_issubclass`
  - all under `src/backends/rs/emitter/rs_emitter.py`
- `cs_emitter_shared_type_id_residual`
  - `py_runtime_value_type_id`
  - `py_runtime_value_isinstance`
  - `py_runtime_type_id_is_subtype`
  - `py_runtime_type_id_issubclass`
  - all under `src/backends/cs/emitter/cs_emitter.py`
- `crossruntime_mutation_helper_residual`
  - `py_append`
  - `py_pop`
  - both under `src/backends/cs/emitter/cs_emitter.py`

Representative guards:
- inventory source of truth: [check_crossruntime_pyruntime_emitter_inventory.py](/workspace/Pytra/tools/check_crossruntime_pyruntime_emitter_inventory.py)
- unit guard: [test_check_crossruntime_pyruntime_emitter_inventory.py](/workspace/Pytra/test/unit/tooling/test_check_crossruntime_pyruntime_emitter_inventory.py)
- representative manifest:
  - freeze `smoke_file + smoke_tests + source_guard_paths` per residual bucket inside the inventory tool.
- representative smoke:
  - C++: [test_east3_cpp_bridge.py](/workspace/Pytra/test/unit/backends/cpp/test_east3_cpp_bridge.py)
  - Rust: [test_py2rs_smoke.py](/workspace/Pytra/test/unit/backends/rs/test_py2rs_smoke.py)
  - C#: [test_py2cs_smoke.py](/workspace/Pytra/test/unit/backends/cs/test_py2cs_smoke.py)
- source guard:
  - Rust/C# thin seams and the C# bytes/bytearray residual lane are now frozen through source-guard patterns in the inventory tool.

## C++ Re-Audit Snapshot (S2-01)

- already-upstreamed typed lane:
  - `cpp_emitter.py` lowers list mutation directly to `py_list_append_mut` / `py_list_extend_mut` / `py_list_pop_mut` / `py_list_clear_mut` / `py_list_reverse_mut` / `py_list_sort_mut`.
  - `stmt.py` lowers list subscript assignment directly to `py_list_set_at_mut`.
- object-bridge-only residual:
  - `call.py` keeps `py_append` / `py_extend` / `py_pop` / `py_clear` / `py_reverse` / `py_sort` / `py_set_at` only as wrapper-name inventory for object-bridge contexts.
- representative regression:
  - tooling guard freezes the `py_list_*_mut` direct typed-lane surface in `cpp_emitter.py` / `stmt.py`.
  - tooling guard fails closed if wrapper names escape `call.py`.

## Header Shrink Handoff (S4-01)

- After emitter shrink completes, the header surface tool must keep both `typed_collection_compat` and `shared_type_id_compat` empty.
- The only remaining header bucket on the emitter side is `object_bridge_mutation`, and it is now explicitly handed off to the follow-up [20260312-p4-crossruntime-pyruntime-residual-caller-shrink.md](./20260312-p4-crossruntime-pyruntime-residual-caller-shrink.md) task.
- Handoff sources of truth:
  - header surface: [check_cpp_pyruntime_header_surface.py](/workspace/Pytra/tools/check_cpp_pyruntime_header_surface.py)
  - header unit guard: [test_check_cpp_pyruntime_header_surface.py](/workspace/Pytra/test/unit/tooling/test_check_cpp_pyruntime_header_surface.py)
  - follow-up task: `P4-CROSSRUNTIME-PYRUNTIME-RESIDUAL-CALLER-SHRINK-01`

## Decision log

- 2026-03-12: This task is a prerequisite for later `py_runtime.h` shrink, but it should not block current higher-priority parser/compiler work, so it is tracked as `P4`.
- 2026-03-12: The order is inventory and emitter-contract realignment first, then header shrink handoff, not header deletion first.
- 2026-03-12: `S1-01` is now closed by adopting the existing inventory tool as the source of truth for this follow-up task and freezing the current residuals into five buckets (`cpp_emitter_object_bridge_residual`, `cpp_emitter_shared_type_id_residual`, `rs_emitter_shared_type_id_residual`, `cs_emitter_shared_type_id_residual`, `crossruntime_mutation_helper_residual`).
- 2026-03-12: `S2-01` freezes the C++ direct typed-lane helpers (`py_list_*_mut`) separately from the object-bridge wrapper names (`py_append` family), and fails closed if wrapper symbols escape `call.py`.
- 2026-03-12: The first `S2-01` bundle locks C++ wrapper re-entry so `py_append` / `py_extend` / `py_pop` / `py_clear` / `py_reverse` / `py_sort` / `py_set_at` must not reappear in `cpp_emitter.py`, `runtime_expr.py`, or `stmt.py`, and fixes the representative split as `typed list append/set_at -> py_list_*_mut(rc_list_ref(...))` versus `pyobj Any list -> obj_to_list_ref_or_raise(..., "py_append" | "py_set_at")`.
- 2026-03-12: `S2-02` is now fixed as `Rust = thin shared type_id seam only` and `C# = the same thin seam plus intentional bytes/bytearray compat residuals for py_append / py_pop / py_get / py_slice / py_set`.
- 2026-03-12: `S3-01` is now closed by adding source-guard patterns for the Rust/C# thin seams and the C# bytes/bytearray residual lane to the inventory tool, and by fixing the representative smoke files as `test_east3_cpp_bridge.py`, `test_py2rs_smoke.py`, and `test_py2cs_smoke.py`.
- 2026-03-12: The second `S3-01` bundle freezes a representative manifest (`smoke_file + smoke_tests + source_guard_paths`) per residual bucket so test-name drift for the C++ object bridge, C++ shared type_id, Rust thin seam, C# thin seam, and C# bytes compat residual now fails closed in the inventory tool.
- 2026-03-12: `S4-01` fixes the header-surface handoff as `typed_collection_compat = empty`, `shared_type_id_compat = empty`, and `object_bridge_mutation = follow-up residual caller owned`, then hands that residual bucket to `P4-CROSSRUNTIME-PYRUNTIME-RESIDUAL-CALLER-SHRINK-01`.
- 2026-03-12: The second `S3-01` bundle freezes a representative manifest (`smoke_file + smoke_tests + source_guard_paths`) per residual bucket so test-name drift for the C++ object bridge, C++ shared type_id, Rust thin seam, C# thin seam, and C# bytes compat residual now fails closed in the inventory tool.
