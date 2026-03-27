<a href="../../../ja/plans/archive/20260311-p4-crossruntime-pyruntime-emitter-align.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P4: Align residual `py_runtime` contracts across the C++/Rust/C# emitters

Last updated: 2026-03-11

Related TODO:
- `ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-ALIGN-01` in `docs/en/todo/index.md`

Background:
- `P0-CPP-PYRUNTIME-CONTRACT-SHRINK-01` already narrowed most typed-lane mutation wrappers and generic `type_id` wrappers out of `py_runtime.h`.
- The next shrink stage depends on aligning the remaining emitter-side `py_runtime` usage across C++/Rust/C#, so the `object bridge residual` and the shared `type_id` contract are explicit instead of mixed together.
- Today `src/backends/cpp/emitter/`, `src/backends/rs/emitter/rs_emitter.py`, and `src/backends/cs/emitter/cs_emitter.py` still mix mutation-helper calls, `type_id` helpers, and runtime-mirror definitions.

Goal:
- Bucket the residual `py_runtime` contract that remains in the C++/Rust/C# emitters and make drift fail fast.
- Lock the boundary between `object bridge residual`, `shared type_id contract`, and `cross-runtime bridge residual` in docs, tooling, and smoke tests.

Scope:
- `src/backends/cpp/emitter/*.py`
- `src/backends/rs/emitter/rs_emitter.py`
- `src/backends/cs/emitter/cs_emitter.py`
- As needed, `src/runtime/rs/pytra*/built_in/py_runtime.rs`
- As needed, `src/runtime/cs/pytra*/built_in/py_runtime.cs`
- `tools/*pyruntime*inventory*.py`
- `test/unit/tooling/*inventory*.py`
- `test/unit/backends/cpp/test_east3_cpp_bridge.py`
- `test/unit/backends/rs/test_py2rs_smoke.py`
- `test/unit/backends/cs/test_py2cs_smoke.py`

Out of scope:
- Further shrinking `py_runtime.h` itself
- A full redesign of the Rust/C#/C++ runtimes
- Changing the `Any/object` boundary
- `JsonValue` or nominal-ADT feature work

Acceptance criteria:
- Residual `py_runtime` symbols in the C++/Rust/C# emitters are bucketed in inventory tooling, and unclassified reintroduction fails fast.
- The C++ emitter's `object bridge residual` does not get mixed with the Rust/C#/C++ shared `type_id` contract.
- Rust/C# type predicate and runtime-type-id lanes use the canonical helper names.
- Representative smoke and contract tests pass.

Residual-bucket end state:
- `cpp_object_bridge_residual`: reserve this bucket for the C++ emitter's object fallback only, and do not allow anything outside `py_append/extend/pop/clear/reverse/sort/set_at`.
- `shared_type_id_contract`: allow only `py_runtime_type_id`, `py_isinstance`, `py_is_subtype`, and `py_issubclass`, and treat those helper names as canonical across the C++/Rust/C# emitters.
- `crossruntime_object_bridge_residual`: isolate non-C++ emitter mutation helpers that still need object-bridge behavior; for now this bucket allows only C# `py_append` / `py_pop`.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_crossruntime_pyruntime_emitter_inventory.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_crossruntime_pyruntime_emitter_inventory.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_east3_cpp_bridge.py'`
- `PYTHONPATH=src:test/unit python3 -m unittest discover -s test/unit/backends/rs -p 'test_py2rs_smoke.py' -k type_predicate`
- `PYTHONPATH=src:test/unit python3 -m unittest discover -s test/unit/backends/cs -p 'test_py2cs_smoke.py' -k type_predicate`
- `python3 tools/build_selfhost.py`
- `python3 tools/check_transpiler_version_gate.py`
- `python3 tools/run_regen_on_version_bump.py --dry-run`
- `git diff --check`

Breakdown:
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-ALIGN-01-S1-01] Bucket residual `py_runtime` symbols across the C++/Rust/C# emitters and add an inventory drift guard.
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-ALIGN-01-S1-02] Lock the end state for `object bridge residual`, `shared type_id contract`, and `cross-runtime bridge residual` in docs.
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-ALIGN-01-S2-01] Clean up representative C++ object-bridge mutation-helper residuals.
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-ALIGN-01-S2-02] Align Rust/C# `type_id` and type-predicate lowering to the shared contract.
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-ALIGN-01-S3-01] Refresh representative smoke tests, docs, and archive the task.

Decision log:
- 2026-03-11: Opened as the post-`P0-CPP-PYRUNTIME-CONTRACT-SHRINK-01` follow-up. This P4 is about making the cross-runtime emitter contract explicit and aligned, not about directly shrinking `py_runtime.h` again.
- 2026-03-11: As `S1-01`, we added `tools/check_crossruntime_pyruntime_emitter_inventory.py` and its unit test, then bucketed emitter-side residual `py_runtime` symbols into `cpp_object_bridge_residual`, `shared_type_id_contract`, and `crossruntime_object_bridge_residual`.
- 2026-03-11: As `S1-02`, we fixed the end state of those three buckets in the docs. C++ object fallback stays isolated in `cpp_object_bridge_residual`, cross-language type-predicate / type-id helpers stay in `shared_type_id_contract`, and the remaining C# list bridge stays isolated in `crossruntime_object_bridge_residual`.
- 2026-03-11: As `S2-01`, we centralized the C++ emitter object-bridge helper names into `CppCallEmitter`'s canonical map, so the residual `py_append/extend/pop/clear/reverse/sort/set_at` symbols remain in `call.py` only. The inventory guard was updated to lock that end state.
- 2026-03-11: As `S2-02`, we centralized Rust/C# `py_runtime_type_id` / `py_isinstance` / `py_is_subtype` / `py_issubclass` lowering behind per-emitter helper seams, so representative `isinstance(...)` lowering and EAST3 `ObjTypeId/IsInstance/IsSubtype/IsSubclass` lowering now share the same contract entrypoints.
- 2026-03-11: As `S3-01`, we re-ran the crossruntime inventory, the representative C++ bridge lane, Rust/C# `type_predicate` smoke, and selfhost build, then synchronized docs and archive to the representative end state.
