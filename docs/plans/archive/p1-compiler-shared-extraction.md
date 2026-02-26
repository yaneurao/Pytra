<a href="../../docs-ja/plans/archive/p1-compiler-shared-extraction.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# TASK GROUP: TG-P1-COMP-SHARED

Last updated: 2026-02-22

Related TODO:
- `docs-ja/todo/index.md` `ID: P1-COMP-01` to `P1-COMP-08`

Background:
- Cross-language logic such as import-graph analysis and module-index construction is concentrated in `py2cpp.py`.

Objective:
- Extract shared analysis into reusable APIs under `src/pytra/compiler/` for all `py2*` CLIs.

In scope:
- Import-graph analysis
- Module EAST map / symbol index / type schema construction
- Deps dump API
- Explicit boundary documentation among `CodeEmitter`, parser, and compiler shared layer

Out of scope:
- Language-specific codegen optimization
- Runtime output format changes

Acceptance criteria:
- Shared analysis APIs are usable outside `py2cpp`
- `py2cpp.py` shrinks toward C++-specific responsibilities
- Boundary definitions (`CodeEmitter` / parser / compiler shared layer) are documented

Validation commands:
- `python3 tools/check_py2cpp_transpile.py`
- `python3 test/unit/test_py2cpp_features.py`

`P1-COMP-08` migration plan (adopt shared analysis APIs in other language CLIs):

1. Phase 0 (freeze API)
   - Define shared analysis API entry points under `src/pytra/compiler/`.
   - Minimum API units: `import_graph`, `module_east_map`, `symbol_index`, `type_schema`, `deps_dump`.
   - Freeze return schemas visible from CLIs (dict schema), treating `py2cpp` as the reference implementation.
2. Phase 1 (apply first to `py2rs.py`)
   - Prohibit direct calls to `py2cpp.py`-specific helpers from `py2rs.py`; receive module-analysis results only via shared APIs.
   - Validate output differences with `tools/check_py2rs_transpile.py`.
3. Phase 2 (expand to `py2cs.py` / `py2js.py` / `py2ts.py`)
   - Use the same API in these CLIs and unify the pre-import-resolution stage.
   - Move FS-dependent pre-processing before `meta.import_bindings` into the shared layer.
4. Phase 3 (expand to preview languages: `py2go.py` / `py2java.py` / `py2swift.py` / `py2kotlin.py`)
   - Unify diagnostic format for failures (analysis failure / transpile failure), limiting language-specific CLIs to presentation responsibilities.
   - Reach a state where each `tools/check_py2<lang>_transpile.py` uses the same preprocessing API.
5. Phase 4 (retire legacy paths)
   - Remove duplicated project-analysis code from each CLI including `py2cpp.py`.
   - Add regression tests in the shared API layer and shift CLI-layer tests toward wiring tests.

Completion conditions:
- Every non-C++ CLI performs project analysis through shared APIs in `src/pytra/compiler/`.
- Project-analysis implementations remaining in `py2cpp.py` are removed except C++-specific helpers.
- Existing transpile checks (`tools/check_py2*.py`) pass without regressions.

Decision log:
- 2026-02-22: Initial draft.
- 2026-02-22: For `P1-COMP-06` / `P1-COMP-07`, documented boundaries for `CodeEmitter`, EAST parser, and compiler shared layer in `docs-ja/spec/spec-dev.md`.
- 2026-02-22: For `P1-COMP-08`, added a 5-phase migration plan starting from `py2rs.py` and rolling shared analysis APIs into other language CLIs.
