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
- [ ] [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S1-01] Inventory quality gaps in `sample/kotlin/01` (redundant cast / loop / no-op / `any` fallback) and lock improvement priority.
- [ ] [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S2-01] Reduce same-type conversion chains in Kotlin emitter numeric output and prioritize typed paths.
- [ ] [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S2-02] Add fastpath to lower simple `range` loops into canonical loops.
- [ ] [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S2-03] Connect `write_rgb_png` from no-op to native runtime call, and fail closed when unresolved.
- [ ] [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S2-04] Add typed-container fastpath in `sample/01` `pixels` path to suppress `MutableList<Any?>` fallback.
- [ ] [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S3-01] Add regression tests (code fragments + parity) and lock regenerated diffs of `sample/kotlin/01`.

Decision Log:
- 2026-03-01: Per user instruction, we finalized the policy to plan `sample/kotlin/01` quality improvement as P1 and add it to TODO.
