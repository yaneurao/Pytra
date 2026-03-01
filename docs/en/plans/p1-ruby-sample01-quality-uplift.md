# P1: `sample/ruby/01` Quality Uplift (Narrowing the Gap vs C++ Quality)

Last updated: 2026-03-01

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
- [ ] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S1-01] Inventory quality gaps in `sample/ruby/01` (redundant cast / loop / truthy / temporary initialization) and lock improvement priority.
- [ ] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S2-01] Reduce same-type conversion chains in Ruby emitter numeric output and prioritize typed paths.
- [ ] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S2-02] Add fastpath that lowers simple `range` loops into canonical loops.
- [ ] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S2-03] Optimize insertion conditions of `__pytra_truthy` in comparison/logical expressions and prioritize native Ruby conditions.
- [ ] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S2-04] Add typed-assignment fastpath in `sample/01` (`r/g/b` etc.) to reduce unnecessary `nil` initialization.
- [ ] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S3-01] Add regression tests (code fragments + parity) and lock regenerated diffs of `sample/ruby/01`.

Decision Log:
- 2026-03-01: Per user instruction, we finalized the policy to plan `sample/ruby/01` quality improvement as P1 and add it to TODO.
