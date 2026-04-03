<a href="../../../ja/spec/archive/20260328-spec-cpp-optimizer.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# C++ Optimizer Specification

This document defines the responsibilities and contracts of the `CppOptimizer` layer, applied after lowering from `EAST3` to the C++ backend.

## 1. Purpose

- Separate C++ backend-specific optimizations from the emitter, reducing the scope of `CppEmitter`'s responsibilities.
- Perform semantics-preserving optimizations at the structured IR stage (before text output), improving readability, performance, and maintainability.
- Avoid fragile post-stringification optimizations (regex-based replacements).

## 2. Non-Goals

- Replacing the `EAST3` common optimization layer (`EAST3 -> EAST3`).
- Substituting for machine-level optimizations that belong to the C++ compiler (`g++/clang++`).
- Text-based rewrites of already-stringified `.cpp` files.

## 3. Pipeline Position

Standard order:

1. `EAST2 -> EAST3` lowering
2. `EAST3 Optimizer` (common)
3. `EAST3 Optimizer cpp` (optional)
4. `EAST3 -> C++` lowering (backend IR construction)
5. `CppOptimizer` (C++ IR -> C++ IR)
6. `CppEmitter` (C++ IR -> C++ source text)
7. C++ compiler optimization (`-O2/-O3`, etc.)

Notes:

- `CppOptimizer` takes a structured representation (C++ IR/AST) as input, not text.
- Even if the current implementation has not yet separated the C++ IR, the optimizer module should be split from the emitter as a matter of responsibility, to be made independent incrementally.

## 4. Responsibility Boundary Between `CppOptimizer` and `CppEmitter`

`CppOptimizer` responsibilities:

- Semantics-preserving optimizations specific to the C++ backend.
- Reduction of redundant temporaries / redundant casts introduced during lowering.
- IR normalization for shaping into C++ syntax (e.g., finalizing counted loops into for-loop form).
- Structuring the IR so that the subsequent emitter can operate as a simple "syntax printer".

`CppEmitter` responsibilities:

- Deterministically outputting IR nodes as C++ syntax.
- Formatting responsibilities: indentation, newlines, trivia, include ordering.
- No data-flow analysis or optimization logic, except for minimal local branching due to syntax requirements.

Boundary rules:

- Transformations that require analysis in order to preserve semantics belong in `CppOptimizer`.
- The responsibility of "producing the same string from the same input IR" is concentrated in `CppEmitter`.

## 5. Input/Output Contract

Input:

- The C++ backend IR produced after `EAST3 -> C++ lowering` (per module).
- Type information, borrow/ownership information, and meta-information for side-effect analysis must be accessible.

Output:

- The same C++ backend IR (`Cpp IR -> Cpp IR`).
- The following must be preserved:
  - Evaluation order
  - Exception-raising timing
  - Presence/count of side effects
  - RC / ownership semantics (`rc<T>`, `py_*` runtime API contracts)

Prohibitions:

- Rewrites that implicitly change runtime API contracts.
- Applying insufficiently proven optimizations (fail-open).

## 6. Pass Manager Contract

- `CppOptimizer` is composed of an ordered sequence of passes.
- Passes must be deterministic.
- The same output is guaranteed for the same input and the same settings.

`PassContext` (recommended):

- `opt_level`
- `target_cpp_std` (e.g., c++17)
- `debug_flags`
- `runtime_mode` (conversion modes for bounds/div/mod/negative-index, etc.)

`PassResult` (recommended):

- `changed: bool`
- `change_count: int`
- `warnings: list[str]`
- `elapsed_ms: float`

## 7. Optimization Levels

- `O0`:
  - `CppOptimizer` disabled (zero passes).
- `O1` (default):
  - Only local, easily safety-proven transformations.
- `O2`:
  - `O1` + moderate transformations such as loop / temporary cleanup.

Notes:

- The `O*` here refers to the "pre-generation optimization level".
- This is a separate layer from the C++ compiler's `-O*`, and must not be confused with it.

## 8. Recommended v1 Passes

| Pass | Purpose | Representative Transformation | Guard |
| --- | --- | --- | --- |
| `CppDeadTempPass` | Reduce redundant temporaries | Inline pure temporaries used only once | No side effects / evaluation order preserved |
| `CppNoOpCastPass` | Remove meaningless casts | Eliminate casts where actual types match | Statically prove type match |
| `CppConstConditionPass` | Clean up constant conditional branches | `if (true) A else B` -> `A` | No side-effect change from removing one branch |
| `CppRangeForShapePass` | Finalize counted-loop for-loop shape | Normalize to C++ for node | Preserve iteration bounds, increment, evaluation order |
| `CppRuntimeFastPathPass` | Simplify runtime call expressions | Substitute lightweight helpers only when type is certain | Fully equivalent to existing runtime contracts |

## 9. CLI / Debug Contract

Recommended options:

- `--cpp-opt-level {0,1,2}`
- `--cpp-opt-pass +PASS,-PASS`
- `--dump-cpp-ir-before-opt <path>`
- `--dump-cpp-ir-after-opt <path>`
- `--dump-cpp-opt-trace <path>`

Compatibility operation:

- If existing `-O*` options are present, map them to `--cpp-opt-level` during the transition period, allowing future separation.

## 10. Test Contract

Minimum requirements:

- Per-pass unit tests (IR in/out diff verification)
- Pipeline integration tests (generated C++ is compilable both with and without the optimizer)
- Parity tests (match Python execution results)
- `sample/` regression (including performance degradation monitoring)

Required perspectives:

- Semantics must match between `O0` and `O1/O2`.
- Passes must be suppressed in cases where they should not be applied.

## 11. Recommended File Layout

- `src/toolchain/emit/cpp/optimizer/cpp_optimizer.py`
- `src/toolchain/emit/cpp/optimizer/passes/*.py`
- `src/toolchain/emit/cpp/optimizer/context.py`
- `src/toolchain/emit/cpp/optimizer/trace.py`

## 12. Introduction Phases

### Phase 1

- Add optimizer entry point (effectively a no-op)
- Introduce `O0/O1`, trace, and 2 passes (`CppDeadTempPass`, `CppNoOpCastPass`)
- Move equivalent logic from within the emitter

### Phase 2

- Introduce loop-related passes (`CppRangeForShapePass`)
- Limited introduction of runtime call simplification pass
- Further reduce branching/analysis logic in `CppEmitter`

### Phase 3

- Metric-based optimization (finalize pass enablement policy)
- Automate regression detection (speed, size, compatibility)

## 13. Compatibility Policy

- Prioritize compatibility with the existing `py2cpp.py` CLI.
- Always provide `O0` to allow isolation.
- Do not accept changes that break stdout/artifact matching for existing fixtures/samples.
