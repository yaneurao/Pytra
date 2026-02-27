# P0: Implement the Common EAST3 Optimizer Layer

Last updated: 2026-02-26

Related TODO:
- `ID: P0-EAST3-OPT-01` in `docs/ja/todo/index.md`

Background:
- The common EAST3 optimizer spec (`docs/ja/spec/spec-east3-optimizer.md`) is already defined, but the implementation path is not prepared.
- Optimization logic has tended to spread into emitters, making responsibility boundaries unclear.
- We have already decided that normalization such as `for ... in range(...)` and unused loop-var binding reduction belongs to the common layer, not backend-specific conversion.

Goal:
- Implement a common `EAST3 -> EAST3` optimizer with operational guarantees for meaning preservation, fail-closed behavior, and determinism.

In scope:
- `src/pytra/compiler/east_parts/east3_optimizer.py` (new)
- `src/pytra/compiler/east_parts/east3_opt_passes/*.py` (new)
- `src/pytra/compiler/transpile_cli.py` (CLI option wiring)
- Pass unit tests and integration regression (`test/unit`, `tools/*`)

Out of scope:
- Re-design of `EAST2` construction/type-resolution logic
- Backend-specific structuring (for example, C++ `for (i=...; ...; ++i)`)
- Post-processing optimization over already-stringified code

Acceptance criteria:
- `O0/O1/O2` and pass-level on/off can be controlled from CLI.
- Default `O1` passes (cast/literal/range-loop normalization) work, and `O2` can apply additional loop passes.
- Existing parity (`stdout`/artifacts) is preserved.
- Fail-closed behavior is confirmed in inapplicable cases (side effects, uncertain evaluation order).

Verification commands:
- `python3 tools/check_todo_priority.py`
- `python3 -m unittest discover -s test/unit -p 'test_east3_*optimizer*.py'`
- `python3 tools/runtime_parity_check.py --case-root sample --targets cpp,rs,cs,js,ts --all-samples --ignore-unstable-stdout`

Decision log:
- 2026-02-26: Initial draft created. Based on `spec-east3-optimizer`, implementation rollout is split into S1/S2/S3.
- 2026-02-26: Completed `P0-EAST3-OPT-01-S1-01` by adding `east3_optimizer.py` / `east3_opt_passes/` skeleton and `test_east3_optimizer.py`, fixing a minimal pass-manager and trace-render path.
- 2026-02-26: Completed `P0-EAST3-OPT-01-S1-02` by wiring `--east3-opt-level` / `--east3-opt-pass` / dump options through `transpile_cli`, `py2cpp`, and all non-C++ CLIs, then locking routes with `test_east3_optimizer_cli.py` and parser-wrapper tests.
- 2026-02-26: Completed `P0-EAST3-OPT-01-S2-01` by adding `NoOpCastCleanupPass` / `LiteralCastFoldPass`, updating `build_default_passes()` to the `O1` default set, and syncing pass-unit tests plus CLI trace expectations.
- 2026-02-26: Completed `P0-EAST3-OPT-01-S2-02` by adding `RangeForCanonicalizationPass` / `UnusedLoopVarElisionPass`, canonicalizing constant `range(...)` loops to `StaticRangeForPlan`, and introducing fail-closed underscore-elision for provably unused loop vars (guarded against dynamic-name inspection calls).
- 2026-02-26: Completed `P0-EAST3-OPT-01-S2-03` by adding `LoopInvariantHoistLitePass` / `StrengthReductionFloatLoopPass` as `O2`-only passes, with conservative guards for non-empty static-range preheader hoist and power-of-two float-division reciprocal rewrite.
- 2026-02-26: Completed `P0-EAST3-OPT-01-S3-01` by expanding pass unit coverage to 21 cases, locking O2 gating, dynamic-name-resolution guards, and non-application behavior (zero-step, non-power-of-two divisors, and post-loop reads).
- 2026-02-27: Completed `P0-EAST3-OPT-01-S3-02` by adding `--east3-opt-level` to `runtime_parity_check.py` and rerunning `sample/py` 18 cases × `cpp,rs,cs,js,ts` across `O0/O1/O2`; all three levels produced `17 pass / 1 fail` (existing `18_mini_language_interpreter:cpp` compile failure) with no new level-dependent diffs, logged in `work/logs/east3_opt_parity_o{0,1,2}.json`.
- 2026-02-27: Completed `P0-EAST3-OPT-01-S3-03` by syncing `spec-east3-optimizer` (ja/en) to implementation reality, updating pass-status/fail-closed guard descriptions, and documenting operations for trace capture, pass isolation, and `runtime_parity_check --east3-opt-level`.

## Breakdown

- [x] [ID: P0-EAST3-OPT-01-S1-01] Add optimizer entry (`east3_optimizer.py`) and pass manager skeleton (`PassContext`/`PassResult`).
- [x] [ID: P0-EAST3-OPT-01-S1-02] Implement CLI options (`--east3-opt-level`, `--east3-opt-pass`, dump/trace) and lock the `O0/O1/O2` contract.
- [x] [ID: P0-EAST3-OPT-01-S2-01] Implement `NoOpCastCleanupPass` / `LiteralCastFoldPass` and establish the default `O1` set.
- [x] [ID: P0-EAST3-OPT-01-S2-02] Implement `RangeForCanonicalizationPass` / `UnusedLoopVarElisionPass` to reflect `for ... in range(...)` boundary decisions.
- [x] [ID: P0-EAST3-OPT-01-S2-03] Add `LoopInvariantHoistLitePass` / `StrengthReductionFloatLoopPass` as `O2`-only.
- [x] [ID: P0-EAST3-OPT-01-S3-01] Add pass-level unit tests (input/output EAST3 diff, inapplicable guards, meaning preservation).
- [x] [ID: P0-EAST3-OPT-01-S3-02] Run `sample` regressions + parity checks and confirm compatibility under `O0`/`O1`/`O2` switching.
- [x] [ID: P0-EAST3-OPT-01-S3-03] Sync implementation diff back to `spec-east3-optimizer` and document operations (trace checks / issue isolation).
