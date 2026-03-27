<a href="../../../ja/plans/archive/20260312-p4-crossruntime-pyruntime-emitter-residual-reduction.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P4 Crossruntime PyRuntime Emitter Residual Reduction

Last updated: 2026-03-12

Purpose:
- Reduce the remaining emitter-side residual contracts in the C++ / Rust / C# emitters before shrinking `py_runtime.h` further.
- Restore the archived inventory as a live task and freeze the next buckets and order in the source of truth.
- Reclassify which callers can return to typed lanes and which seams intentionally remain before the final header shrink.

Background:
- The archived plan already fixed the residual inventory and representative guards needed before `py_runtime.h` shrink, but there is no live task that says which bucket is next.
- The current inventory tool already tracks residual buckets, reduction order, and representative smoke lanes, but it does not carry active bundle metadata.
- Because the work requires C++ / Rust / C# emitter changes, the shrink order cannot be driven from the header surface alone.

Out of scope:
- Immediate large-scale deletion inside `py_runtime.h`.
- Full runtime rewrites for Rust or C#.
- A new object model or a redesigned type_id system.

Acceptance criteria:
- The live TODO shows the current residual bundles and reduction order.
- The inventory tool fails closed on the current residual buckets and active bundle metadata.
- The reduction bundles can progress in this order: `crossruntime_mutation_helper_residual`, `cpp_emitter_object_bridge_residual`, `rs_emitter_shared_type_id_residual`, `cs_emitter_shared_type_id_residual`, `cpp_emitter_shared_type_id_residual`.
- The `docs/en/` mirror carries the same bundle order and acceptance criteria as the Japanese source.

## Child tasks

- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-RESIDUAL-REDUCTION-01-S1-01] Restore the current residual buckets, reduction order, and active bundle metadata into the live plan / TODO / inventory tool.
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-RESIDUAL-REDUCTION-01-S2-01] Reduce `crossruntime_mutation_helper_residual` until only the must-remain C# bytearray seam is left.
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-RESIDUAL-REDUCTION-01-S2-02] Reduce `cpp_emitter_object_bridge_residual` and move removable callers back into typed lanes.
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-RESIDUAL-REDUCTION-01-S3-01] Reduce the Rust / C# shared type_id residuals around thin seams.
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-RESIDUAL-REDUCTION-01-S3-02] Re-audit the final C++ shared type_id residual until only the intentional contract remains.

## Current residual buckets

- `crossruntime_mutation_helper_residual`
  - goal: shrink it to the C# bytearray must-remain seam only
- `cpp_emitter_object_bridge_residual`
  - goal: return removable callers to typed lanes and leave only the minimal object-bridge wrapper seam
- `rs_emitter_shared_type_id_residual`
  - goal: shrink the Rust shared type-id seam to thin helpers only
- `cs_emitter_shared_type_id_residual`
  - goal: shrink the C# shared type-id seam to thin helpers only
- `cpp_emitter_shared_type_id_residual`
  - goal: re-evaluate the final intentional C++ shared type-id contract

## Reduction order

1. `crossruntime_mutation_helper_residual`
2. `cpp_emitter_object_bridge_residual`
3. `rs_emitter_shared_type_id_residual`
4. `cs_emitter_shared_type_id_residual`
5. `cpp_emitter_shared_type_id_residual`

## Representative guard

- inventory source of truth: [check_crossruntime_pyruntime_emitter_inventory.py](/workspace/Pytra/tools/check_crossruntime_pyruntime_emitter_inventory.py)
- unit guard: [test_check_crossruntime_pyruntime_emitter_inventory.py](/workspace/Pytra/test/unit/tooling/test_check_crossruntime_pyruntime_emitter_inventory.py)
- representative smoke:
  - C++: [test_east3_cpp_bridge.py](/workspace/Pytra/test/unit/backends/cpp/test_east3_cpp_bridge.py)
  - Rust: [test_py2rs_smoke.py](/workspace/Pytra/test/unit/backends/rs/test_py2rs_smoke.py)
  - C#: [test_py2cs_smoke.py](/workspace/Pytra/test/unit/backends/cs/test_py2cs_smoke.py)

## Decision log

- 2026-03-12: Restore the archived `P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01` inventory, representative smoke lanes, and reduction order as a live `P4` task so the next shrink bundle is visible from TODO again.
- 2026-03-12: `S1-01` freezes the current residual buckets, reduction order, and active bundle metadata in the inventory tool and unit test, and keeps every bundle status at `planned` until active work begins.
- 2026-03-12: `S2-01` shrinks the C# mutation residual down to the `bytearray` seam only and makes `bytes.pop()/append()` fail closed in the emitter. The remaining helpers are the bytearray `py_append/py_pop` lane and the index/slice compatibility helpers.
- 2026-03-12: Started `S2-02` by switching the C++ object-bridge labels in `call.py` from wrapper names like `\"py_append\"` to plain operation labels like `\"append\"`, so the residual bucket only counts actual object-helper callers.
- 2026-03-12: Completed `S2-02` by retargeting the remaining C++ `py_runtime_object_type_id` / `py_runtime_object_isinstance` callers to `py_runtime_value_type_id` / `py_runtime_value_isinstance`. `cpp_emitter_object_bridge_residual` now uses an empty bucket as its end state.
- 2026-03-12: Closed `S3-01` without further code changes. The Rust/C# emitters and inventory/source guards already sit at the thin shared type-id seam (`py_runtime_value_*`, `py_runtime_type_id_is_*`), so the remaining work is the final C++ shared type-id re-audit only.
- 2026-03-12: `S3-02` fixed the final C++ shared type-id residual to the exact five thin-helper pairs (`py_runtime_value_type_id`, `py_runtime_value_isinstance`, `py_runtime_type_id_is_subtype`, `py_runtime_type_id_issubclass`) and put the three C++ emitter files under the same source-guard inventory as Rust/C#. Old `py_runtime_object_*` and generic alias names are now forbidden from re-entering the C++ emitter.
