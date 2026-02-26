# P3: Resume microgpt Source-Preservation Tasks

Last updated: 2026-02-26

Related TODO:
- `ID: P3-MSP-REVIVE-01` in `docs-ja/todo/index.md`

Background:
- `P3-MSP-01` to `P3-MSP-09` were moved to archive and are no longer visible from active TODO.
- Per user request, microgpt tasks should be restored as unfinished TODO items to resume ongoing operation.
- To avoid conflicts with existing history, resumed work is managed under new IDs.

Goal:
- Restore preservation/regression-monitoring tasks based on `materials/refs/microgpt/microgpt-20260222.py` back into active TODO operations.

In scope:
- Verification path for transpile / compile / run on original microgpt input
- Regression stage classification and recurrence-detection procedure
- TODO/context synchronization in `docs-ja`

Out of scope:
- microgpt model-quality or training-convergence improvements
- Expansion to non-microgpt large cases

Acceptance criteria:
- Resumed microgpt tasks are trackable in `docs-ja/todo/index.md`.
- Verification commands and expected outcomes for original input are re-confirmed.
- The mapping between archive history (old IDs) and resumed tasks (new IDs) is traceable in docs.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_microgpt_original_py2cpp_regression.py --expect-stage any-known`
- `python3 src/py2cpp.py materials/refs/microgpt/microgpt-20260222.py -o work/out/microgpt_revival.cpp`

Decision log:
- 2026-02-26: Per user request, decided to restore archive-migrated microgpt tasks into active TODO under new IDs.

## Breakdown

- [ ] [ID: P3-MSP-REVIVE-01-S1-01] Create a mapping table between archived `P3-MSP-*` history and resumed scope, and clarify resumed targets.
- [ ] [ID: P3-MSP-REVIVE-01-S1-02] Re-confirm current transpile / syntax-check / execution steps for original `microgpt` input and lock expected values.
- [ ] [ID: P3-MSP-REVIVE-01-S2-01] Revisit `check_microgpt_original_py2cpp_regression.py` against operation baseline and update recurrence-detection conditions.
- [ ] [ID: P3-MSP-REVIVE-01-S2-02] Prepare an operational log template for reclassifying failures into parser / lower / runtime responsibilities.
- [ ] [ID: P3-MSP-REVIVE-01-S3-01] Add microgpt-specific fixtures/smoke if needed and stabilize CI monitoring.
- [ ] [ID: P3-MSP-REVIVE-01-S3-02] Document migration-back conditions (done definition) for returning resumed tasks to archive.
