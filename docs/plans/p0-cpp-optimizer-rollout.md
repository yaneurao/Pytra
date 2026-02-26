# P0: Introduce a Post-Lowering Optimization Layer for the C++ Backend (`CppOptimizer`)

Last updated: 2026-02-26

Related TODO:
- `ID: P0-CPP-OPT-01` in `docs-ja/todo/index.md`

Background:
- We are reducing `CppEmitter` responsibilities, but C++-specific optimization decisions are still easy to mix into emitter logic.
- The responsibility boundary between `CppOptimizer` and `CppEmitter` is already defined in `spec-cpp-optimizer` and needs to be reflected in implementation.
- The direction is structured-IR optimization, not post-generation text optimization.

Goal:
- Introduce `CppOptimizer` after `EAST3 -> C++ lowering` and shrink `CppEmitter` to a deterministic syntax emitter.

In scope:
- `src/hooks/cpp/optimizer/` (new)
- Optimizer wiring in `src/py2cpp.py` and the C++ backend path
- `src/hooks/cpp/emitter/` (optimization responsibility migration)
- C++ regression tests and sample benchmarking path

Out of scope:
- C++ runtime API spec changes
- Replacing compiler `-O*` (`g++/clang++`)
- Regex-based optimization on generated `.cpp` strings

Acceptance criteria:
- `CppOptimizer` supports `O0/O1/O2`, pass-level on/off, and dump/trace.
- v1 passes are implemented (`dead temp`, `no-op cast`, `const condition`, `range-for shape`).
- Optimization branching inside `CppEmitter` is reduced while keeping a clear boundary.
- C++ transpile/parity regressions stay on baseline.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 -m unittest discover -s test/unit -p 'test_py2cpp_*.py'`
- `python3 tools/runtime_parity_check.py --case-root sample --targets cpp --all-samples --ignore-unstable-stdout`

Decision log:
- 2026-02-26: Initial draft created. Broke down the `spec-cpp-optimizer` boundary into implementable S1/S2/S3 steps.
- 2026-02-26: Completed `P0-CPP-OPT-01-S1-01` by adding `src/hooks/cpp/optimizer/` scaffold (`context/trace/passes/cpp_optimizer`), wiring no-op optimization in `emit_cpp_from_east`, and validating with `test_cpp_optimizer.py` plus existing `test_east3_cpp_bridge.py`.

## Breakdown

- [x] [ID: P0-CPP-OPT-01-S1-01] Add the `src/hooks/cpp/optimizer/` skeleton (`optimizer/context/trace/passes`) and no-op wiring.
- [ ] [ID: P0-CPP-OPT-01-S1-02] Add `CppOptimizer` invocation in the `py2cpp` execution path and wire `--cpp-opt-level`, `--cpp-opt-pass`, and dump options.
- [ ] [ID: P0-CPP-OPT-01-S2-01] Implement `CppDeadTempPass` / `CppNoOpCastPass` and migrate equivalent emitter logic.
- [ ] [ID: P0-CPP-OPT-01-S2-02] Add `CppConstConditionPass` / `CppRangeForShapePass` and pin IR normalization before C++ structuring.
- [ ] [ID: P0-CPP-OPT-01-S2-03] Introduce `CppRuntimeFastPathPass` in a limited scope while preserving runtime contract equivalence.
- [ ] [ID: P0-CPP-OPT-01-S3-01] Reduce optimization branching on `CppEmitter` and align boundaries to `spec-cpp-optimizer`.
- [ ] [ID: P0-CPP-OPT-01-S3-02] Lock C++ regressions (`test_py2cpp_*`, `check_py2cpp_transpile.py`, `runtime_parity_check --targets cpp`).
- [ ] [ID: P0-CPP-OPT-01-S3-03] Measure performance/size/generated diff baselines and record introduction effects in context docs.
