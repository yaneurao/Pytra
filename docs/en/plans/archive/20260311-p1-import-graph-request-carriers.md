<a href="../../../ja/plans/archive/20260311-p1-import-graph-request-carriers.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: structure import-graph request carriers

Last updated: 2026-03-11

Related TODO:
- `docs/en/todo/archive/20260311.md` entry `ID: P1-IMPORT-GRAPH-REQUEST-CARRIERS-01`

Background:
- The current import graph still assumes the string list returned by `collect_import_modules()`, so the difference between `Import` and `ImportFrom`, the imported `symbol`, and dot-only relative-import submodule candidates are discarded too early.
- Even the recent `from . import helper` fix had to special-case `"." -> ".helper"` flattening inside `collect_import_modules()`.
- To improve cases such as `from . import a, b`, package-export vs submodule disambiguation, and graph diagnostics, the graph needs a structured carrier before the final string flatten.

Goal:
- Align import-graph inputs around a structured request carrier with `kind/module/symbol`, and demote the string flatten to a compatibility helper.
- Start by adding the helper plus focused regressions, then move representative graph lanes toward carrier-first behavior bundle by bundle.

In scope:
- Introduce `collect_import_requests()`
- Turn `collect_import_modules()` into a compatibility helper
- Lock a structured-carrier regression for `from . import helper`
- Keep TODO / plan / English mirror consistent

Out of scope:
- New relative-import semantics
- A one-shot rewrite of the entire import graph
- Full resolution of package-export vs submodule ambiguity

Acceptance criteria:
- `collect_import_requests()` preserves `kind/module/symbol` for both `Import` and `ImportFrom`.
- `collect_import_modules()` works as a compatibility wrapper over the structured carrier without breaking existing smoke tests.
- The representative `from . import helper` regression passes in unit and CLI smoke coverage.
- `python3 tools/check/check_todo_priority.py`, focused unit tests, `python3 tools/build_selfhost.py`, and `git diff --check` pass.

Verification commands:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/common -p 'test_import_graph_issue_structure.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_py2x_cli.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

Decision log:
- 2026-03-11: While fixing `from . import helper`, it became clear that the import graph still only saw a flattened module string. The follow-up will therefore introduce a structured request helper first instead of attempting a full graph rewrite immediately.
- 2026-03-11: `S2-02` switched both `analyze_import_graph()` and `east1_build._analyze_import_graph_impl()` to a carrier-first loop over `collect_import_requests()` + `collect_import_request_modules()`, and locked representative `from . import helper` graph regressions in both lanes.
- 2026-03-11: Once the graph lane and the `east1_build` mirror both used the request carrier directly, the remaining work was only docs / archive closeout, so the task was archived.

## Breakdown

- [x] [ID: P1-IMPORT-GRAPH-REQUEST-CARRIERS-01-S1-01] Lock the current string-flatten gap and the staged end state in plan/TODO.
- [x] [ID: P1-IMPORT-GRAPH-REQUEST-CARRIERS-01-S2-01] Add `collect_import_requests()` plus focused regressions and demote `collect_import_modules()` to a compatibility helper.
- [x] [ID: P1-IMPORT-GRAPH-REQUEST-CARRIERS-01-S2-02] Move representative import-graph / east1_build lanes to carrier-first behavior.
- [x] [ID: P1-IMPORT-GRAPH-REQUEST-CARRIERS-01-S3-01] Refresh docs / archive and close the task.
