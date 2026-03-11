# P1: Structure import-graph issue carriers

Last updated: 2026-03-11

Related TODO:
- `docs/en/todo/index.md` `ID: P1-IMPORT-GRAPH-ISSUE-STRUCTURE-01`

Background:
- Import-graph analysis still stores `relative_imports`, `missing_modules`, and similar issues as string lists in the form `"<file>: <module>"`.
- The frontend later reparses those strings through [transpile_cli.py](/workspace/Pytra/src/toolchain/frontends/transpile_cli.py) `split_graph_issue_entry()`, so both producer and consumer remain stringly-typed.
- `P1-IMPORT-DIAGNOSTIC-STRUCTURE-01` already moved import diagnostics toward a structured-first seam, so the next step is to give import-graph issues the same treatment and reduce brittle `file: module` reinterpretation.

Goal:
- Move import-graph issue carriers onto a helper-structured seam and reduce stringly logic in `validate_import_graph_or_raise()` and the graph report formatter.
- Keep the current CLI details and `--dump-deps` report output unchanged while only reorganizing the producer/consumer boundary.

In scope:
- Add helper APIs for import-graph issue entries
- Normalize representative carriers for `relative_imports`, `missing_modules`, `cycles`, and `reserved_conflicts`
- Add focused unit tests and source-contract coverage
- Keep TODO / plan / English mirror in sync

Out of scope:
- Changes to the import-graph algorithm itself
- Semantic changes to relative-import, missing-module, or cycle detection
- A full redesign of all import diagnostics

Acceptance criteria:
- Direct `"<file>: <module>"` concatenation and reparsing for graph issues is centralized behind helper APIs.
- `validate_import_graph_or_raise()` and `format_import_graph_report()` keep their current output contract.
- Focused unit tests cover the helper directly, and existing representative CLI/report regressions continue to pass.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_import_graph_issue_structure.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_py2x_cli.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

Decision log:
- 2026-03-11: Opened this task immediately after `P1-IMPORT-DIAGNOSTIC-STRUCTURE-01`. The first stage keeps raw string lists in place, but introduces import-graph helper APIs so producer-side formatting and consumer-side splitting are centralized in one seam.

## Breakdown

- [ ] [ID: P1-IMPORT-GRAPH-ISSUE-STRUCTURE-01-S1-01] Inventory the current import-graph issue carriers and lock the staged end state in the plan/TODO.
- [ ] [ID: P1-IMPORT-GRAPH-ISSUE-STRUCTURE-01-S2-01] Add shared helpers plus focused unit tests for graph issue entries, and route both `split_graph_issue_entry()` and producer-side formatting through them.
- [ ] [ID: P1-IMPORT-GRAPH-ISSUE-STRUCTURE-01-S2-02] Align `validate_import_graph_or_raise()`, `format_import_graph_report()`, and the `east1_build` mirror to the helper-structured seam.
- [ ] [ID: P1-IMPORT-GRAPH-ISSUE-STRUCTURE-01-S3-01] Refresh representative CLI/report regressions, docs, and archive state, then close the task.
