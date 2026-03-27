<a href="../../../ja/plans/archive/20260311-p1-ir-entrypoint-facade-pruning.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: Prune `toolchain.ir.core` facade importers

Last updated: 2026-03-11

Related TODO:
- `ID: P1-IR-ENTRYPOINT-FACADE-PRUNING-01` in `docs/ja/todo/index.md`

Background:
- `P1-IR-CORE-DECOMPOSITION-01` and `P1-IR-CORE-IMPORT-SURFACE-01` reduced `src/toolchain/ir/core.py` to a thin facade that mainly forwards to `core_entrypoints` plus stmt/module bridge helpers.
- However, part of the compiler frontend and several representative test/backend lanes still import `convert_path`, `convert_source_to_east_with_backend`, and `EastBuildError` from `toolchain.ir.core`.
- Keeping `core.py` as a compatibility facade is reasonable, but letting internal compiler and regression lanes depend on it keeps the boundary between entrypoint surface and compatibility surface blurry.

Goal:
- Move internal compiler code and representative regression lanes onto `toolchain.ir.core_entrypoints`, leaving `toolchain.ir.core` as an external compatibility facade only.
- Add a source-contract guard that fails fast when facade dependence is reintroduced.

Scope:
- `src/toolchain/frontends/transpile_cli.py`
- `src/toolchain/ir/core.py`
- `src/toolchain/ir/core_entrypoints.py`
- representative test/backend importers (`test/unit/common/*`, `test/unit/backends/*`, `test/unit/ir/test_east2_to_east3_lowering.py`)
- `test/unit/ir/test_east_core_source_contract_import_surface.py`
- `docs/ja/todo/index.md` / `docs/en/todo/index.md`
- `docs/ja/plans/p1-ir-entrypoint-facade-pruning.md` / `docs/en/plans/p1-ir-entrypoint-facade-pruning.md`

Out of scope:
- Parser / IR / runtime spec changes
- Removing public exports from `toolchain.ir.core`
- Backend feature additions

Acceptance criteria:
- `src/toolchain/frontends/transpile_cli.py` imports from `toolchain.ir.core_entrypoints`, not `toolchain.ir.core`.
- Representative test/backend lanes obtain `convert_path`, `convert_source_to_east_with_backend`, and `EastBuildError` from `core_entrypoints`.
- `test_east_core_source_contract_import_surface.py` locks source-side `toolchain.ir.core` importers to zero and fails fast if representative test lanes regress to the facade.
- Representative regressions (`test_east_core*.py`, `test_prepare_selfhost_source.py`, `build_selfhost.py`) pass.

Checks:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east_core*.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/selfhost -p 'test_prepare_selfhost_source.py'`
- `python3 tools/build_selfhost.py`
- `python3 tools/check_transpiler_version_gate.py`
- `python3 tools/run_regen_on_version_bump.py --dry-run`
- `git diff --check`

Breakdown:
- [x] [ID: P1-IR-ENTRYPOINT-FACADE-PRUNING-01-S1-01] Inventory residual importers and classify them as `src_compiler`, `representative_tests`, or `compat_only`.
- [x] [ID: P1-IR-ENTRYPOINT-FACADE-PRUNING-01-S1-02] Fix the policy that `toolchain.ir.core` remains an external compatibility facade while internal compiler and representative regression lanes use `core_entrypoints`.
- [x] [ID: P1-IR-ENTRYPOINT-FACADE-PRUNING-01-S2-01] Move `transpile_cli` and representative test/backend importers onto `core_entrypoints`.
- [x] [ID: P1-IR-ENTRYPOINT-FACADE-PRUNING-01-S2-02] Fail fast on facade reentry with a source-contract guard.
- [x] [ID: P1-IR-ENTRYPOINT-FACADE-PRUNING-01-S3-01] Run representative regressions and version gates, then archive the task.

Decision log:
- 2026-03-11: Initial draft. The current residual importers are `src/toolchain/frontends/transpile_cli.py`, `test/unit/common/test_self_hosted_signature.py`, 11 backend smoke tests, `test/unit/backends/cpp/test_east3_cpp_bridge.py`, and `test/unit/ir/test_east2_to_east3_lowering.py`.
- 2026-03-11: `toolchain.ir.core` stays as a public compatibility facade, but internal compiler code and representative regression lanes must canonically use `toolchain.ir.core_entrypoints`. Dependence on `core.py` is treated as external-user compatibility only and is forbidden again by internal source-contract tests.
- 2026-03-11: `S2-01` moved `src/toolchain/frontends/transpile_cli.py`, `test_self_hosted_signature.py`, 11 backend smoke tests, `test_east3_cpp_bridge.py`, and `test_east2_to_east3_lowering.py` onto `toolchain.ir.core_entrypoints`.
- 2026-03-11: `S2-02` updated `test_east_core_source_contract_import_surface.py` so source-side `toolchain.ir.core` importers are fixed at zero and the representative test/backend lanes also fail fast if they regress to the facade.
- 2026-03-11: `S3-01` re-ran the representative regressions (`test_east_core*.py`, `test_prepare_selfhost_source.py`, `test_self_hosted_signature.py`, `test_east3_cpp_bridge.py`, `test_east2_to_east3_lowering.py`), version gates, and selfhost build, then archived the task.
