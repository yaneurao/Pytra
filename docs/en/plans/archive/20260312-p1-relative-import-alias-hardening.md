<a href="../../../ja/plans/archive/20260312-p1-relative-import-alias-hardening.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: Lock the representative contract for aliased relative imports

Last updated: 2026-03-12

Related TODO:
- `ID: P1-RELATIVE-IMPORT-ALIAS-HARDENING-01` in `docs/ja/todo/index.md`

Background:
- Sibling / parent relative `from-import` is already implemented, and `from .helper import f`, `from ..util import two`, and `from .. import helper` are covered by representative regressions.
- However, relative imports that use `as` aliases are not yet fully closed out in docs and focused tests.
- In nested package layouts such as Pytra-NES, patterns like `from .. import helper as h` and `from ..helper import f as g` are realistic, so leaving them without locked regressions makes regressions slower to detect.

Goal:
- Lock the current support for aliased relative `from-import` across the import graph, CLI, C++ multi-file smoke, and spec/support matrix.

Scope:
- `from .helper import f as g`
- `from ..helper import f as g`
- `from .. import helper as h`
- Alias carriers in import graph / module metadata
- `py2x.py --target cpp` single-file / multi-file regressions
- Representative examples in support matrix / import spec

Out of scope:
- New relative import implementation
- Python-illegal syntax such as `import .m`
- New wildcard import functionality
- Changing relative-import root-escape policy

Acceptance criteria:
- `from .. import helper as h` passes as current support in import graph and CLI / C++ smoke.
- `from ..helper import f as g` and `from .helper import f as g` pass as current support in CLI / C++ smoke.
- In import graph / metadata, module aliases normalize to `binding_kind=module`, and symbol aliases normalize through `import_symbols`.
- Spec / support matrix explicitly mention the alias representative cases and do not contradict the implementation contract.

Verification commands:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/common -p 'test_relative_import_semantics.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/common -p 'test_import_graph_issue_structure.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_py2x_cli.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_py2cpp_features.py' -k relative_import_alias`
- `git diff --check`

Decision log:
- 2026-03-12: After TODO became empty, filed this `P1` follow-up to lock the current relative-import contract through Pytra-NES-style alias cases.

## Breakdown

- [x] [ID: P1-RELATIVE-IMPORT-ALIAS-HARDENING-01-S1-01] Lock the target contract and representative scope for aliased relative imports in the plan / TODO.
- [x] [ID: P1-RELATIVE-IMPORT-ALIAS-HARDENING-01-S2-01] Lock module-alias and symbol-alias metadata carriers with focused import-graph / normalization tests.
- [x] [ID: P1-RELATIVE-IMPORT-ALIAS-HARDENING-01-S2-02] Lock current support for aliased relative imports in `py2x.py` and C++ multi-file smoke tests.
- [x] [ID: P1-RELATIVE-IMPORT-ALIAS-HARDENING-01-S3-01] Sync representative alias cases into `spec-import` and the C++ support matrix.

- 2026-03-12: Verified that the current implementation already accepts `from .. import helper as h` and `from ..helper import f as g`, then added import-graph, CLI, and C++ multi-file build/run regressions to close `S2-01` and `S2-02`.
- 2026-03-12: Updated `validate_from_import_symbols_or_raise()` to normalize relative `module_id` values against the importer's `__init__.py` chain as well, so focused import-graph cases that still carry raw relative module ids also converge to absolute module ids for aliased symbol bindings.
- 2026-03-12: Added aliased representative cases to `spec-import` and the C++ support matrix, closing `from .. import helper as h` / `from ..helper import f as g` as current-support docs contracts.
