<a href="../../ja/plans/p0-pytra-src-3layer-bootstrap.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Bootstrap 3-Layer Separation Inside `src/pytra` (`frontends` / `ir` / `backend`)

Last updated: 2026-03-03

Related TODO:
- `ID: P0-PYTRA-SRC-3LAYER-01` in `docs/ja/todo/index.md`

Background:
- Currently, `src/pytra/compiler` mixes Python input handling (frontend-equivalent) and EAST processing (IR-equivalent), which makes ownership boundaries unclear.
- Existing imports depend on the `pytra.*` namespace, so cutting directly to `src/frontends` is likely to be a breaking change.
- The requirement is: first separate `frontends` / `ir` while keeping `src/pytra` namespace, and proceed with migration safely in phases.

Goal:
- Introduce `src/pytra/frontends` and `src/pytra/ir`, and gradually relocate responsibilities from `src/pytra/compiler`.
- Keep `src/backends` as-is, and lock dependency direction to `frontends -> ir -> backends`.
- Keep `pytra/std` / `pytra/built_in` / `runtime` separated as runtime support layer and out of this 3-layer relocation scope.

In scope:
- `src/pytra/compiler` (organize frontend-equivalent and IR-equivalent parts)
- `src/pytra/frontends` (new)
- `src/pytra/ir` (new)
- Compatibility shims for import paths (during phased migration)
- Boundary guards (disallowed import checks)
- Docs (responsibility-boundary explanation in `docs/ja/spec`)

Out of scope:
- Backend output-quality improvements
- Runtime feature additions
- Large moves of `src/pytra/std` / `src/pytra/built_in` / `src/runtime`
- Final move under top-level `src/frontends` (not done in this task)

Acceptance criteria:
- `src/pytra/frontends` / `src/pytra/ir` are introduced, and target modules are relocated according to ownership.
- `src/pytra/compiler` is reduced mostly to compatibility layer (re-export / thin bridge), and can block inflow of new implementations.
- `py2x` and existing `py2*.py` run without regression.
- Boundary guard is added and can detect reverse-flow imports between `frontends` and `ir`.

Verification commands (planned):
- `python3 tools/check/check_todo_priority.py`
- `python3 tools/check/check_noncpp_east3_contract.py --skip-transpile`
- `python3 -m unittest discover -s test/unit -p test_py2x_cli.py`
- `python3 tools/check/check_py2cpp_transpile.py`
- `python3 tools/check/check_py2rs_transpile.py`
- `python3 tools/check/check_py2js_transpile.py`
- `python3 tools/check/check_py2ts_transpile.py`
- `python3 tools/check/check_py2go_transpile.py`
- `python3 tools/check/check_py2java_transpile.py`
- `python3 tools/check/check_py2kotlin_transpile.py`
- `python3 tools/check/check_py2swift_transpile.py`
- `python3 tools/check/check_py2rb_transpile.py`
- `python3 tools/check/check_py2lua_transpile.py`
- `python3 tools/check/check_py2php_transpile.py`
- `python3 tools/check/check_py2scala_transpile.py`
- `python3 tools/check/check_py2nim_transpile.py`

## Breakdown

- [x] [ID: P0-PYTRA-SRC-3LAYER-01-S1-01] Inventory `src/pytra/compiler` and classify into `frontends` / `ir` / compatibility layer.
- [x] [ID: P0-PYTRA-SRC-3LAYER-01-S1-02] Define directory conventions and import boundaries (dependency direction) while preserving `src/pytra` namespace.
- [x] [ID: P0-PYTRA-SRC-3LAYER-01-S2-01] Introduce `src/pytra/frontends` / `src/pytra/ir` and place minimal bootstrap modules.
- [x] [ID: P0-PYTRA-SRC-3LAYER-01-S2-02] Relocate frontend-equivalent modules from Python input through EAST1 generation into `src/pytra/frontends`.
- [x] [ID: P0-PYTRA-SRC-3LAYER-01-S2-03] Relocate IR-equivalent modules for EAST1/2/3, lower/optimizer/analysis into `src/pytra/ir`.
- [x] [ID: P0-PYTRA-SRC-3LAYER-01-S2-04] Convert `src/pytra/compiler` to compatibility shims and prepare re-export paths without breaking existing imports.
- [x] [ID: P0-PYTRA-SRC-3LAYER-01-S3-01] Add boundary guards (disallowed imports / reverse-flow dependencies) and lock recurrence prevention.
- [x] [ID: P0-PYTRA-SRC-3LAYER-01-S3-02] Run major unit/transpile regressions and confirm no regressions.
- [x] [ID: P0-PYTRA-SRC-3LAYER-01-S3-03] Reflect new responsibility boundaries and migration policy in `docs/ja/spec` (and `docs/en/spec` if needed).

## S1 Inventory Results (2026-03-03)

Frontend candidates (phased move to `src/pytra/frontends`):
- `src/pytra/compiler/transpile_cli.py`
- `src/pytra/compiler/stdlib/frontend_semantics.py`
- `src/pytra/compiler/stdlib/signature_registry.py`
- `src/pytra/compiler/east_parts/east1_build.py` (EAST1 build and import-graph resolution)

IR candidates (phased move to `src/pytra/ir`):
- `src/pytra/compiler/east.py`
- `src/pytra/compiler/east_parts/east1.py`
- `src/pytra/compiler/east_parts/east2.py`
- `src/pytra/compiler/east_parts/east3.py`
- `src/pytra/compiler/east_parts/east2_to_east3_lowering.py`
- `src/pytra/compiler/east_parts/east3_optimizer.py`
- `src/pytra/compiler/east_parts/east3_opt_passes/*`
- `src/pytra/compiler/east_parts/east_io.py`
- `src/pytra/compiler/east_parts/east2_to_human_repr.py`
- `src/pytra/compiler/east_parts/east3_to_human_repr.py`
- `src/pytra/compiler/east_parts/core.py`
- `src/pytra/compiler/east_parts/code_emitter.py`

Compatibility layer / path preservation (keep under `src/pytra/compiler`):
- `src/pytra/compiler/__init__.py`
- `src/pytra/compiler/py2x_wrapper.py`
- `src/pytra/compiler/backend_registry.py`
- `src/pytra/compiler/backend_registry_static.py`
- `src/pytra/compiler/js_runtime_shims.py`
- `src/pytra/compiler/transpiler_versions.json`
- `src/pytra/compiler/east_parts/__init__.py`
- `src/pytra/compiler/east_parts/cli.py` (during migration, keep as thin CLI facade referencing `pytra.ir`)

Boundary rules fixed in S1-02:
- Dependency direction is `frontends -> ir -> backends` in principle; reverse-direction imports are prohibited.
- `frontends` handles input interpretation and EAST1 construction only, and must not include target-language-specific branches.
- `ir` handles only EAST1/2/3, lower/optimizer/analysis, and IR I/O; it must not contain CLI arg parsing or runtime-copy processing.
- `compiler` is limited to compatibility shims and thin integration bridges; it is not treated as destination for new logic implementation.
- `backends -> frontends` imports are prohibited. Shared processing should be placed in `toolchain/emit/common` or `pytra/ir`.

Decision log:
- 2026-03-03: Adopted policy to introduce `frontends` / `ir` while preserving `src/pytra` namespace; final migration to top-level `src/frontends` is deferred to a later phase.
- 2026-03-03: Ran inventory on tracked files with `git ls-files src/pytra/compiler`, classifying `transpile_cli/stdlib/east1_build` as frontend candidates, EAST core/lower/optimizer/human/io as IR candidates, and registry/wrapper/version/shim as compatibility layer.
- 2026-03-03: To avoid ownership conflicts during migration, decided to keep `compiler/east_parts/cli.py` in compatibility layer for now and only allow references to `pytra.ir`.
- 2026-03-03: Added `src/pytra/frontends/__init__.py`, `src/pytra/frontends/python_frontend.py`, `src/pytra/ir/__init__.py`, `src/pytra/ir/pipeline.py`, introducing minimal bootstrap path delegating to existing `pytra.compiler.*` implementations.
- 2026-03-03: Added `tools/unittest/test_pytra_layer_bootstrap.py` and locked public APIs (`pytra.frontends` and `pytra.ir` importability). Confirmed non-regression with `test_py2x_cli.py`, major transpile checks (`rs/js`), and version gate.
- 2026-03-03: Moved implementations to `src/pytra/frontends/{east1_build.py,frontend_semantics.py,signature_registry.py}`; old `src/pytra/compiler/east_parts/east1_build.py` and `src/pytra/compiler/stdlib/{frontend_semantics.py,signature_registry.py}` were converted to compatibility shims.
- 2026-03-03: Switched stdlib references in `src/pytra/compiler/east_parts/core.py` to `pytra.frontends.*`, and updated `East1BuildHelpers` references in `py2cpp`/`multifile_writer`/`transpile_cli` to new path.
- 2026-03-03: Changed `pytra.frontends.__init__` to lazy delegation to avoid import-time cycles. Confirmed pass for `test_stdlib_signature_registry.py`, `test_east1_build.py`, `test_pytra_layer_bootstrap.py`, `check_py2{cpp,rs,js}_transpile.py`, `check_noncpp_east3_contract.py --skip-transpile`, `check_transpiler_version_gate.py --base-ref HEAD`.
- 2026-03-03: Added IR core modules as `src/pytra/ir/{core,east1,east2,east3,east2_to_east3_lowering,east3_optimizer,east_io}.py` and `src/pytra/ir/east3_opt_passes/*`, and converted old `src/pytra/compiler/east_parts/*` side to compatibility shims.
- 2026-03-03: Switched EAST stage references in `transpile_cli` and `frontends/east1_build` to `pytra.ir.*`. Solved cycle issue where `ir/east_io` depended via `compiler.east` by switching to direct `ir.core` reference.
- 2026-03-03: After IR migration, ran and passed regressions: `test_east{2_to_east3_lowering,3_optimizer,3_non_escape_interprocedural_pass,3_lifetime_analysis_pass}`, `check_py2{cpp,rs,js}_transpile.py`, `check_noncpp_east3_contract --skip-transpile`, `check_transpiler_version_gate --base-ref HEAD`.
- 2026-03-03: Moved `transpile_cli` implementation to `src/pytra/frontends/transpile_cli.py`; converted old `src/pytra/compiler/transpile_cli.py` to compatibility shim. `python_frontend` switched to new path (`pytra.frontends.transpile_cli`).
- 2026-03-03: Re-ran compatibility-path regressions and confirmed pass: `test_py2x_cli.py`, `test_pytra_layer_bootstrap.py`, `test_stdlib_signature_registry.py`, `check_py2{cpp,rs,js}_transpile.py`, `check_noncpp_east3_contract --skip-transpile`, `check_transpiler_version_gate --base-ref HEAD`.
- 2026-03-03: Added boundary guard `tools/check/check_pytra_layer_boundaries.py`: prohibit `frontends -> backends` / `ir -> backends` / `backends -> frontends`, and allow `ir -> frontends` only from `ir/core.py` via static import monitoring.
- 2026-03-03: At guard introduction time, `toolchain/emit/cpp/emitter/multifile_writer.py` directly referenced `pytra.frontends.east1_build`, so it was reverted to compatibility shim path (`pytra.compiler.east_parts.east1_build`) to eliminate reverse-flow dependency.
- 2026-03-03: Confirmed passes after guard introduction: `check_pytra_layer_boundaries.py`, `test_py2x_cli.py`, `check_py2{cpp,rs,js}_transpile.py`, `check_noncpp_east3_contract --skip-transpile`, `check_transpiler_version_gate --base-ref HEAD`.
- 2026-03-03: As major regressions for S3-02, batch-ran `check_pytra_layer_boundaries`, `check_noncpp_east3_contract --skip-transpile`, `test_py2x_cli`, `check_py2{cpp,rs,js,ts,go,java,kotlin,swift,rb,lua,php,scala,nim}_transpile`, `check_transpiler_version_gate --base-ref HEAD`; all passed.
- 2026-03-03: Updated responsibility boundary docs in `docs/ja/spec`: reflected in `spec-folder.md` (3 layers + compatibility), `spec-east.md` (file responsibility matrix, post-migration source of truth), `spec-stdlib-signature-source-of-truth.md` (reference layer / consumer paths), and `spec-options.md` (source-of-truth path for shared CLI options).
