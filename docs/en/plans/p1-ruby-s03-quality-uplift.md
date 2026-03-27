<a href="../../ja/plans/p1-ruby-s03-quality-uplift.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: sample/ruby/03 Output Quality Uplift (Julia Hot Path)

Last updated: 2026-03-02

Related TODO:
- `ID: P1-RUBY-S03-QUALITY-01` in `docs/ja/todo/index.md`

Background:
- `sample/ruby/03_julia_set.rb` satisfies behavioral compatibility, but generic helpers remain on hot paths, reducing readability and runtime efficiency.
- Representative examples include inner-loop `__pytra_div` calls, triple `pixels.append`, excessive parentheses, and same-type cast helpers.

Goal:
- Shift generated code for `sample/ruby/03` toward "known-type-path first" and reduce redundant output.
- Reduce helper dependency on hot paths incrementally without breaking parity.

Scope:
- `src/hooks/ruby/emitter/` (expression/statement/operator rendering)
- Ruby codegen regressions in `test/unit`
- `sample/ruby/03_julia_set.rb` (regeneration verification)

Out of scope:
- Full redesign of Ruby runtime API
- Bulk rollout to other samples/backends
- Changes to image quality or arithmetic semantics (integer division / divide-by-zero contract)

Acceptance criteria:
- In `sample/ruby/03`, all of the following hold:
  - Unnecessary `__pytra_div` is reduced on known-type `float/int` paths.
  - Redundant assignments in `r/g/b` initialization are reduced.
  - Redundant output from excessive parentheses and same-type cast helpers is reduced.
  - Redundant calls around pixel writes are degraded.
- `check_py2rb_transpile.py` and `runtime_parity_check --targets ruby --case 03_julia_set` pass.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2rb_transpile.py`
- `python3 tools/regenerate_samples.py --langs ruby --stems 03_julia_set --force`
- `python3 tools/runtime_parity_check.py --case-root sample --targets ruby --case 03_julia_set --ignore-unstable-stdout`

Decision log:
- 2026-03-02: Filed a P1 plan for improvements in `sample/ruby/03` based on user direction.
- 2026-03-02: Inventory of `sample/ruby/03_julia_set.rb` fixed priorities as `1) hot-path division helper 2) triple pixel append 3) r/g/b initialization 4) excessive parentheses 5) same-type cast helper`.
- 2026-03-02: Fixed fail-closed boundary as "apply fastpath only for known numeric types (`int/float/bool`) and side-effect-free expressions; keep existing helper paths for `Any/object/union/call-side-effect`."
- 2026-03-02: Added `_strip_outer_parens` and simple-expression fastpath for `BinOp` in Ruby emitter, reducing redundant parentheses in `if/while` conditions and `zx2 = zx * zx` style expressions.
- 2026-03-02: Added precedence guards (`Add/Sub` vs `Mult/Div/...`) for `BinOp` fastpath and fixed fail-closed implementation that keeps right-operand grouping like `255.0 * (1.0 - t)`.
- 2026-03-02: Updated `test_py2rb_smoke.py` and added parenthesis-quality regressions for `sample/01` and `sample/03`. Passed `runtime_parity_check --case-root sample --targets ruby --ignore-unstable-stdout 03_julia_set`.
- 2026-03-02: Added peephole for consecutive `append` and degraded to `owner.concat([..])` when same owner + safe args (Name/Constant/Attribute/Subscript) appear in runs of 2+.
- 2026-03-02: Confirmed `pixels.concat([r, g, b])` in `sample/ruby/01` / `sample/ruby/03`. Re-passed `test_py2rb_smoke` and `03_julia_set` parity.
- 2026-03-02: Added `test_sample03_reduces_redundant_parentheses_in_binop_and_conditions` and locked regression detection for parenthesis degradation + `concat` degradation (`S3-01`).
- 2026-03-02: Re-ran `tools/regenerate_samples.py --langs ruby --stems 01_mandelbrot,03_julia_set --force` and `runtime_parity_check ... 03_julia_set`, completing `S3-02`.
- 2026-03-02: Added direct `/` fastpath for `Div` only when "RHS is non-zero numeric constant," reducing `__pytra_div` dependency without breaking divide-by-zero contracts (`S2-01`).
- 2026-03-02: `t = __pytra_div((i - 1), 254.0)` in `sample/ruby/06` degraded to `(__pytra_float(i - 1)) / 254.0`. Confirmed parity pass for `03/06`.
- 2026-03-02: Added numeric-constant fastpath for `_render_float_cast` (`int -> <n>.0`, `float -> literal`) to suppress same-type cast helper calls (`S2-05`).
- 2026-03-02: Added conservative peephole for `Assign*` chains + `If`, removing pre-initialization only when the true branch is equivalent to pre-init (`S2-03`).

## Breakdown

- [x] [ID: P1-RUBY-S03-QUALITY-01-S1-01] Inventory redundant fragments in `sample/ruby/03` (`__pytra_div` / append / initialization / parentheses / cast) and fix priority order.
- [x] [ID: P1-RUBY-S03-QUALITY-01-S1-02] Specify fail-closed applicability boundaries (known-type conditions, arithmetic-semantic preservation conditions).
- [x] [ID: P1-RUBY-S03-QUALITY-01-S2-01] Add emitter fastpath to reduce `__pytra_div` dependency on known-type division paths.
- [x] [ID: P1-RUBY-S03-QUALITY-01-S2-02] Add output rules to reduce redundant calls around `pixels.append`.
- [x] [ID: P1-RUBY-S03-QUALITY-01-S2-03] Update branch output to reduce redundant assignments in `r/g/b` initialization.
- [x] [ID: P1-RUBY-S03-QUALITY-01-S2-04] Add normalization rules to reduce excessive parentheses in Ruby output.
- [x] [ID: P1-RUBY-S03-QUALITY-01-S2-05] Suppress unnecessary same-type conversion helper calls (`__pytra_float/__pytra_int`).
- [x] [ID: P1-RUBY-S03-QUALITY-01-S3-01] Add unit/golden regressions to detect recurrence of redundant patterns.
- [x] [ID: P1-RUBY-S03-QUALITY-01-S3-02] Verify non-regression through `sample/ruby/03` regeneration and transpile/parity.

## Inventory Results (S1-01)

- `__pytra_div` hot path: `__pytra_div(y, __hoisted_cast_1)` / `__pytra_div(x, __hoisted_cast_2)` / `__pytra_div(i, __hoisted_cast_3)` remain in `zy0/zx/t` computations.
- Triple append: `pixels.append(r); pixels.append(g); pixels.append(b);` triggers 3 calls per pixel.
- Redundant initialization: equivalent `r=g=b=0` is emitted as `r=0; g=0; b=0;` and then reassigned inside `if`.
- Excessive parentheses: examples include `if (i >= max_iter)`, `zx2 = (zx * zx)`, `zy = (((2.0 * zx) * zy) + cy)`.
- Same-type cast helpers: obvious same-type/simple-expression helper calls remain, such as `__pytra_float((height - 1))` and `__pytra_int((255.0 * ...))`.

## Applicability Boundaries (S1-02)

- Numeric-operation fastpath applies only when `resolved_type` is `int/int64/float/float64/bool`.
- For expressions containing `Any/object/union/unknown`, keep helpers (`__pytra_div`, `__pytra_float`, `__pytra_int`).
- For expressions containing function call/attribute call, suppress parentheses/helper degradation to preserve side-effect order.
- Division scope is only `Div`. Keep existing helpers for `FloorDiv`/`Mod` to preserve Python compatibility.
- Append degradation applies only when element types in bytearray/list are known; keep existing path when unresolved.
