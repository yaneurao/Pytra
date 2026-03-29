<a href="../../../ja/plans/archive/20260311-p0-relative-import-project-layout-hardening.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: relative import project layout hardening

Last updated: 2026-03-11

Related TODO:
- `docs/en/todo/index.md` entry `ID: P0-RELATIVE-IMPORT-PROJECT-LAYOUT-HARDENING-01`

Background:
- Relative import itself is already supported, and representative sibling / package-root parent regressions have already been archived.
- Real projects such as Pytra-NES use a project-style layout like `pkg/main.py -> .subpkg.mod -> ..util.bits`, so one-file and two-file cases alone are not enough to catch regressions early.
- The current tests lock `from .helper import f` and `from ..util import two` separately, but there is no single entrypoint smoke that exercises a nested package chain end to end.

Goal:
- Lock a Pytra-NES-like nested package layout as a representative smoke and make the current relative-import contract fail fast at project level.
- Keep root-escape fail-closed behavior and the current diagnostics contract unchanged while making the supported / unsupported boundary explicit.

In scope:
- `py2x.py --target cpp` project-style relative import smoke
- Nested package chain with sibling + parent relative imports
- Residual representative regressions for `from . import module` and root escape
- TODO / plan / English mirror consistency

Out of scope:
- New relative-import semantics
- Namespace packages or `pyproject.toml`-based root inference
- Wildcard import / absolute import / import-graph redesign

Acceptance criteria:
- A representative nested-package smoke containing `from .cpu.runner import run` and `from ..util.bits import low_nibble` passes under `py2x.py --target cpp`.
- `from . import helper` is also locked by a representative regression for the current contract.
- Root escape (`from ...bad import x`) continues to fail closed as `input_invalid(kind=unsupported_import_form)`.
- `python3 tools/check/check_todo_priority.py`, the focused unit tests, `python3 tools/build_selfhost.py`, and `git diff --check` pass.

Verification commands:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_py2x_cli.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/common -p 'test_import_diagnostics.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

Decision log:
- 2026-03-11: The active TODO became empty, so this follow-up was opened for residual relative-import hardening. The priority is not new semantics but lifting a Pytra-NES-style nested package layout into regression coverage.
- 2026-03-11: The first representative smoke is `pkg/nes/main.py -> from .cpu.runner import run`, `pkg/nes/cpu/runner.py -> from ..util.bits import low_nibble`, locked as a successful `py2x.py --target cpp` entrypoint case.
- 2026-03-11: `from . import helper` still failed because the import graph only treated `ImportFrom.module="."` as a dependency and never tried the package-local submodule candidate. Dot-only relative `ImportFrom` forms now flow `.helper` / `..helper` into the graph as package-local submodule candidates.

## Breakdown

- [x] [ID: P0-RELATIVE-IMPORT-PROJECT-LAYOUT-HARDENING-01-S1-01] Lock the current support / residual gap in plan/TODO.
- [x] [ID: P0-RELATIVE-IMPORT-PROJECT-LAYOUT-HARDENING-01-S2-01] Add a project-style nested-package relative import smoke under `py2x.py --target cpp`.
- [x] [ID: P0-RELATIVE-IMPORT-PROJECT-LAYOUT-HARDENING-01-S2-02] Align representative regressions for `from . import module` and root-escape diagnostics with the current contract.
- [x] [ID: P0-RELATIVE-IMPORT-PROJECT-LAYOUT-HARDENING-01-S3-01] Refresh docs / archive and close the task.
