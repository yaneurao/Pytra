<a href="../../ja/plans/p1-kotlin-sample01-quality-uplift.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: `sample/kotlin/01` Quality Uplift (Narrowing the Gap vs C++ Quality)

Last updated: 2026-03-01

Related TODO:
- `ID: P1-KOTLIN-SAMPLE01-QUALITY-01` in `docs/ja/todo/index.md`

Background:
- `sample/kotlin/01_mandelbrot.kt` has a large quality gap compared with `sample/cpp/01_mandelbrot.cpp`.
- Major gaps are:
  - Image output falls back to `__pytra_noop(...)`, causing functional loss in generated code.
  - Same-type wrappers `__pytra_float` / `__pytra_int` are inserted repeatedly in numeric expressions, hurting readability and runtime efficiency.
  - Simple loops are lowered into `while` with `__step_*`, causing redundancy.
  - Fallback to `MutableList<Any?>` is frequent, so typed-container optimization is not effective.

Objective:
- Raise Kotlin backend output quality for `sample/01` to native quality and reduce the gap from C++ output.

Scope:
- `src/hooks/kotlin/emitter/*`
- `src/runtime/kotlin/pytra/*` (as needed)
- `test/unit/test_py2kotlin_*`
- Regenerate `sample/kotlin/01_mandelbrot.kt`

Out of scope:
- Bulk optimization across all Kotlin backend cases
- Large EAST3 spec expansion
- Concurrent modifications on C++/Go backend sides

Acceptance Criteria:
- In `sample/kotlin/01_mandelbrot.kt`, PNG output becomes a real runtime function call instead of no-op.
- Same-type `__pytra_float/__pytra_int` chains are significantly reduced on numeric hot paths.
- Simple cases of `range(stop)` / `range(start, stop, 1)` are lowered into canonical loops.
- In hot paths such as `pixels`, fallback to `MutableList<Any?>` is minimized and typed containers are preferred.
- unit/transpile/parity pass.

Validation Commands:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2kotlin*.py' -v`
- `python3 tools/check_py2kotlin_transpile.py`
- `python3 tools/regenerate_samples.py --langs kotlin --force`
- `python3 tools/runtime_parity_check.py --case-root sample --targets kotlin 01_mandelbrot`

Breakdown:
- [x] [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S1-01] Inventory quality gaps in `sample/kotlin/01` (redundant cast / loop / no-op / `any` fallback) and lock improvement priority.
- [x] [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S2-01] Reduce same-type conversion chains in Kotlin emitter numeric output and prioritize typed paths.
- [x] [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S2-02] Add fastpath to lower simple `range` loops into canonical loops.
- [x] [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S2-03] Connect `write_rgb_png` from no-op to native runtime call, and fail closed when unresolved.
- [x] [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S2-04] Add typed-container fastpath in `sample/01` `pixels` path to suppress `MutableList<Any?>` fallback.
- [x] [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S3-01] Add regression tests (code fragments + parity) and lock regenerated diffs of `sample/kotlin/01`.

Decision Log:
- 2026-03-01: Per user instruction, we finalized the policy to plan `sample/kotlin/01` quality improvement as P1 and add it to TODO.
- 2026-03-02: [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S1-01] We audited `sample/kotlin/01_mandelbrot.kt` and fixed key bottlenecks at `__pytra_float` 78 calls / `__pytra_int` 41 calls / `__pytra_noop(write_rgb_png)` 1 call / 3 `while ((...))` sites / 3 `pixels` re-wraps. Priority was fixed as `S2-03(write_rgb_png) -> S2-01(cast reduction) -> S2-02(canonical loop) -> S2-04(append typed fastpath)`.
- 2026-03-02: [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S2-01] Added runtime-cast normalization (remove redundant same-type wrapping) and `_needs_cast` checks in the Kotlin emitter, reducing unnecessary `__pytra_float/__pytra_int` around assignment/return/arithmetic.
- 2026-03-02: [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S2-02] Added a `step==1` fastpath in `ForCore(StaticRangeForPlan)` and canonicalized `while ((...))` forms to `while (i < stop)`.
- 2026-03-02: [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S2-03] Wired `write_rgb_png` directly to `__pytra_write_rgb_png(...)` in the emitter and added a `BufferedImage`/`ImageIO`-based implementation in `src/runtime/kotlin/pytra/py_runtime.kt`, removing the no-op.
- 2026-03-02: [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S2-04] Added an append fastpath when `MutableList<Any?>` is already known, reducing `pixels = __pytra_as_list(...); pixels.add(...)` to `pixels.add(...)`.
- 2026-03-02: [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S3-01] Added regression tests and passed `test_py2kotlin_smoke` (14), `check_py2kotlin_transpile` (131), and `runtime_parity_check(sample/01,kotlin)`. In `sample/kotlin/01`, `__pytra_float` reduced 78->10, `__pytra_int` 41->17, and `__pytra_noop` 1->0.
