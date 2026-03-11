# P4: emitter-side `py_runtime.h` shrink follow-up

Last updated: 2026-03-11

Related TODO:
- `ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01` in `docs/ja/todo/index.md`

Background:
- `P0-CPP-PYRUNTIME-CONTRACT-SHRINK-01` and `P4-CROSSRUNTIME-PYRUNTIME-FINAL-THINCOMPAT-REMOVAL-01` already removed the generic `py_runtime_type_id` / `py_isinstance` layer from `py_runtime.h`.
- Even so, `py_runtime.h` still keeps object-bridge mutation helpers and shared `type_id` thin helpers. Shrinking it further now depends on aligning caller-side emitter contracts rather than editing the header in isolation.
- The existing C++/Rust/C# emitters already moved part of their surface onto thin helper naming, but the remaining helper dependencies and their removal order are not yet fixed. Without that contract, future shrink work will fall back into tiny local edits again.

Goal:
- Classify the remaining emitter-side `py_runtime` helper dependencies across C++/Rust/C# and lock the caller-side contract needed for further `py_runtime.h` shrink.
- Fail closed on re-entry for mutation helpers, object bridge helpers, and shared `type_id` helpers through docs / tooling / smoke tests.

In scope:
- `src/backends/cpp/emitter/`
- `src/backends/rs/emitter/rs_emitter.py`
- `src/backends/cs/emitter/cs_emitter.py`
- runtime helper inventory tooling as needed
- representative C++ / Rust / C# smoke and contract tests
- `docs/ja/todo/index.md`
- `docs/ja/plans/p4-crossruntime-pyruntime-emitter-shrink-followup.md`

Out of scope:
- physically splitting `py_runtime.h`
- full runtime-mirror regeneration
- redesigning the `type_id` contract
- changing language-level `Any/object` semantics

Acceptance criteria:
- Remaining emitter-side `py_runtime` helper dependencies are bucketed and tooling detects unclassified re-entry.
- The removal order for mutation helpers / object bridge / shared `type_id` is fixed in docs/source guards.
- Representative C++/Rust/C# regressions lock the current thin-helper / object-bridge contract as the source of truth.
- After this follow-up, the remaining `py_runtime.h` shrink candidates are limited to helpers that are still intentionally required by the caller-side contract.

End state:
- `cpp_emitter_object_bridge_residual`: places where the C++ emitter still requires object-bridge helpers. Re-entry from typed lanes is forbidden.
- `cpp_emitter_shared_type_id_residual`: places where the C++ emitter still uses shared `type_id` thin helpers. Re-entry to generic helpers is forbidden.
- `rs_emitter_shared_type_id_residual`: shared `type_id` helper usage that remains in the Rust emitter.
- `cs_emitter_shared_type_id_residual`: shared `type_id` helper usage that remains in the C# emitter.
- `crossruntime_mutation_helper_residual`: mutation-helper usage across C++/Rust/C# emitters. Re-entry from non-object-bridge lanes is forbidden.

Bundle order:
1. Bucket the residual helper dependencies and add inventory/tests.
2. Fix the end state and removal order in docs/source guards.
3. Move the remaining C++ emitter helper dependencies onto thin/object-bridge seams.
4. Align the Rust/C# emitter helper dependencies to the shared contract.
5. Refresh representative smoke/docs/archive.

Checks:
- `python3 tools/check_todo_priority.py`
- `python3 tools/build_selfhost.py`
- `python3 tools/check_transpiler_version_gate.py`
- `python3 tools/run_regen_on_version_bump.py --dry-run`
- `git diff --check`

Breakdown:
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01] Align the remaining emitter-side helper dependencies across C++/Rust/C# so `py_runtime.h` can shrink further.
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01-S1-01] Bucket residual emitter-side `py_runtime` helper usage across C++/Rust/C# and add inventory/tests.
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01-S1-02] Fix the end state and removal order for mutation / `type_id` / object-bridge helpers in docs/source guards.
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01-S2-01] Move remaining C++ emitter helper dependencies onto thin/object-bridge seams.
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01-S2-02] Align remaining Rust emitter helper dependencies to the shared contract.
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01-S2-03] Align remaining C# emitter helper dependencies to the shared contract.
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01-S3-01] Refresh representative smoke/docs/archive and close the follow-up.

Decision log:
- 2026-03-11: Created as the next follow-up after `P4-CROSSRUNTIME-PYRUNTIME-FINAL-THINCOMPAT-REMOVAL-01` completed. The generic thin compat layer is gone from the header, so the next shrink step must classify and reduce caller-side residual helper contracts instead.
- 2026-03-11: Completed `S1-01` by retargeting `tools/check_crossruntime_pyruntime_emitter_inventory.py` onto thin-helper names and classifying the current residuals into `cpp_emitter_object_bridge_residual`, `cpp_emitter_shared_type_id_residual`, `rs_emitter_shared_type_id_residual`, `cs_emitter_shared_type_id_residual`, and `crossruntime_mutation_helper_residual`. C++ now tracks `py_runtime_object_*` and `py_runtime_type_id_*`, Rust/C# track `py_runtime_value_*` / `py_runtime_type_id_*`, and mutation helpers are limited to the C++ object-bridge fallback plus the C# bytes/bytearray lane.
