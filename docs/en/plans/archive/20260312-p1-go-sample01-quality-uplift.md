# P1: `sample/go/01` Quality Uplift (Narrowing the Gap vs C++ Quality)

Last updated: 2026-03-01

Related TODO:
- `ID: P1-GO-SAMPLE01-QUALITY-01` in `docs/ja/todo/index.md`

Background:
- `sample/go/01_mandelbrot.go` has lower generated-code quality compared with `sample/cpp/01_mandelbrot.cpp`.
- Major gaps are:
  - Multiple inserted `__pytra_float` / `__pytra_int` in numeric operations, hurting readability and runtime efficiency.
  - Even simple forward loops are lowered through generic step-based lowering, creating redundancy.
  - Image output is disabled as `__pytra_noop(...)`, causing functional loss in generated code.
  - Frequent fallback to `[]any`, so optimizations based on type information are not effective.

Objective:
- Raise Go backend output quality for `sample/01` to a "practically usable native quality" level and reduce the gap from C++ output.

Scope:
- `src/hooks/go/emitter/*`
- `src/runtime/go/pytra/*` (as needed)
- `test/unit/test_py2go_*`
- Regenerate `sample/go/01_mandelbrot.go`

Out of scope:
- Bulk optimization across all Go backend cases
- Major additions to EAST3 optimization specs
- Adjustments on C++/Rust backend sides

Acceptance Criteria:
- In `sample/go/01_mandelbrot.go`, PNG output becomes a real function call instead of no-op.
- Same-type `__pytra_float/__pytra_int` chains are significantly reduced on numeric hot paths.
- For locations lowerable to `for i := 0; i < n; i++`, canonical loops are preferred.
- In `sample/go/01_mandelbrot.go`, typed containers are preferred for `pixels` etc., minimizing fallback to `[]any`.
- unit/transpile checks and sample parity pass.

Validation Commands:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2go*.py' -v`
- `python3 tools/check_py2go_transpile.py`
- `python3 tools/regenerate_samples.py --langs go --force`
- `python3 tools/runtime_parity_check.py --case-root sample --targets go 01_mandelbrot`

Breakdown:
- [ ] [ID: P1-GO-SAMPLE01-QUALITY-01-S1-01] Inventory quality gaps in `sample/go/01` (redundant cast / loop / no-op / `any` fallback), and lock the improvement priority order.
- [ ] [ID: P1-GO-SAMPLE01-QUALITY-01-S2-01] Reduce same-type conversion chains in Go emitter numeric output and prioritize typed paths.
- [ ] [ID: P1-GO-SAMPLE01-QUALITY-01-S2-02] Add a fastpath that lowers `range(stop)` / `range(start, stop, 1)` patterns into canonical `for` loops.
- [ ] [ID: P1-GO-SAMPLE01-QUALITY-01-S2-03] Connect the `write_rgb_png` path from no-op to native runtime call, and fail closed when unresolved.
- [ ] [ID: P1-GO-SAMPLE01-QUALITY-01-S2-04] Add a typed-container fastpath to suppress `[]any` fallback in the `sample/01` `pixels` hot path.
- [ ] [ID: P1-GO-SAMPLE01-QUALITY-01-S3-01] Add regression tests (code fragments + parity) and lock regenerated diffs of `sample/go/01`.

Decision Log:
- 2026-03-01: Per user instruction, we finalized the policy to plan `sample/go/01` quality improvement as P1 and add it to TODO.
