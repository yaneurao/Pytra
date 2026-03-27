<a href="../../../ja/plans/archive/20260312-p1-relative-import-native-path-bundle.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: relative-import native-path bundle rollout

Last updated: 2026-03-12

Related TODO:
- `ID: P1-RELATIVE-IMPORT-NATIVE-PATH-BUNDLE-01` in `docs/ja/todo/index.md`

Background:
- The second-wave rollout order is already fixed as `locked_js_ts_smoke_bundle -> native_path_bundle(go/nim/swift) -> jvm_package_bundle(java/kotlin/scala)`.
- The coverage inventory, backend-parity docs, and second-wave rollout handoff now need a live task for the next bundle, namely `go/nim/swift`.
- The next step is to lock representative smoke / fail-closed policy on the path-oriented backends that are closest to the current Pytra-NES-style layout.

Goal:
- Promote `go/nim/swift` as the active native-path bundle handoff.
- Lock the representative scenarios, verification lane, and the boundary to the follow-up JVM bundle in docs, tooling, and contracts.

Scope:
- Add the live native-path bundle plan / TODO / contract / checker / test
- Update the coverage inventory / second-wave rollout handoff / backend-parity docs
- Fix `go/nim/swift` on the `native_path_bundle_rollout` lane

Out of scope:
- Full support claims for Go/Nim/Swift
- Implementing the follow-up JVM package bundle
- Changing relative-import semantics

Acceptance criteria:
- The live handoff points to this plan instead of the old planning task.
- `go/nim/swift` are fixed as the `native_path_bundle_rollout` lane in contracts, checkers, and docs.
- `java/kotlin/scala` remain the follow-up bundle on `remaining_second_wave_rollout_planning`.

Verification commands:
- `python3 tools/check_relative_import_backend_coverage.py`
- `python3 tools/check_relative_import_secondwave_rollout_contract.py`
- `python3 tools/check_relative_import_native_path_bundle_contract.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_backend_coverage.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_secondwave_rollout_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_native_path_bundle_contract.py'`
- `python3 tools/check_todo_priority.py`
- `git diff --check`

Decision log:
- 2026-03-12: The completed planning task moves to archive, and the next live handoff switches to `P1-RELATIVE-IMPORT-NATIVE-PATH-BUNDLE-01`.
- 2026-03-12: The representative native-path bundle backends are fixed as `go/nim/swift`, and the representative scenarios stay `parent_module_alias` / `parent_symbol_alias`.
- 2026-03-12: The live verification lane becomes `native_path_bundle_rollout`, while the follow-up JVM bundle stays on `remaining_second_wave_rollout_planning`.
- 2026-03-12: Lock `go/nim/swift` on direct native-emitter function-body smoke instead of CLI top-level `print(...)`, and require backend-specific fail-closed diagnostics for relative wildcard imports.
- 2026-03-12: Raise `go/nim/swift` to `transpile_smoke_locked` in the coverage inventory while keeping the rollout handoff on the active `native_path_bundle_rollout` and the JVM bundle as the explicit follow-up.
- 2026-03-12: Sync the focused helper split and handoff wording to the current state, then archive the task once the JVM package bundle handoff is clean.

## Breakdown

- [x] [ID: P1-RELATIVE-IMPORT-NATIVE-PATH-BUNDLE-01] Lock the live handoff and representative rollout contract for the `go/nim/swift` native-path bundle.
- [x] [ID: P1-RELATIVE-IMPORT-NATIVE-PATH-BUNDLE-01-S1-01] Add the live plan / TODO / contract / checker and switch the coverage handoff to the native-path bundle.
- [x] [ID: P1-RELATIVE-IMPORT-NATIVE-PATH-BUNDLE-01-S2-01] Add representative native-emitter transpile-smoke / fail-closed regressions for `go/nim/swift`.
- [x] [ID: P1-RELATIVE-IMPORT-NATIVE-PATH-BUNDLE-01-S2-02] Sync backend-parity docs / coverage inventory to the native-path bundle current state and spell out the JVM follow-up handoff.
- [x] [ID: P1-RELATIVE-IMPORT-NATIVE-PATH-BUNDLE-01-S3-01] Sync focused docs / tests / handoff wording to the current state and close the task.
