<a href="../../../ja/plans/archive/20260312-p1-import-graph-frontend-decomposition.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: Import Graph Frontend Decomposition

Last updated: 2026-03-12

Related TODO:
- `ID: P1-IMPORT-GRAPH-FRONTEND-DECOMPOSITION-01` in `docs/ja/todo/index.md`

Background:
- The relative-import normalization cluster has already been split into dedicated modules, but the import-graph build/analyze/report helpers are still concentrated inside [transpile_cli.py](/workspace/Pytra/src/toolchain/frontends/transpile_cli.py) and [east1_build.py](/workspace/Pytra/src/toolchain/frontends/east1_build.py).
- Module queues, module-id fallback, graph issue/report formatting, and analysis assembly still live too close to frontend entrypoints.
- The representative selfhost / CLI / import-graph regressions already exist, so the next step is to move this cluster into dedicated modules without redesigning the algorithm.

Goal:
- Split the import-graph build/analyze/report cluster into dedicated frontend module(s).
- Shrink `transpile_cli.py` and `east1_build.py` back to orchestration entrypoints.
- Add focused tooling/source contracts so later import-graph fixes stay localized.

In scope:
- Splitting import-graph path / queue / module-id helpers
- Splitting import-graph analysis / report helpers
- Retargeting frontend entrypoints to the split modules
- Preserving focused tooling/source contracts and existing regressions

Out of scope:
- Redesigning the import-graph algorithm
- Adding new relative-import features
- Changing wildcard / duplicate-binding diagnostic contracts
- Adding runtime import

Acceptance criteria:
- A representative import-graph helper cluster no longer lives directly inside `transpile_cli.py` / `east1_build.py`, but in dedicated frontend module(s).
- Focused tooling/source contracts lock the post-split helper ownership.
- Existing import-graph / CLI / selfhost regressions pass.
- `python3 tools/build_selfhost.py` passes.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_import_graph_issue_structure.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_py2x_cli.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_relative_import_normalization_source_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/selfhost -p 'test_prepare_selfhost_source.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

Breakdown:
- [x] [ID: P1-IMPORT-GRAPH-FRONTEND-DECOMPOSITION-01-S1-01] Make the live plan/TODO active and lock the split target cluster plus verification lane.
- [x] [ID: P1-IMPORT-GRAPH-FRONTEND-DECOMPOSITION-01-S2-01] Split path / queue / module-id helpers into dedicated modules and retarget the entrypoint callers.
- [x] [ID: P1-IMPORT-GRAPH-FRONTEND-DECOMPOSITION-01-S2-02] Split analysis / report helpers into dedicated modules and add focused tooling/source contracts.
- [x] [ID: P1-IMPORT-GRAPH-FRONTEND-DECOMPOSITION-01-S3-01] Freeze the residual helper layout in docs/source contracts and close the archive-ready end state.

Decision log:
- 2026-03-12: After closing the relative-import normalization decomposition and the legacy diagnostic cleanup, the remaining import-graph build/analyze/report cluster became the next focused decomposition target. This task is limited to frontend-module split work and explicitly excludes algorithm redesign.
- 2026-03-12: Moved `is_pytra_module_name`, module-id fallback, user-module path resolve, structured import-request helpers, and graph file sorting into `import_graph_frontend_helpers.py`, then retargeted `transpile_cli.py` and `east1_build.py` to import that split module. Selfhost support extraction now reads the new helper module too, so `S2-01` is considered complete.
- 2026-03-12: Moved `split_graph_issue_entry`, `graph_cycle_dfs`, `format_import_graph_report`, `finalize_import_graph_analysis`, `resolve_module_name*`, and `validate_import_graph_or_raise` into `import_graph_analysis_helpers.py`, then retargeted `transpile_cli.py`, `east1_build.py`, `prepare_selfhost_source.py`, and the focused source-contract test to the split layout. This closes `S2-02`.
- 2026-03-12: Froze `import_graph_frontend_helpers.py` and `import_graph_analysis_helpers.py` as the residual helper layout in the source contracts, selfhost extraction guard, and plan, then treated the now-orchestrating `transpile_cli.py` / `east1_build.py` end state as archive-ready.
