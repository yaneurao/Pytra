# P1: relative import long-tail bundle rollout

Last updated: 2026-03-12

Related TODO:
- `ID: P1-RELATIVE-IMPORT-LONGTAIL-BUNDLE-01` in `docs/ja/todo/index.md`

Background:
- The second-wave rollout `locked_js_ts_smoke_bundle -> native_path_bundle(go/nim/swift) -> jvm_package_bundle(java/kotlin/scala)` has already been archived.
- The current coverage baseline now fixes `rs/cs/go/java/js/kotlin/nim/scala/swift/ts` as `transpile_smoke_locked`, leaving only `lua/php/ruby` without representative verification.
- The backend coverage inventory, second-wave handoff, and backend parity docs now need to point at the `lua/php/ruby` long-tail bundle as the next live rollout.

Goal:
- Fix `lua/php/ruby` as the next live rollout bundle.
- Align the representative long-tail scenarios, verification lane, and fail-closed lane across docs, tooling, and contracts.

Scope:
- Add the live long-tail bundle plan / TODO / contract / checker / tests
- Convert the JVM package bundle contract to archive semantics
- Update backend coverage, the second-wave handoff, and backend parity docs to the long-tail live handoff

Out of scope:
- Full support claims for Lua / PHP / Ruby backends
- Changes to relative-import semantics
- Backend work beyond representative long-tail smoke

Acceptance criteria:
- The next live handoff points to this plan and fixes `lua/php/ruby` on `longtail_relative_import_rollout`.
- `java/kotlin/scala` move into the archived JVM bundle / `transpile_smoke_locked` baseline.
- The backend coverage inventory, second-wave contract, and backend parity docs no longer reference the deleted live JVM plan.
- `python3 tools/check_relative_import_*contract.py` and the matching unit tests pass.

Verification commands:
- `python3 tools/check_relative_import_backend_coverage.py`
- `python3 tools/check_relative_import_secondwave_rollout_contract.py`
- `python3 tools/check_relative_import_jvm_package_bundle_contract.py`
- `python3 tools/check_relative_import_longtail_bundle_contract.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_backend_coverage.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_secondwave_rollout_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_jvm_package_bundle_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_longtail_bundle_contract.py'`
- `python3 tools/check_todo_priority.py`
- `git diff --check`

Decision log:
- 2026-03-12: The JVM package bundle is now treated as an archived bundle with representative smoke locked, and the next live rollout moves to the `lua/php/ruby` long-tail bundle.
- 2026-03-12: The active long-tail lane stays `longtail_relative_import_rollout`, with `backend_specific_fail_closed` fixed as the fail-closed lane.
- 2026-03-12: The second-wave bundle order remains as historical contract context, while the next live rollout handoff is updated to the long-tail bundle.
- 2026-03-12: For `lua/php/ruby`, the current representative contract is explicit backend-native rejection of relative-import projects, with wildcard relative imports fixed to the same `unsupported relative import form` fail-closed family.
- 2026-03-12: The coverage inventory and backend parity docs keep `contract_state=not_locked` for `lua/php/ruby`, while publishing representative evidence through the `backend_native_fail_closed` lane.

## Breakdown

- [ ] [ID: P1-RELATIVE-IMPORT-LONGTAIL-BUNDLE-01] Fix the `lua/php/ruby` long-tail bundle live handoff and representative rollout contract.
- [x] [ID: P1-RELATIVE-IMPORT-LONGTAIL-BUNDLE-01-S1-01] Add the live long-tail plan / TODO / contract / checker / docs handoff and switch the JVM bundle contract to archive semantics.
- [x] [ID: P1-RELATIVE-IMPORT-LONGTAIL-BUNDLE-01-S2-01] Add representative transpile-smoke / fail-closed regressions for `lua/php/ruby` and lock backend-native explicit rejection as the current contract.
- [x] [ID: P1-RELATIVE-IMPORT-LONGTAIL-BUNDLE-01-S2-02] Sync backend parity docs / coverage inventory / handoff wording to the current `not_locked + backend_native_fail_closed` state and make the task close-ready.
