<a href="../../../ja/plans/archive/20260311-p1-cpp-pyruntime-header-shrink.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: Shrink the remaining `py_runtime.h` surface for real

Last updated: 2026-03-11

Related TODO:
- `ID: P1-CPP-PYRUNTIME-HEADER-SHRINK-01` in `docs/en/todo/index.md`

Background:
- `P0-CPP-PYRUNTIME-CONTRACT-SHRINK-01` already cleaned up most typed-lane mutation wrappers and generic `type_id` ownership.
- `P4-CROSSRUNTIME-PYRUNTIME-EMITTER-ALIGN-01` aligned the residual emitter-side contract across C++/Rust/C# and made drift fail fast.
- That leaves `src/runtime/cpp/native/core/py_runtime.h` in a state where the remaining helpers can now be split into “must remain compatibility seam” vs “still removable wrappers”.

Goal:
- Classify the remaining `py_runtime.h` helpers into `object bridge mutation`, `typed collection compatibility`, and `shared type_id compatibility`, then lock the removal order.
- Prepare source/tooling/smoke so the next shrink steps can remove overloads in bundle-sized slices.

Scope:
- `src/runtime/cpp/native/core/py_runtime.h`
- `tools/check_cpp_pyruntime_header_surface.py`
- `test/unit/tooling/test_check_cpp_pyruntime_header_surface.py`
- As needed, `tools/check_cpp_pyruntime_contract_inventory.py`
- As needed, `test/unit/backends/cpp/test_cpp_runtime_iterable.py`
- As needed, `test/unit/backends/cpp/test_cpp_runtime_type_id.py`

Out of scope:
- Reducing line count by physically splitting `py_runtime.h` alone
- Full redesign of the Rust/C#/C++ runtimes
- Changing the `Any/object` boundary
- Reworking the cross-runtime emitter contract itself

Acceptance criteria:
- The remaining `py_runtime.h` helpers are inventory-classified by category and unclassified reintroduction fails fast.
- The boundaries between `object bridge mutation`, `typed collection compatibility`, and `shared type_id compatibility` are locked in docs/tests/source.
- Representative C++ runtime tests pass.
- At least one bundle of residual wrappers is removed from the header.

End state:
- `object_bridge_mutation`: only mutation helpers that take `object&` remain, explicitly marked as the C++ object-bridge seam.
- `typed_collection_compat`: this should normally be an empty bucket; only unavoidable generated-runtime local typed-collection helpers may remain as exceptions.
- `shared_type_id_compat`: only thin compatibility helpers for `py_is_subtype` / `py_issubclass` / `py_runtime_type_id` / `py_isinstance` remain.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_cpp_pyruntime_header_surface.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_cpp_pyruntime_header_surface.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_iterable.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_type_id.py'`
- `python3 tools/build_selfhost.py`
- `python3 tools/check_transpiler_version_gate.py`
- `python3 tools/run_regen_on_version_bump.py --dry-run`
- `git diff --check`

Breakdown:
- [x] [ID: P1-CPP-PYRUNTIME-HEADER-SHRINK-01-S1-01] Inventory the remaining `py_runtime.h` helpers into `object_bridge_mutation`, `typed_collection_compat`, and `shared_type_id_compat`, and add tooling.
- [x] [ID: P1-CPP-PYRUNTIME-HEADER-SHRINK-01-S1-02] Lock the target end state and bundle-sized removal order in docs/source guards.
- [x] [ID: P1-CPP-PYRUNTIME-HEADER-SHRINK-01-S2-01] Remove unnecessary list/dict wrappers from `typed_collection_compat` in bundle-sized slices.
- [x] [ID: P1-CPP-PYRUNTIME-HEADER-SHRINK-01-S2-02] Further narrow the thin `shared_type_id_compat` wrappers under source-guard coverage.
- [x] [ID: P1-CPP-PYRUNTIME-HEADER-SHRINK-01-S3-01] Refresh representative runtime tests, docs, and archive the task.

Decision log:
- 2026-03-11: Opened as the follow-up after `P4-CROSSRUNTIME-PYRUNTIME-EMITTER-ALIGN-01`. The next step is not more emitter work, but actually shrinking the residual surface inside `py_runtime.h`.
- 2026-03-11: As `S1-01`, we inventoried the remaining helpers into `object_bridge_mutation`, `typed_collection_compat`, and `shared_type_id_compat`, then added a drift guard.
- 2026-03-11: As `S1-02`, we added header-surface source guards in `test_cpp_runtime_iterable.py` and fixed the removal order so the next shrink starts from `typed_collection_compat`.
- 2026-03-11: As the first `S2-01` bundle, we removed the unused `py_set_at(dict<K, V>& ...)` wrapper from the header, inventory, and source guards. The remaining `typed_collection_compat` lane is now only `py_append(list<T>& ...)`.
- 2026-03-11: As the second `S2-01` bundle, we restored local concrete lists in the C++ emitter to the value lane and resynced the local array append in generated `json.cpp` to direct `.append(...)`, then removed `py_append(list<T>& ...)` from the header, inventory, and source guards. The object helper `iter_ops.cpp` stays on `py_list_append_mut(obj_to_list_ref_or_raise(...))`, and the `typed_collection_compat` bucket is now empty.
- 2026-03-11: As the first `S2-02` bundle, we retargeted the C++ emitter and runtime regressions to `py_runtime_object_type_id` / `py_runtime_type_id_is_subtype` / `py_runtime_type_id_issubclass`, then removed the `py_is_subtype` / `py_issubclass` / `py_runtime_type_id(const object&)` aliases from the header. The remaining `shared_type_id_compat` bucket is now only template `py_runtime_type_id` and `py_isinstance`.
- 2026-03-11: We closed `S2-02` by fixing the remaining `shared_type_id_compat` surface at exactly two helpers: template `py_runtime_type_id` and `py_isinstance`. Any further removal now depends on cross-runtime emitter/generated follow-up rather than header-only cleanup.
- 2026-03-11: As `S3-01`, we refreshed representative runtime tests, header-surface tooling, docs, and archive state, then closed the task.
