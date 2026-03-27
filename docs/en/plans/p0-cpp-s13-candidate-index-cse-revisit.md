<a href="../../ja/plans/p0-cpp-s13-candidate-index-cse-revisit.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Re-run Selective CSE/Hoisting for sample/13 `candidates` Selection

Last updated: 2026-03-02

Related TODO:
- `ID: P0-CPP-S13-CANDIDATE-CSE-02` in `docs/ja/todo/index.md`

Background:
- In sample/13 `candidates` selection, there are places where index expressions and intermediate element-access results can be shared, making redundant recomputation and temporary expressions likely.
- Some handling already exists, but improvement item #6 needed to be explicitly tracked as a P0 task.

Goal:
- Apply CSE/hoisting to index computation and element access in `candidates` selection logic, stabilizing C++ output readability and hot-path efficiency in sample/13.

In scope:
- `src/hooks/cpp/emitter/expr.py`
- `src/hooks/cpp/emitter/stmt.py`
- `test/unit/test_py2cpp_codegen_issues.py`
- `sample/cpp/13_maze_generation_steps.cpp` (regeneration check)

Out of scope:
- Introducing a general CSE pass for all EAST3
- Batch rollout beyond sample/13
- Runtime API changes

Acceptance criteria:
- Duplicate index computation is reduced in sample/13 `candidates` selection.
- Element access is emitted via a single path (single evaluation after hoisting).
- Transpile/unit checks pass with no behavior regressions.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/regenerate_samples.py --langs cpp --stems 13_maze_generation_steps --force`

Decision log:
- 2026-03-02: Based on the user instruction "Add #6 to TODO as P0 as well", item #6 for sample/13 was filed as a rerun task.
- 2026-03-02: Added an emitter path (`src/hooks/cpp/emitter/stmt.py`) that hoists complex indexes into `auto __idx_* = ...;` and rewrites to `candidates[__idx_*]` when `Assign(Name = Subscript(...))` has a `Name` owner and a complex index.
- 2026-03-02: Updated sample/13 regression cases in `test_py2cpp_codegen_issues.py` and locked in `__idx_*` hoist output.
- 2026-03-02: Ran `python3 tools/regenerate_samples.py --langs cpp --stems 13_maze_generation_steps --force` / `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v` / `python3 tools/check_py2cpp_transpile.py`; confirmed all passed.

## Breakdown

- [x] [ID: P0-CPP-S13-CANDIDATE-CSE-02-S1-01] Inventory duplicated index/element-access fragments in sample/13 `candidates` selection.
- [x] [ID: P0-CPP-S13-CANDIDATE-CSE-02-S1-02] Specify applicability boundaries (known type, no side effects, fail-closed).
- [x] [ID: P0-CPP-S13-CANDIDATE-CSE-02-S2-01] Implement hoisted output for index computation and element access in CppEmitter.
- [x] [ID: P0-CPP-S13-CANDIDATE-CSE-02-S2-02] Lock fallback behavior for non-applicable cases and preserve semantics.
- [x] [ID: P0-CPP-S13-CANDIDATE-CSE-02-S3-01] Add unit tests to detect recurrence of duplicate expressions.
- [x] [ID: P0-CPP-S13-CANDIDATE-CSE-02-S3-02] Verify no regressions with `sample/cpp/13` regeneration and transpile checks.
