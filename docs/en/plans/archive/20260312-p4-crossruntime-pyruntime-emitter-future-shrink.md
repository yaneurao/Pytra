# P4 Crossruntime PyRuntime Emitter Future Shrink

Last updated: 2026-03-12

Purpose:
- Define the remaining C++ / Rust / C# emitter follow-up needed before `py_runtime.h` can shrink further or the thin seams can move elsewhere.
- Treat the archived `P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01` / `...-RESIDUAL-REDUCTION-01` result as the current baseline and make the next low-priority follow-up visible again.
- Fix the bundle order for reducing the remaining `shared type_id thin seam` and the C# `bytearray` compatibility seam before a future header-shrink or runtime SoT task.

Background:
- The earlier emitter-shrink P4 tasks are already archived, and the current residual inventory is now fixed in [check_crossruntime_pyruntime_emitter_inventory.py](/workspace/Pytra/tools/check_crossruntime_pyruntime_emitter_inventory.py).
- The current residuals are intentional seams rather than unclassified debt, but further `py_runtime.h` shrink will still require emitter-side follow-up across C++ / Rust / C#.
- In particular, the C++ emitter still uses `py_runtime_value_*` / `py_runtime_type_id_is_*`, Rust/C# still carry the shared thin helper contract, and C# still keeps a `bytearray` mutation compatibility seam.
- This is not an immediate blocker, so it belongs in low-priority `P4`.

Out of scope:
- Fully shrinking `py_runtime.h` in this task.
- Rewriting the Rust / C# runtime builtins wholesale.
- Introducing a new object system or type-id model.

Acceptance criteria:
- The current emitter residual baseline and future bundle order are fixed in the live TODO / plan / inventory tool.
- The remaining seams across C++ / Rust / C# are classified in terms of `future_reducible` vs `must_remain_until_runtime_task`.
- Representative smoke / source guard / inventory drift guards cover the future-shrink baseline.
- The handoff condition to a later `py_runtime.h` shrink or runtime SoT task is written down.
- The English mirror stays in sync with the Japanese source of truth.

## Child Tasks

- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-FUTURE-SHRINK-01-S1-01] Lock the future-shrink follow-up baseline and bundle order into the live plan / TODO / inventory tool.
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-FUTURE-SHRINK-01-S2-01] Re-audit the C++ emitter shared type-id thin seam and classify reducible callers vs must-remain seam.
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-FUTURE-SHRINK-01-S2-02] Re-audit the Rust / C# shared thin helper seam and the C# bytearray compatibility seam, then lock the future reduction order.
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-FUTURE-SHRINK-01-S3-01] Refresh representative smoke / source guard / inventory drift guard for the future-shrink baseline.
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-FUTURE-SHRINK-01-S4-01] Connect the future emitter shrink handoff to the next header-shrink / runtime-SoT task.

## Current Baseline

- `cpp_emitter_shared_type_id_residual`
  - `py_runtime_value_type_id`
  - `py_runtime_value_isinstance`
  - `py_runtime_type_id_is_subtype`
  - `py_runtime_type_id_issubclass`
  - source guard paths:
    - `src/backends/cpp/emitter/cpp_emitter.py`
    - `src/backends/cpp/emitter/runtime_expr.py`
    - `src/backends/cpp/emitter/stmt.py`
- `rs_emitter_shared_type_id_residual`
  - the same 4 helper names
  - source guard path:
    - `src/backends/rs/emitter/rs_emitter.py`
- `cs_emitter_shared_type_id_residual`
  - the same 4 helper names
  - source guard path:
    - `src/backends/cs/emitter/cs_emitter.py`
- `crossruntime_mutation_helper_residual`
  - `py_append`
  - `py_pop`
  - source guard path:
    - `src/backends/cs/emitter/cs_emitter.py`
  - current interpretation:
    - `bytearray` compatibility seam only

## Future Representative Guard Baseline

- `cpp_emitter_shared_type_id_residual`
  - smoke: `test/unit/backends/cpp/test_east3_cpp_bridge.py`
  - representative tests:
    - `test_render_expr_supports_east3_obj_boundary_nodes`
    - `test_transpile_representative_nominal_adt_match_emits_if_else_chain`
  - source guard paths:
    - `src/backends/cpp/emitter/cpp_emitter.py`
    - `src/backends/cpp/emitter/runtime_expr.py`
    - `src/backends/cpp/emitter/stmt.py`
- `rs_emitter_shared_type_id_residual`
  - smoke: `test/unit/backends/rs/test_py2rs_smoke.py`
  - representative tests:
    - `test_type_predicate_nodes_are_lowered_without_legacy_bridge`
  - source guard path:
    - `src/backends/rs/emitter/rs_emitter.py`
- `cs_emitter_shared_type_id_residual`
  - smoke: `test/unit/backends/cs/test_py2cs_smoke.py`
  - representative tests:
    - `test_type_predicate_nodes_are_lowered_without_legacy_bridge`
  - source guard path:
    - `src/backends/cs/emitter/cs_emitter.py`
- `crossruntime_mutation_helper_residual`
  - smoke: `test/unit/backends/cs/test_py2cs_smoke.py`
  - representative tests:
    - `test_bytearray_mutation_stays_on_runtime_helpers_but_list_append_does_not`
    - `test_bytearray_index_and_slice_compat_helpers_stay_explicit`
  - source guard path:
    - `src/backends/cs/emitter/cs_emitter.py`
- inventory drift guard:
  - the future representative subset is fixed by `FUTURE_REPRESENTATIVE_LANE_MANIFEST` and `FUTURE_SOURCE_GUARD_PATHS` in `check_crossruntime_pyruntime_emitter_inventory.py`.

## Future Reduction Order

1. `cpp_emitter_shared_type_id_residual`
2. `rs_emitter_shared_type_id_residual`
3. `cs_emitter_shared_type_id_residual`
4. `crossruntime_mutation_helper_residual`

## C++ Shared Type ID Classification

- `future_reducible`
  - `py_runtime_value_type_id` in `src/backends/cpp/emitter/cpp_emitter.py`
  - Interpretation:
    - value type-id lookups can still move into emitter-local metadata or lowered helpers and are independent from the nominal ADT match / type-predicate shared seam.
- `must_remain_until_runtime_task`
  - `py_runtime_value_isinstance` in `src/backends/cpp/emitter/runtime_expr.py`
  - `py_runtime_value_isinstance` in `src/backends/cpp/emitter/stmt.py`
  - `py_runtime_type_id_is_subtype` in `src/backends/cpp/emitter/runtime_expr.py`
  - `py_runtime_type_id_issubclass` in `src/backends/cpp/emitter/runtime_expr.py`
  - Interpretation:
    - these are the representative thin seam for nominal ADT match and type-predicate lowering, so they stay intentional residuals until the runtime / type-id ownership task moves first.

## Rust / C# Shared Type ID Classification

- `future_reducible`
  - none
- `must_remain_until_runtime_task`
  - Rust:
    - `py_runtime_value_type_id`
    - `py_runtime_value_isinstance`
    - `py_runtime_type_id_is_subtype`
    - `py_runtime_type_id_issubclass`
  - C#:
    - `py_runtime_value_type_id`
    - `py_runtime_value_isinstance`
    - `py_runtime_type_id_is_subtype`
    - `py_runtime_type_id_issubclass`
  - Interpretation:
    - In both backends the shared thin helper is itself the runtime contract, so a runtime / type-id ownership task must move first before the seam can move backend-local.

## C# Bytearray Compatibility Classification

- `future_reducible`
  - `py_append` in `src/backends/cs/emitter/cs_emitter.py`
  - `py_pop` in `src/backends/cs/emitter/cs_emitter.py`
  - Interpretation:
    - This seam is limited to `bytearray` compatibility and can eventually move back into backend-local helpers without changing the shared type-id contract.
- `must_remain_until_runtime_task`
  - none

## Handoff Condition

- The C++ emitter must not reintroduce generic or object-type-id aliases beyond the current thin helper seam.
- The Rust / C# emitters must not grow the shared thin helper surface.
- The C# `bytearray` compatibility seam must not expand back to list / bytes mutation.
- Once those remain fixed in the inventory tool, this task hands off to a later header-shrink / runtime-externalization task.

## Handoff Targets

- `cpp_header_shrink`
  - target plan:
    - `docs/ja/plans/archive/20260312-p0-cpp-pyruntime-final-shrink.md`
  - trigger bucket:
    - `cpp_emitter_shared_type_id_residual`
  - handoff condition:
    - the `future_reducible` subset stays limited to `py_runtime_value_type_id`, and representative/source-guard drift stays empty.
- `runtime_sot_followup`
  - target plan:
    - `docs/ja/plans/p2-runtime-sot-linked-program-integration.md`
  - trigger bucket:
    - `rs_emitter_shared_type_id_residual`
  - handoff condition:
    - the shared `type_id` seam stays must-remain-only until runtime/type-id ownership moves into a runtime SoT task.
- `cs_bytearray_localization`
  - target plan:
    - `docs/ja/plans/archive/20260312-p4-crossruntime-pyruntime-residual-caller-shrink.md`
  - trigger bucket:
    - `crossruntime_mutation_helper_residual`
  - handoff condition:
    - the C# `bytearray` compatibility seam remains isolated to `py_append` / `py_pop` and does not expand back to list or bytes mutation.

## Decision Log

- 2026-03-12: The archived `P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01` / `...-RESIDUAL-REDUCTION-01` tasks already completed the current residual cleanup, so this follow-up is limited to future reduction only.
- 2026-03-12: `S1-01` fixes the current residual inventory as the baseline and sets the future reduction order to `C++ shared type_id -> Rust shared type_id -> C# shared type_id -> C# bytearray compat`.
- 2026-03-12: `S2-01` splits the C++ shared type-id residual into `future_reducible=py_runtime_value_type_id only` and `must_remain_until_runtime_task=nominal ADT match / type-predicate seam`, and the inventory tool now guards the same classification.
- 2026-03-12: `S2-02` fixes Rust/C# shared thin seams as `must_remain_until_runtime_task` and classifies the C# `bytearray` compatibility seam (`py_append` / `py_pop`) as `future_reducible`, with the inventory tool guarding the same split.
- 2026-03-12: `S3-01` fixes the representative smoke / source guard subset the future follow-up actually depends on via `FUTURE_REPRESENTATIVE_LANE_MANIFEST` and `FUTURE_SOURCE_GUARD_PATHS`, so drift is checked against the future baseline rather than only the full current inventory.
- 2026-03-12: `S4-01` fixes the handoff targets as `cpp_header_shrink` / `runtime_sot_followup` / `cs_bytearray_localization`, and the inventory tool now guards the target plan path, trigger bucket, and handoff condition for each.
