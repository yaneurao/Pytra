<a href="../../../ja/plans/archive/20260311-p1-relative-import-closeout.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: Align the current relative-import contract across entrypoints, docs, and smoke

Last updated: 2026-03-11

Related TODO:
- `docs/ja/todo/index.md` `ID: P1-RELATIVE-IMPORT-CLOSEOUT-01`

Background:
- `P0-RELATIVE-IMPORT-SUPPORT-01` already implemented relative `from-import`, and current HEAD accepts `from .helper import f`, `from ..pkg import y`, `from . import x`, and `from .helper import *`.
- However, parts of the support matrix are stale: [docs/ja/language/cpp/spec-support.md](/workspace/Pytra/docs/ja/language/cpp/spec-support.md) and its English mirror still describe relative and wildcard imports as unsupported.
- In addition, `py2x.py` has no representative relative-import regression, so experiments such as Pytra-NES can still look blocked even though the feature already works.

Goal:
- Reflect the current relative-import contract in `py2x.py` entrypoint regressions and in the support matrix.
- Remove stale “unsupported” claims and make regressions fail fast if relative import support breaks again.

Scope:
- `test/unit/tooling/test_py2x_cli.py`
- `docs/ja/language/cpp/spec-support.md`
- `docs/en/language/cpp/spec-support.md`
- `docs/ja/todo/index.md`
- `docs/en/todo/index.md`

Out of scope:
- Adding new import syntax
- Python-illegal syntax such as `import .m`
- Full `__package__` / namespace package compatibility
- New wildcard-import functionality

Acceptance criteria:
- A representative `py2x.py --target cpp` regression exists for sibling relative import success.
- A representative `py2x.py --target cpp` regression exists for root-escape relative import failing closed with `kind=unsupported_import_form`.
- The C++ support matrix rows for relative import and wildcard import match the current contract.
- Progress memos stay compressed to one-line cluster summaries.

Checks:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_py2x_cli.py' -k relative_import`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k relative`
- `git diff --check`

Breakdown:
- [x] [ID: P1-RELATIVE-IMPORT-CLOSEOUT-01-S1-01] Fix the current relative-import contract and stale surfaces in the plan / TODO.
- [x] [ID: P1-RELATIVE-IMPORT-CLOSEOUT-01-S2-01] Add representative relative-import regressions for the `py2x.py` entrypoint.
- [x] [ID: P1-RELATIVE-IMPORT-CLOSEOUT-01-S2-02] Sync the C++ support matrix rows for relative and wildcard import to the current contract.
- [x] [ID: P1-RELATIVE-IMPORT-CLOSEOUT-01-S3-01] Re-run targeted regressions and close the task with docs / archive updates.

Decision log:
- 2026-03-11: The active TODO was empty, so this follow-up was opened. Relative import itself is already implemented, so this task focuses on entrypoint regressions and stale docs rather than new parser work.
- 2026-03-11: Added representative `py2x.py --target cpp` regressions for sibling relative-import success and root-escape fail-closed (`kind=unsupported_import_form`) in `test_py2x_cli.py`.
- 2026-03-11: Synced the C++ support-matrix rows so relative import is marked `supported` and wildcard import is marked `partial` with unresolved wildcard fail-closed behavior.
- 2026-03-11: With the targeted regressions and support-matrix wording aligned to the current contract, this close-out task was archived and future readers should refer back to `P0-RELATIVE-IMPORT-SUPPORT-01` together with this note.
