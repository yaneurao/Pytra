# TODO (Open)

> `docs-ja/` is the source of truth. `docs/` is its translation mirror.

<a href="../../docs-ja/todo/index.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

Last updated: 2026-02-26

## Context Rules

- Every task must include an `ID` and a context file (`docs-ja/plans/*.md`).
- Priority overrides must be instructed in chat using `docs-ja/plans/instruction-template.md` format; do not use `todo2.md`.
- Default execution target is the highest-priority unfinished ID (smallest `P<number>`, first in order within same priority). Do not move to lower priority without explicit override.
- If any `P0` is unfinished, do not start `P1` or below.
- Before starting, confirm `Background` / `Out of scope` / `Acceptance criteria` in the context file.
- Progress notes and commit messages must include the same `ID` (example: `[ID: P0-XXX-01] ...`).
- Keep progress memo in `docs-ja/todo/index.md` to one line; detailed judgment/verification logs belong in the context file (`docs-ja/plans/*.md`) `Decision log`.
- If one `ID` is large, split into child tasks (`-S1`, `-S2`, ...) in the context file while keeping parent checkbox open until parent is done.
- If uncommitted changes remain due to interruption, do not start another `ID` until completing the same `ID` or reverting diffs.
- When updating `docs-ja/todo/index.md` / `docs-ja/plans/*.md`, run `python3 tools/check_todo_priority.py` and confirm new progress `ID` matches top unfinished `ID` (or its child).
- Append work-time decisions to the context file `Decision log`.

## Notes

- This file stores unfinished tasks only.
- Completed tasks are moved to history via `docs-ja/todo/archive/index.md`.
- `docs-ja/todo/archive/index.md` is index-only; history bodies are saved by date in `docs-ja/todo/archive/YYYYMMDD.md`.

## Unfinished Tasks

### P3: Java backend direct EAST3 native generation (sidecar removal) (Low)

Context: [docs-ja/plans/p3-java-native-rollout.md](../plans/p3-java-native-rollout.md)

1. [ ] [ID: P3-JAVA-NATIVE-01] Migrate Java backend to direct `EAST3 -> Java native emitter`, removing sidecar JS dependency from the default path.
2. [ ] [ID: P3-JAVA-NATIVE-01-S1-01] Document Java backend contract (input EAST3 responsibilities, fail-closed behavior for unsupported nodes, runtime boundary) and clarify diffs from preview output.
3. [ ] [ID: P3-JAVA-NATIVE-01-S1-02] Add native emitter skeleton under `src/hooks/java/emitter` and pass minimal executable path for module/function/class.
4. [ ] [ID: P3-JAVA-NATIVE-01-S1-03] Add backend switch wiring in `py2java.py`; make native default and isolate old sidecar as compatibility mode.
5. [ ] [ID: P3-JAVA-NATIVE-01-S2-01] Implement native expression/statement coverage (arithmetic, conditionals, loops, function calls, basic built-ins) and pass early `sample/py` cases.
6. [ ] [ID: P3-JAVA-NATIVE-01-S2-02] Connect class/instance/isinstance paths and runtime hooks in native route and pass OOP cases.
7. [ ] [ID: P3-JAVA-NATIVE-01-S2-03] Add minimal compatibility for `import math` and image runtime calls (`png`/`gif`) for practical sample cases.
8. [ ] [ID: P3-JAVA-NATIVE-01-S3-01] Pass `check_py2java_transpile` / unit smoke / parity with native as default and lock regression detection.
9. [ ] [ID: P3-JAVA-NATIVE-01-S3-02] Regenerate `sample/java` and replace preview summary output with native implementation output.
10. [ ] [ID: P3-JAVA-NATIVE-01-S3-03] Update Java descriptions in `docs-ja/how-to-use.md` / `docs-ja/spec/spec-import.md` from sidecar assumptions and sync operation steps.

### P0: Implement common EAST3 optimizer layer (Highest)

Context: [docs-ja/plans/p0-east3-optimizer-rollout.md](../plans/p0-east3-optimizer-rollout.md)

1. [x] [ID: P0-EAST3-OPT-01] Introduce common `EAST3 -> EAST3` optimizer and reflect pass manager / opt-level / fail-closed contract into implementation.
2. [x] [ID: P0-EAST3-OPT-01-S1-01] Add optimizer entry (`east3_optimizer.py`) and pass manager skeleton (`PassContext`/`PassResult`).
3. [x] [ID: P0-EAST3-OPT-01-S1-02] Implement CLI options (`--east3-opt-level`, `--east3-opt-pass`, dump/trace`) and lock `O0/O1/O2` contract.
4. [x] [ID: P0-EAST3-OPT-01-S2-01] Implement `NoOpCastCleanupPass` / `LiteralCastFoldPass` and establish default `O1` set.
5. [x] [ID: P0-EAST3-OPT-01-S2-02] Implement `RangeForCanonicalizationPass` / `UnusedLoopVarElisionPass` and reflect `for ... in range(...)` boundary.
6. [x] [ID: P0-EAST3-OPT-01-S2-03] Add `LoopInvariantHoistLitePass` / `StrengthReductionFloatLoopPass` as `O2`-only.
7. [x] [ID: P0-EAST3-OPT-01-S3-01] Add pass unit tests (input/output EAST3 diff, non-application guards, semantics preservation).
8. [x] [ID: P0-EAST3-OPT-01-S3-02] Run sample regressions + parity checks and verify compatibility under `O0`/`O1`/`O2` switching.
9. [x] [ID: P0-EAST3-OPT-01-S3-03] Sync implementation diffs to `spec-east3-optimizer` and document operations (trace checks / troubleshooting).
- `P0-EAST3-OPT-01-S1-01` Added `east3_optimizer.py`, `east3_opt_passes/noop_pass.py`, and `test_east3_optimizer.py`, fixing the minimal pass-manager + trace-output path.
- `P0-EAST3-OPT-01-S1-02` Wired optimizer CLI options through common/non-C++/`py2cpp` routes and fixed the end-to-end entry path with `test_east3_optimizer_cli.py` plus parser-wrapper tests.
- `P0-EAST3-OPT-01-S2-01` Implemented `NoOpCastCleanupPass` / `LiteralCastFoldPass`, updated `build_default_passes()` to the `O1` default set, and synchronized pass-unit tests plus CLI trace expectations.
- `P0-EAST3-OPT-01-S2-02` Added `RangeForCanonicalizationPass` / `UnusedLoopVarElisionPass` with fail-closed guards for constant `range(...)` canonicalization (`StaticRangeForPlan`) and underscore elision of provably unused loop vars.
- `P0-EAST3-OPT-01-S2-03` Added `LoopInvariantHoistLitePass` / `StrengthReductionFloatLoopPass` as `O2`-only passes with conservative guards for non-empty static-range preheader hoist and power-of-two float-division strength reduction.
- `P0-EAST3-OPT-01-S3-01` Expanded pass unit coverage to 21 cases, locking O2 gating, dynamic-name-resolution guards, and non-application behavior (zero-step, non-power-of-two divisors, and post-loop variable reads).
- `P0-EAST3-OPT-01-S3-02` Added `--east3-opt-level` to `runtime_parity_check.py` and reran `sample/py` 18 cases × `cpp,rs,cs,js,ts` under `O0/O1/O2`; all levels produced `17 pass / 1 fail` with no inter-level diff (existing `18_mini_language_interpreter:cpp` compile failure), logs at `work/logs/east3_opt_parity_o{0,1,2}.json`.
- `P0-EAST3-OPT-01-S3-03` Synced `docs-ja/spec/spec-east3-optimizer.md` / `docs/spec/spec-east3-optimizer.md` to implementation status, adding pass-status matrix, fail-closed guard notes, and operations for `trace`, pass isolation, and `runtime_parity_check --east3-opt-level`.

### P0: Introduce C++ post-lowering optimizer layer (`CppOptimizer`) (Highest)

Context: [docs-ja/plans/p0-cpp-optimizer-rollout.md](../plans/p0-cpp-optimizer-rollout.md)

1. [ ] [ID: P0-CPP-OPT-01] Introduce `CppOptimizer` after `EAST3 -> C++ lowering` and separate optimization responsibilities from `CppEmitter`.
2. [x] [ID: P0-CPP-OPT-01-S1-01] Add skeleton (`optimizer/context/trace/passes`) under `src/hooks/cpp/optimizer/` and no-op wiring.
3. [x] [ID: P0-CPP-OPT-01-S1-02] Add `CppOptimizer` call path in `py2cpp` and wire `--cpp-opt-level` / `--cpp-opt-pass` / dump options.
4. [x] [ID: P0-CPP-OPT-01-S2-01] Implement `CppDeadTempPass` / `CppNoOpCastPass` and migrate equivalent emitter logic.
5. [x] [ID: P0-CPP-OPT-01-S2-02] Add `CppConstConditionPass` / `CppRangeForShapePass` and lock pre-structuring IR normalization.
6. [x] [ID: P0-CPP-OPT-01-S2-03] Add limited `CppRuntimeFastPathPass` within runtime-contract-equivalent boundaries.
7. [x] [ID: P0-CPP-OPT-01-S3-01] Reduce optimization branching in `CppEmitter` and align boundary with `spec-cpp-optimizer`.
8. [ ] [ID: P0-CPP-OPT-01-S3-02] Lock C++ regressions (`test_py2cpp_*`, `check_py2cpp_transpile.py`, `runtime_parity_check --targets cpp`).
9. [ ] [ID: P0-CPP-OPT-01-S3-03] Measure speed/size/generated-diff baselines and record adoption effects in context docs.
- `P0-CPP-OPT-01-S1-01` Added `src/hooks/cpp/optimizer/` scaffold (`context/trace/passes/cpp_optimizer`) plus no-op wiring in `emit_cpp_from_east`, and locked skeleton regressions with `test_cpp_optimizer.py`.
- `P0-CPP-OPT-01-S1-02` Added `--cpp-opt-level/--cpp-opt-pass/--dump-cpp-*` wiring in `py2cpp` and connected single/multi-file paths; locked CLI acceptance and dump outputs with `test_cpp_optimizer_cli.py` and `test_east3_cpp_bridge.py`.
- `P0-CPP-OPT-01-S2-01` Added `CppDeadTempPass`/`CppNoOpCastPass` for unused-temp elimination and no-op cast cleanup (`casts` metadata and `static_cast` nodes), registered them in `build_default_cpp_passes()`, and expanded `test_cpp_optimizer.py`.
- `P0-CPP-OPT-01-S2-02` Added `CppConstConditionPass`/`CppRangeForShapePass` for constant-branch pruning and runtime `range(...)` loop normalization to `StaticRangeForPlan`, then wired them into the default pass set and `test_cpp_optimizer.py`.
- `P0-CPP-OPT-01-S2-03` Added `CppRuntimeFastPathPass` (O2-only) for contract-equivalent fast paths (`Unbox` same-type fold, `Box(object)` fold, `ObjBool(bool)` fold), then wired it into default passes and added O1/O2 behavior checks in `test_cpp_optimizer.py`.
- `P0-CPP-OPT-01-S3-01` Removed char-compare optimization branching (`_try_optimize_char_compare`) from `CppEmitter._render_compare_expr` to keep compare optimization on the optimizer side; validated with `test_py2cpp_features::test_str_index_char_compare_optimized_and_runtime`.

### P3: Go/Swift/Kotlin backend direct EAST3 native generation (sidecar removal) (Low)

Context: [docs-ja/plans/p3-go-swift-kotlin-native-rollout.md](../plans/p3-go-swift-kotlin-native-rollout.md)

1. [ ] [ID: P3-GSK-NATIVE-01] Migrate Go/Swift/Kotlin backends to direct `EAST3 -> <lang> native emitter` and remove default sidecar JS dependency.
2. [ ] [ID: P3-GSK-NATIVE-01-S1-01] Define common migration contract (EAST3 node coverage, fail-closed behavior, runtime boundary).
3. [ ] [ID: P3-GSK-NATIVE-01-S1-02] Finalize isolation policy for 3-language sidecar compatibility mode (default native / opt-in legacy).
4. [ ] [ID: P3-GSK-NATIVE-01-S2-01] Implement Go native emitter skeleton and default switch in `py2go.py`.
5. [ ] [ID: P3-GSK-NATIVE-01-S2-02] Implement Go basic expression/statement/class coverage and pass early `sample/py` cases.
6. [ ] [ID: P3-GSK-NATIVE-01-S3-01] Implement Swift native emitter skeleton and default switch in `py2swift.py`.
7. [ ] [ID: P3-GSK-NATIVE-01-S3-02] Implement Swift basic expression/statement/class coverage and pass early `sample/py` cases.
8. [ ] [ID: P3-GSK-NATIVE-01-S4-01] Implement Kotlin native emitter skeleton and default switch in `py2kotlin.py`.
9. [ ] [ID: P3-GSK-NATIVE-01-S4-02] Implement Kotlin basic expression/statement/class coverage and pass early `sample/py` cases.
10. [ ] [ID: P3-GSK-NATIVE-01-S5-01] Pass transpile/smoke/parity regressions for all 3 languages in native-default mode and update CI path.
11. [ ] [ID: P3-GSK-NATIVE-01-S5-02] Regenerate `sample/go` / `sample/swift` / `sample/kotlin` and sync docs.

### P3: Resume microgpt source-preservation tasks (Low)

Context: [docs-ja/plans/p3-microgpt-revival.md](../plans/p3-microgpt-revival.md)

1. [ ] [ID: P3-MSP-REVIVE-01] Resume archived `microgpt` preservation tasks under new IDs and restore them to active TODO monitoring.
2. [ ] [ID: P3-MSP-REVIVE-01-S1-01] Create mapping table between archived `P3-MSP-*` history and resumed scope.
3. [ ] [ID: P3-MSP-REVIVE-01-S1-02] Reconfirm current transpile/syntax-check/run procedure for original `microgpt` input and lock expected outcomes.
4. [ ] [ID: P3-MSP-REVIVE-01-S2-01] Revisit `check_microgpt_original_py2cpp_regression.py` and update recurrence-detection conditions.
5. [ ] [ID: P3-MSP-REVIVE-01-S2-02] Prepare logging template for failure reclassification into parser/lower/runtime responsibilities.
6. [ ] [ID: P3-MSP-REVIVE-01-S3-01] Add fixture/smoke reinforcement for `microgpt` if needed and stabilize CI monitoring.
7. [ ] [ID: P3-MSP-REVIVE-01-S3-02] Document migration-back conditions (completion definition) for returning resumed tasks to archive.

### P4: Full multi-language selfhost completion (Very low)

Context: [docs-ja/plans/p4-multilang-selfhost-full-rollout.md](../plans/p4-multilang-selfhost-full-rollout.md)

1. [ ] [ID: P4-MULTILANG-SH-01] Gradually establish selfhost for `cpp/rs/cs/js/ts/go/java/swift/kotlin` and make full multistage monitoring passable.
2. [ ] [ID: P4-MULTILANG-SH-01-S1-01] Fix and document unfinished stage1/stage2/stage3 causes per language, with blocking-chain priority.
3. [ ] [ID: P4-MULTILANG-SH-01-S1-02] Define runner contracts for languages without multistage runners (go/java/swift/kotlin) and settle implementation policy for `runner_not_defined` removal.
4. [ ] [ID: P4-MULTILANG-SH-01-S2-01] Resolve Rust stage1 selfhost failure (from-import acceptance) and move to stage2.
5. [ ] [ID: P4-MULTILANG-SH-01-S2-02] Resolve C# stage2 compile failure and pass stage3 conversion.
6. [ ] [ID: P4-MULTILANG-SH-01-S2-03] Resolve JS stage2 dependency transpile failure and pass multistage.
7. [ ] [ID: P4-MULTILANG-SH-01-S3-01] Resolve TypeScript preview-only status and move to selfhost-executable generation mode.
8. [ ] [ID: P4-MULTILANG-SH-01-S3-02] Connect with Go/Java/Swift/Kotlin native-backend tasks and enable selfhost execution chains.
9. [ ] [ID: P4-MULTILANG-SH-01-S4-01] Integrate all-language multistage regressions into CI and continuously detect failure-category recurrence.
10. [ ] [ID: P4-MULTILANG-SH-01-S4-02] Document completion template (stage pass/exclusion conditions per language) and lock operation rules.
