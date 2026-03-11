# P0: Shrink the C++ `py_runtime.h` contract (object bridge and shared `type_id` contract cleanup)

Last updated: 2026-03-11

Related TODO:
- `ID: P0-CPP-PYRUNTIME-CONTRACT-SHRINK-01` in `docs/en/todo/index.md`

Background:
- `src/runtime/cpp/native/core/py_runtime.h` is now more shrinkable after transitive include cleanup and typed-dict helper removal.
- The remaining bulk is no longer simple dead code inside the header. It is concentrated in `object`-bridge mutation helpers and the shared `type_id` contract.
- `py_append/py_extend/py_pop/py_clear/py_reverse/py_sort/py_set_at` are already largely upstreamed out of the typed C++ lane, but C++ object fallback, generated runtime code, and the C# runtime mirror still depend on them.
- `py_runtime_type_id/py_isinstance/py_is_subtype` are still referenced as a shared contract by generated `type_id` built-ins, native compiler wrappers, and Rust/C# runtime/emitter paths. Removing them from the header without reassigning ownership would create drift.

Goal:
- Remove from `py_runtime.h` the surfaces that remain only because of shared compatibility, not because the typed lane still needs them.
- Shrink mutation helpers to an object-bridge-only surface.
- Move `type_id` shared-contract ownership toward generated/shared helper seams so `py_runtime.h` becomes a thin compatibility layer instead of the policy owner.

Scope:
- `src/runtime/cpp/native/core/py_runtime.h`
- `src/backends/cpp/emitter/call.py`
- `src/backends/cpp/emitter/cpp_emitter.py`
- `src/runtime/cpp/generated/built_in/type_id.cpp`
- `src/runtime/cpp/native/compiler/transpile_cli.cpp`
- `src/runtime/cpp/native/compiler/backend_registry_static.cpp`
- `src/runtime/rs/pytra-core/built_in/py_runtime.rs`
- `src/runtime/cs/pytra-core/built_in/py_runtime.cs`
- `src/backends/rs/emitter/rs_emitter.py`
- `src/backends/cs/emitter/cs_emitter.py`
- `test/unit/backends/cpp/test_cpp_runtime_iterable.py`
- `test/unit/backends/cpp/test_cpp_runtime_type_id.py`
- `test/unit/backends/cpp/test_py2cpp_codegen_issues.py`
- `test/unit/backends/cpp/test_east3_cpp_bridge.py`
- Rust/C# smoke tests when needed

Out of scope:
- Reducing line count only by physically splitting `py_runtime.h`.
- Removing the `Any/object` boundary itself.
- Fully migrating the Rust/C#/C++ `type_id` contract to a pure-generated source of truth in one step.
- Nominal ADT or `JsonValue` language changes.

Acceptance criteria:
- Mutation helpers in `py_runtime.h` are no longer a typed-C++-lane surface; they are narrowed to object bridge / compatibility use.
- Ownership of `py_runtime_type_id/py_isinstance/py_is_subtype` is documented and guarded so `py_runtime.h` is no longer the sole policy source.
- The typed C++ emitter lane does not regress into unnecessary use of `py_append/py_extend/py_pop/py_clear/py_reverse/py_sort/py_set_at`.
- Every residual caller is classified as one of `typed_lane_removable`, `object_bridge_required`, or `shared_runtime_contract`, and unclassified reintroduction is caught by tests/tooling.
- `test_cpp_runtime_iterable.py`, `test_cpp_runtime_type_id.py`, `test_east3_cpp_bridge.py`, `test_py2cpp_codegen_issues.py`, relevant Rust/C# smoke tests, and `build_selfhost.py` pass.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_iterable.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_type_id.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_east3_cpp_bridge.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_codegen_issues.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/rs -p 'test_py2rs_smoke.py' -k type_id`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cs -p 'test_py2cs_smoke.py' -k type_id`
- `python3 tools/build_selfhost.py`
- `python3 tools/check_transpiler_version_gate.py`
- `python3 tools/run_regen_on_version_bump.py --dry-run`
- `git diff --check`

Breakdown:
- [x] [ID: P0-CPP-PYRUNTIME-CONTRACT-SHRINK-01-S1-01] Inventory remaining mutation-helper and `type_id` callers into `typed_lane_removable`, `object_bridge_required`, and `shared_runtime_contract`, and lock why each group remains.
- [x] [ID: P0-CPP-PYRUNTIME-CONTRACT-SHRINK-01-S1-02] Lock the target end state for `py_runtime.h` and reflect the mutation-helper / `type_id` shrink order in docs and source guards.
- [x] [ID: P0-CPP-PYRUNTIME-CONTRACT-SHRINK-01-S2-01] Push the remaining `py_append/extend/pop/clear/reverse/sort/set_at` dependencies out of the typed C++ emitter lane in bundle-sized changes.
- [x] [ID: P0-CPP-PYRUNTIME-CONTRACT-SHRINK-01-S2-02] Narrow mutation helpers in `py_runtime.h` to object-bridge / compatibility overloads only, and lock residual callers with labels.
- [x] [ID: P0-CPP-PYRUNTIME-CONTRACT-SHRINK-01-S3-01] Reassign shared ownership for `py_runtime_type_id/py_isinstance/py_is_subtype`, and retarget native compiler wrappers and generated `type_id` built-ins to thin helper seams.
- [ ] [ID: P0-CPP-PYRUNTIME-CONTRACT-SHRINK-01-S3-02] Align Rust/C#/C++ residual `type_id` callers to the shared contract and catch unclassified reintroduction with smoke/contract tests.
- [ ] [ID: P0-CPP-PYRUNTIME-CONTRACT-SHRINK-01-S4-01] Update labels, source guards, and docs for the remaining `py_runtime.h` surface and leave the task ready for archive.

Decision log:
- 2026-03-11: After transitive-include cleanup and typed-dict / typed-mutation upstreaming, the remaining `py_runtime.h` shrink work was reduced to two pillars: mutation helpers and the shared `type_id` contract.
- 2026-03-11: This task intentionally excludes physical header splitting and focuses only on contract shrinkage that reduces burden for other-language runtime implementations.
- 2026-03-11: `S1` is limited to inventory plus target-end-state locking before implementation, and work should proceed in bundle-sized slices rather than helper-by-helper micro-commits.
- 2026-03-11: As `S1-01`, added `tools/check_cpp_pyruntime_contract_inventory.py` and locked the remaining `symbol × path` callers into three buckets: `typed_lane_removable`, `object_bridge_required`, and `shared_runtime_contract`. This now guards native compiler wrappers, generated `json/type_id`, and the C++ emitter mutation lane against unclassified reintroduction.
- 2026-03-11: As `S1-02`, expanded `test_cpp_runtime_iterable.py` and `test_check_cpp_pyruntime_contract_inventory.py` so the mutation-helper end state is fixed as `typed=container overload / compat=object overload`, and the `type_id` end state is fixed as `py_tid_*` delegation plus the generated `type_id.h` include.
- 2026-03-11: As `S2-01`, removed `py_append/extend/pop/clear/reverse/sort/set_at` wrapper calls from the C++ emitter / stmt lane and lowered user-emitted C++ directly to `py_list_*_mut(obj_to_list_ref_or_raise(...))`. The `typed_lane_removable` bucket is now intentionally empty; residual callers are limited to generated runtime code and the shared `type_id` contract.
- 2026-03-11: As `S2-02`, removed the `rc<list<T>>` mutation wrappers from `py_runtime.h`, leaving `py_append` only for generated-runtime local-list compatibility plus the object-bridge seam, and leaving `py_extend/pop/clear/reverse/sort/set_at` only as the object-bridge seam. Typed lanes now canonically call `py_list_*_mut` directly, and the source guards lock that end state.
- 2026-03-11: As `S3-01`, split the thin type-id seam into `py_runtime_object_type_id`, `py_runtime_object_isinstance`, `py_runtime_type_id_is_subtype`, and `py_runtime_type_id_issubclass`, then retargeted generated `type_id.cpp` and the native compiler wrappers to that seam instead of the generic wrappers. The inventory now excludes those generated/native callers from the old-wrapper residual set.
- 2026-03-11: As a representative `S3-02` bundle, we included `py_issubclass` in the residual shared-contract inventory and aligned Rust/C# `IsSubclass` lowering from `py_is_subtype` to `py_issubclass`. The C++ emitter keeps `py_issubclass` as the canonical lowering, and cross-runtime drift is now locked by inventory plus backend smoke tests.
