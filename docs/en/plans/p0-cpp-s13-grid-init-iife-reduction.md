<a href="../../ja/plans/p0-cpp-s13-grid-init-iife-reduction.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Reduce IIFE Usage in sample/13 C++ `grid` Initialization

Last updated: 2026-03-02

Related TODO:
- `ID: P0-CPP-S13-GRID-IIFE-REDUCE-01` in `docs/ja/todo/index.md`

Background:
- In `sample/cpp/13_maze_generation_steps.cpp`, 2D `grid` initialization can be emitted as IIFE form `([&]() { ... return tmp; })()`, increasing code size and reducing readability.
- This path often matches patterns that only append to an empty array a fixed number of times, so it can be reduced to regular loop-based initialization.

Goal:
- Identify `grid` initialization patterns that do not require an IIFE and reduce them to normal statement sequences (declaration + loop + append).
- Improve sample/13 readability and suppress unnecessary lambda generation.

In scope:
- `src/hooks/cpp/emitter/stmt.py`
- `src/hooks/cpp/emitter/collection_expr.py`
- `tools/unittest/test_py2cpp_codegen_issues.py`
- `sample/cpp/13_maze_generation_steps.cpp` (regeneration check)

Out of scope:
- Redesign of expression trees for all initialization expressions
- Node-spec changes across all EAST3
- Simultaneous rollout to other backends

Acceptance criteria:
- Unnecessary IIFE is no longer re-emitted in sample/13 `grid` initialization.
- Initialization is reduced to semantics-preserving normal statements, and generated code becomes shorter.
- Existing transpile/unit tests pass with no behavior regressions.

Verification commands (planned):
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check/check_py2cpp_transpile.py`
- `python3 tools/gen/regenerate_samples.py --langs cpp --stems 13_maze_generation_steps --force`

Decision log:
- 2026-03-02: Per user direction, filed reduction of sample/13 `grid` initialization IIFE as P0.
- 2026-03-02: Confirmed current output is `list<list<int64>>(cell_h, list<int64>(cell_w, 1))`, and `[&]() -> list<list<int64>> { ... }()` IIFE is not being re-emitted.
- 2026-03-02: Ran `python3 tools/gen/regenerate_samples.py --langs cpp --stems 13_maze_generation_steps --force` / `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v` / `python3 tools/check/check_py2cpp_transpile.py`; confirmed all passed.

## Breakdown

- [x] [ID: P0-CPP-S13-GRID-IIFE-REDUCE-01-S1-01] Inventory IIFE initialization fragments in sample/13 and lock reducibility conditions.
- [x] [ID: P0-CPP-S13-GRID-IIFE-REDUCE-01-S1-02] Specify boundary conditions for "reducible / keep IIFE" (fail-closed).
- [x] [ID: P0-CPP-S13-GRID-IIFE-REDUCE-01-S2-01] Update CppEmitter initialization output and convert reducible patterns to normal statements.
- [x] [ID: P0-CPP-S13-GRID-IIFE-REDUCE-01-S2-02] Keep fallback path so non-reducible cases return to current IIFE output.
- [x] [ID: P0-CPP-S13-GRID-IIFE-REDUCE-01-S3-01] Add unit tests to detect IIFE recurrence and incorrect reduction.
- [x] [ID: P0-CPP-S13-GRID-IIFE-REDUCE-01-S3-02] Verify no regressions with `sample/cpp/13` regeneration and transpile checks.
