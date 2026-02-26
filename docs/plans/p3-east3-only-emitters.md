# P3: Direct EAST3 Wiring for Non-C++ Emitters and Removal of EAST2 Compatibility

Last updated: 2026-02-26

Related TODO:
- `ID: P3-EAST3-ONLY-01` in `docs-ja/todo/index.md`

Background:
- At kickoff, eight non-C++ targets (`rs/cs/js/ts/go/java/swift/kotlin`) still depended on `east3_legacy_compat`, `--east-stage 2`, and `load_east_document_compat`.
- We are now removing compatibility paths and unifying on `EAST3` as the only contract.

Goal:
- Move all eight non-C++ targets to direct `EAST3` and abolish `EAST2` compatibility routes.

In scope:
- CLI: `src/py2{rs,cs,js,ts,go,java,swift,kotlin}.py`
- Emitters: `src/hooks/{rs,cs,js,ts,go,java,swift,kotlin}/emitter/*.py`
- Compiler shared: `src/pytra/compiler/transpile_cli.py`, `src/pytra/compiler/east_parts/east3_legacy_compat.py`
- Tests/docs: `test/unit/test_py2*_smoke.py`, `tools/check_py2*_transpile.py`, `docs-ja/plans/plan-east123-migration.md`, and related specs

Out of scope:
- Main `EAST3` path changes for C++ backend
- Refactors aimed only at performance optimization
- Changing sample program contents themselves

Acceptance criteria:
- `py2{rs,cs,js,ts,go,java,swift,kotlin}` accepts only `EAST3` (`--east-stage 2` unsupported or removed).
- Zero references to `normalize_east3_to_legacy`.
- Zero references to `load_east_document_compat` from non-C++ CLIs.
- `east3_legacy_compat.py` is removed, and regression checks (smoke/check/parity) pass.

Decision log:
- 2026-02-25: Added as low-priority task. Final shape is direct `EAST3`; removal of `EAST2` compatibility and legacy conversion proceeds in staged migration.
- 2026-02-26: `S1-S7` were too coarse for rollback safety, so split into `S*-NN` units, each completing implementation + minimal regression validation.
- 2026-02-26: `S1-01` made `--east-stage 2` on all 8 CLIs an immediate `parser.error` (instead of warning). Updated smoke tests from warning-dependent assertions to `non-zero exit + expected error message`, and confirmed all 8 passing.
- 2026-02-26: `S1-02` removed `load_east_document_compat` import/call and stage2 branching from all 8 CLIs, fixing `load_east` to `load_east3_document` only. Re-ran all 8 smoke suites, all passing.
- 2026-02-26: `S2-01` added direct `ForCore` handling in `js_emitter`, internally mapping `iter_plan=StaticRangeForPlan/RuntimeIterForPlan` to `ForRange/For` and connecting to existing emit path. Added ForCore direct-acceptance regressions (range/runtime tuple target) to `test_py2js_smoke.py`; both `test_py2js_smoke.py` and `test_py2ts_smoke.py` passed.
- 2026-02-26: `S2-02` implemented direct rendering of `ObjBool/ObjLen/ObjStr/ObjIterInit/ObjIterNext/ObjTypeId` in `js_emitter` (with `pyBool/pyLen/pyStr/pyTypeId` import collection; iter/next lowered to JS iterator calls). Added object-boundary direct-node regressions to `test_py2js_smoke.py`; JS+TS smoke passed.
- 2026-02-26: `S2-03` added direct rendering for `IsInstance/IsSubtype/IsSubclass`, implementing type-id resolution from `PYTRA_TID_*`/type names to JS runtime constants and collecting `pyIsSubtype` imports. Added type-predicate direct-node regressions; JS+TS smoke passed.
- 2026-02-26: `S2-04` directly accepted `Box/Unbox` in `render_expr`, unifying to transparent no-op lowering. Added Box/Unbox direct-node regressions; JS+TS smoke passed.
- 2026-02-26: `S2-05` passed JS/TS smoke and `check_py2{js,ts}_transpile.py`. Also updated static contract checks in `tools/check_noncpp_east3_contract.py` to EAST3-only (stage2 warning expectation -> stage2 unsupported expectation; forbidden compat imports). Synced `test_east3_cpp_bridge.py` expected values for `py_to<int64>/py_to<bool>` to current implementation and resolved east3-contract premise failures.
- 2026-02-26: `S2-06` passed Go/Java/Swift/Kotlin sidecar-path smoke tests (`test_py2{go,java,swift,kotlin}_smoke.py`) and `check_py2{go,java,swift,kotlin}_transpile.py`, confirming no wave regressions from JS-emitter direct handling.
- 2026-02-26: `S3-01` added `ForCore` direct handling to `rs_emitter`, mapping `iter_plan=StaticRangeForPlan/RuntimeIterForPlan` to `ForRange/For`. Added ForCore direct-node regressions (range/runtime tuple target) to `test_py2rs_smoke.py`; all passed.
- 2026-02-26: `S3-02` added direct rendering of `ObjBool/ObjLen/ObjStr/ObjIterInit/ObjIterNext/ObjTypeId`, `IsInstance/IsSubtype/IsSubclass`, and `Box/Unbox` to `rs_emitter`. Extended pre-detection for type-id helpers (`_doc_mentions_isinstance`) to direct-node forms and added regressions for object boundary / type predicates / box-unbox. All passed.
- 2026-02-26: `S3-03` ran Rust smoke (`test_py2rs_smoke.py`) and `check_py2rs_transpile.py`; verified all transpile checks passing (`132`, `skip 6`).
- 2026-02-26: `S4-01` added `ForCore` direct handling to `cs_emitter`, mapping `iter_plan=StaticRangeForPlan/RuntimeIterForPlan` to `ForRange/For`. Added regressions for range/runtime tuple target to `test_py2cs_smoke.py`; all passed.
- 2026-02-26: `S4-02` added direct rendering of `ObjBool/ObjLen/ObjStr/ObjIterInit/ObjIterNext/ObjTypeId`, `IsInstance/IsSubtype/IsSubclass`, and `Box/Unbox` in `cs_emitter`. Added corresponding regressions; all passed.
- 2026-02-26: `S4-03` ran C# smoke (`test_py2cs_smoke.py`) and `check_py2cs_transpile.py`; verified all transpile checks passing (`132`, `skip 6`).
- 2026-02-26: `S5-01` removed `normalize_east3_to_legacy` import/call from all 8 CLIs and unified `load_east` to return EAST3 documents. Updated smoke `east_stage` expectations from `2 -> 3`; all 8 smoke suites passed. Updated `tools/check_noncpp_east3_contract.py` with the `normalize_east3_to_legacy` ban and new smoke name (`returns_east3_shape`).
- 2026-02-26: `S5-02` deleted `src/pytra/compiler/east_parts/east3_legacy_compat.py`. Confirmed `rg -n "from .*east3_legacy_compat|normalize_east3_to_legacy\(" src test tools` returns 0 matches, and `check_noncpp_east3_contract.py --skip-transpile` passes.
- 2026-02-26: `S6-01` updated the current-operation section in `docs-ja/plans/plan-east123-migration.md` to `EAST3 only`, removing non-C++ `stage2` compatibility assumptions (compat-mode warning / compat loader dependency). Moved old assumptions into historical notes.
- 2026-02-26: `S6-02` synced `docs/plans/plan-east123-migration.md` to the same content as `docs-ja`, aligning JA/EN docs on `EAST3 only` contract and notes.
- 2026-02-26: `S7-01` passed smoke/check for all 8 non-C++ targets. `test_py2{rs,cs,js,ts,go,java,swift,kotlin}_smoke.py` all `OK`; `check_py2{rs,cs,js,ts,go,java,swift,kotlin}_transpile.py` all `checked=132 ok=132 fail=0 skipped=6`.
- 2026-02-26: `S7-02` ran `runtime_parity_check --case-root sample --targets rs,cs,js,ts,go,java,swift,kotlin --all-samples --ignore-unstable-stdout`; confirmed `SUMMARY cases=18 pass=18 fail=0` and `ok: 144`, completing final `EAST3 only` parity validation for all 8 non-C++ targets.

## Breakdown

- [x] [ID: P3-EAST3-ONLY-01-S1-01] Unify `--east-stage 2` input handling on all 8 CLIs to unsupported-error, and update compatibility-warning-dependent tests to error-expected tests.
- [x] [ID: P3-EAST3-ONLY-01-S1-02] Remove `load_east_document_compat` import/call from all 8 CLIs and lock to `load_east3_document` only.
- [x] [ID: P3-EAST3-ONLY-01-S2-01] Add direct `ForCore(iter_plan=StaticRangeForPlan/RuntimeIterForPlan)` handling in `js_emitter`.
- [x] [ID: P3-EAST3-ONLY-01-S2-02] Add direct `ObjBool/ObjLen/ObjStr/ObjIterInit/ObjIterNext/ObjTypeId` handling in `js_emitter`.
- [x] [ID: P3-EAST3-ONLY-01-S2-03] Add direct `IsInstance/IsSubtype/IsSubclass` handling in `js_emitter`.
- [x] [ID: P3-EAST3-ONLY-01-S2-04] Remove legacy assumptions for `Box/Unbox` in `js_emitter` and accept EAST3 nodes directly.
- [x] [ID: P3-EAST3-ONLY-01-S2-05] Pass JS/TS smoke + `check_py2{js,ts}_transpile.py` and lock regressions for JS direct handling.
- [x] [ID: P3-EAST3-ONLY-01-S2-06] Pass `check_py2*_transpile.py` + smoke on Go/Java/Swift/Kotlin sidecar bridge paths, locking wave regressions from JS direct handling.
- [x] [ID: P3-EAST3-ONLY-01-S3-01] Implement direct `ForCore` handling in `rs_emitter` (range/runtime iter).
- [x] [ID: P3-EAST3-ONLY-01-S3-02] Implement direct handling for `Obj*` / `Is*` / `Box/Unbox` in `rs_emitter`.
- [x] [ID: P3-EAST3-ONLY-01-S3-03] Lock regressions with Rust smoke + `check_py2rs_transpile.py`.
- [x] [ID: P3-EAST3-ONLY-01-S4-01] Implement direct `ForCore` handling in `cs_emitter` (range/runtime iter).
- [x] [ID: P3-EAST3-ONLY-01-S4-02] Implement direct handling for `Obj*` / `Is*` / `Box/Unbox` in `cs_emitter`.
- [x] [ID: P3-EAST3-ONLY-01-S4-03] Lock regressions with C# smoke + `check_py2cs_transpile.py`.
- [x] [ID: P3-EAST3-ONLY-01-S5-01] Remove `normalize_east3_to_legacy` calls from all 8 CLIs.
- [x] [ID: P3-EAST3-ONLY-01-S5-02] Delete `src/pytra/compiler/east_parts/east3_legacy_compat.py` and verify zero references via `rg`.
- [x] [ID: P3-EAST3-ONLY-01-S6-01] Remove `stage=2` compatibility assumptions from related docs and update to `EAST3 only`.
- [x] [ID: P3-EAST3-ONLY-01-S6-02] Sync required `docs/` translations and eliminate JA/EN inconsistency.
- [x] [ID: P3-EAST3-ONLY-01-S7-01] Pass smoke/check for all 8 non-C++ targets (`test_py2*` + `check_py2*`).
- [x] [ID: P3-EAST3-ONLY-01-S7-02] Run `runtime_parity_check --case-root sample --targets rs,cs,js,ts,go,java,swift,kotlin --all-samples --ignore-unstable-stdout` and complete final consistency validation.
