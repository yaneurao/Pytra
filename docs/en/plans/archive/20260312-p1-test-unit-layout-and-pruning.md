<a href="../../../ja/plans/archive/20260312-p1-test-unit-layout-and-pruning.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: Reorganize `test/unit` layout and clean up unused tests

Last updated: 2026-03-04

Related TODO:
- `ID: P1-TEST-UNIT-LAYOUT-PRUNE-01` in `docs/ja/todo/index.md`

Background:
- `test/unit/` mixes language-specific tests, IR tests, tooling tests, and selfhost-related tests, which hurts discoverability and maintainability.
- Backend tests such as `test_py2*_smoke.py` and common-layer tests such as `test_east*` and `test_code_emitter.py` sit at the same level, making responsibility boundaries hard to read.
- Some tests left over from older migrations appear to be unused in current operation because they are outside discover targets and have no individual execution path.

Goal:
- Reorganize `test/unit` into directories grouped by responsibility and reduce the cost of finding relevant tests.
- Inventory unused-test candidates mechanically and decide, with documented rationale, whether each should be deleted, merged, or kept.
- Keep existing unit, transpile, and selfhost regression paths working after the reorganization.

Scope:
- Re-layout files under `test/unit/`, for example into `common`, `backends/<lang>`, `ir`, `tooling`, and `selfhost`
- Update test-path references in `tools/` and `docs/`
- Classify and clean up unused-test candidates, either by deletion or integration
- Optionally add checks that prevent these issues from returning

Out of scope:
- Improving backend code quality
- Changing fixture semantics
- Changing parity-test specifications

Acceptance criteria:
- `test/unit` is reorganized into responsibility-based folders, removing the current top-level mixture.
- Main execution paths, including `unittest discover`, `tools/check_py2*_transpile.py`, and selfhost checks, work with the new paths.
- The unused-test cleanup records why each candidate was deleted, merged, or kept, including reference usage and execution evidence.
- To avoid accidental deletion, anything deleted must first be confirmed unused by at least one full discover run and a reference scan.

Verification commands, planned:
- `python3 tools/check_todo_priority.py`
- `python3 -m unittest discover -s test/unit -p 'test*.py'`
- `rg -n "test/unit/|test_py2.*smoke" tools docs/ja docs/en -g '*.py' -g '*.md'`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/check_py2rs_transpile.py`
- `python3 tools/check_py2cs_transpile.py`
- `python3 tools/check_py2js_transpile.py`
- `python3 tools/check_py2ts_transpile.py`
- `python3 tools/check_py2go_transpile.py`
- `python3 tools/check_py2java_transpile.py`
- `python3 tools/check_py2swift_transpile.py`
- `python3 tools/check_py2kotlin_transpile.py`
- `python3 tools/check_py2rb_transpile.py`
- `python3 tools/check_py2lua_transpile.py`
- `python3 tools/check_py2scala_transpile.py`
- `python3 tools/check_py2php_transpile.py`
- `python3 tools/check_py2nim_transpile.py`

## Breakdown

- [x] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S1-01] Inventory current tests in `test/unit` by responsibility class, `common/backends/ir/tooling/selfhost`, and finalize the move map.
- [x] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S1-02] Define the target directory conventions and finalize naming and placement rules.
- [x] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S2-01] Move test files into the new directories and update reference paths in `tools/` and `docs/` in one batch.
- [x] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S2-02] Update CI and local scripts so `unittest discover` and individual execution paths work under the new layout.
- [x] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S3-01] Extract unused-test candidates and write an audit memo that decides `delete/integrate/keep`.
- [x] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S3-02] Delete or integrate already-classified unused tests and add recurrence-prevention checks if needed.
- [x] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S4-01] Run the main unit, transpile, and selfhost regressions and confirm no regressions after the reorganization and cleanup.
- [x] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S4-02] Reflect the new test-layout conventions and operating procedure in `docs/ja/spec` and `docs/en/spec` when needed.

Decision log:
- 2026-03-04: On user request, filed a P1 task for responsibility-based folder reorganization and unused-test cleanup in `test/unit`. Deletions are allowed only in staged form with explicit audit evidence.
- 2026-03-04: Completed `S1-01`. Classified all 71 files under `test/unit` and fixed the move map. The breakdown is `backends/*:29, ir:10, tooling:5, selfhost:3, common:23`. `S2-01` uses this map to perform the reorganization.
- 2026-03-04: Completed `S1-02`. Fixed the target placement conventions for `test/unit` as responsibility directories, naming rules, discover and execution rules, and checks required when adding new tests. This established the move criteria for `S2` and later.
- 2026-03-04: Completed `S2-01`. Moved 71 `test/unit/test_*.py` files into `common/backends/<lang>/ir/tooling/selfhost` via `git mv` and updated the fixed test paths in `tools/run_local_ci.py` and `tools/check_noncpp_east3_contract.py`. Because turning `test/unit/backends` into a package would conflict with `src/backends`, the policy is to avoid `__init__.py` there, with discover-path handling updated in `S2-02`.
- 2026-03-04: Completed `S2-02`. Replaced `test/unit/test_discovery_router.py` with a manual `load_tests + importlib` loader so `python3 -m unittest discover -s test/unit -p 'test*.py'` can recurse even under non-package directories. The previously broken `from comment_fidelity import ...` path was stabilized by adding root-level `comment_fidelity.py`, and the three smoke discovers for Go, Swift, and Kotlin were confirmed to pass. `tools/check_gsk_native_regression.py` was also updated to reference the new paths under `test/unit/backends/*`.
- 2026-03-04: Completed `S3-01`. Ran a reference scan over all `test/unit/test*.py` entries against `tools/docs` and extracted zero-reference candidates, `test_pylib_*` and `test_east3_to_human_repr.py`. All of them were judged to be active regressions under discover, so deletion and integration were both deferred and the result was `keep`.
- 2026-03-04: Completed `S3-02`. Based on the `S3-01` audit result of zero delete or integration candidates, closed the step without code changes. Recurrence prevention is covered by the rule that forbids direct placement under `test/unit` and by keeping `test_discovery_router` fixed.
- 2026-03-04: Completed `S4-01`. Re-ran the main regressions, including `test/unit/common/test_py2x_smoke_common.py`, `test/unit/backends/{go,swift,kotlin}/test_py2*_smoke.py`, `test/unit/selfhost/test_prepare_selfhost_source.py`, and `tools/check_noncpp_east3_contract.py --skip-transpile`, and confirmed all passed.
- 2026-03-04: Completed `S4-02`. Updated the test-path references in `docs/ja/spec` and `docs/en/spec`, previously pointing at `test/unit/test_*.py`, to the new `common/backends/ir/tooling/selfhost` layout.

## S3-01 Audit Memo (2026-03-04)

- Extraction procedure:
- Enumerate all `test/unit/test*.py` files and count `rg -n <basename> tools docs/ja docs/en` hits for each basename.
- Treat anything with 0 to 1 hits as an unused candidate, then re-evaluate it by whether it actually runs under discover.
- Candidates and decisions:
- `test/unit/common/test_pylib_argparse.py` and the other 8 `test_pylib_*` files:
- Decision: keep. `test/unit/common` discover passes 36 tests, and these files guard shim regressions under `src/pytra/*`, so they cannot be deleted.
- `test/unit/ir/test_east3_to_human_repr.py`:
- Decision: keep. A dedicated discover run under `test/unit/ir` passes 3 tests, and the file protects the compatibility-wrapper contract for `east2/east3` human-readable representations.
- `test/unit/test_discovery_router.py`:
- Decision: keep. It is required as the top-level discover router when `test/unit/backends` remains non-package.
- Audit conclusion:
- In this `S3-01` pass, there were zero deletion or integration targets. `S3-02` therefore closes with `no candidates`.

## S1-01 Inventory Results (2026-03-04)

- Total count: 71 files matching `test/unit/test*.py`
- Classification summary:
- `backends/*`: 29
- `ir`: 10
- `tooling`: 5
- `selfhost`: 3
- `common`: 23
- Fixed target destinations:
- `test/unit/backends/<lang>/`: `test_py2<lang>_smoke.py` and other backend-specific tests
- `test/unit/ir/`: `test_east*.py`
- `test/unit/tooling/`: CLI, manifest, parity-tool, and related operational tests
- `test/unit/selfhost/`: selfhost build, diff, and regression tests
- `test/unit/common/`: cross-language, pylib, profile, and bootstrap tests not covered above
- Primary mapping, explicit examples:
- `backends/cpp`:
- `test_check_microgpt_original_py2cpp_regression.py`, `test_cpp_*.py`, `test_py2cpp_*.py`, `test_east3_cpp_bridge.py`, `test_noncpp_east3_contract_guard.py`
- Backend tests for each language:
- `test_py2{rs,cs,js,ts,go,java,swift,kotlin,rb,lua,php,nim}_smoke.py`, `test_check_py2scala_transpile.py`, `test_py2scala_smoke.py`
- `ir`:
- `test_east1_build.py`, `test_east2_to_east3_lowering.py`, `test_east3_*.py`, `test_east_core.py`, `test_east_stage_boundary_guard.py`
- `tooling`:
- `test_docs_ja_guard.py`, `test_gen_makefile_from_manifest.py`, `test_ir2lang_cli.py`, `test_pytra_cli.py`, `test_runtime_parity_check_cli.py`
- `selfhost`:
- `test_check_selfhost_cpp_diff.py`, `test_prepare_selfhost_source.py`, `test_selfhost_virtual_dispatch_regression.py`
- `common`:
- The remaining 23 files, such as `test_code_emitter.py`, `test_py2x_smoke_common.py`, `test_pylib_*.py`, and `test_language_profile.py`

## S1-02 Target Directory Conventions (2026-03-04)

- Root structure:
- `test/unit/common/`: shared tests that are neither IR-specific nor backend-specific
- `test/unit/backends/<lang>/`: tests specific to a language backend, where `<lang>` is `cpp,rs,cs,js,ts,go,java,swift,kotlin,rb,lua,scala,php,nim`
- `test/unit/ir/`: IR tests for EAST1, EAST2, EAST3, optimizations, and boundary contracts
- `test/unit/tooling/`: operational tests such as CLI, parity, manifest, and docs guards
- `test/unit/selfhost/`: selfhost generation, diff, and regression tests
- File naming:
- Keep filenames in `test_*.py` form, and in principle do not change the basename when moving files, so history tracking and existing references remain intact.
- Prefer `test_<lang>_*.py` or `test_py2<lang>_*.py` for new backend-specific tests so they stay easy to distinguish from `common`.
- Execution rules:
- Keep `python3 -m unittest discover -s test/unit -p 'test*.py'` as the standard full-run command.
- Individual runs should remain possible per domain via `python3 -m unittest discover -s test/unit/<domain> -p 'test*.py'`.
- Reference-update rule:
- If `tools/` or `docs/` still reference an old path, update it to the new path in the same commit during `S2-01`.
- Rule when adding tests:
- Every new test must be classified into one of `common/backends/ir/tooling/selfhost`, and direct placement under `test/unit` is forbidden.
