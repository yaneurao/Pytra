<a href="../../../ja/plans/archive/20260312-p1-go-sample01-quality-uplift.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: Improve `sample/go/01` quality and narrow the gap with C++

Last updated: 2026-03-02

Related TODO:
- `ID: P1-GO-SAMPLE01-QUALITY-01` in `docs/ja/todo/index.md`

Background:
- `sample/go/01_mandelbrot.go` has lower generated-code quality than `sample/cpp/01_mandelbrot.cpp`.
- The main differences are:
  - Numeric expressions contain repeated `__pytra_float` and `__pytra_int` insertions, hurting readability and runtime efficiency.
  - Even simple forward loops are lowered through a generic step-based form, making them verbose.
  - Image output is disabled as `__pytra_noop(...)`, so the generated program is functionally incomplete.
  - There are many `[]any` fallbacks, so optimizations based on type information are not effective.

Goal:
- Raise the Go backend output for `sample/01` to practical native-code quality and reduce the gap from the C++ output.

Scope:
- `src/hooks/go/emitter/*`
- `src/runtime/go/pytra/*` where needed
- `tools/unittest/test_py2go_*`
- Regeneration of `sample/go/01_mandelbrot.go`

Out of scope:
- Bulk optimization across all Go backend cases
- Large additions to the EAST3 optimization specification
- Adjustments on the C++ or Rust backend side

Acceptance criteria:
- PNG output in `sample/go/01_mandelbrot.go` becomes a real function call instead of a no-op.
- Same-type `__pytra_float` and `__pytra_int` chains are significantly reduced in numeric hot paths.
- Where lowering to `for i := 0; i < n; i++` style is possible, canonical loops are preferred.
- Typed containers are preferred for `pixels` and similar paths in `sample/go/01_mandelbrot.go`, minimizing fallback to `[]any`.
- Unit checks, transpile checks, and sample parity all pass.

Verification commands:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2go*.py' -v`
- `python3 tools/check/check_py2go_transpile.py`
- `python3 tools/gen/regenerate_samples.py --langs go --force`
- `python3 tools/check/runtime_parity_check.py --case-root sample --targets go 01_mandelbrot`

Breakdown:
- [x] [ID: P1-GO-SAMPLE01-QUALITY-01-S1-01] Inventory the quality gaps in `sample/go/01`, redundant casts, loop shape, no-op image output, and `any` fallback, and fix the improvement priority order.
- [x] [ID: P1-GO-SAMPLE01-QUALITY-01-S2-01] Reduce same-type conversion chains in Go emitter numeric output and prioritize typed paths.
- [x] [ID: P1-GO-SAMPLE01-QUALITY-01-S2-02] Add a fast path that lowers `range(stop)` and `range(start, stop, 1)` to canonical `for`.
- [x] [ID: P1-GO-SAMPLE01-QUALITY-01-S2-03] Replace the no-op `write_rgb_png` path with a native runtime call and fail closed when unresolved.
- [x] [ID: P1-GO-SAMPLE01-QUALITY-01-S2-04] Add a typed-container fast path for the `pixels` hot path in `sample/01` to reduce `[]any` fallback.
- [x] [ID: P1-GO-SAMPLE01-QUALITY-01-S3-01] Add regression tests, code fragments plus parity, and lock the regenerated diff for `sample/go/01`.

Decision log:
- 2026-03-01: At the user's request, planned the quality improvement of `sample/go/01` as a P1 task and fixed the policy of adding it to TODO.
- 2026-03-01: Compared `sample/go/01_mandelbrot.go` with `sample/cpp/01_mandelbrot.cpp` and fixed the priority order as follows:
  - P1: Functional loss where `write_rgb_png` falls back to `__pytra_noop(...)`
  - P2: Hot-path degradation where `pixels` falls back to `[]any` and `append` is wrapped in `__pytra_as_list`
  - P3: Redundant same-type cast chains in `__pytra_float` and `__pytra_int`, such as `__pytra_float(float64(...))`
  - P4: Redundant lowering where `range(..., step=1)` still emits a generic step-branch loop like `(__step>=0 && ...) || ...`
- 2026-03-02: Completed `S2-01`. Added fast paths for known-type numeric casts in `_render_binop_expr`, `_render_compare_expr`, math calls, and assignment casts, reducing doubled `__pytra_float` and `__pytra_int`. Regenerating `sample/go/01_mandelbrot.go` confirmed reduced forms such as `var x2 float64 = (x * x)`. `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2go_smoke.py' -v` passed. The four failures in `python3 tools/check/check_py2go_transpile.py`, unsupported `Try`, `Yield`, and `Swap`, were recorded as known out-of-scope categories.
- 2026-03-02: Completed `S2-02`. Added a constant-step fast path to `StaticRangeForPlan`, changing `step==1` into `for i := start; i < stop; i += 1` and `step==-1` into `for i := start; i > stop; i -= 1`. Regenerating `sample/go/01_mandelbrot.go` confirmed forms such as `for i := int64(0); i < max_iter; i += 1` and forward canonical loops for `y` and `x`. `test_py2go_smoke` passed, and the four failures in `check_py2go_transpile` remained the same known unsupported categories.
- 2026-03-02: Completed `S2-03`. Removed the no-op image-API route and connected `write_rgb_png`, `save_gif`, and `grayscale_palette` to Go runtime hooks, `__pytra_write_rgb_png`, `__pytra_save_gif`, and `__pytra_grayscale_palette`. `save_gif` now accepts the keywords `delay_cs` and `loop`, while unsupported keywords fail closed. After `python3 tools/gen/regenerate_samples.py --langs go --force`, `sample/go/01` now calls `__pytra_write_rgb_png(...)` and `sample/go/05` calls `__pytra_save_gif(..., int64(5), int64(0))`. In `runtime_parity_check`, `01_mandelbrot` still showed `artifact_size_mismatch`, `python:5761703`, `go:5761708`, so the final parity convergence was deferred to `S3-01`.
- 2026-03-02: Completed `S2-04`. Added typed fast paths for `append` and `pop` on `[]any` owners, reducing `append(__pytra_as_list(pixels), ...)` into `append(pixels, ...)`. Regenerating `sample/go/01` confirmed `pixels = append(pixels, r/g/b)`. `test_py2go_smoke` passed, and the four `Try/Yield/Swap` failures in `check_py2go_transpile` were unchanged.
- 2026-03-02: Completed `S3-01`. Added regression fragments to `test_py2go_smoke` for numeric casts, canonical loops, image runtime hooks, and the `pixels` append fast path, and brought `python3 tools/check/runtime_parity_check.py --case-root sample --targets go 01_mandelbrot` to pass, `cases=1 pass=1 fail=0`. The PNG runtime was aligned with the Python implementation's stored-deflate output. `tools/check/check_py2go_transpile.py` was also aligned with the same expected-fail set used by the other backends, `finally/try_raise/yield_generator_min/tuple_assign`, and confirmed as `checked=131 ok=131 fail=0 skipped=10`.
