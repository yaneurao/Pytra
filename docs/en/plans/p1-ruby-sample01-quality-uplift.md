<a href="../../ja/plans/p1-ruby-sample01-quality-uplift.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: `sample/ruby/01` Quality Uplift (Narrowing the Gap vs C++ Quality)

Last updated: 2026-03-02

Related TODO:
- `ID: P1-RUBY-SAMPLE01-QUALITY-01` in `docs/ja/todo/index.md`

Background:
- `sample/ruby/01_mandelbrot.rb` has a large quality gap compared with `sample/cpp/01_mandelbrot.cpp`.
- Major gaps are:
  - Simple loops fall back to `while` lowering with `__step_*`, hurting readability and optimization room.
  - Same-type wrappers `__pytra_int` / `__pytra_float` / `__pytra_div` are inserted repeatedly in numeric expressions.
  - `__pytra_truthy` is over-inserted even around comparisons, blocking native Ruby expressions.
  - Unnecessary temporary initializations remain on known-typed paths (e.g., `r/g/b` initialized to `nil`).

Objective:
- Raise Ruby backend output quality for `sample/01` to native quality and reduce the gap from C++ output.

Scope:
- `src/hooks/ruby/emitter/*`
- `src/hooks/common/*` (as needed)
- `src/runtime/ruby/py_runtime.rb` (as needed)
- `test/unit/test_py2ruby_*`
- Regenerate `sample/ruby/01_mandelbrot.rb`

Out of scope:
- Bulk optimization across all Ruby backend cases
- Large EAST3 specification changes
- Concurrent modifications on C++/Go/Kotlin/Swift backend sides

Acceptance Criteria:
- Simple `range` loops in `sample/ruby/01_mandelbrot.rb` are lowered into canonical loops.
- Same-type `__pytra_int/__pytra_float/__pytra_div` chains in numeric hot paths are significantly reduced.
- Over-insertion of `__pytra_truthy` around comparisons/logical expressions is suppressed, and native Ruby conditions are preferred.
- Remove unnecessary temporary initialization (e.g., `r/g/b` `nil` initialization) on typed paths.
- unit/transpile/parity pass.

Validation Commands:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2ruby*.py' -v`
- `python3 tools/check_py2ruby_transpile.py`
- `python3 tools/regenerate_samples.py --langs ruby --force`
- `python3 tools/runtime_parity_check.py --case-root sample --targets ruby 01_mandelbrot`

Breakdown:
- [x] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S1-01] Inventory quality gaps in `sample/ruby/01` (redundant cast / loop / truthy / temporary initialization) and lock improvement priority.
- [x] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S2-01] Reduce same-type conversion chains in Ruby emitter numeric output and prioritize typed paths.
- [x] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S2-02] Add fastpath that lowers simple `range` loops into canonical loops.
- [x] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S2-03] Optimize insertion conditions of `__pytra_truthy` in comparison/logical expressions and prioritize native Ruby conditions.
- [x] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S2-04] Add typed-assignment fastpath in `sample/01` (`r/g/b` etc.) to reduce unnecessary `nil` initialization.
- [x] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S3-01] Add regression tests (code fragments + parity) and lock regenerated diffs of `sample/ruby/01`.

Decision Log:
- 2026-03-01: Per user instruction, we finalized the policy to plan `sample/ruby/01` quality improvement as P1 and add it to TODO.
- 2026-03-02: [ID: P1-RUBY-SAMPLE01-QUALITY-01-S1-01] Audited `sample/ruby/01` and `sample/cpp/01`, and fixed improvement priority.
- 2026-03-02: [ID: P1-RUBY-SAMPLE01-QUALITY-01-S2-02] Added canonical-while fastpath for `step=1/-1` in `ForCore(StaticRange)`, reducing `__step_*` in `sample/ruby/01` from 12 -> 0.
- 2026-03-02: [ID: P1-RUBY-SAMPLE01-QUALITY-01-S2-01] Added a Ruby-emitter cast helper that skips known-type `int/float/bool` conversions and reduced `__pytra_int` chains around loop initialization/bounds in `sample/ruby/01` (reduced to forms like `while y < height`).
- 2026-03-02: [ID: P1-RUBY-SAMPLE01-QUALITY-01-S2-03] Suppressed `__pytra_truthy` on conditions with bool-fixed nodes and reduced output to native Ruby conditions such as `if (it >= max_iter)`.
- 2026-03-02: [ID: P1-RUBY-SAMPLE01-QUALITY-01-S2-04] For `AnnAssign(value=None)` with `declare=true` and scalar `decl_type`, stopped emitting `nil` initialization, removing `r/g/b = nil` in `sample/ruby/01`.
- 2026-03-02: [ID: P1-RUBY-SAMPLE01-QUALITY-01-S3-01] Extended `sample01` fragment checks in `test_py2rb_smoke.py` (loop/cast/truthy/nil init) and finalized regression lock with `runtime_parity_check --targets ruby 01_mandelbrot` pass.

## S1-01 Audit Results

Measured fragments (`sample/01`):

- Ruby output: `__pytra_int` 18 sites / `__pytra_float` 3 sites / `__pytra_div` 4 sites / `__pytra_truthy` 3 sites / `__step_*` 12 sites.
- C++ output: `py_to<float64>` 5 sites, `py_div` 0 sites, `py_truthy` 0 sites, already reduced to simple `for`.

Gap categories and priority:

1. Loop shape: Ruby degrades to `__step_* + while` (largest readability loss for `for i in range(...)`).
2. Numeric wrapper chains: same-type `__pytra_int/__pytra_div` chains remain on hot paths.
3. Temporary initialization: `r/g/b = nil` remains before typed branches.
4. Truthy overuse: some paths still route comparison expressions through `__pytra_truthy(...)`.

Implementation order:

1. `S2-02` (loop canonicalization)
2. `S2-01` (reduce same-type numeric casts)
3. `S2-04` (reduce typed initialization)
4. `S2-03` (optimize truthy insertion conditions)
