# P1: relative import JVM package bundle rollout

Last updated: 2026-03-12

Related TODO:
- `ID: P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01` in `docs/ja/todo/index.md`

Background:
- The second-wave rollout order is already fixed as `locked_js_ts_smoke_bundle -> native_path_bundle(go/nim/swift) -> jvm_package_bundle(java/kotlin/scala)`.
- The `go/nim/swift` native-path bundle already fixed representative transpile smoke and the fail-closed lane, and now belongs to the current `transpile_smoke_locked` baseline.
- The coverage inventory, second-wave rollout handoff, and backend-parity docs still point at the archived native-path bundle as the next live task, so the JVM package bundle handoff is stale.

Goal:
- Fix `java/kotlin/scala` as the next live rollout bundle.
- Switch the native-path bundle to archive semantics while aligning docs, tooling, and contracts on the JVM package bundle live handoff.

Scope:
- Add the live plan / TODO / contract / checker for the JVM package bundle
- Switch the native-path bundle contract to archive semantics
- Update the second-wave rollout handoff, coverage inventory, and backend-parity docs

Out of scope:
- Full support claims for Java / Kotlin / Scala backends
- Long-tail (`lua/php/ruby`) rollout implementation
- Changes to relative-import semantics themselves

Acceptance criteria:
- The next live handoff points to this plan instead of the archived native-path plan.
- `java/kotlin/scala` are fixed on the `jvm_package_bundle_rollout` lane in contracts, checkers, and docs.
- `go/nim/swift` move into the `transpile_smoke_locked` baseline and the native-path bundle contract becomes archive semantics.
- `lua/php/ruby` remain on `defer_until_jvm_package_bundle_complete`.

Verification commands:
- `python3 tools/check_relative_import_backend_coverage.py`
- `python3 tools/check_relative_import_secondwave_rollout_contract.py`
- `python3 tools/check_relative_import_native_path_bundle_contract.py`
- `python3 tools/check_relative_import_jvm_package_bundle_contract.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_backend_coverage.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_secondwave_rollout_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_native_path_bundle_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_jvm_package_bundle_contract.py'`
- `PYTHONPATH=src:test/unit:test/unit/backends python3 -m unittest discover -s test/unit/backends/go -p 'test_py2go_smoke.py' -k relative_import_native_path_bundle -v`
- `PYTHONPATH=src:test/unit:test/unit/backends python3 -m unittest discover -s test/unit/backends/nim -p 'test_py2nim_smoke.py' -k relative_import_native_path_bundle -v`
- `PYTHONPATH=src:test/unit:test/unit/backends python3 -m unittest discover -s test/unit/backends/swift -p 'test_py2swift_smoke.py' -k relative_import_native_path_bundle -v`
- `python3 tools/check_todo_priority.py`
- `git diff --check`

Decision log:
- 2026-03-12: The native-path bundle is now treated as a locked representative-smoke baseline and moves to archive semantics before the JVM package bundle becomes the next live rollout.
- 2026-03-12: The current non-C++ rollout handoff is fixed as `rs/cs/go/js/nim/swift/ts=transpile_smoke_locked`, `java/kotlin/scala=jvm_package_bundle_rollout`, and `lua/php/ruby=defer_until_jvm_package_bundle_complete`.
- 2026-03-12: `P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01-S1-01` is a closeout-first bundle that switches the live handoff in plans, TODO, contracts, checkers, and docs before backend smoke is added in later bundles.

## Breakdown

- [ ] [ID: P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01] Fix the `java/kotlin/scala` JVM package bundle as the next live rollout and align the handoff after native-path closeout.
- [x] [ID: P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01-S1-01] Switch the native-path bundle to archive semantics and add the live JVM package bundle plan / TODO / contract / checker / docs handoff.
- [ ] [ID: P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01-S2-01] Add representative transpile-smoke / fail-closed regressions for `java/kotlin/scala`.
- [ ] [ID: P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01-S2-02] Sync backend-parity docs / coverage inventory / handoff wording to the current JVM bundle state and make the task close-ready.
