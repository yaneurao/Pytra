<a href="../../../ja/plans/archive/20260312-p1-relative-import-secondwave-planning.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: relative-import second-wave rollout planning

Last updated: 2026-03-12

Related TODO:
- `ID: P1-RELATIVE-IMPORT-SECONDWAVE-PLANNING-01` in `docs/ja/todo/index.md`

Background:
- The current relative-import verification coverage is already fixed as `cpp=build_run_locked`, `rs/cs=transpile_smoke_locked`, and every other non-C++ backend as `not_locked`.
- The first-wave `rs/cs` smoke task has been archived, but the `second_wave_rollout_planning` handoff referenced by coverage inventory and backend-parity docs still has no live plan.
- Before the Pytra-NES-style project layout is widened to more backends, the second-wave backend set, order, representative scenarios, and fail-closed baseline need to be locked as a live contract.

Goal:
- Provide the canonical live plan for second-wave relative-import rollout.
- Lock the second-wave backend set, representative scenarios, verification lane, and fail-closed baseline in tooling contracts and docs handoff.

Scope:
- Add the second-wave rollout planning contract
- Update coverage-inventory / backend-parity docs handoff
- Add the live TODO / plan / checker / unit test

Out of scope:
- Implementing the second-wave backends
- Changing relative-import semantics
- Widening support claims

Acceptance criteria:
- The second-wave backend order is fixed in the live contract, checker, and docs.
- The representative scenarios are fixed as `parent_module_alias` / `parent_symbol_alias`.
- The coverage inventory / backend-parity docs handoff points to this live plan instead of the archived first-wave plan.

Verification commands:
- `python3 tools/check/check_relative_import_secondwave_rollout_contract.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_check_relative_import_secondwave_rollout_contract.py'`
- `python3 tools/check/check_relative_import_backend_coverage.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_check_relative_import_backend_coverage.py'`
- `python3 tools/check/check_todo_priority.py`
- `git diff --check`

Decision log:
- 2026-03-12: Immediately after archiving the first-wave `rs/cs` smoke task, the second-wave planning task is made live so the next handoff stays anchored.
- 2026-03-12: The second-wave backend set is fixed as `go/java/js/kotlin/nim/scala/swift/ts`; the representative scenarios stay `parent_module_alias` / `parent_symbol_alias`; the verification lane stays `second_wave_rollout_planning`; and the fail-closed baseline remains `backend_specific_fail_closed`.
- 2026-03-12: The second-wave rollout order is fixed as backend-group bundles `locked_js_ts_smoke_bundle -> native_path_bundle(go/nim/swift) -> jvm_package_bundle(java/kotlin/scala)`. The native/path-oriented targets go first because they are closest to the current path-root relative-import semantics, while the JVM package bundle stays as the follow-up rollout.
- 2026-03-12: `S3-01` syncs the coverage-inventory handoff and backend-parity docs to the bundle order plus next/follow-up bundle metadata, then closes the task.

## Breakdown

- [x] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-PLANNING-01] Lock the live contract, docs handoff, and verification lane for second-wave relative-import rollout.
- [x] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-PLANNING-01-S1-01] Add the live plan / TODO plus the second-wave rollout contract, checker, and docs handoff.
- [x] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-PLANNING-01-S2-01] Break the second-wave backend rollout order into backend-group bundles for representative smoke / fail-closed rollout.
- [x] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-PLANNING-01-S3-01] Sync coverage docs / support wording / archive handoff to the current second-wave state and close the task.
