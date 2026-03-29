<a href="../../../ja/plans/archive/20260312-p1-relative-import-jvm-package-bundle.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: Relative-import JVM package bundle rollout

Last updated: 2026-03-12

Related TODO:
- `ID: P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01` in `docs/ja/todo/index.md`

Background:
- The second-wave rollout order is already fixed as `locked_js_ts_smoke_bundle -> native_path_bundle(go/nim/swift) -> jvm_package_bundle(java/kotlin/scala)`.
- The `go/nim/swift` native-path bundle has already locked representative transpile smoke and its fail-closed lane, and in the current coverage it has been promoted to the `transpile_smoke_locked` baseline.
- The coverage inventory, second-wave rollout handoff, and backend-parity docs still reference the archived native-path bundle as the next live task, so the handoff to the JVM package bundle remains stale.

Goal:
- Fix `java/kotlin/scala` as the next live rollout bundle.
- Switch the native-path bundle to archive semantics while synchronizing the JVM package bundle live handoff across docs, tooling, and contracts.

Scope:
- Add the live plan, TODO, contract, and checker
- Switch the archived native-path bundle contract
- Update the second-wave rollout handoff, coverage inventory, and backend-parity docs

Out of scope:
- Full support claims for the Java, Kotlin, and Scala backends
- Long-tail rollout implementation for `lua/php/ruby`
- Changes to relative-import semantics themselves

Acceptance criteria:
- The next live handoff refers to this plan rather than the archived native-path plan.
- `java/kotlin/scala` are fixed as the `jvm_package_bundle_rollout` lane in contracts, checkers, and docs.
- `go/nim/swift` move to the `transpile_smoke_locked` baseline, and the native-path bundle contract takes on archive semantics.
- `lua/php/ruby` remain under `defer_until_jvm_package_bundle_complete`.

Verification commands:
- `python3 tools/check/check_relative_import_backend_coverage.py`
- `python3 tools/check/check_relative_import_secondwave_rollout_contract.py`
- `python3 tools/check/check_relative_import_native_path_bundle_contract.py`
- `python3 tools/check/check_relative_import_jvm_package_bundle_contract.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_check_relative_import_backend_coverage.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_check_relative_import_secondwave_rollout_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_check_relative_import_native_path_bundle_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_check_relative_import_jvm_package_bundle_contract.py'`
- `PYTHONPATH=src:test/unit:tools/unittest/backends python3 -m unittest discover -s tools/unittest/emit/go -p 'test_py2go_smoke.py' -k relative_import_native_path_bundle -v`
- `PYTHONPATH=src:test/unit:tools/unittest/backends python3 -m unittest discover -s tools/unittest/emit/nim -p 'test_py2nim_smoke.py' -k relative_import_native_path_bundle -v`
- `PYTHONPATH=src:test/unit:tools/unittest/backends python3 -m unittest discover -s tools/unittest/emit/swift -p 'test_py2swift_smoke.py' -k relative_import_native_path_bundle -v`
- `python3 tools/check/check_todo_priority.py`
- `git diff --check`

Decision log:
- 2026-03-12: The native-path bundle is treated as the current baseline with representative smoke locked, then moved to archive semantics, and the JVM package bundle is promoted to the next live rollout.
- 2026-03-12: The current non-C++ rollout handoff is fixed as `rs/cs/go/js/nim/swift/ts=transpile_smoke_locked`, `java/kotlin/scala=jvm_package_bundle_rollout`, and `lua/php/ruby=defer_until_jvm_package_bundle_complete`.
- 2026-03-12: `P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01-S1-01` is defined as a closeout-first bundle that switches the live plan, TODO, contract, checker, and docs handoff, with additional backend smoke deferred to later bundles.
- 2026-03-12: `P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01-S2-01` fixes representative package-style transpile smoke for `java/kotlin/scala`, and wildcard relative imports remain fail-closed in backend-native emitters.
- 2026-03-12: Under `P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01-S2-02`, the coverage inventory is synchronized to the current smoke state, and `java/kotlin/scala` are recorded as keeping long-tail handoff ownership under the active `jvm_package_bundle_rollout` while also carrying `transpile_smoke_locked` evidence.
- 2026-03-12: The evidence lane in `P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01-S2-02` is fixed as `java/kotlin/scala=package_project_transpile` and `go/nim/swift=native_emitter_function_body_transpile`, and the follow-up long-tail lane is unified as `longtail_relative_import_rollout / defer_until_jvm_package_bundle_complete`.
- 2026-03-12: In `P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01-S3-01`, the JVM bundle contract checker was connected to the current smoke-locked coverage and long-tail handoff snapshot, and the parent task was closed after aligning focused docs, tests, and handoff wording.

## Breakdown

- [x] [ID: P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01] Fix the JVM package bundle for `java/kotlin/scala` as the next live rollout and align the handoff after native-path closeout.
- [x] [ID: P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01-S1-01] Switch the native-path bundle to archive semantics and add the live plan, TODO, contract, checker, and docs handoff for the JVM package bundle.
- [x] [ID: P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01-S2-01] Add representative transpile-smoke and fail-closed regressions for `java/kotlin/scala`.
- [x] [ID: P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01-S2-02] Synchronize backend-parity docs, coverage inventory, and handoff wording to the current JVM bundle state so the task is ready to close.
- [x] [ID: P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01-S3-01] Align focused docs, tests, and handoff wording to the current smoke-locked state and close the JVM package bundle task.
