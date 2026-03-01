# P0: `range(len-1, -1, -1)` Multilingual Regression (Add Test + Pass All Backends)

Last updated: 2026-03-01

Related TODO:
- `ID: P0-MULTILANG-DOWNRANGE-01` in `docs/ja/todo/index.md`

Background:
- In the context of C# self-hosting, we confirmed cases where `range(len-1, -1, -1)` (downcount range) does not work correctly.
- Further investigation confirmed the same defect also exists in `js/ts/rs` (inconsistent mode resolution when converting `ForCore -> ForRange`).
- There is currently no shared regression test in `test/` that pins this case, so recurrence cannot be detected.

Goal:
- Add a shared downcount-range case to `test/`, and pass transpile/execution (where possible) across all backends.
- Unify mode resolution for `ForCore(StaticRangeForPlan)` across backends and correctly handle `range(len-1, -1, -1)`.

In scope:
- `test/fixtures/*` (add new case)
- `test/unit/test_py2cs_smoke.py`
- `test/unit/test_py2js_smoke.py`
- `test/unit/test_py2ts_smoke.py`
- `test/unit/test_py2rs_smoke.py`
- `src/hooks/cs/emitter/cs_emitter.py`
- `src/hooks/js/emitter/js_emitter.py`
- `src/hooks/rs/emitter/rs_emitter.py`
- `src/pytra/compiler/east_parts/code_emitter.py` (if needed: shared mode-resolution helper)
- `tools/runtime_parity_check.py` (if needed: new fixture wiring)

Out of scope:
- Performance optimization across all existing samples
- Loop spec changes outside `range`
- Backend-specific style optimization (parentheses/formatting)

Acceptance criteria:
- A shared fixture that includes `range(len-1, -1, -1)` is added under `test/`.
- Transpilation for that fixture succeeds on `cpp/rs/cs/js/ts/go/java/swift/kotlin/ruby/lua`.
- For runnable backends (those with available toolchains in CI/local), expected values match (example: `sum_rev([1,2,3]) == 6`).
- In `cs/js/ts/rs`, generated loop conditions do not become an incorrect ascending condition (for example `i < -1`).
- Existing transpile/smoke/parity paths pass without regression.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
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
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2*smoke.py' -v`
- `python3 tools/runtime_parity_check.py --case-root fixture --targets cpp,rs,cs,js,ts,go,java,swift,kotlin,ruby,lua <new_case> --ignore-unstable-stdout`

Breakdown:
- [x] [ID: P0-MULTILANG-DOWNRANGE-01-S1-01] Add a minimal fixture for `range(len-1, -1, -1)` to `test/fixtures` and pin expected output.
- [x] [ID: P0-MULTILANG-DOWNRANGE-01-S1-02] Reproduce and record baseline logs for currently failing backends (`cs/js/ts/rs`) and passing backends.
- [x] [ID: P0-MULTILANG-DOWNRANGE-01-S2-01] Unify range-mode resolution for `ForCore(StaticRangeForPlan)` and derive descending/ascending/dynamic from `step` when `iter_plan` is absent.
- [x] [ID: P0-MULTILANG-DOWNRANGE-01-S2-02] Remove the fixed `range_mode='ascending'` fallback in `ForCore -> ForRange` conversion for `cs/js/rs` emitters and use the shared resolution result.
- [x] [ID: P0-MULTILANG-DOWNRANGE-01-S2-03] Add the same-case regression to `ts` (JS preview path) and pin that the `js` fix is reflected.
- [x] [ID: P0-MULTILANG-DOWNRANGE-01-S3-01] Add the fixture case to smoke/transpile tests for each backend and make recurrence detection continuous.
- [x] [ID: P0-MULTILANG-DOWNRANGE-01-S3-02] Verify expected-value parity on runnable targets and record results in the decision log.

Decision log:
- 2026-03-01: Per user instruction, we created this as P0 multilingual regression for `range(len-1, -1, -1)` and fixed the strategy to prioritize test addition + passing all backends.
- 2026-03-01: Added minimal fixture `test/fixtures/control/range_downcount_len_minus1.py` and pinned it to a simple output case without `py_assert_stdout` dependency (expected value `10`).
- 2026-03-01: Added `CodeEmitter.resolve_forcore_static_range_mode()` and implemented a shared path that determines `ascending/descending/dynamic` from constant `step` even when `iter_plan.range_mode` is missing.
- 2026-03-01: Removed fixed `range_mode='ascending'` from `ForCore -> ForRange` conversion in `cs/js/rs`, and switched to shared mode resolution results. For `dynamic`, it now generates sign-branch conditions on `step`.
- 2026-03-01: Added downcount regression to `ts` (JS preview) and pinned that `for (...; i > -1; ... )` is emitted.
- 2026-03-01: Parity run found a negative-step stop-boundary off-by-one in Lua (`stop-1`), so we fixed Lua emitter `static_fastpath` to `descending => stop+1` and added a dynamic-step branch path.
- 2026-03-01: Verification results
  - `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2js_smoke.py' -v` pass (22)
  - `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2ts_smoke.py' -v` pass (15)
  - `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cs_smoke.py' -v` pass (44)
  - `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2rs_smoke.py' -v` pass (29)
  - `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2lua_smoke.py' -v` pass (19)
  - `python3 tools/runtime_parity_check.py --case-root fixture --targets cpp,rs,cs,js,ts,go,java,swift,kotlin,ruby,lua range_downcount_len_minus1` pass (`ok=10`, `swift=toolchain_missing`)
