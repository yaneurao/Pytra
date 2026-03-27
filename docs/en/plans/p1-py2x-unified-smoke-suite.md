<a href="../../ja/plans/p1-py2x-unified-smoke-suite.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: Unified `py2x` Smoke Test Integration (All Languages)

Last updated: 2026-03-04

Related TODO:
- `ID: P1-PY2X-SMOKE-UNIFY-01` in `docs/ja/todo/index.md`

Background:
- `test/unit/test_py2*_smoke.py` duplicates common verification viewpoints across languages (CLI path, `--east-stage 2` rejection, minimal fixture conversion).
- On the other hand, output fragments and runtime-contract checks are highly language-specific, so blindly unifying into one file reduces regression detection strength.
- Since `py2x` is now the canonical entrypoint, shared viewpoints can be consolidated as `py2x`-based parameterized smoke tests.

Goal:
- Consolidate common smoke viewpoints for all languages into one shared `py2x`-based test suite.
- Reduce language-specific smoke tests to "contracts unique to that language" only, removing duplication.

In scope:
- Inventory common smoke viewpoints scattered across `test/unit/test_py2*_smoke.py`
- Add shared smoke tests in `test/unit` (target-parameterized)
- Reduce already-shared cases from each language smoke and reorganize around language-specific cases
- Confirm consistency with `tools/check_py2*_transpile.py` and existing unit execution paths

Out of scope:
- Backend code generation quality improvements
- Parity test spec changes
- Selfhost multi-stage spec changes

Acceptance criteria:
- Shared smoke viewpoints (CLI success, `--east-stage 2` rejection, basic transpilation) run for all targets via one shared test suite.
- Each `test_py2*_smoke.py` is reorganized around language-specific contract checks, with reduced duplication of shared viewpoints.
- Major `test_py2*_smoke.py` and `check_py2*_transpile.py` pass.
- When new targets are added, minimum regression coverage is activated by adding one entry in the shared smoke suite.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `python3 -m unittest discover -s test/unit -p 'test_py2x_smoke*.py'`
- `python3 -m unittest discover -s test/unit -p 'test_py2*_smoke.py'`
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

- [x] [ID: P1-PY2X-SMOKE-UNIFY-01-S1-01] Inventory common and language-specific viewpoints in `test_py2*_smoke.py` and finalize commonization targets.
- [x] [ID: P1-PY2X-SMOKE-UNIFY-01-S2-01] Add new shared smoke tests parameterized by `py2x` target.
- [x] [ID: P1-PY2X-SMOKE-UNIFY-01-S2-02] Reduce already-commonized cases from each language smoke and keep only language-specific checks.
- [x] [ID: P1-PY2X-SMOKE-UNIFY-01-S2-03] Explicitly document responsibility boundaries between shared and language-specific smoke in test-code comments and this plan.
- [x] [ID: P1-PY2X-SMOKE-UNIFY-01-S3-01] Run unit/transpile regressions and confirm no regression after integration.
- [x] [ID: P1-PY2X-SMOKE-UNIFY-01-S3-02] Reflect smoke-test operational rules in `docs/ja/spec` (and `docs/en/spec` if needed).

Decision log:
- 2026-03-04: Per user instruction, adopted "one smoke suite for all languages." To preserve detection power, final structure is two-tier: "shared smoke + language-specific smoke".
- 2026-03-04: Completed `S1-01`. Inventoried test names in 14 files under `test/unit/test_py2*_smoke.py` and fixed commonization targets. Targets moved to shared smoke: `(A) stage2 rejection` (14/14), `(B) minimal CLI success` (14/14), `(C) load_east default/from_json + profile loading` (13/14), `(D) add fixture minimal transpile` (13/14). Since `py2cpp` does not have `load_east/profile`, policy was fixed so shared smoke requires `py2x` CLI check + stage2 rejection for `target=cpp`, while `load_east/profile` is required for non-cpp 13 languages. Language-specific viewpoints total 192 tests after removing duplicates; `S2-02` reduces only shared viewpoints from per-language smoke.
- 2026-03-04: Completed `S2-01`. Added `test/unit/test_py2x_smoke_common.py` and implemented shared smoke via `py2x --target` parameterization. Added `minimal CLI success` and `stage2 rejection` for all 14 languages, plus `load_east default/from_json` and `add fixture transpile` for non-cpp 13 languages, and core-hook checks in non-cpp backend specs. Confirmed `OK` with `PYTHONPATH=src:. python3 -m unittest discover -s test/unit -p 'test_py2x_smoke*.py' -v` (6 tests).
- 2026-03-04: Completed `S2-02`. Reduced already-commonized cases from all 14 existing `test_py2*_smoke.py` files (CLI success / `--east-stage 2` rejection / `load_east default+json` / `add fixture`) and kept only language-specific verification. Total reductions: 53 tests (`py2cpp` 1 + non-cpp 13 languages x 4). `PYTHONPATH=src:. python3 -m unittest discover -s test/unit -p 'test_py2*_smoke.py' -v` reported 232 tests `OK`; `test_py2x_smoke*.py` reported 6 tests `OK`.
- 2026-03-04: Completed `S2-03`. Added module documentation in `test_py2x_smoke_common.py` to state shared responsibilities explicitly, and added comments to all 14 files (`test_py2{cpp,rs,cs,js,ts,go,java,swift,kotlin,rb,lua,scala,php,nim}_smoke.py`) stating they retain only language-specific responsibilities. Reconfirmed `OK` for `test_py2x_smoke*.py` (6 tests) and `test_py2*_smoke.py` (232 tests) with boundaries explicit in code.
- 2026-03-04: Completed `S3-01`. During regression runs, `check_py2js_transpile.py` failed because `check_noncpp_east3_contract.py` assumed the old structure (shared cases still present in each language smoke). Updated that script to the new structure: added required-pattern checks for `test_py2x_smoke_common.py`, and enforced required boundary comments + forbidden shared-case functions in language-specific smoke. After updates, all `check_py2{cpp,rs,cs,js,ts,go,java,swift,kotlin,rb,lua,scala,php,nim}_transpile.py` were `OK`, plus `test_py2x_smoke*.py` 6 tests `OK` and `test_py2*_smoke.py` 232 tests `OK`.
- 2026-03-04: Completed `S3-02`. Added operational rules to `docs/ja/spec/spec-tools.md` and `docs/en/spec/spec-tools.md`: shared smoke is `test_py2x_smoke_common.py`, and per-language smoke covers only language-specific contracts. Also documented recommended regression order including `check_noncpp_east3_contract.py` (shared smoke -> language-specific smoke -> transpile checks).

## S1-01 Inventory Results (2026-03-04)

- Target: 14 files in `test/unit/test_py2*_smoke.py` (`cpp,rs,cs,js,ts,go,java,swift,kotlin,rb,lua,scala,php,nim`)
- Aggregate results (function-name basis):
  - Common candidate A: `stage2` rejection tests 14/14
  - Common candidate B: minimal CLI success tests 14/14 (with naming differences)
  - Common candidate C: `load_east_defaults_to_stage3...` + `load_east_from_json` + `load_<lang>_profile_contains_core_sections` 13/14 (except cpp)
  - Common candidate D: `transpile_add_fixture_*` 13/14 (except cpp)
  - Language-specific tests: 192 (mainly emitter/runtime contracts)
- Minimal responsibilities for shared smoke to add in `S2-01`:
  - All 14 languages: minimal `py2x` CLI success / `--east-stage 2` rejection
  - Non-cpp 13 languages: `load_east` default/from_json / profile / add-fixture transpile
- In `S2-02`, only the shared responsibilities above are reduced from each language smoke; language-specific contracts (generated-code fragments, runtime connectivity, language-specific regressions) remain.
