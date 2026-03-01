# P2: Minimal Import Generation via EAST Resolution Data + CodeEmitter Dependency Collection

Last updated: 2026-02-28

Related TODO:
- `ID: P2-EAST-IMPORT-RESOLUTION-01` in `docs/ja/todo/index.md`

Background:
- Some backends always emit fixed `import` / `using` / `#include` strings, requiring dummy code to avoid unused dependency warnings (e.g., Go `var _ = math.Pi`).
- Dependency determination is currently scattered per emitter, and implementation policy is not aligned across languages.
- The `CodeEmitter` base has mechanisms to read `meta.import_bindings` / `qualified_symbol_refs`, but there is still no common API for node-level resolution info and import collection.

Objective:
- Keep "which identifier/call originates from which import" at EAST level, and aggregate dependent modules in `CodeEmitter` base.
- Make each language emitter responsible only for mapping "dependency key -> language-specific import statement," and generate minimal imports under a common policy.

Scope:
- Add import resolution data to EAST3 node attributes or side tables
- Dependency collection APIs in `src/pytra/compiler/east_parts/code_emitter.py` (`register/finalize`)
- Import output paths in each backend emitter (inventory and staged migration for fixed import removal)
- Import regression tests (no unused imports, emit only required imports)

Out of scope:
- Non-import performance topics such as image runtime or numeric optimization
- Changes to existing language semantics (operator behavior, type rules)
- Fully migrating all backends in one PR

Acceptance Criteria:
- Import resolution info (`resolved_import` equivalent) is referenceable on EAST side.
- `CodeEmitter` base provides a single dependency collection API with deduplication and stable ordering.
- In pilot backend(s) (at least Go), remove fixed imports and dummy unused-avoidance code, and emit only required imports.
- Regression tests can detect both "no unused imports" and "no missing required imports."

Validation Commands (planned):
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2go_smoke.py' -v`
- `python3 tools/check_py2go_transpile.py`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/check_py2java_transpile.py`

Decision Log:
- 2026-02-28: Per user instruction, filed P2 plan to determine import dependencies via "EAST resolution data + CodeEmitter base aggregation."
- 2026-03-01: Introduced `meta.import_resolution` (`schema_version=1`) and made `bindings` / `qualified_refs` the source of truth (legacy `import_bindings` / `qualified_symbol_refs` kept for compatibility).
- 2026-03-01: Updated `CodeEmitter.load_import_bindings_from_meta()` / `_resolve_imported_symbol()` to prioritize `import_resolution` and fallback to legacy keys when missing, under fail-closed policy.
- 2026-03-01: Fixed condition that parser-recorded missing/invalid values are not promoted into resolvable entries (empty/missing values are treated as unresolved), preserving compatibility with existing behavior.
- 2026-03-01: Added dependency collection API to `CodeEmitter` base (`require_dep` / `require_dep_any` / `require_deps` / `finalize_deps`), sharing deduplication and stable ordering (default sort).
- 2026-03-01: Connected Go native emitter to `CodeEmitter` dependency collection API and migrated `math` import registration to AST-scan-on-demand.
- 2026-03-01: Removed `var _ = math.Pi` from Go output and confirmed zero residue after regenerating `sample/go`.
- 2026-03-01: Passed `test_py2go_smoke.py` (11 tests). `check_py2go_transpile.py` keeps known 4 fails for `Try/Yield/Swap` (out of scope for this task).
- 2026-03-01: As import regression, fixed in `test_py2go_smoke.py` that "no import when math unused" and "import only when math used"; connected recurrence prevention to CI path with `sample/go` regeneration.

## Breakdown

- [x] [ID: P2-EAST-IMPORT-RESOLUTION-01-S1-01] Define spec that EAST3 keeps import resolution info (module/symbol) per identifier/call.
- [x] [ID: P2-EAST-IMPORT-RESOLUTION-01-S1-02] Record resolution info to `meta` or node attributes in parser/lowering and define fail-closed rules for missing values.
- [x] [ID: P2-EAST-IMPORT-RESOLUTION-01-S2-01] Add dependency collection APIs such as `require_dep` / `finalize_deps` to `CodeEmitter` base.
- [x] [ID: P2-EAST-IMPORT-RESOLUTION-01-S2-02] Remove hardcoded backend imports and migrate step-by-step to base dependency API (pilot: Go).
- [x] [ID: P2-EAST-IMPORT-RESOLUTION-01-S2-03] In pilot backend (Go), remove unused-avoidance dummies such as `var _ = math.Pi` and emit only required imports.
- [x] [ID: P2-EAST-IMPORT-RESOLUTION-01-S3-01] Add import regression tests (minimum needed / forbid unused / forbid missing deps) and lock them in CI.

## S1 Specification (Final)

`Module.meta.import_resolution` (`schema_version=1`):

- `schema_version: int`  
  Fixed to `1` for now.
- `bindings: list[ImportBinding]`  
  Source-of-truth import bindings collected by parser/lowering.
- `qualified_refs: list[QualifiedSymbolRef]`  
  Resolved references for `from ... import ...` (including local names).

`ImportBinding`:

- `module_id: str` (required)
- `export_name: str` (empty string allowed when `binding_kind="module"`)
- `local_name: str` (required)
- `binding_kind: "module" | "symbol"` (required)
- `source_file: str` (optional)
- `source_line: int` (optional)

`QualifiedSymbolRef`:

- `module_id: str` (required)
- `symbol: str` (required)
- `local_name: str` (required)

fail-closed rules:

- Entries with empty/missing required values in `module_id` / `local_name` / `symbol` / `export_name` are not registered to the resolution table.
- Fallback to legacy keys (`import_bindings` / `qualified_symbol_refs` / `import_symbols` / `import_modules`) is allowed only when `import_resolution` is missing or both `bindings` / `qualified_refs` are empty.
