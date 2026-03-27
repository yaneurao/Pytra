<a href="../../ja/plans/p0-east3-lifetime-analysis-foundation.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Introduce EAST3 Variable Lifetime Analysis Foundation (Backend-Common)

Last updated: 2026-03-02

Related TODO:
- `ID: P0-EAST3-LIFETIME-ANALYSIS-01` in `docs/ja/todo/index.md`

Background:
- Existing EAST3 optimization has interprocedural non-escape summaries, but does not retain variable-level live-range / last-use information.
- As a result, rationale for C++ `object` / `rc` reduction is skewed toward emitter-side logic, making it hard to roll out the same optimization policy to other backends including Rust.
- If each backend owns its own lifetime judgment logic, responsibility boundaries break down and every output-quality improvement causes duplicated rework.

Goal:
- Generate backend-agnostic lifetime annotations (definition points, use points, last-use, live-range) in EAST3.
- Connect with existing non-escape analysis to create a mechanical basis for classifying `escaping values as conservative` and `local non-escaping values as optimization candidates`.
- Shift emitters (C++/Rust, etc.) toward simply consuming these annotations.

In scope:
- `src/pytra/compiler/east_parts/east3_optimizer.py`
- `src/pytra/compiler/east_parts/east3_opt_passes/*` (add new lifetime pass set)
- `src/pytra/compiler/east_parts/east3_opt_passes/non_escape_interprocedural_pass.py` (connection points only as needed)
- `test/unit/test_east3_optimizer*.py`
- `test/unit/test_east3_lifetime_*.py` (new)
- Minimal required additions to `spec-east3-optimizer`

Out of scope:
- Actual replacement implementation in C++/Rust emitters (`rc -> value`, borrow/move conversion)
- High-precision alias/points-to analysis (this plan targets a practical fail-closed minimum)
- Runtime spec changes

Acceptance criteria:
- After EAST3 pass execution, deterministic `live-range` and `last-use` annotations are available for each local variable.
- Analysis results remain conservative and deterministic across reruns for cases including branches, loops, tuple unpacking, and function calls.
- Cases including unresolved calls/dynamic calls are excluded from lifetime-optimization candidates in fail-closed mode.
- Existing optimizer regressions and transpile smoke (`py2cpp`/`py2rs`) pass with no regressions.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_lifetime_*.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_optimizer*.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/check_py2rs_transpile.py`

Decision log:
- 2026-03-02: Per user direction, fixed P0 policy to commonize variable lifetime analysis in EAST3 before backend-specific optimization.
- 2026-03-02: [ID: `P0-EAST3-LIFETIME-ANALYSIS-01-S1-01`] Added `east3_lifetime_v1` contract (`cfg/def_use/variables` and `fail_closed` rules) to `docs/ja/spec/spec-east3-optimizer.md`, fixing the lifetime annotation schema.
- 2026-03-02: [ID: `P0-EAST3-LIFETIME-ANALYSIS-01-S1-02`] Added `LifetimeAnalysisPass`, implementing a foundation that builds block-local CFG and def-use indexes per `FunctionDef/ClassDef method` and annotates `meta.lifetime_analysis`.
- 2026-03-02: [ID: `P0-EAST3-LIFETIME-ANALYSIS-01-S2-01`] Implemented backward data-flow (`live_in/live_out` fixed-point) in the same pass and confirmed deterministic convergence on CFGs including branches/loops.
- 2026-03-02: [ID: `P0-EAST3-LIFETIME-ANALYSIS-01-S2-02`] Added annotations on statement-node `meta` for `lifetime_node_id/defs/uses/live_in/live_out/last_use_vars` and output variable summaries including `last_use_nodes`.
- 2026-03-02: [ID: `P0-EAST3-LIFETIME-ANALYSIS-01-S2-03`] Integrated `escape_summary.arg_escape` and `Return/Yield` usage into lifetime-class decisions, adding automatic classification into `escape_or_unknown` and `local_non_escape_candidate`.
- 2026-03-02: [ID: `P0-EAST3-LIFETIME-ANALYSIS-01-S3-01`] Added new `test_east3_lifetime_analysis_pass.py`, locking regressions for branches, loops, tuple unpack, calls (including dynamic), determinism, and non-escape integration.
- 2026-03-02: [ID: `P0-EAST3-LIFETIME-ANALYSIS-01-S3-02`] Re-ran `test_east3_optimizer*.py` / `test_east3_lifetime_analysis_pass.py` / `check_py2cpp_transpile.py` / `check_py2rs_transpile.py` and confirmed no regressions (`py2cpp: checked=136 ok=136 fail=0`, `py2rs: checked=131 ok=131 fail=0`).

## Breakdown

- [x] [ID: P0-EAST3-LIFETIME-ANALYSIS-01-S1-01] Specify lifetime annotation schema (`def/use`, `live_in/live_out`, `last_use`, `lifetime_class`) and fail-closed rules.
- [x] [ID: P0-EAST3-LIFETIME-ANALYSIS-01-S1-02] Add a foundation that generates block-local CFG and def-use indexes from EAST3 function/method bodies.
- [x] [ID: P0-EAST3-LIFETIME-ANALYSIS-01-S2-01] Compute liveness (`live_in/live_out`) via backward data-flow and implement fixed-point convergence including loops.
- [x] [ID: P0-EAST3-LIFETIME-ANALYSIS-01-S2-02] Determine last-use points from use sequences and annotate node `meta` with `last_use` / `live_range`.
- [x] [ID: P0-EAST3-LIFETIME-ANALYSIS-01-S2-03] Integrate non-escape summary and exclude `escape` values from lifetime-optimization candidates.
- [x] [ID: P0-EAST3-LIFETIME-ANALYSIS-01-S3-01] Add unit tests including branches/loops/tuple unpack/calls and lock determinism + fail-closed behavior.
- [x] [ID: P0-EAST3-LIFETIME-ANALYSIS-01-S3-02] Run optimizer regressions + `check_py2cpp_transpile`/`check_py2rs_transpile` and confirm no regressions.
