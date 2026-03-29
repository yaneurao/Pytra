<a href="../../ja/plans/p1-swift-sample01-quality-uplift.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: `sample/swift/01` Quality Uplift (Narrowing the Gap vs C++ Quality)

Last updated: 2026-03-01

Related TODO:
- `ID: P1-SWIFT-SAMPLE01-QUALITY-01` in `docs/ja/todo/index.md`

Background:
- `sample/swift/01_mandelbrot.swift` has a large quality gap compared with `sample/cpp/01_mandelbrot.cpp`.
- Major gaps are:
  - Image output falls back to `__pytra_noop(...)`, losing executable functionality.
  - Same-type wrappers `__pytra_float` / `__pytra_int` are repeatedly inserted in numeric operations.
  - Simple loops fall back to `while` lowering with `__step_*`.
  - Frequent fallback to `[Any]` prevents typed-container optimization.

Objective:
- Raise Swift backend output quality for `sample/01` to native quality and reduce the gap from C++ output.

Scope:
- `src/hooks/swift/emitter/*`
- `src/runtime/swift/pytra/*` (as needed)
- `tools/unittest/test_py2swift_*`
- Regenerate `sample/swift/01_mandelbrot.swift`

Out of scope:
- Bulk optimization across all Swift backend cases
- Large EAST3 specification changes
- Concurrent modifications on Go/Kotlin backend sides

Acceptance Criteria:
- In `sample/swift/01_mandelbrot.swift`, PNG output becomes a real runtime function call instead of no-op.
- Same-type `__pytra_float/__pytra_int` chains are significantly reduced on numeric hot paths.
- Simple `range` loops are lowered into canonical loops.
- In hot paths such as `pixels`, fallback to `[Any]` is minimized and typed containers are preferred.
- unit/transpile/parity pass.

Validation Commands:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2swift*.py' -v`
- `python3 tools/check/check_py2swift_transpile.py`
- `python3 tools/gen/regenerate_samples.py --langs swift --force`
- `python3 tools/check/runtime_parity_check.py --case-root sample --targets swift 01_mandelbrot`

Breakdown:
- [x] [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S1-01] Inventory quality gaps in `sample/swift/01` (redundant cast / loop / no-op / `any` fallback) and lock improvement priority.
- [x] [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S2-01] Reduce same-type conversion chains in Swift emitter numeric output and prioritize typed paths.
- [x] [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S2-02] Add fastpath that lowers simple `range` loops into canonical loops.
- [x] [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S2-03] Connect `write_rgb_png` from no-op to native runtime call, and fail closed when unresolved.
- [x] [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S2-04] Add typed-container fastpath in `sample/01` `pixels` path to suppress `[Any]` fallback.
- [x] [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S3-01] Add regression tests (code fragments + parity) and lock regenerated diffs of `sample/swift/01`.

Decision Log:
- 2026-03-01: Per user instruction, we finalized the policy to plan `sample/swift/01` quality improvement as P1 and add it to TODO.
- 2026-03-02: [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S1-01] We audited `sample/swift/01_mandelbrot.swift` and fixed key bottlenecks at `__pytra_float` 78 calls / `__pytra_int` 39 calls / `__pytra_noop(write_rgb_png)` 1 call / 3 `while ((...))` sites / 3 `pixels` re-wraps. Priority was fixed as `S2-03(write_rgb_png) -> S2-01(cast reduction) -> S2-02(canonical loop) -> S2-04(append typed fastpath)`.
- 2026-03-02: [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S2-01] Added runtime-cast normalization (remove redundant same-type wrapping) and `_needs_cast` checks in the Swift emitter, reducing unnecessary `__pytra_float/__pytra_int` around assignment/return/arithmetic.
- 2026-03-02: [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S2-02] Added a `step==1` fastpath in `ForCore(StaticRangeForPlan)` and canonicalized `while ((...))` forms to `while (i < stop)`.
- 2026-03-02: [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S2-03] Wired `write_rgb_png` directly to `__pytra_write_rgb_png(...)` in the emitter and added a pure-Swift PNG writer in `src/runtime/swift/pytra/py_runtime.swift`, removing the no-op.
- 2026-03-02: [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S2-04] Added an append fastpath when `[Any]` is already known, reducing `pixels = __pytra_as_list(...); pixels.append(...)` to `pixels.append(...)`.
- 2026-03-02: [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S3-01] Added regression tests and passed `test_py2swift_smoke` (12), `check_py2swift_transpile` (131), and `runtime_parity_check(sample/01,swift)`. In `sample/swift/01`, `__pytra_float` reduced 78->10, `__pytra_int` 39->17, and `__pytra_noop` 1->0.
