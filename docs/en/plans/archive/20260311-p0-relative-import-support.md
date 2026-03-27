<a href="../../../ja/plans/archive/20260311-p0-relative-import-support.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Official Relative Import Support (`from .m import x`)

Last updated: 2026-03-11

Related TODO:
- `docs/en/todo/index.md` item `ID: P0-RELATIVE-IMPORT-SUPPORT-01`

Background:
- The current self-hosted parser rejects `from .xxx import ...` immediately with `relative import is not supported`.
- The frontend CLI maps that parser error to `kind=unsupported_import_form`, which blocks multi-file experiments such as Pytra-NES before codegen.
- Wildcard import is already supported, so relative import is now the main missing piece in the import graph / export table / diagnostics path.
- Accepting the syntax in the parser is not enough; `meta.import_bindings`, `meta.import_symbols`, `qualified_symbol_refs`, and the import graph must all converge on absolute `module_id`s before backends consume the result.

Goal:
- Support `from .m import x`, `from ..pkg import y`, `from . import x`, and `from .m import *` in multi-file transpilation.
- Keep unresolved relative imports fail-closed with `input_invalid`, instead of emitting ambiguous generated code.
- Preserve existing diagnostics and behavior for absolute import, wildcard import, import cycles, missing modules, and duplicate bindings.

Scope:
- Self-hosted parser acceptance for relative `from-import`
- Relative-module normalization across EAST and import metadata
- Import-graph resolution for relative modules
- CLI diagnostic updates
- Representative unit / CLI regressions
- Spec sync in `spec-user.md` and `spec-import.md`

Out of scope:
- Invalid Python syntax such as `import .m`
- Runtime dynamic import (`__import__`, `importlib`)
- Full `__package__` / `__main__` compatibility
- Full namespace-package compatibility

Policy:
- Stage 1 uses static normalization against the importing file path and the entry-root module layout.
- If a relative import escapes above the entry root, it fails closed as `kind=unsupported_import_form`.
- If normalization succeeds but the target module does not exist, it fails as `kind=missing_module`.
- The parser accepts raw relative module text; the frontend rewrites it into absolute `module_id`s before validation and backend handoff.

Acceptance criteria:
- `from .helper import f` succeeds for sibling modules.
- `from ..common import f` normalizes correctly inside nested package-like layouts.
- `from .helper import *` works under the existing wildcard-import contract.
- Root-escape relative imports fail with `kind=unsupported_import_form`.
- Missing-module / missing-symbol / duplicate-binding diagnostics stay consistent with absolute imports.

Checks:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/selfhost -p 'test_prepare_selfhost_source.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

Breakdown:
- [x] [ID: P0-RELATIVE-IMPORT-SUPPORT-01-S1-01] Fix the syntax / diagnostics / root-escape policy for relative imports in plan and spec.
- [x] [ID: P0-RELATIVE-IMPORT-SUPPORT-01-S2-01] Make the self-hosted parser accept relative `from-import` while preserving raw module text and `ImportFrom.level`.
- [x] [ID: P0-RELATIVE-IMPORT-SUPPORT-01-S2-02] Normalize relative modules to absolute `module_id`s during frontend module-map construction and rewrite EAST / import metadata.
- [x] [ID: P0-RELATIVE-IMPORT-SUPPORT-01-S2-03] Update import-graph diagnostics to distinguish root escape from missing modules and fail closed.
- [x] [ID: P0-RELATIVE-IMPORT-SUPPORT-01-S3-01] Add representative CLI / unit regressions for success, missing, duplicate, root escape, and wildcard cases.
- [x] [ID: P0-RELATIVE-IMPORT-SUPPORT-01-S3-02] Sync the import wording in `spec-user.md`, `spec-import.md`, and tutorial docs.

Decision log:
- 2026-03-11: Raised relative import support to `P0`. The first compatibility target is deterministic static normalization under the entry-root module layout, not full Python runtime package semantics.
- 2026-03-11: Completed `S1-01` by fixing the syntax / diagnostics / root-escape policy. Stage 1 canonical surface is `from .m import x` / `from ..pkg import y` / `from . import x` / `from .m import *`; `import .m` stays out of scope; root escape reports `kind=unsupported_import_form`; a missing normalized module reports `kind=missing_module`.
- 2026-03-11: Completed `S2-01` by routing self-hosted `from-import` parsing through a shared helper so `from .helper import f` and `from . import f` are accepted before frontend normalization. The parser preserves raw module text in EAST / import metadata and only adds `ImportFrom.level` at parser time.
- 2026-03-11: Completed `S2-02/S2-03` by normalizing relative `from-import` through the importer path + entry root in the import graph, rewriting `ImportFrom.module` / import metadata to absolute `module_id`s during module-map construction, and classifying root escape as `unsupported_import_form` while routing normalized missing targets to `missing_module`.
- 2026-03-11: Completed `S3-01/S3-02` by adding representative regressions for sibling success, relative wildcard success, missing relative module, duplicate relative binding, and root escape, and by syncing tutorial import wording to the current contract.
