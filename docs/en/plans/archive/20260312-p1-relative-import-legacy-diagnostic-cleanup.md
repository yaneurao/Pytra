# P1: Relative Import Legacy Diagnostic Cleanup

Last updated: 2026-03-12

Related TODO:
- `ID: P1-RELATIVE-IMPORT-LEGACY-DIAGNOSTIC-CLEANUP-01` in `docs/ja/todo/index.md`

Background:
- The current relative-import contract already uses `relative_import_escape` as the canonical diagnostic kind.
- However, [transpile_cli.py](/workspace/Pytra/src/toolchain/frontends/transpile_cli.py) still contained fallback logic that rewrote the old `unsupported_import_form: relative import is not supported` wording into `relative_import_escape`.
- In the live codebase there is effectively no producer left that emits `unsupported_import_form` for relative-import failures, so the old wording had become noise apart from one focused negative test.

Goal:
- Remove the legacy `unsupported_import_form` fallback from the live relative-import diagnostic contract.
- Align focused common/tooling tests on the current `relative_import_escape` surface.
- Keep the live docs / plans / source contracts on one canonical wording for relative-import diagnostics.

In scope:
- Removing the legacy relative-import fallback from `transpile_cli.py`
- Updating focused tests that still assumed the old relative-import wording
- Locking the current `relative_import_escape` diagnostic contract in docs/source contracts

Out of scope:
- Extending relative-import functionality itself
- Changing the import-graph algorithm
- Rewriting archived historical docs
- Redesigning wildcard / duplicate-binding diagnostics

Acceptance criteria:
- No live source path still treats `unsupported_import_form` as the relative-import contract.
- Focused import-diagnostic / CLI regressions pass on the current `relative_import_escape` surface.
- `python3 tools/build_selfhost.py` passes.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_import_diagnostics.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_py2x_cli.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k relative_import`
- `python3 tools/build_selfhost.py`
- `git diff --check`

Breakdown:
- [x] [ID: P1-RELATIVE-IMPORT-LEGACY-DIAGNOSTIC-CLEANUP-01-S1-01] Lock the live plan/TODO and inventory the remaining producer/consumer paths for the legacy relative-import fallback.
- [x] [ID: P1-RELATIVE-IMPORT-LEGACY-DIAGNOSTIC-CLEANUP-01-S2-01] Remove the relative-import `unsupported_import_form` / legacy-message fallback from `transpile_cli.py` and realign the focused import-diagnostic tests to the current contract.
- [x] [ID: P1-RELATIVE-IMPORT-LEGACY-DIAGNOSTIC-CLEANUP-01-S2-02] Align CLI / backend smoke / source contracts on the current `relative_import_escape` wording and lock the archive-ready end state.

Decision log:
- 2026-03-12: After archiving the relative import normalization decomposition task, the next cleanup target became the legacy `unsupported_import_form` relative-import fallback. The live producer is effectively gone and only focused negative tests still referenced the old wording.
- 2026-03-12: In `S1-01`, the inventory confirmed that the live producer is already `relative_import_escape`; the legacy relative-import lane only remained in `transpile_cli.py` fallback logic and a direct-injection case in `test_import_diagnostics.py`.
- 2026-03-12: In `S2-01`, the `unsupported_import_form` / `relative import is not supported` fallback was removed from `transpile_cli.py`, and the focused import-diagnostic test was switched to a `None` expectation for that no-longer-supported legacy input.
- 2026-03-12: In `S2-02`, CLI / backend smoke / source contracts were aligned on the `relative_import_escape` wording, leaving the legacy wording only in a negative regression and fixing the archive-ready end state.
