<a href="../../../ja/plans/archive/20260311-p1-ir-core-import-surface-pruning.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: Shrink `toolchain.ir.core` as an import hub

Last updated: 2026-03-11

Related TODO:
- `ID: P1-IR-CORE-IMPORT-SURFACE-01` in `docs/ja/todo/index.md`

Background:
- `P1-IR-CORE-DECOMPOSITION-01` and `P2-EAST-CORE-MODULARIZATION-01` reduced `core.py` itself to a 214-line thin facade.
- Even so, `core.py` still carries more than 150 `toolchain.ir.*` helper imports, and several split modules plus some tests/entrypoints still use `toolchain.ir.core` as their import hub.
- That keeps internal dependencies concentrated on `core.py`, leaving cycles and public/private surface boundaries harder to control.

Objective:
- Recast `toolchain.ir.core` as an external thin facade and move internal split-module dependencies onto dedicated modules.
- Separate the public surface such as `convert_path`, `convert_source_to_east*`, and `EastBuildError` from internal helper imports.

Scope:
- `src/toolchain/ir/core.py`
- `src/toolchain/ir/core_entrypoints.py`
- `src/toolchain/ir/core_expr_*.py`
- `src/toolchain/ir/core_module_parser.py`
- `src/toolchain/ir/core_stmt_parser.py`
- `src/toolchain/compiler/east_parts/*`
- `tools/unittest/ir/test_east_core_source_contract_*.py`
- `docs/ja/todo/index.md` / `docs/en/todo/index.md`
- `docs/ja/plans/p1-ir-core-import-surface-pruning.md` / `docs/en/plans/p1-ir-core-import-surface-pruning.md`

Out of scope:
- New EAST/EAST3 language features
- Runtime/backend feature additions
- Re-expanding `core.py` by adding new convenience re-exports

Acceptance criteria:
- Representative internal split modules stop routing through `toolchain.ir.core` and import dedicated modules directly.
- The public surface that remains on `toolchain.ir.core` is written down in this plan and locked by source-contract coverage.
- Representative regressions keep passing: `test_east_core*.py`, `test_prepare_selfhost_source.py`, and `tools/build_selfhost.py`.

Validation commands:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/ir -p 'test_east_core*.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/selfhost -p 'test_prepare_selfhost_source.py'`
- `python3 tools/build_selfhost.py`
- `python3 tools/check/check_transpiler_version_gate.py`
- `python3 tools/run/run_regen_on_version_bump.py --dry-run`
- `git diff --check`

Breakdown:
- [x] [ID: P1-IR-CORE-IMPORT-SURFACE-01-S1-01] Inventory `toolchain.ir.core` importers and classify them as `public_entrypoint`, `internal_split_module`, `tests_only`, or `bridge_compat`.
- [x] [ID: P1-IR-CORE-IMPORT-SURFACE-01-S1-02] Define the public surface that remains on `toolchain.ir.core` and the policy that forbids internal imports through it.
- [x] [ID: P1-IR-CORE-IMPORT-SURFACE-01-S2-01] Move representative internal split-module lanes onto dedicated-module imports and reduce `core.py`-mediated dependencies.
- [x] [ID: P1-IR-CORE-IMPORT-SURFACE-01-S2-02] Align tests and helper lanes to the public surface or dedicated modules as appropriate.
- [x] [ID: P1-IR-CORE-IMPORT-SURFACE-01-S3-01] Add an import-surface guard for `toolchain.ir.core` so internal reintroduction fails fast.
- [x] [ID: P1-IR-CORE-IMPORT-SURFACE-01-S4-01] Re-run representative regressions, confirm non-regression, and archive the task.

Decision log:
- 2026-03-11: After `P1-IR-CORE-DECOMPOSITION-01`, `core.py` still carried 157 `toolchain.ir.*` imports and retained several `from toolchain.ir.core import ...` internal users, so this task was opened.
- 2026-03-11: The first inventory classifies importers into `public_entrypoint`, `internal_split_module`, `tests_only`, and `bridge_compat`. Representative examples are `frontends/transpile_cli.py` / backend smoke tests, `core_entrypoints.py` / `core_string_semantics.py` / `core_module_parser.py` / `core_stmt_parser.py` / `core_expr_primary.py` / `core_expr_lowered.py` / `core_expr_call_args.py`, `test_east_core_source_contract_*`, and `compiler/east_parts/__init__.py`.
- 2026-03-11: Canonical facade exports on `toolchain.ir.core` are fixed as `CORE_PUBLIC_FACADE_EXPORTS = (EastBuildError, convert_path, convert_source_to_east, convert_source_to_east_with_backend)`, while `convert_source_to_east_self_hosted`, `_sh_parse_stmt_block*`, and `INT_TYPES/FLOAT_TYPES` are isolated as `CORE_BRIDGE_COMPAT_EXPORTS` and kept only as temporary compatibility surface.
- 2026-03-11: Internal `toolchain.ir.core_*` split modules must not add new `toolchain.ir.core` import-hub dependencies. Existing lanes are migration debt to be moved in `S2-01/S2-02`, and only `public_entrypoint` plus `bridge_compat` remain permitted facade users.
- 2026-03-11: As the first representative `S2-01` bundle, `core_entrypoints`, `core_string_semantics`, `core_expr_primary`, `core_expr_lowered`, and `core_expr_call_args` now import `core_module_parser` / `core_expr_shell` directly instead of routing through `toolchain.ir.core`.
- 2026-03-11: In the helper / bridge slice of `S2-02`, `INT_TYPES/FLOAT_TYPES` were moved into `core_numeric_types.py`, and `east2_to_human_repr` plus `east_parts.__init__` stopped importing them from `toolchain.ir.core`.
- 2026-03-11: `core_stmt_parser` and `core_module_parser` have a wider dependency set, so they now depend on new `core_stmt_parser_support` / `core_module_parser_support` modules rather than `toolchain.ir.core`. This removes direct `from toolchain.ir.core import (...)` usage under `src/toolchain/ir`; only tests, public entrypoints, and bridge-compat lanes remain.
- 2026-03-11: Added `test_east_core_source_contract_import_surface.py` to fail fast if `toolchain.ir.core` is reintroduced under `src/toolchain/ir`, and to lock remaining source-side facade imports to the public surface used by `frontends/transpile_cli.py`.
- 2026-03-11: Re-ran representative regressions (`test_east_core*.py`, `test_prepare_selfhost_source.py`, `tools/build_selfhost.py`, `check_transpiler_version_gate.py`, `run_regen_on_version_bump.py --dry-run`) and judged the thin-facade import surface stable enough to archive.
