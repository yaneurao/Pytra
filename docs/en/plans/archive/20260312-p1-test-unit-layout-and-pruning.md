# P1: Reorganize `test/unit` Layout and Prune Unused Tests

Last updated: 2026-03-04

Related TODO:
- `ID: P1-TEST-UNIT-LAYOUT-PRUNE-01` in `docs/ja/todo/index.md`

Background:
- `test/unit/` currently mixes language-specific, IR, tooling, and self-host tests, reducing discoverability and maintainability.
- Backend tests such as `test_py2*_smoke.py` and common-layer tests such as `test_east*` / `test_code_emitter.py` are side by side at the same level, making responsibility boundaries hard to read.
- Among tests left from past migrations, some candidates appear to be unused in current operations (not in discover target and no individual execution path).

Goal:
- Reorganize `test/unit` into responsibility-based directories to reduce test discovery cost.
- Mechanically inventory "unused test candidates" and decide deletion/integration/retention with rationale.
- Preserve existing unit/transpile/selfhost regression paths after reorganization.

Scope:
- Relocation under `test/unit/` (e.g., `common`, `backends/<lang>`, `ir`, `tooling`, `selfhost`)
- Update test-path references in `tools/` / `docs/`
- Classification and cleanup of unused-test candidates (delete or integrate)
- Add recurrence-prevention checks if needed

Out of scope:
- Backend output quality improvements
- Semantic changes to fixtures
- Parity test spec changes

Acceptance criteria:
- `test/unit` is reorganized into responsibility-based folders and mixed top-level placement is resolved.
- Major execution paths (`unittest discover`, `tools/check_py2*_transpile.py`, selfhost checks) pass under new paths.
- Cleanup decisions for unused tests include documented rationale (`delete/integrate/keep`) with reference usage/execution evidence.
- To prevent accidental deletion, deletion candidates must pass unused confirmation via at least one full discover run and a reference scan.

Verification commands (planned):
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

- [x] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S1-01] Inventory current tests in `test/unit` by responsibility classification (common/backends/ir/tooling/selfhost) and finalize move map.
- [ ] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S1-02] Define target directory conventions and finalize naming/placement rules.
- [ ] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S2-01] Move test files into new directories and batch-update reference paths in `tools/` / `docs/`.
- [ ] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S2-02] Update CI/local scripts so `unittest discover` and individual execution paths pass under the new structure.
- [ ] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S3-01] Extract unused-test candidates and produce an audit memo with `delete/integrate/keep` decisions.
- [ ] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S3-02] Delete or integrate classified unused tests and add recurrence-prevention checks if required.
- [ ] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S4-01] Run major unit/transpile/selfhost regressions and verify non-regression after reorganization/cleanup.
- [ ] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S4-02] Reflect new test layout conventions and operational procedures in `docs/ja/spec` (and `docs/en/spec` if needed).

Decision log:
- 2026-03-04: Based on user direction, filed a P1 task for responsibility-based folder reorganization and unused-test cleanup for `test/unit`. Adopted a phased policy requiring audit rationale before any deletion.
- 2026-03-04: Completed `S1-01`. Classified all 71 files under `test/unit` and fixed move map. Classification summary: `backends/*:29, ir:10, tooling:5, selfhost:3, common:23`. `S2-01` will execute directory reorganization according to this map.

## S1-01 Inventory Results (2026-03-04)

- Total: 71 files in `test/unit/test*.py`
- Classification summary:
- `backends/*`: 29
- `ir`: 10
- `tooling`: 5
- `selfhost`: 3
- `common`: 23
- Target destinations (fixed):
- `test/unit/backends/<lang>/`: `test_py2<lang>_smoke.py` series + backend-specific tests
- `test/unit/ir/`: `test_east*.py` series
- `test/unit/tooling/`: CLI/manifest/parity tool tests
- `test/unit/selfhost/`: selfhost build/diff/regression tests
- `test/unit/common/`: cross-lang / pylib / profile / bootstrap tests not included above
- Primary mapping (explicit):
- `backends/cpp`:
- `test_check_microgpt_original_py2cpp_regression.py`, `test_cpp_*.py`, `test_py2cpp_*.py`, `test_east3_cpp_bridge.py`, `test_noncpp_east3_contract_guard.py`
- Per-language backends:
- `test_py2{rs,cs,js,ts,go,java,swift,kotlin,rb,lua,php,nim}_smoke.py`, `test_check_py2scala_transpile.py`, `test_py2scala_smoke.py`
- `ir`:
- `test_east1_build.py`, `test_east2_to_east3_lowering.py`, `test_east3_*.py`, `test_east_core.py`, `test_east_stage_boundary_guard.py`
- `tooling`:
- `test_docs_ja_guard.py`, `test_gen_makefile_from_manifest.py`, `test_ir2lang_cli.py`, `test_pytra_cli.py`, `test_runtime_parity_check_cli.py`
- `selfhost`:
- `test_check_selfhost_cpp_diff.py`, `test_prepare_selfhost_source.py`, `test_selfhost_virtual_dispatch_regression.py`
- `common`:
- Remaining 23 files (`test_code_emitter.py`, `test_py2x_smoke_common.py`, `test_pylib_*.py`, `test_language_profile.py`, etc.)
