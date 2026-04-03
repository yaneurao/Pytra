<a href="../../ja/spec/spec-agent-coder.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# AI Agent Operations Specification — For Code Implementors

This document defines the rules for AI agents responsible for implementing, fixing, and testing code.

## 1. Golden Files / Test Generation

- **Golden files (east1/east2/east3/east3-opt/linked/selfhost) are not managed by git (covered by `.gitignore`).** Regenerate them locally with `python3 tools/gen/regenerate_golden.py`. Do not commit golden files. Manual editing is also prohibited.
- **Sample regeneration must be done exclusively via `python3 tools/gen/regenerate_samples.py`.**

## 2. `tools/` Placement Rules

- **Adding new `.py` files directly under `tools/` is prohibited.** Always place them in one of `tools/check/`, `tools/gen/`, or `tools/run/`.
- **When adding, deleting, or moving files, always update the `tools/README.md` ledger at the same time.** Files must not be added without updating the ledger.
- The CI check `python3 tools/check/check_tools_ledger.py` cross-references files against the ledger. Any file not listed in the ledger will cause a FAIL.
- `tools/unregistered/` has been deleted. Even temporary or experimental scripts must be placed in the proper directories (`tools/check/`, `tools/gen/`, `tools/run/`) from the start, and deleted when no longer needed.

## 3. `test/` Placement Rules

- **Do not create directories under `test/fixture/` arbitrarily.** Follow the existing directory structure (`source/py/`, `east1/py/`, `east2/`, `east3/`, `east3-opt/`, `linked/`).
- **Do not create new subdirectories directly under `test/`** (to prevent typo directories like `test/fixtures/`).

## 4. Emitter Prohibitions

- The emitter faithfully renders EAST3. The following are prohibited:
  - Adding casts (if there is no cast in EAST, it is a resolve bug)
  - Changing variable types
  - Changing loop variable types in for-range
  - Hardcoding name mappings not present in `mapping.json`
  - Re-implementing type inference
  - **Traversing the EAST body to determine types** (e.g., inferring the return type from the presence of a Return node)
- **If EAST information is insufficient, fix EAST (resolve/compile/optimize) rather than writing workarounds in the emitter.**
- **If a workaround appears to be necessary, report it to the user first before implementing.** Do not add implementations that violate the spec.
- See `docs/ja/spec/spec-emitter-guide.md` for details.

## 5. Runtime Prohibitions

- Do not hardcode type_id table sizes or values in runtime headers (fixed-size arrays like `g_type_table[4096]` are prohibited).
- Hand-written TID constants (e.g., `PYTRA_TID_VALUE_ERROR = 12`) are prohibited. Use the constants from the linker-generated `pytra.built_in.type_id_table`.
- Do not rewrite source-of-truth files (such as `src/pytra/utils/*.py`) to work around transpiler limitations (e.g., manually converting `with` statements to open/close). The correct fix is to make the emitter handle them.

## 6. Commit Rules

- Agents may commit without asking for user permission each time, once the work is logically complete.
- Split commits into logical units and include a message that clearly conveys the intent of the change.
- TODO-completion commits must include the `ID` in the message (e.g., `[ID: P0-XXX-01] ...`).
- **When a task is complete, change `[ ]` to `[x]` for the corresponding task in `docs/ja/todo/index.md`, add a completion note (e.g., count), and commit.** Forgetting to check it off may cause other agents to start the same task.

## 7. Version Updates

- The internal version gate (`transpiler_versions.json`) is obsolete. Verify changes via parity check.
- The public release version is managed in `docs/VERSION`. Agents may update `PATCH`. `MINOR` / `MAJOR` updates require an explicit user instruction.

## 8. Selfhost Operations

- In selfhost target code (such as `src/toolchain/misc/east.py`), do not use dynamic imports (`try/except ImportError` fallback, lazy imports via `importlib`).
- In selfhost target code, dependency on the Python standard `ast` module is prohibited.
- In Python code intended for transpilation, direct `import` of Python standard modules (`json`, `pathlib`, `sys`, etc.) is prohibited. Use `pytra.std.*` instead.
