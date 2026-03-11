# P0: Shrink the final residual surface of `py_runtime.h`

Last updated: 2026-03-12

Related TODO:
- `ID: P0-CPP-PYRUNTIME-FINAL-SHRINK-01` in `docs/ja/todo/index.md`

Background:
- Earlier header-shrink work and cross-runtime residual-caller cleanup reduced `src/runtime/cpp/native/core/py_runtime.h` to a much smaller residual surface.
- The remaining header surface is now mainly the 9 `object_bridge_mutation` helpers and 4 thin `type_id` helpers; larger blockers such as transitive includes and typed collection compatibility are already gone.
- The next step is no longer "clean the header in isolation" but "retarget callers, then remove header helpers."
- `tools/check_cpp_pyruntime_header_surface.py` still points at an archived follow-up instead of an active final-shrink task.

Goal:
- Restore the final `py_runtime.h` shrink as an active task and lock the current residual inventory, target end state, and bundle order in docs/tooling.
- Push `object_bridge_mutation` helpers further upstream so the object wrappers in the header can be removed.
- Align thin `type_id` helper ownership across shared callers and minimize the final header surface.

In scope:
- `src/runtime/cpp/native/core/py_runtime.h`
- `tools/check_cpp_pyruntime_header_surface.py`
- `test/unit/tooling/test_check_cpp_pyruntime_header_surface.py`
- `tools/check_cpp_pyruntime_contract_inventory.py` if needed
- `src/runtime/cpp/native/compiler/*.cpp` if needed
- `src/runtime/cpp/generated/**/*.cpp` if needed
- `src/backends/{cpp,rs,cs}/**/*.py` if needed
- JA/EN TODO and plan docs

Out of scope:
- Superficially shrinking line count by physically splitting `py_runtime.h`
- Any `Any/object` language-spec change
- Full runtime redesign for C++/Rust/C#
- Feature work outside runtime/import contracts

Acceptance criteria:
- `tools/check_cpp_pyruntime_header_surface.py` points to the active task/plan and fail-closes on current residual inventory and bundle order drift.
- At least one bundle of `object_bridge_mutation` helpers is removed from the header after caller-side upstreaming.
- Shared `type_id` ownership is stabilized across native/generated/Rust/C# callers without reintroducing generic aliases into the header.
- Representative C++ runtime tests and tooling tests pass.
- JA and EN docs point to the same active end state.

Target end state:
- `object_bridge_mutation`
  - `py_append/py_set_at/py_extend/py_pop/py_clear/py_reverse/py_sort` are removed or reduced to the minimum object-only seam.
- `shared_type_id_thin_helpers`
  - `py_runtime_type_id_is_subtype`
  - `py_runtime_type_id_issubclass`
  - `py_runtime_object_type_id`
  - `py_runtime_object_isinstance`
  - No broader generic aliases return to the header.
- `typed_collection_compat`
  - stays empty.

Bundle order:
1. `S1-01`: lock current residual inventory / active handoff / bundle order in docs, tooling, and tests.
2. `S2-01`: upstream `object_bridge_mutation` callers bundle-by-bundle and remove header wrappers.
3. `S2-02`: align native/generated/Rust/C# callers on the thin `type_id` seam and re-check remaining header aliases.
4. `S3-01`: update representative runtime tests, source guards, docs, and archive the task.

Validation commands:
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
- [ ] [ID: P0-CPP-PYRUNTIME-FINAL-SHRINK-01-S1-01] Lock the current residual inventory / target end state / bundle order in docs, tooling, and tests under the active plan.
- [ ] [ID: P0-CPP-PYRUNTIME-FINAL-SHRINK-01-S2-01] Upstream `object_bridge_mutation` callers in 5-10 item bundles and remove header wrappers bundle-by-bundle.
- [ ] [ID: P0-CPP-PYRUNTIME-FINAL-SHRINK-01-S2-02] Align native/generated/Rust/C# callers on the thin `type_id` helper seam and ensure generic aliases do not return to the header.
- [ ] [ID: P0-CPP-PYRUNTIME-FINAL-SHRINK-01-S3-01] Refresh representative runtime tests, source guards, docs, and archive the task.

Decision log:
- 2026-03-12: TODO became empty, so the final `py_runtime.h` shrink was promoted as a new top-priority `P0`.
- 2026-03-12: This task is an active follow-up after the archived residual-caller cleanup. The first bundle is intentionally limited to restoring the active handoff, inventory, and bundle-order contract.
- 2026-03-12: `S1-01` switched `check_cpp_pyruntime_header_surface.py` from the archived `P4` handoff to this active `P0`, and locked the target end state plus bundle order in tooling/tests.
