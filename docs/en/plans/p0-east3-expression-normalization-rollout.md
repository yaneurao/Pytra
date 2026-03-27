<a href="../../ja/plans/p0-east3-expression-normalization-rollout.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: EAST3 Expression-Normalization Rollout (Multi-Backend Commonization)

Last updated: 2026-03-02

Related TODO:
- `ID: P0-EAST3-EXPR-NORM-ROLL-01` in `docs/ja/todo/index.md`

Background:
- Currently each backend emitter (`cpp/rs/cs/js/go/java/swift/kotlin/ruby/lua/scala`) assembles expressions such as binary ops, comparisons, and range conditions independently as strings.
- As a result, semantically equivalent expressions diverge across backends, and omissions in simplification are common (unnecessary parentheses, identity casts, generalized forms left for `start=0` / `step=1`).
- Existing `P0-EAST3-RESERVE-COUNT-NORM-01` addresses only `reserve` count expressions; similar issues remain in other expression categories.

Goal:
- Move backend-common semantic decisions for expressions into EAST3, so emitters focus on rendering language-specific notation.
- Clarify the boundary: normalization responsibility belongs to EAST3, notation responsibility belongs to emitters, and prevent recurrence of redundant expressions.

In scope:
- Expression-normalization passes in EAST3 optimizer/lowering (including new passes)
- Common expression assembly paths in `src/hooks/*/emitter` (BinOp/Compare/ForRange conditions/trip_count, etc.)
- Regression tests (optimizer + per-backend codegen snippets)
- Representative diff checks in regenerated `sample` outputs (prioritize `01/08/18`)

Out of scope:
- Notation optimizations for language-specific features (for example concrete API choices such as `format!`, `Math.floor`)
- Runtime API redesign
- Full simultaneous backend switch (phased adoption is assumed)

Acceptance criteria:
- EAST3 introduces common expression normalization metadata/nodes and preserves common forms for at least `BinOp/Compare/StaticRange conditions`.
- Common string-assembly logic in emitters is reduced in phases and replaced with rendering of EAST3-normalized forms.
- Representative cases including `sample/cpp/18` show fewer redundant expressions (unnecessary parentheses/identity casts/generalized forms).
- `check_*_transpile` and related unit tests pass with no regressions.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_optimizer.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/check_py2rs_transpile.py`
- `python3 tools/check_py2scala_transpile.py`
- `python3 tools/regenerate_samples.py --langs cpp,rs,scala --stems 01_mandelbrot,08_langtons_ant,18_mini_language_interpreter --force`

Breakdown:
- [x] [ID: P0-EAST3-EXPR-NORM-ROLL-01-S1-01] Inventory expression-assembly responsibilities across backends (BinOp/Compare/ForRange/trip_count) and finalize EAST3 migration targets.
- [x] [ID: P0-EAST3-EXPR-NORM-ROLL-01-S1-02] Define boundary specs for "semantics decided by EAST3" and "notation decided by emitters" (including fail-closed conditions).
- [x] [ID: P0-EAST3-EXPR-NORM-ROLL-01-S1-03] Fix prioritization of normalization categories (identity cast, unnecessary parentheses, range conditions, trip_count, comparison chains).
- [x] [ID: P0-EAST3-EXPR-NORM-ROLL-01-S2-01] Add common expression-normalization passes in EAST3 and retain results as structured metadata (`normalized_expr` family).
- [x] [ID: P0-EAST3-EXPR-NORM-ROLL-01-S2-02] Switch C++ emitter to EAST3-normalized forms for non-`reserve` expression categories and reduce dependency on string assembly.
- [x] [ID: P0-EAST3-EXPR-NORM-ROLL-01-S2-03] Use Rust/Scala as next pilots and switch rendering paths to the same normalized forms.
- [x] [ID: P0-EAST3-EXPR-NORM-ROLL-01-S2-04] Minimize coexistence period with legacy paths and lock fail-closed/fallback conditions when normalized forms are missing.
- [x] [ID: P0-EAST3-EXPR-NORM-ROLL-01-S3-01] Add unit tests (optimizer + emitter) to detect recurrence of redundant expressions.
- [x] [ID: P0-EAST3-EXPR-NORM-ROLL-01-S3-02] Run `sample` regeneration and transpile/parity checks to verify quality improvements and no regressions in representative cases.

Decision log:
- 2026-03-02: Per user direction, filed a new P0 plan to move expression normalization as a whole into EAST3 rather than limiting it to `reserve`.
- 2026-03-02: [ID: P0-EAST3-EXPR-NORM-ROLL-01-S1-01] Completed cross-backend inventory and fixed EAST3 migration targets for `BinOp/Compare/ForRange/trip_count`.
- 2026-03-02: [ID: P0-EAST3-EXPR-NORM-ROLL-01-S1-02] Fixed fail-closed boundary contract as `normalized_expr`: semantics in EAST3, notation in emitters.
- 2026-03-02: [ID: P0-EAST3-EXPR-NORM-ROLL-01-S1-03] Fixed normalization-category priority order as `trip_count/range conditions -> identity cast -> comparison chains -> parentheses`.
- 2026-03-02: [ID: P0-EAST3-EXPR-NORM-ROLL-01-S2-01] Added `ExpressionNormalizationPass`, attaching `normalized_expr_version=east3_expr_v1` to `BinOp/Compare` and `ForCore(StaticRange)` condition expressions.
- 2026-03-02: [ID: P0-EAST3-EXPR-NORM-ROLL-01-S2-02] Switched C++ `ForCore` condition expressions to prefer `normalized_exprs.for_cond_expr`, beginning rollout beyond `reserve`.
- 2026-03-02: [ID: P0-EAST3-EXPR-NORM-ROLL-01-S2-03] Added `normalized_exprs.for_cond_expr` reference paths for Rust/Scala `ForCore` as pilot-backend rollout.
- 2026-03-02: [ID: P0-EAST3-EXPR-NORM-ROLL-01-S2-04] Fixed policy: when normalized forms are missing, fall back to legacy condition expressions; keep existing fail-closed behavior for `reserve_hints`.
- 2026-03-02: [ID: P0-EAST3-EXPR-NORM-ROLL-01-S3-01] Expanded optimizer/unit and C++ codegen regression tests, adding recurrence detection for normalization metadata.
- 2026-03-02: [ID: P0-EAST3-EXPR-NORM-ROLL-01-S3-02] Ran `sample(01/08/18)` parity for `cpp/rs/scala` and confirmed `cases=3 pass=3 fail=0` (fixed Scala `ArrayBuffer[Any]` type mismatch and incorrect `continue` detection).

## S1-01 Inventory Results (Cross-Backend)

Cross-checking `kind == "BinOp" / "Compare" / StaticRangeForPlan / range_mode / reserve_hints` via `rg` fixed the following migration targets.

| backend | Current expression-assembly responsibilities (representative locations) | EAST3 migration targets |
| --- | --- | --- |
| C++ | `BinOp/Compare` in `src/hooks/cpp/emitter/cpp_emitter.py`; range conditions / `reserve_hints` in `src/hooks/cpp/emitter/stmt.py` | Normal forms for `BinOp/Compare`, `StaticRange` condition expressions, trip count |
| Rust | `render_expr` / `_emit_for_range` in `src/hooks/rs/emitter/rs_emitter.py` | Normal forms for `BinOp/Compare`, range condition expressions |
| Scala | `render_expr` / `emit ForCore` in `src/hooks/scala/emitter/scala_native_emitter.py` | Normal forms for `BinOp/Compare`, range condition expressions |
| C#/JS/Go/Java/Swift/Kotlin/Ruby/Lua | `BinOp/Compare` branches and `StaticRangeForPlan` condition assembly in each `*_emitter` | Phased migration to common normalized-form references (phase 2 onward) |

Notes:
- `trip_count` already introduced `reserve_hints[*].count_expr` in advance (`P0-EAST3-RESERVE-COUNT-NORM-01`).
- This plan extends that model to other categories and reduces expression recomputation inside emitters.

## S1-02 Responsibility Boundary (Semantics vs Notation)

Contract:
- EAST3 optimizer decides semantics in a backend-agnostic way.
  - Attach `normalized_expr_version = "east3_expr_v1"`.
  - Store EAST3 expression nodes (such as `Constant/BinOp/Compare/IfExp/Name`) in `normalized_expr`.
- Emitters render language-specific notation.
  - Responsible only for operator tokens, minimal parentheses by precedence, and standard API naming (`Math.*`, `std::*`, etc.).
  - Must not re-synthesize equivalent-meaning expressions on the emitter side.

Fail-closed conditions:
- `normalized_expr_version` mismatch.
- Missing `normalized_expr`.
- `kind` in `normalized_expr` is outside the backend-implemented allowed subset.
- If any of the above occurs, disable the optimization path and fall back to the legacy path (prioritizing avoidance of invalid code generation).

## S1-03 Priority of Normalization Targets

Priority (high -> low):
1. `trip_count` / `range conditions` (`StaticRange` boundary expressions)  
2. identity cast (`py_to<T>(T)` / same-type chains in `static_cast<T>(T)`)  
3. comparison chains (normal form for `Compare`, suppress unnecessary intermediate truthy conversion)  
4. unnecessary parentheses (where operator precedence is preserved by normalized form)

Rollout order:
1. Expand C++ first adopter scope beyond `reserve`.
2. Use Rust/Scala as pilot backends to reference the same normalized form.
3. Roll out to the remaining backends and gradually shrink legacy string-assembly responsibilities.
