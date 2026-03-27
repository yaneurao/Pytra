<a href="../../../ja/plans/archive/20260312-p0-relative-import-diagnostic-realign.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Realign the relative import diagnostic contract

Last updated: 2026-03-12

Related TODO:
- `docs/ja/todo/index.md` item `ID: P0-RELATIVE-IMPORT-DIAGNOSTIC-REALIGN-01`

Background:
- Relative import itself is already implemented in the current frontend / import-graph flow, and sibling / parent-package / `from . import helper` cases already work.
- However, the diagnostic surface still contains stale `relative import is not supported` and `kind=unsupported_import_form` messages.
- In that state, supported relative imports and fail-closed cases such as root escape / invalid relative imports look identical to users, which makes it look as if relative import as a whole is unsupported.
- That stale messaging is a practical blocker for experiments like `Pytra-NES`, which rely heavily on package-relative imports.

Goal:
- Separate supported relative imports from fail-closed relative imports at the diagnostic layer.
- Stop using blanket `unsupported_import_form` for this lane and define a current contract for relative-import root escape / invalid relative imports.
- Realign representative CLI / import-graph / backend smoke regressions to the current support state.

In scope:
- import diagnostics helpers in `transpile_cli.py`
- relative-import issue kind in import-graph validation / reports
- import diagnostics / import-graph structure / CLI / backend smoke tests
- TODO / plan / English mirror sync

Out of scope:
- adding new relative-import functionality itself
- redesigning wildcard import / duplicate binding / cycle detection
- large carrier renames across the parser / import graph
- extending import syntax acceptance in `core_stmt_parser.py` / `core_module_parser.py`

Acceptance criteria:
- Existing tests for supported relative imports keep passing.
- Fail-closed relative imports such as root escape are reported with a dedicated relative-import kind instead of `unsupported_import_form`.
- `transpile_cli._classify_import_user_error()` and `validate_import_graph_or_raise()` use the same relative-import diagnostic contract.
- Representative unit / CLI / backend regressions are updated to the current contract.
- `docs/ja/todo/index.md` keeps only one-line progress summaries while details stay in this plan's decision log.

Checks:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_import_diagnostics.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_import_graph_issue_structure.py'`
- `PYTHONPATH=src python3 test/unit/tooling/test_py2x_cli.py -k relative_import -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k relative_import`
- `python3 tools/build_selfhost.py`
- `git diff --check`

Decision log:
- 2026-03-12: Opened this as a `P0` task focused on stale diagnostics, not on new relative-import functionality. The priority is `P0` because this is currently blocking user experiments.
- 2026-03-12: In `S2-01`, keep the internal carrier name (`relative_import_entries`) unchanged and switch only the user-facing diagnostic kind to `relative_import_escape` first. Internal field renames stay for later slices.
- 2026-03-12: In `S2-02`, also realign the structured import envelope so that the canonical code/message becomes `relative_import_escape`. The old `unsupported_import_form: relative import is not supported` string remains only as a legacy fallback.
- 2026-03-12: Frontend helpers, import-graph validation, and focused common tests were already aligned to `relative_import_escape`. The remaining mismatch was stale `unsupported_import_form` wording in spec docs and unfinished task markers in TODO/plan.
- 2026-03-12: `S3-01` is limited to wording cleanup in spec / plan / TODO. It does not add new relative-import functionality; the archive-ready condition is a single `relative_import_escape` contract across CLI, import graph, backend smoke, and spec.

## Breakdown

- [x] [ID: P0-RELATIVE-IMPORT-DIAGNOSTIC-REALIGN-01-S1-01] Lock the current stale diagnostics, desired contract, and representative failing surfaces into the plan and TODO.
- [x] [ID: P0-RELATIVE-IMPORT-DIAGNOSTIC-REALIGN-01-S2-01] Switch relative-import root escape to a dedicated diagnostic kind and align the frontend helper, import-graph validation, and focused tests.
- [x] [ID: P0-RELATIVE-IMPORT-DIAGNOSTIC-REALIGN-01-S2-02] Update CLI / backend smoke / import-graph structure tests to the current contract.
- [x] [ID: P0-RELATIVE-IMPORT-DIAGNOSTIC-REALIGN-01-S3-01] Clean up the remaining stale wording and lock the archive-ready end state in the plan.
