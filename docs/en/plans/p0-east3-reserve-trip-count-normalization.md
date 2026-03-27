<a href="../../ja/plans/p0-east3-reserve-trip-count-normalization.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: EAST3-Led `reserve` Count-Expression Normalization (Remove C++ Emitter String Assembly)

Last updated: 2026-03-02

Related TODO:
- `ID: P0-EAST3-RESERVE-COUNT-NORM-01` in `docs/ja/todo/index.md`

Background:
- In current `reserve` emission, eligibility is determined in EAST3 (`reserve_hints`), but count-expression assembly is still done by C++ emitter-side string generation.
- This leaves redundant expressions in `sample/cpp/18_mini_language_interpreter.cpp`, such as `lines.reserve(((var_count) <= (0) ? 0 : (var_count) - (0)));`.
- User requirements call for moving expression-normalization responsibility to EAST3, with backends focused strictly on rendering already normalized expressions.

Goal:
- Finalize normalization of `reserve` count expressions in EAST3 and remove dependence on string assembly in the C++ emitter.
- Reduce `reserve` expressions in sample/18 to readable normal forms and prevent recurrence of the same class of redundant expressions.

In scope:
- `src/pytra/compiler/east_parts/east3_opt_passes/safe_reserve_hint_pass.py`
- `src/pytra/compiler/east_parts/east3_opt_passes/*` (new pass if needed)
- `src/hooks/cpp/emitter/stmt.py`
- `test/unit/*` (EAST3 optimizer / C++ codegen regressions)
- `sample/cpp/18_mini_language_interpreter.cpp` (regeneration result)

Out of scope:
- Spec changes for `reserve` applicability (still only unconditional append + static range)
- `reserve` output optimization in non-C++ backends
- Full introduction of a general expression-simplification engine

Acceptance criteria:
- EAST3 `reserve_hints` stores count expressions (AST or equivalent structured representation), and C++ emitter renders them directly.
- Remove StaticRange count-expression string assembly from C++ emitter or reduce it to a minimal fallback-only path.
- `lines.reserve(...)` in `sample/cpp/18_mini_language_interpreter.cpp` is updated from old form with `- (0)` and excessive parentheses.
- `tools/check_py2cpp_transpile.py` and related unit tests pass.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_optimizer.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/regenerate_samples.py --langs cpp --stems 18_mini_language_interpreter --force`
- `python3 tools/check_py2cpp_transpile.py`

Breakdown:
- [x] [ID: P0-EAST3-RESERVE-COUNT-NORM-01-S1-01] Define `reserve_hints` extension spec (`count_expr` format / fail-closed conditions / compatibility handling).
- [x] [ID: P0-EAST3-RESERVE-COUNT-NORM-01-S1-02] Specify normalization rules for `StaticRange` count expressions (simplification rules such as `start=0,step=1`).
- [x] [ID: P0-EAST3-RESERVE-COUNT-NORM-01-S2-01] Generate normalized `count_expr` in EAST3 optimizer and attach it to `reserve_hints`.
- [x] [ID: P0-EAST3-RESERVE-COUNT-NORM-01-S2-02] Switch C++ emitter to `count_expr` rendering and remove dependence on string assembly.
- [x] [ID: P0-EAST3-RESERVE-COUNT-NORM-01-S2-03] Implement fail-closed behavior for missing/invalid `count_expr` and prevent invalid `reserve` output.
- [x] [ID: P0-EAST3-RESERVE-COUNT-NORM-01-S3-01] Add unit tests (optimizer + emitter) to detect recurrence of old redundant `reserve` expressions.
- [x] [ID: P0-EAST3-RESERVE-COUNT-NORM-01-S3-02] Regenerate `sample/cpp/18` and run transpile checks to verify no regressions.

Decision log:
- 2026-03-02: Per user direction, filed a P0 plan to move `reserve` count-expression normalization responsibility from C++ emitter to EAST3.
- 2026-03-02: [ID: P0-EAST3-RESERVE-COUNT-NORM-01-S1-01] Finalized contract storing `reserve_hints[*].count_expr` as EAST3 expression nodes and fail-closed conditions.
- 2026-03-02: [ID: P0-EAST3-RESERVE-COUNT-NORM-01-S1-02] Fixed normalization rules for `StaticRange` trip count (ascending/descending + step simplification).
- 2026-03-02: [ID: P0-EAST3-RESERVE-COUNT-NORM-01-S2-01] Added implementation in `SafeReserveHintPass` to generate `count_expr` (`IfExp/Compare/BinOp`) and store it in hints.
- 2026-03-02: [ID: P0-EAST3-RESERVE-COUNT-NORM-01-S2-02] Switched C++ emitter to rendering `reserve_hints[*].count_expr` and removed start/stop/step string-assembly paths.
- 2026-03-02: [ID: P0-EAST3-RESERVE-COUNT-NORM-01-S2-03] Fixed fail-closed policy to suppress `reserve` output when `count_expr_version` mismatches or `count_expr` is invalid.
- 2026-03-02: [ID: P0-EAST3-RESERVE-COUNT-NORM-01-S3-01] Updated/added optimizer and codegen unit tests to detect recurrence of old `(n) - (0)` fragments and missing `count_expr`.
- 2026-03-02: [ID: P0-EAST3-RESERVE-COUNT-NORM-01-S3-02] Regenerated `sample/cpp/18` and confirmed no regressions through `check_py2cpp_transpile` and unit tests.

## S1 Implementation Results (2026-03-02)

### S1-01: `reserve_hints` Extension Spec (`count_expr`)

- Added keys:
  - `reserve_hints[*].count_expr`: stores trip count as EAST3 expression nodes (minimum subset: `Constant/Name/BinOp/Compare/IfExp`).
  - `reserve_hints[*].count_expr_version`: string `"east3_expr_v1"`.
- Compatibility handling:
  - Keep existing `count_kind`, while emitter reads `count_expr` first.
  - If `count_expr` is missing, do not emit `reserve` (fail-closed). Do not revert to legacy string assembly.
- Fail-closed conditions:
  - Suppress `reserve` output when `count_expr` is not a dict, has invalid `kind`, lacks required child nodes, or includes unsupported operators.
  - Also suppress when `safe != true`, `owner` is empty, or hint kind mismatches.

### S1-02: `StaticRange` Count-Expression Normalization Rules

- Preconditions:
  - As in existing spec, applicability remains limited to `unconditional append + StaticRangeForPlan + safety conditions satisfied`.
- Normalization:
  - `step == 0` is treated as invalid; no `count_expr` is generated.
  - `range_mode=ascending`:
    - `step_abs == 1`: `stop <= start ? 0 : stop - start`
    - `step_abs > 1`: `stop <= start ? 0 : (stop - start + (step_abs - 1)) / step_abs`
  - `range_mode=descending`:
    - `step_abs == 1`: `stop >= start ? 0 : start - stop`
    - `step_abs > 1`: `stop >= start ? 0 : (start - stop + (step_abs - 1)) / step_abs`
- Simplification:
  - For `start=0` / `step=1`, expressions naturally simplify to `stop <= 0 ? 0 : stop`.
  - Unnecessary `- (0)` and excessive parentheses are suppressed by emitter-side rendering rules.
