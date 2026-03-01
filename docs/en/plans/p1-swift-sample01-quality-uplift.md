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
- `test/unit/test_py2swift_*`
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
- `python3 tools/check_py2swift_transpile.py`
- `python3 tools/regenerate_samples.py --langs swift --force`
- `python3 tools/runtime_parity_check.py --case-root sample --targets swift 01_mandelbrot`

Breakdown:
- [ ] [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S1-01] Inventory quality gaps in `sample/swift/01` (redundant cast / loop / no-op / `any` fallback) and lock improvement priority.
- [ ] [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S2-01] Reduce same-type conversion chains in Swift emitter numeric output and prioritize typed paths.
- [ ] [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S2-02] Add fastpath that lowers simple `range` loops into canonical loops.
- [ ] [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S2-03] Connect `write_rgb_png` from no-op to native runtime call, and fail closed when unresolved.
- [ ] [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S2-04] Add typed-container fastpath in `sample/01` `pixels` path to suppress `[Any]` fallback.
- [ ] [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S3-01] Add regression tests (code fragments + parity) and lock regenerated diffs of `sample/swift/01`.

Decision Log:
- 2026-03-01: Per user instruction, we finalized the policy to plan `sample/swift/01` quality improvement as P1 and add it to TODO.
