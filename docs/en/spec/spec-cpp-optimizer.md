<a href="../../ja/spec/spec-cpp-optimizer.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# C++ Optimizer Specification

This document defines the responsibilities and contracts of the `CppOptimizer` layer that runs after lowering from `EAST3` into the C++ backend representation.

## 1. Objectives

- Separate C++ backend-specific optimization logic from `CppEmitter`.
- Apply semantics-preserving transforms on structured IR before text emission.
- Avoid fragile post-emission text rewrites.

## 2. Non-goals

- Replacing the common `EAST3 -> EAST3` optimizer.
- Replacing machine/codegen optimization that belongs to `g++/clang++`.
- Regex-like rewriting on already emitted `.cpp` text.

## 3. Pipeline Placement

Canonical order:

1. `EAST2 -> EAST3` lowering
2. `EAST3 Optimizer` (common)
3. `EAST3 Optimizer cpp` (optional)
4. `EAST3 -> C++` lowering (to backend IR)
5. `CppOptimizer` (`Cpp IR -> Cpp IR`)
6. `CppEmitter` (`Cpp IR -> C++ source text`)
7. C++ compiler optimization (`-O2/-O3` etc.)

Notes:

- `CppOptimizer` consumes structured representation (C++ IR/AST), not source text.
- Even if the current implementation has no fully separated C++ IR yet, the optimizer module should be isolated and extracted incrementally.

## 4. Responsibility Boundary: `CppOptimizer` vs `CppEmitter`

`CppOptimizer` responsibilities:

- C++ backend-specific semantics-preserving optimization.
- Reduce redundant temporaries/casts introduced by lowering.
- IR normalization that prepares backend syntax materialization.
- Keep downstream emission deterministic and simple.

`CppEmitter` responsibilities:

- Deterministic serialization from IR nodes to C++ syntax.
- Formatting concerns (indentation/newlines/trivia/include rendering).
- Minimal local branching for syntax, but no dataflow-heavy optimization logic.

Boundary rule:

- If a transform needs analysis/proof for semantic safety, it belongs to `CppOptimizer`.

## 5. Input/Output Contract

Input:

- Module-level C++ backend IR after `EAST3 -> C++` lowering.
- Metadata needed for type, ownership, and side-effect reasoning.

Output:

- Same backend IR kind (`Cpp IR -> Cpp IR`).
- Must preserve:
  - evaluation order
  - exception timing
  - side-effect existence/count
  - RC/ownership semantics (`rc<T>`, `py_*` runtime API contract)

Forbidden:

- Implicit runtime-contract changes.
- Fail-open optimization when safety proof is insufficient.

## 6. Pass Manager Contract

- `CppOptimizer` is an ordered pass pipeline.
- Passes must be deterministic.
- Same input/options must produce the same output.

Recommended `PassContext`:

- `opt_level`
- `target_cpp_std` (for example c++17)
- `debug_flags`
- `runtime_mode` (bounds/div/mod/negative-index modes)

Recommended `PassResult`:

- `changed: bool`
- `change_count: int`
- `warnings: list[str]`
- `elapsed_ms: float`

## 7. Optimization Levels

- `O0`: disable `CppOptimizer`.
- `O1` (default): conservative local transforms only.
- `O2`: `O1` plus moderate loop/temp simplification.

Note:

- These levels are pre-emission optimization levels.
- They are distinct from C++ compiler `-O*` levels.

## 8. Recommended v1 Passes

| Pass | Purpose | Example transform | Guard |
| --- | --- | --- | --- |
| `CppDeadTempPass` | remove redundant temporaries | inline pure one-use temps | side-effect free + order preserved |
| `CppNoOpCastPass` | remove useless casts | drop cast where static type already matches | static proof required |
| `CppConstConditionPass` | simplify constant branches | `if (true) A else B -> A` | no side-effect change |
| `CppRangeForShapePass` | finalize counted-loop shape | normalize to C++ for-loop node form | preserve bounds/increment/eval order |
| `CppRuntimeFastPathPass` | simplify runtime calls | switch to fast helper only when type is statically fixed | exact equivalence to runtime contract |

## 9. CLI / Debug Contract

Recommended options:

- `--cpp-opt-level {0,1,2}`
- `--cpp-opt-pass +PASS,-PASS`
- `--dump-cpp-ir-before-opt <path>`
- `--dump-cpp-ir-after-opt <path>`
- `--dump-cpp-opt-trace <path>`

Compatibility operation:

- If legacy `-O*` exists, map it to `--cpp-opt-level` during migration and allow later decoupling.

## 10. Test Contract

Minimum requirements:

- per-pass unit tests (IR in/out diff)
- pipeline integration tests (generated C++ compiles with/without optimizer)
- parity tests (same runtime behavior as Python)
- regression checks on `sample/` (including performance trend)

Required focus:

- semantic equivalence across `O0` vs `O1/O2`
- explicit suppression on cases where optimization must not apply

## 11. Recommended File Layout

- `src/hooks/cpp/optimizer/cpp_optimizer.py`
- `src/hooks/cpp/optimizer/passes/*.py`
- `src/hooks/cpp/optimizer/context.py`
- `src/hooks/cpp/optimizer/trace.py`

## 12. Rollout Phases

### Phase 1

- add optimizer entry (effectively no-op)
- add `O0/O1`, trace, and 2 passes (`CppDeadTempPass`, `CppNoOpCastPass`)
- migrate equivalent logic out of emitter

### Phase 2

- add loop pass (`CppRangeForShapePass`)
- limited rollout of runtime-call fast-path pass
- further reduce branching/analysis in `CppEmitter`

### Phase 3

- metric-driven pass policy
- automated regression detection (speed/size/parity)

## 13. Compatibility Policy

- Preserve existing `py2cpp.py` CLI behavior first.
- Always provide `O0` for issue isolation.
- Do not accept changes that break fixture/sample stdout or artifact parity.
