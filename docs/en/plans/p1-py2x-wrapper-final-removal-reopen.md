# P1: Recover Remaining Work for `py2x` Unification (Complete Removal of Legacy `py2*.py` Wrappers)

Last updated: 2026-03-04

Related TODO:
- `ID: P1-PY2X-WRAPPER-REMOVE-REOPEN-01` in `docs/ja/todo/index.md`

Background:
- `P1-PY2X-SINGLE-ENTRY-01` is already archived, but legacy wrappers such as `src/py2rs.py` / `src/py2cs.py` still remain as real files.
- `tools/check_multilang_selfhost_stage1.py`, `tools/check_noncpp_east3_contract.py`, and `test/unit/test_py2*_smoke.py` still depend on wrapper filenames.
- In this state, even if we claim to have unified to `py2x.py`, actual operations still maintain wrappers.

Goal:
- Finalize `py2x.py` (regular) / `py2x-selfhost.py` (self-host) as the only CLI entrypoints.
- Remove the `src/py2*.py` wrapper set and `toolchain/compiler/py2x_wrapper.py`.
- Replace wrapper-dependent checks/regressions with `py2x`-based checks and prevent reintroduction.

Scope:
- `src/py2{rs,cs,js,ts,go,java,kotlin,swift,rb,lua,scala,php,nim}.py` and `toolchain/compiler/py2x_wrapper.py`
- Replacement in `tools/` / `test/` / `docs/` where wrapper names are directly referenced
- Recurrence-prevention guardrails (static checks)

Out of scope:
- Quality improvements to backend conversion logic
- Expansion of self-host multistage specs
- EAST spec changes

Acceptance criteria:
- Under `src/`, only `py2x.py` and `py2x-selfhost.py` remain as `py2*.py` files.
- No references remain in `tools/` / `test/` / `docs/` to `src/py2{rs,cs,js,ts,go,java,kotlin,swift,rb,lua,scala,php,nim}.py`.
- Major transpile checks and smoke tests pass after wrapper removal.
- Wrapper reintroduction is detected fail-fast in CI/local checks.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `rg -n "src/py2(rs|cs|js|ts|go|java|kotlin|swift|rb|lua|scala|php|nim)\\.py" src tools test docs`
- `python3 tools/check_legacy_cli_references.py`
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

## S1-01 Inventory Results (2026-03-04)

- `tools` (highest-priority replacement):
  - direct CLI references: `check_noncpp_east3_contract.py`, `check_transpiler_version_gate.py`
  - self-host references: `check_multilang_selfhost_stage1.py`, `check_multilang_selfhost_multistage.py`, `prepare_selfhost_source_cs.py`, `check_cs_single_source_selfhost_compile.py`
- `test/unit` (second-priority replacement):
  - wrapper module import dependency: `test_py2{rs,cs,js,ts,go,java,kotlin,swift,rb,lua,scala,php,nim}_smoke.py` (13 files)
  - wrapper concrete-file string dependency (checks that read `ROOT / "src" / "py2*.py"`): `test_py2{rs,cs,js,ts,go,java,kotlin,swift,rb,lua,scala}_smoke.py` (11 files)
- `docs` (replace actual operational path first):
  - user-facing: `docs/ja/how-to-use.md`, `docs/en/how-to-use.md`
  - spec: `py2*.py` names remain in `docs/ja/spec/*.md`, `docs/en/spec/*.md`
  - history-oriented `docs/*/plans` / `docs/*/todo/archive` are kept as factual records; `S2-03` prioritizes replacement in operational docs

Replacement order (fixed):
1. In `S2-01`, update direct wrapper references in `tools` to `py2x.py` / `py2x-selfhost.py` and backend module references.
2. In `S2-02`, update import/string dependencies in `test/unit` to `py2x`-based references.
3. In `S2-03`, update operational/spec docs in `docs/ja|en` to the canonical `py2x` entrypoints.
4. In `S3-01`, delete wrapper set `src/py2*.py` and `toolchain/compiler/py2x_wrapper.py`.
5. In `S3-02/S3-03`, lock with reintroduction guards and regression checks.

## Breakdown

- [x] [ID: P1-PY2X-WRAPPER-REMOVE-REOPEN-01-S1-01] Re-inventory remaining wrapper references across `tools/test/docs/selfhost` and finalize replacement order.
- [x] [ID: P1-PY2X-WRAPPER-REMOVE-REOPEN-01-S2-01] Replace direct wrapper references in `tools/` with `py2x` / backend module references.
- [x] [ID: P1-PY2X-WRAPPER-REMOVE-REOPEN-01-S2-02] Replace wrapper-file-dependent tests in `test/unit` with `py2x`-based or backend-module-based tests.
- [x] [ID: P1-PY2X-WRAPPER-REMOVE-REOPEN-01-S2-03] Update wrapper-name references in `docs/ja` / `docs/en` to canonical `py2x` entrypoints.
- [x] [ID: P1-PY2X-WRAPPER-REMOVE-REOPEN-01-S3-01] Delete wrapper set `src/py2*.py` and `toolchain/compiler/py2x_wrapper.py` (`py2x.py` / `py2x-selfhost.py` excluded).
- [x] [ID: P1-PY2X-WRAPPER-REMOVE-REOPEN-01-S3-02] Update static guards to detect wrapper reintroduction and lock the post-removal layout.
- [x] [ID: P1-PY2X-WRAPPER-REMOVE-REOPEN-01-S3-03] Run transpile/smoke regressions and verify non-regression after wrapper removal.

Decision log:
- 2026-03-04: Returned archived `P1-PY2X-SINGLE-ENTRY-01` as a reopen item. Redefined completion criteria from "introduce `py2x`" to "remove legacy wrapper concrete files."
- 2026-03-04: As `S1-01`, re-inventoried wrapper references across `tools/test/docs/selfhost`, and fixed replacement order as "tools -> test -> docs -> wrapper removal -> guard/regression."
- 2026-03-04: As a lead-in to `S2-01`, removed wrapper-concrete-file assumptions in `tools/check_noncpp_east3_contract.py` and restructured checks around `py2x.py` + backend layer + smoke contracts. Also replaced language direct dependencies in `tools/check_transpiler_version_gate.py` from `src/py2*.py` to `src/py2x.py`, and removed those two files from the allowlist in `tools/check_legacy_cli_references.py` to block reintroduction.
- 2026-03-04: Completed `S2-01`. Updated `tools/check_multilang_selfhost_stage1.py` / `tools/check_multilang_selfhost_multistage.py` to `src/py2x.py --target <lang>`, and made `--target` explicit for JS/RS/CS stage2/stage3 executions as well. Simplified `tools/prepare_selfhost_source_cs.py` to `src/py2x.py -> selfhost/py2x_cs.py` seed generation, and moved `tools/check_cs_single_source_selfhost_compile.py` to the `py2x` basis. Confirmed `rg -n "py2(rs|cs|js|ts|go|java|kotlin|swift|rb|lua|scala|php|nim)\\.py" tools` returns 0, and related tool runs (stage1/multistage/cs-single-source) do not crash.
- 2026-03-04: Completed `S2-02`. Replaced wrapper import / wrapper concrete-file string dependencies in `test/unit/test_py2{rs,cs,js,ts,go,java,kotlin,swift,rb,lua,scala,php,nim}_smoke.py` with backend-module + `load_east3_document(..., target_lang=<lang>)` basis, and aligned Lua smoke with runtime externalization (`dofile("py_runtime.lua")`) expectations. Confirmed `OK` on `PYTHONPATH=src:. python3 -m unittest discover -s test/unit -p 'test_py2*_smoke.py' -v` (298 tests).
- 2026-03-04: Completed `S2-03`. Unified execution examples in operational docs around `py2x.py --target <lang>`, and updated `how-to-use` wrapper notes to deprecation/phased-removal policy. Replaced `src/py2cpp.py` assumptions in `spec-runtime/spec-options/spec-east/spec-east3-optimizer/spec-dev/spec-tools` (ja/en) with `src/py2x.py --target cpp` or `src/toolchain/emit/cpp/cli.py`, and standardized self-host sync procedure to `python3 tools/prepare_selfhost_source.py`. Confirmed `rg -n "python3?\\s+src/py2(rs|cs|js|ts|go|java|kotlin|swift|rb|lua|scala|php|nim|cpp)\\.py" docs/ja docs/en --glob '!**/plans/**' --glob '!**/todo/**' --glob '!**/archive/**' --glob '!**/language/**'` returns 0.
- 2026-03-04: Completed `S3-01`. Deleted `src/py2{rs,cs,js,ts,go,java,kotlin,swift,rb,lua,scala,php,nim}.py` and `src/toolchain/compiler/py2x_wrapper.py`, then resolved remaining dependencies by migrating `test/unit/test_error_classification_cross_lang.py` to `load_east3_document(..., target_lang=...)` and updating the anchor in `src/toolchain/emit/cs/emitter/cs_emitter.py` to `src/py2x.py`. Regression checks passed: `python3 tools/check_legacy_cli_references.py`, `python3 -m unittest discover -s test/unit -p 'test_error_classification_cross_lang.py' -v`, and `PYTHONPATH=src:. python3 -m unittest discover -s test/unit -p 'test_py2*_smoke.py' -v` (298 tests).
- 2026-03-04: Completed `S3-02`. Updated `tools/check_legacy_cli_references.py` to fail-fast on reintroduction of any `src/py2*.py` concrete file other than `src/py2x.py` / `src/py2x-selfhost.py`, and on regeneration of `toolchain/compiler/py2x_wrapper.py`. Also emptied path/import allowlists to lock the post-removal layout, and confirmed `OK` from `python3 tools/check_legacy_cli_references.py`.
- 2026-03-04: Completed `S3-03`. Ran all `check_py2{cpp,rs,cs,js,ts,go,java,swift,kotlin,rb,lua,scala,php,nim}_transpile.py` and confirmed fail=0, then re-ran `PYTHONPATH=src:. python3 -m unittest discover -s test/unit -p 'test_py2*_smoke.py' -v` (298 tests) with `OK`. Locked transpile/smoke non-regression after wrapper removal.
