<a href="../../ja/spec/spec-east3-optimizer.md">
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
- Direct lowering into backend syntax forms (for example, C++ `for (init; cond; inc)` generation).
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
  - `non_escape_policy`
    - `unknown_call_escape` (treat unresolved calls as escape)
    - `unknown_attr_call_escape` (treat dynamic attribute calls as escape)
    - `global_write_escape` (treat global/nonlocal writes as escape)
    - `return_escape_by_default` (treat return boundaries as escape by default)
    - `yield_escape_by_default` (treat yield boundaries as escape by default)
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

## 8. v1 Pass Set (Implementation Synced: 2026-02-27)

| Pass | opt-level | Status | Example transform | Primary guard |
| --- | --- | --- | --- | --- |
| `NoOpCastCleanupPass` | `O1` | implemented | remove cast entries where `from == to` | only when static type equality is proven |
| `LiteralCastFoldPass` | `O1` | implemented | fold literal `static_cast` call to `Constant` | literal + lossless (same-type) only |
| `RangeForCanonicalizationPass` | `O1` | implemented | `RuntimeIterForPlan(py_range)` -> `StaticRangeForPlan` | currently limited to constant-int args (1..3) with `step != 0` |
| `UnusedLoopVarElisionPass` | `O1` | implemented | rename provably unused loop var binding to `_` | skip on body/`orelse`/post-loop reads or dynamic name introspection (`locals`, etc.) |
| `LoopInvariantHoistLitePass` | `O2` | implemented | hoist first invariant assignment of non-empty static-range loop to preheader | requires statically non-empty loop, side-effect-free expr, and no reassignment |
| `StrengthReductionFloatLoopPass` | `O2` | implemented | rewrite `float` loop `x / C` into `x * (1/C)` | `C` must be finite, non-zero, and power-of-two absolute value |
| `RedundantWrapperCtorPass` | - | planned | remove redundant `bytes(bytes_expr)` | safe ephemeral/alias-free only |
| `DeadTempCleanupPass` | - | planned | remove dead temporary assignments | no side effects / references |

Notes:

- Current implementation intentionally prioritizes fail-closed behavior with conservative applicability.
- `O0` disables all passes, `O1` runs `O1` passes, `O2` runs `O1 + O2` passes.

### 8.1 Responsibility Boundary for `for ... in range(...)`

- The common optimizer may normalize `for ... in range(...)` into a backend-agnostic counted-loop representation.
- `for _ in range(5)` is an optimization candidate only when actual-use analysis proves the variable is unused; identifier naming (`_`) alone is not sufficient.
- If safety cannot be proven, skip the transform (fail-closed), including cases such as:
  - the loop variable is read in body/`else`/after-loop scope,
  - closure capture can observe the variable,
  - dynamic name-introspection paths (`locals`/`globals`/`vars`/`eval`) may observe it.
- Backend syntax materialization (for example, C++ `for (i = 0; i < n; ++i)`) belongs to `EAST3 -> <lang>` lowering / emitter, not to the common optimizer.

### 8.2 Responsibility Boundary for Expression Normalization (`EAST3` vs emitter)

- Expression normalizations that are semantically shared across backends (for example, identity-cast elimination, `StaticRange` trip-count/condition simplification, comparison-chain normalization) must be performed in `EAST3 -> EAST3`.
- Normalization outputs must be kept as structured form (node or metadata) so emitters can consume them without re-deriving semantics.
- Emitter responsibility is limited to target-language rendering:
  - operator/token spelling, runtime/API symbol choice, and minimal precedence-safe parentheses;
  - target-language surface constraints (for example, `Math.floor`-style mapping).
- For expression categories with normalized data, emitters must not rebuild equivalent semantics by ad-hoc string construction.
- If normalized data is missing/invalid, use fail-closed behavior and suppress the optimization output (no unsafe `reserve`/condition emission).
- Policy: semantics are decided in `EAST3`; syntax is decided in emitters.

## 9. Language-specific Layer

- Optional `east3_optimizer_<lang>.py` runs after common layer.
- It must keep the same safety contract.
- Use it only for target-specific codegen constraints.
- Backend syntax materialization may be handled in this layer or in the emitter.

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

### 10.1 Operations (Trace and Isolation)

1. Start with default `O1`, and capture before/after EAST3 plus optimizer trace.

```bash
python src/py2cpp.py sample/py/01_mandelbrot.py out.cpp \
  --dump-east3-before-opt work/logs/east3_before.json \
  --dump-east3-after-opt work/logs/east3_after.json \
  --dump-east3-opt-trace work/logs/east3_trace.txt
```

2. If behavior regresses, isolate passes via `--east3-opt-pass` (example disables range-loop passes).

```bash
python src/py2cpp.py sample/py/01_mandelbrot.py out.cpp \
  --east3-opt-level 2 \
  --east3-opt-pass -RangeForCanonicalizationPass,-UnusedLoopVarElisionPass
```

3. Validate `O0/O1/O2` compatibility under the same runtime-parity procedure.

```bash
python tools/runtime_parity_check.py --case-root sample --all-samples \
  --targets cpp,rs,cs,js,ts --ignore-unstable-stdout \
  --east3-opt-level 0 --summary-json work/logs/east3_opt_parity_o0.json
python tools/runtime_parity_check.py --case-root sample --all-samples \
  --targets cpp,rs,cs,js,ts --ignore-unstable-stdout \
  --east3-opt-level 1 --summary-json work/logs/east3_opt_parity_o1.json
python tools/runtime_parity_check.py --case-root sample --all-samples \
  --targets cpp,rs,cs,js,ts --ignore-unstable-stdout \
  --east3-opt-level 2 --summary-json work/logs/east3_opt_parity_o2.json
```

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
