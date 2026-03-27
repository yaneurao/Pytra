<a href="../../../ja/plans/archive/20260311-p1-import-graph-issue-structure.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: Structure import-graph issue carriers

Last updated: 2026-03-11

Related TODO:
- `docs/en/todo/archive/20260311.md` `ID: P1-IMPORT-GRAPH-ISSUE-STRUCTURE-01`

Background:
- Import-graph analysis used to keep `relative_imports`, `missing_modules`, and similar issues as string lists in the form `"<file>: <module>"`.
- The frontend then reparsed those strings through [transpile_cli.py](/workspace/Pytra/src/toolchain/frontends/transpile_cli.py) `split_graph_issue_entry()`, leaving both producer and consumer stringly-typed.
- `P1-IMPORT-DIAGNOSTIC-STRUCTURE-01` already moved import diagnostics toward a structured-first seam, so the next step was to give import-graph issues the same treatment and reduce brittle `file: module` reinterpretation.

Goal:
- Move import-graph issue carriers onto a helper-structured seam and reduce stringly logic in `validate_import_graph_or_raise()` and the report formatter.
- Keep the current CLI detail and `--dump-deps` output contract unchanged while only reorganizing the producer/consumer boundary.

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
- 2026-03-11: Opened this task immediately after `P1-IMPORT-DIAGNOSTIC-STRUCTURE-01`. The first stage keeps raw string lists in place, but introduces graph-issue helpers so producer-side formatting and consumer-side splitting are centralized in one seam.
- 2026-03-11: Fixed `make_graph_issue_entry()`, `normalize_graph_issue_entry()`, `format_graph_issue_entry()`, and `dict_any_get_graph_issue_entries()` as the canonical seam, with producers keeping structured entries while exporting legacy text lists for compatibility.
- 2026-03-11: Locked `validate_import_graph_or_raise()`, `format_import_graph_report()`, and the `east1_build` mirror to read structured entries first, and fixed representative regressions so structured keys win over stale legacy text.

## Completed breakdown

- [x] [ID: P1-IMPORT-GRAPH-ISSUE-STRUCTURE-01-S1-01] Inventory the current import-graph issue carriers and lock the staged end state in the plan/TODO.
- [x] [ID: P1-IMPORT-GRAPH-ISSUE-STRUCTURE-01-S2-01] Add shared helpers plus focused unit tests for graph issue entries, and route both `split_graph_issue_entry()` and producer-side formatting through them.
- [x] [ID: P1-IMPORT-GRAPH-ISSUE-STRUCTURE-01-S2-02] Align `validate_import_graph_or_raise()`, `format_import_graph_report()`, and the `east1_build` mirror to the helper-structured seam.
- [x] [ID: P1-IMPORT-GRAPH-ISSUE-STRUCTURE-01-S3-01] Refresh representative CLI/report regressions, docs, and archive state, then close the task.

## Outcome

- Import-graph issues now have a structured-first seam through `missing_module_entries` / `relative_import_entries`, while legacy `missing_modules` / `relative_imports` remain compatibility exports only.
- The report formatter and validator both prefer structured entries while keeping the existing text contract.
- Focused helper tests, CLI relative-import regressions, and representative report/validator regressions all passed before archiving.
