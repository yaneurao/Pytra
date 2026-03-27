<a href="../../../ja/plans/archive/20260311-p0-relative-import-package-root-01.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Stabilize package-style relative-import root inference

Last updated: 2026-03-11

Related TODO:
- `docs/en/todo/index.md` `ID: P0-RELATIVE-IMPORT-PACKAGE-ROOT-01`

Background:
- Current relative-import support accepts sibling imports such as `from .helper import f`, but package-internal parent imports such as `from ..util import g` still fail with `unsupported_import_form`.
- In the current implementation, [transpile_cli.py](/workspace/Pytra/src/toolchain/frontends/transpile_cli.py) `rewrite_relative_imports_in_module_east_map()` and `analyze_import_graph()` treat `entry_path.parent` as the root and do not infer the package root from an `__init__.py` chain.
- Package-style projects such as Pytra-NES rely on `pkg/sub/main.py -> from ..util import ...`, so this gap blocks real experiments.

Goal:
- Infer the package root from the `__init__.py` chain and officially support parent relative imports inside a package during multi-file transpilation.
- Keep root escape fail-closed and preserve the current diagnostics contract.

In scope:
- A shared helper that infers the package root from the entry file
- Updating `rewrite_relative_imports_in_module_east_map()` and `analyze_import_graph()` to use that root
- Representative CLI and metadata regressions for parent relative-import success and root-escape failure
- Keeping TODO / plan / English mirror in sync

Out of scope:
- Changes to the import-graph algorithm itself
- Semantic changes to wildcard or absolute imports
- Namespace-package or `pyproject.toml`-based root inference

Acceptance criteria:
- `pkg/sub/main.py` can successfully transpile `from ..util import f` in multi-file mode.
- Module metadata and import bindings are rewritten to normalized absolute `module_id`s.
- `from ...bad import x` that escapes the package root still fails closed as `unsupported_import_form`.
- Representative CLI / metadata regressions and selfhost build pass.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 test/unit/tooling/test_py2x_cli.py -k relative_import -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k relative_import`
- `python3 tools/build_selfhost.py`
- `python3 tools/check_transpiler_version_gate.py`
- `python3 tools/run_regen_on_version_bump.py --dry-run`
- `git diff --check`

Decision log:
- 2026-03-11: Opened this task after the TODO became empty. A local probe showed that sibling relative imports already work, while `pkg2/sub/main.py -> from ..util import two` still fails with `unsupported_import_form`. v1 only targets package-root inference from an `__init__.py` chain.
- 2026-03-11: Locked the representative gap. `pkg/main.py -> from .helper import f` succeeds, but `pkg/sub/main.py -> from ..util import two` still fails with `unsupported_import_form` because the current root is treated as `entry_path.parent`.
- 2026-03-11: Added `resolve_import_graph_entry_root()` and rewrote `pkg/sub/main.py -> from ..util import two` against the inferred package root `pkg`, while keeping root escape fail-closed as `unsupported_import_form`.
- 2026-03-11: Closed `S3-01` by refreshing docs/archive and moving the package-style parent-relative-import success plus root-escape fail-closed contract into history.

## Breakdown

- [x] [ID: P0-RELATIVE-IMPORT-PACKAGE-ROOT-01-S1-01] Lock the current root-inference gap and representative package layout in the plan/TODO.
- [x] [ID: P0-RELATIVE-IMPORT-PACKAGE-ROOT-01-S2-01] Add the package-root inference helper and switch `rewrite_relative_imports_in_module_east_map()` / `analyze_import_graph()` to it.
- [x] [ID: P0-RELATIVE-IMPORT-PACKAGE-ROOT-01-S2-02] Add representative CLI / metadata regressions for parent relative-import success and root-escape failure.
- [x] [ID: P0-RELATIVE-IMPORT-PACKAGE-ROOT-01-S3-01] Refresh docs / archive and close the task.
