<a href="../../../ja/plans/archive/20260312-p1-relative-import-longtail-bundle.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: relative import long-tail bundle rollout

Last updated: 2026-03-12

Related TODO:
- `ID: P1-RELATIVE-IMPORT-LONGTAIL-BUNDLE-01` in `docs/en/todo/archive/20260312.md`

Background:
- After the second-wave rollout was archived, `lua/php/ruby` remained as the last long-tail relative-import backends.
- Before claiming support, the representative relative-import project was fixed as explicit backend-native rejection, so the coverage inventory now preserves an archived `fail_closed_locked + backend_native_fail_closed` baseline.
- The current live handoff has moved on to the long-tail support rollout, while this archived bundle remains as the fail-closed baseline and handoff history.

Goal:
- Fix the archived long-tail fail-closed baseline for `lua/php/ruby` as the representative contract.
- Preserve the archived bundle handoff that connects backend coverage / second-wave handoff / backend-parity docs to the next support rollout.

Scope:
- Lock the representative fail-closed regressions and the archived bundle contract
- Sync backend coverage / second-wave handoff / backend-parity docs to the long-tail baseline
- Hand off to `P1-RELATIVE-IMPORT-LONGTAIL-SUPPORT-01` as the active follow-up

Out of scope:
- Implementing relative-import support for Lua / PHP / Ruby backends
- Changing relative-import semantics
- Adding support claims

Acceptance criteria:
- The archived bundle contract fixes `lua/php/ruby` as a `fail_closed_locked + backend_native_fail_closed` baseline.
- Backend parity docs / coverage inventory record both the archived long-tail baseline and the active support rollout handoff.
- The archived bundle checker and matching unit tests pass.

Verification commands:
- `python3 tools/check/check_relative_import_backend_coverage.py`
- `python3 tools/check/check_relative_import_longtail_bundle_contract.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_check_relative_import_backend_coverage.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_check_relative_import_longtail_bundle_contract.py'`
- `python3 tools/check/check_todo_priority.py`
- `git diff --check`

Decision log:
- 2026-03-12: For `lua/php/ruby`, the representative relative-import project was first fixed as explicit backend-native rejection, and the resulting `fail_closed_locked + backend_native_fail_closed` baseline is kept as an archived bundle.
- 2026-03-12: The active follow-up moved to `P1-RELATIVE-IMPORT-LONGTAIL-SUPPORT-01` / `longtail_relative_import_support_rollout`, while this archived bundle now keeps only the current baseline and handoff history.

## Breakdown

- [x] [ID: P1-RELATIVE-IMPORT-LONGTAIL-BUNDLE-01] Fixed the long-tail bundle live handoff and representative contract.
- [x] [ID: P1-RELATIVE-IMPORT-LONGTAIL-BUNDLE-01-S1-01] Added the live plan / TODO / contract / checker and switched the coverage / second-wave handoff / backend-parity docs to the long-tail bundle.
- [x] [ID: P1-RELATIVE-IMPORT-LONGTAIL-BUNDLE-01-S2-01] Added representative fail-closed regressions for `lua/php/ruby` and fixed the current non-support contract.
- [x] [ID: P1-RELATIVE-IMPORT-LONGTAIL-BUNDLE-01-S2-02] Made the task close-ready by documenting the canonical fail-closed end state instead of widening representative transpile smoke.
- [x] [ID: P1-RELATIVE-IMPORT-LONGTAIL-BUNDLE-01-S3-01] Aligned docs / tests / handoff wording to the current long-tail state and closed the task.
