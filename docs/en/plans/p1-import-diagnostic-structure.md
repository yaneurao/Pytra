# P1: Structure Import Diagnostics

Last updated: 2026-03-11

Related TODO:
- `docs/ja/todo/index.md` `ID: P1-IMPORT-DIAGNOSTIC-STRUCTURE-01`

Background:
- Diagnostics around relative imports, wildcard imports, and duplicate import bindings still depend on substring matching of English error text inside [transpile_cli.py](/workspace/Pytra/src/toolchain/frontends/transpile_cli.py) `load_east_document()`.
- Parser-side feature support has improved, but the frontend transport remains brittle: changing parser wording can silently break the CLI contract.
- `duplicate import binding` in particular originates from parser/import semantics, so it should eventually move to a structured parser-to-frontend envelope.

Goal:
- Centralize frontend import-diagnostic classification in one place without breaking the current user-facing contract.
- Create a seam that allows parser-side import diagnostics to move to structured envelopes incrementally.

In scope:
- Helper-izing import exception classification in `transpile_cli.load_east_document()`
- Adding focused unit tests for import diagnostics
- Preparing structured duplicate-binding diagnostics on the parser/import-semantics side
- Keeping TODO / plan / English mirror in sync

Out of scope:
- New relative-import or wildcard-import features
- Changes to missing-module / cycle / import-graph algorithms
- Redesigning all syntax-error transport beyond import diagnostics

Acceptance criteria:
- The current CLI category/detail contract for `wildcard`, `relative import`, and `duplicate_binding` is preserved while `load_east_document()` routes import classification through a single helper seam.
- Focused unit tests directly cover the import diagnostics helper.
- The next slice for structured duplicate-binding transport from parser/import semantics is explicitly recorded in the plan.
- Existing relative-import and wildcard-import regressions continue to pass.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_import_diagnostics.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_py2x_cli.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

Decision log:
- 2026-03-11: After the TODO became empty, opened `P1` for structured import diagnostics as the next step after relative-import / wildcard-import support. v1 keeps the current CLI contract and first centralizes frontend substring matching behind a helper seam.
- 2026-03-11: Completed `S2-01` by routing import exception classification in `load_east_document()` through `_classify_import_user_error()` and locking the wildcard / relative / duplicate-binding CLI contract with focused unit coverage plus one integration test.
- 2026-03-11: Completed `S2-02` by moving duplicate import bindings only to a parser-side structured envelope (`_make_import_build_error` / `parse_import_build_error`). The frontend now prefers that structured payload and reclassifies it back into the current CLI contract, while keeping the legacy string fallback for later cleanup.

## Breakdown

- [x] [ID: P1-IMPORT-DIAGNOSTIC-STRUCTURE-01-S1-01] Inventory the current import-diagnostic transport and lock the staged end state in the plan/TODO.
- [x] [ID: P1-IMPORT-DIAGNOSTIC-STRUCTURE-01-S2-01] Centralize import exception classification in `transpile_cli.load_east_document()` behind one helper and add focused unit tests.
- [x] [ID: P1-IMPORT-DIAGNOSTIC-STRUCTURE-01-S2-02] Add a seam so duplicate import bindings can be transported from parser/import semantics as a structured envelope.
- [ ] [ID: P1-IMPORT-DIAGNOSTIC-STRUCTURE-01-S3-01] Clean up the remaining ad hoc string dependencies in import diagnostics and reach an archivable end state.
