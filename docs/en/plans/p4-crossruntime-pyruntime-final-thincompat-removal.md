# P4: Remove the final `py_runtime.h` thin compat helpers across runtimes

Last updated: 2026-03-11

Related TODO:
- `ID: P4-CROSSRUNTIME-PYRUNTIME-FINAL-THINCOMPAT-REMOVAL-01` in `docs/ja/todo/index.md`

Background:
- `P0-CPP-PYRUNTIME-CONTRACT-SHRINK-01` and `P1-CPP-PYRUNTIME-HEADER-SHRINK-01` already collapsed most high-level compatibility surface in the C++ header.
- `P4-CROSSRUNTIME-PYRUNTIME-THINCOMPAT-01` aligned emitter-side blockers and shared `type_id` naming across C++/Rust/C#, and classified the remaining generic-helper dependencies.
- Even after that, `src/runtime/cpp/native/core/py_runtime.h` still keeps template `py_runtime_type_id` / `py_isinstance`, and checked-in callers still remain in `src/runtime/cpp/generated/std/json.cpp`.
- Rust/C# emitters already use thin helper naming, but the runtime mirrors still expose generic aliases (`py_runtime_type_id`, `py_isinstance`, `py_is_subtype`, `py_issubclass`) as public surface.

Goal:
- Prepare the codebase so the final two generic thin compat helpers can be removed from `py_runtime.h`.
- Classify what is still a blocker versus what is only a migration alias in C++/Rust/C#, and fail closed on unclassified re-entry.

In scope:
- `src/runtime/cpp/native/core/py_runtime.h`
- `src/runtime/cpp/generated/std/json.cpp`
- `src/runtime/rs/pytra/built_in/py_runtime.rs`
- `src/runtime/rs/pytra-core/built_in/py_runtime.rs`
- `src/runtime/cs/pytra/built_in/py_runtime.cs`
- `src/runtime/cs/pytra-core/built_in/py_runtime.cs`
- `tools/check_crossruntime_pyruntime_final_thincompat_inventory.py`
- `test/unit/tooling/test_check_crossruntime_pyruntime_final_thincompat_inventory.py`
- Representative runtime / smoke tests as needed

Out of scope:
- Physically splitting `py_runtime.h` just to make the file shorter
- Redesigning the `type_id` contract itself
- Changing the `Any/object` language boundary
- Full runtime rewrites for C++/Rust/C#

Acceptance criteria:
- The remaining final thin compat residuals are classified by bucket and enforced by tooling.
- Checked-in C++ callers no longer use generic `py_isinstance` / `py_runtime_type_id`.
- The Rust/C# runtime alias end state is fixed in docs/tests/tooling so the public generic alias surface does not grow again.
- Representative C++/Rust/C# regressions pass.
- The bundle order is fixed all the way to the final header removal slice.

End state:
- `cpp_header_final_thincompat_defs`: temporary generic template definitions still left in `py_runtime.h`. Final target: empty.
- `cpp_generated_final_thincompat_blocker`: checked-in generated/native C++ callers still using generic helpers. Final target: empty.
- `rs_runtime_generic_alias_surface`: generic aliases inside the Rust runtime. Only thin-helper delegating internal/private aliases may remain.
- `cs_runtime_generic_alias_surface`: generic aliases inside the C# runtime. Only thin-helper delegating internal/private aliases may remain.

Checks:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_crossruntime_pyruntime_final_thincompat_inventory.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_crossruntime_pyruntime_final_thincompat_inventory.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_type_id.py'`
- `PYTHONPATH=src:test/unit python3 -m unittest discover -s test/unit/backends/rs -p 'test_py2rs_smoke.py' -k type_predicate`
- `PYTHONPATH=src:test/unit python3 -m unittest discover -s test/unit/backends/cs -p 'test_py2cs_smoke.py' -k type_predicate`
- `python3 tools/build_selfhost.py`
- `git diff --check`

Breakdown:
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-FINAL-THINCOMPAT-REMOVAL-01] Remove the final `py_runtime.h` thin compat helpers across runtimes.
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-FINAL-THINCOMPAT-REMOVAL-01-S1-01] Classify the residuals into `cpp_header_final_thincompat_defs` / `cpp_generated_final_thincompat_blocker` / `rs_runtime_generic_alias_surface` / `cs_runtime_generic_alias_surface`, and add inventory/tests.
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-FINAL-THINCOMPAT-REMOVAL-01-S1-02] Fix the target end state and bundle order in docs/source guards.
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-FINAL-THINCOMPAT-REMOVAL-01-S2-01] Move checked-in generated/native C++ callers to thin helpers and empty `cpp_generated_final_thincompat_blocker`.
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-FINAL-THINCOMPAT-REMOVAL-01-S2-02] Shrink the Rust/C# runtime alias surface to internal/private seams.
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-FINAL-THINCOMPAT-REMOVAL-01-S3-01] Remove template `py_runtime_type_id` / `py_isinstance` from `py_runtime.h` and refresh representative regressions/docs/archive.

Decision log:
- 2026-03-11: Created as the next low-priority follow-up after the TODO became empty. The emitter-side blockers are already much smaller, so the next step is to make the remaining generic helper definitions and checked-in callers removable.
