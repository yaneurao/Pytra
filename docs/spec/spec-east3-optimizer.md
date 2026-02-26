<a href="../../docs-ja/spec/spec-east3-optimizer.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# EAST3 Optimizer Specification

This document defines the responsibilities, contracts, and rollout plan of the `EAST3` optimization layer (`EAST3 -> EAST3`).

## 1. Objectives

- Improve generated-code quality and runtime performance right before emitters.
- Keep optimization logic out of emitters to reduce maintenance cost.
- Separate reusable common optimizations from optional language-specific optimizations.

## 2. Non-goals

- Replacing syntax/type-resolution logic before `EAST3`.
- Replacing backend-specific final formatting responsibilities.
- Allowing semantics-changing optimizations.

## 3. Pipeline Placement

The canonical order is:

1. `EAST2 -> EAST3` lowering (`east2_to_east3_lowering.py`)
2. `EAST3 Optimizer` (common)
3. `EAST3 Optimizer <lang>` (optional)
4. target emitter

## 4. Input/Output Contract

### 4.1 Input

- `EAST3` module document (`kind == "Module"`, `east_stage == 3`).

### 4.2 Output

- Output remains `EAST3` (`EAST3 -> EAST3`).
- Must preserve:
  - `east_stage == 3`
  - schema compatibility
  - `source_span` / `repr` / `resolved_type` / `borrow_kind` / `casts`
  - `main_guard_body` split contract

## 5. Safety Contract

- Semantics preservation is mandatory.
- The optimizer must not change:
  - evaluation order
  - exception timing
  - side-effect existence/count
  - short-circuit behavior
- Reordering across potentially side-effectful expressions is forbidden.
- If proof is insufficient, skip transformation (fail-closed).

## 6. Architecture (Pass Manager)

Use an ordered pass pipeline.

- `PassContext`
  - `opt_level`
  - `target_lang` (optional)
  - `debug_flags`
- `PassResult`
  - `changed: bool`
  - `change_count: int`
  - `warnings: list[str]`
  - `elapsed_ms: float`

Execution rules:

- deterministic passes only
- stable output for same input/options
- explicit pass-order dependency

## 7. Optimization Levels

- `O0`: optimizer disabled
- `O1` (default): conservative local transforms only
- `O2`: `O1` plus conservative loop-focused transforms

## 8. Recommended v1 Passes

| Pass | Purpose | Example transform | Guard |
| --- | --- | --- | --- |
| `NoOpCastCleanupPass` | remove useless casts | remove cast when source/target static types are equal | static proof required |
| `LiteralCastFoldPass` | fold literal casts | `cast<int64>(42) -> 42` | lossless literal-only |
| `RedundantWrapperCtorPass` | remove redundant wrappers | redundant `bytes(...)` around bytes-typed temp | only for safe ephemeral cases |
| `LoopInvariantHoistLitePass` | hoist loop-invariant expressions | move invariant denominator/computation to preheader | side-effect-free only |
| `StrengthReductionFloatLoopPass` | reduce loop arithmetic cost | `x / C -> x * invC` | invariant floating-point divisor |
| `DeadTempCleanupPass` | remove dead temps | drop unused temporary assignments | no side-effect references |

## 9. Language-specific Layer

- Optional `east3_optimizer_<lang>.py` runs after common layer.
- It must keep the same safety contract.
- Use it only for target-specific codegen constraints.

Suggested layout:

- `src/pytra/compiler/east_parts/east3_optimizer.py`
- `src/pytra/compiler/east_parts/east3_optimizer_cpp.py`
- `src/pytra/compiler/east_parts/east3_opt_passes/*.py`

## 10. CLI and Debug Contract

Recommended options:

- `--east3-opt-level {0,1,2}` (default: `1`)
- `--east3-opt-pass +PASS,-PASS`
- `--dump-east3-before-opt <path>`
- `--dump-east3-after-opt <path>`
- `--dump-east3-opt-trace <path>`

Recommended trace payload:

- pass execution order
- per-pass `changed/change_count/elapsed_ms`
- final summary

## 11. Test Contract

Minimum requirements:

- per-pass unit tests (`EAST3 in/out` diffs)
- invariant tests (`east_stage`, schema compatibility, type fields)
- regression tests on major `sample/` cases
- parity checks for stdout/artifacts

## 12. Rollout Phases

### Phase 1

- pass manager scaffold
- `O0/O1` support + trace output
- `NoOpCastCleanup` and `LiteralCastFold`

### Phase 2

- loop-focused passes
- language-specific optimizer entry points

### Phase 3

- profile-guided pass policy
- baseline measurement + automatic regression detection

## 13. Compatibility Policy

- Keep existing emitter API stable.
- Default to `O1`, always provide `O0` for debugging.
- New optimizer passes must preserve existing fixture/sample output parity.
