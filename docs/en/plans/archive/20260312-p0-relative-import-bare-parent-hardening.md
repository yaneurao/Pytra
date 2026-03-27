<a href="../../../ja/plans/archive/20260312-p0-relative-import-bare-parent-hardening.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: `from .. import helper` Relative Import Hardening

Last updated: 2026-03-12

Related TODO:
- `ID: P0-RELATIVE-IMPORT-BARE-PARENT-01` in `docs/ja/todo/archive/20260312.md`

Background:
- Relative `from-import` support already exists, and representative tests already cover `from .helper import f`, `from ..pkg import y`, and `from . import helper`.
- However, the form `from .. import helper`, which binds a submodule directly from the parent package, is implemented but not called out clearly in the current spec, tutorial, or support matrix.
- In package-local multi-file projects such as Pytra-NES, `from .. import helper` is a natural form. Leaving it as a behavior that only happens to work makes it easy to regress.
- When implementation is ahead of the spec, users interpret the feature as unsupported. At this stage the parser / frontend / import graph / CLI / C++ multi-file smoke contract should be aligned.

Goal:
- Make `from .. import helper` an explicit part of the currently supported relative import contract.
- Add representative regressions for CLI, import graph, and C++ multi-file conversion so project-style package layouts cannot silently regress.
- Sync docs, spec, support matrix, and tutorial with the current implementation so the feature no longer looks unsupported.

In scope:
- User-facing contract wording for relative imports
- Representative `py2x.py --target cpp` success regression
- Representative import-graph / carrier regression
- Syncing the C++ support matrix, tutorial, and spec

Out of scope:
- New relative import implementation
- Illegal Python syntax such as `import .m`
- Runtime dynamic import
- Full namespace-package compatibility

Acceptance criteria:
- There is a representative test where `pkg/sub/main.py -> from .. import helper` succeeds under `py2x.py --target cpp`.
- There is a representative test showing that import graph / validation treats `from .. import helper` as a package-local submodule import.
- `spec-import.md`, `spec-user.md`, the tutorial, and the C++ support matrix explicitly document `from .. import helper` as a currently supported form.
- Root-escape fail-closed behavior (`from ...oops import x`) and existing relative import regressions remain intact.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_py2x_cli.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_import_graph_issue_structure.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k relative`
- `git diff --check`

Breakdown:
- [x] [ID: P0-RELATIVE-IMPORT-BARE-PARENT-01-S1-01] Fix the current supported contract for `from .. import helper` in the plan/spec.
- [x] [ID: P0-RELATIVE-IMPORT-BARE-PARENT-01-S2-01] Add CLI / import-graph representative regressions that lock package-parent bare import success.
- [x] [ID: P0-RELATIVE-IMPORT-BARE-PARENT-01-S2-02] Sync C++ multi-file smoke and support-matrix/tutorial wording with the current contract.

Decision log:
- 2026-03-12: Created as a new P0 after the TODO list became empty. A probe showed that `pkg/sub/main.py -> from .. import helper` already succeeds, so this is treated as a contract close-out task rather than a new implementation task.
- 2026-03-12: `S1-01` added `from .. import helper` to the accepted-form lists in the spec, tutorial, and support matrix so the current support no longer looks unsupported.
- 2026-03-12: `S2-01` added representative success regressions to `test_py2x_cli.py` and `test_import_graph_issue_structure.py`, fixing package-parent bare import support at both the CLI and import-graph layers.
- 2026-03-12: `S2-02` added a C++ multi-file regression to `test_py2cpp_features.py`, locking the current generated `main.cpp` call path for `from .. import helper` as `helper.f()`.
