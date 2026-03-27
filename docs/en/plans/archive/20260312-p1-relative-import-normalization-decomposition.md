<a href="../../../ja/plans/archive/20260312-p1-relative-import-normalization-decomposition.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: Relative Import Normalization Decomposition

Last updated: 2026-03-12

Related TODO:
- `ID: P1-RELATIVE-IMPORT-NORMALIZATION-DECOMPOSITION-01` in `docs/ja/todo/index.md`

Background:
- Relative import support itself already exists, and representative regressions already cover `from .helper import f`, `from ..pkg import y`, and `from .. import helper`.
- However, the helper cluster for package-root inference, relative module normalization, and EAST metadata rewriting is still concentrated inside [transpile_cli.py](/workspace/Pytra/src/toolchain/frontends/transpile_cli.py), which keeps the frontend too heavy.
- This cluster is also part of the import-graph / CLI / selfhost contract, so it should now be split into focused modules with focused tests instead of merely remaining "working."

Goal:
- Split the relative import normalization cluster still living in `transpile_cli.py` into dedicated modules.
- Lock package-root/path helpers and relative import semantics with focused tests, while keeping existing import-graph / CLI regressions.
- Shrink the responsibility of `transpile_cli.py` so future relative-import fixes stay localized.

In scope:
- Splitting package-root/path helpers
- Splitting relative-import normalization / rewrite helpers
- Adding focused unit tests and source contracts
- Preserving existing CLI / import-graph / selfhost regressions

Out of scope:
- Adding new relative import features
- Extending namespace package support
- Redesigning the import-graph algorithm itself
- Adding runtime import

Acceptance criteria:
- The relative import normalization helpers no longer live as one large cluster directly inside `transpile_cli.py`, but in dedicated frontend module(s).
- Focused unit tests exist for package-root/path helpers and relative import semantics.
- Existing relative import CLI / import-graph regressions still pass.
- `python3 tools/build_selfhost.py` passes.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_relative_import_semantics.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_py2x_cli.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_import_graph_issue_structure.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

Breakdown:
- [x] [ID: P1-RELATIVE-IMPORT-NORMALIZATION-DECOMPOSITION-01-S1-01] Make the active plan / TODO live and fix the split boundary plus verification lane.
- [x] [ID: P1-RELATIVE-IMPORT-NORMALIZATION-DECOMPOSITION-01-S2-01] Split package-root/path helpers and relative import normalization helpers into dedicated frontend modules, and add focused tests.
- [x] [ID: P1-RELATIVE-IMPORT-NORMALIZATION-DECOMPOSITION-01-S2-02] Retarget EAST rewrite / import-graph callers to the split modules and align source contracts plus selfhost regressions.
- [x] [ID: P1-RELATIVE-IMPORT-NORMALIZATION-DECOMPOSITION-01-S3-01] Lock the residual helper layout in source contracts and docs so the plan can be cleanly closed.

Decision log:
- 2026-03-12: After closing out the relative import support contract, the remaining normalization cluster inside `transpile_cli.py` was promoted as the next focused decomposition target.
- 2026-03-12: In `S2-01`, `relative_import_normalization.py` became the dedicated module while `transpile_cli.py` stayed as a thin re-export surface. Focused common tests lock package-root inference, bare-parent import, missing/root-escape, and EAST metadata rewrite.
- 2026-03-12: In `S2-02`, `east1_build.py` import-graph callers were retargeted to the split module, and a dedicated tooling contract now locks the layout across `transpile_cli.py`, `east1_build.py`, and `relative_import_normalization.py`.
- 2026-03-12: In `S3-01`, the residual live helper layout was frozen behind the dedicated module plus source contract, so the relative import normalization decomposition task became archive-ready.
