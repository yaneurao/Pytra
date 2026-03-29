<a href="../../ja/plans/p2-wildcard-import-support.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P2: Official Support for `from ... import *` (Wildcard Import)

Last updated: 2026-03-02

Related TODO:
- `ID: P2-WILDCARD-IMPORT-01` in `docs/ja/todo/index.md`

Background:
- The current self-hosted parser accepts `from M import *` and keeps `binding_kind=wildcard`, but resolution/expansion is unimplemented, leaving undefined symbols in generated code.
- Existing CLI regression tests still expect `from M import *` as `input_invalid`, causing contract mismatch between implementation and tests.
- Documentation also has inconsistent treatment of wildcard imports; spec, implementation, and tests must be aligned to one contract.

Goal:
- Resolve `from M import *` consistently in multi-file conversion and safely pass it to backends, equivalent to normal `from M import name`.
- For unresolvable cases (e.g., publicly exported symbols cannot be statically fixed), return fail-closed `input_invalid` and avoid emitting invalid generated code.

Scope:
- Add wildcard expansion rules to import graph / export table
- Resolve wildcard bindings while building `meta.import_bindings` / `import_symbols`
- Update CLI error handling contract (from unsupported to resolution-failure errors)
- Wildcard import regression tests (unit + multi-file transpile)
- Spec synchronization (`spec-user.md` / `spec-import.md`)

Out of scope:
- Support for relative imports (`from .m import x`)
- Dynamic imports (`__import__`) and runtime-dependent lazy resolution
- Optimization of normal imports unrelated to wildcard imports

Acceptance criteria:
- In multi-file inputs containing `from helper import *`, public symbol references are resolved correctly.
- Same-name symbol conflicts (e.g., `from a import *` + `from b import *`) fail closed as `input_invalid(kind=duplicate_binding)`.
- Unresolvable wildcards (public exports cannot be fixed statically) stop as `input_invalid` without emitting code with unresolved references.
- Existing import regressions (missing module / cycle / relative import) are not broken.

Verification commands (planned):
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_features.py' -v`
- `python3 tools/check/check_py2cpp_transpile.py`
- `python3 tools/check/check_py2rs_transpile.py`

Decision log:
- 2026-03-01: Based on user direction, filed P2 with policy to make `from ... import *` "officially supported + fail-closed when unresolved" instead of rejecting.
- 2026-03-02: Implemented wildcard resolution in `validate_from_import_symbols_or_raise`; unified contract so non-statically-determinable `__all__` fails closed with `kind=unresolved_wildcard`.
- 2026-03-02: Reflected wildcard expansion results into `meta.import_symbols` / `meta.qualified_symbol_refs` / `meta.import_resolution.qualified_refs`, making backend reference resolution available via existing paths.
- 2026-03-02: Added wildcard happy-path/conflict/unresolved unit+CLI regressions to `test_py2cpp_features`, and passed `discover -k validate_from_import_symbols_or_raise` and `discover -k from_import_star`.
- 2026-03-02: Updated `docs/ja/spec/spec-import.md` and `docs/en/spec/spec-import.md` / `docs/en/spec/spec-user.md`, documenting official support for `from ... import *` and `unresolved_wildcard` contract.

## Breakdown

- [x] [ID: P2-WILDCARD-IMPORT-01-S1-01] Specify public-symbol determination rules for wildcard imports (`__all__` priority, public names when undefined).
- [x] [ID: P2-WILDCARD-IMPORT-01-S1-02] Organize which existing import diagnostic contract to align with (unsupported/duplicate/missing) and fix error classification.
- [x] [ID: P2-WILDCARD-IMPORT-01-S2-01] Build wildcard expansion info in import graph/export table and reflect it into `meta.import_bindings` and resolution tables.
- [x] [ID: P2-WILDCARD-IMPORT-01-S2-02] Detect same-name conflicts, non-public names, and unresolved wildcards fail-closed, returning `input_invalid`.
- [x] [ID: P2-WILDCARD-IMPORT-01-S2-03] Update CLI wildcard exception branches and regression expectations to the "official support" contract.
- [x] [ID: P2-WILDCARD-IMPORT-01-S3-01] Add unit/integration tests (`from helper import *` happy path + conflict/failure paths) to lock recurrence detection.
- [x] [ID: P2-WILDCARD-IMPORT-01-S3-02] Synchronize descriptions in `spec-user.md` / `spec-import.md` / TODO with implementation contracts.
