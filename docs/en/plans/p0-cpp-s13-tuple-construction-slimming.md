<a href="../../ja/plans/p0-cpp-s13-tuple-construction-slimming.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Reduce Redundant Wrapping in sample/13 C++ Tuple Construction

Last updated: 2026-03-02

Related TODO:
- `ID: P0-CPP-S13-TUPLE-CTOR-SLIM-01` in `docs/ja/todo/index.md`

Background:
- In `sample/cpp/13_maze_generation_steps.cpp`, double wrapping remains in the form `::std::tuple<...>(::std::make_tuple(...))`.
- This form is semantically redundant and can be reduced to `::std::make_tuple(...)` or `emplace_back(...)`.
- It hurts output readability and line length.

Goal:
- Remove double wrapping in C++ output when constructing tuple values and unify to the shortest equivalent representation.
- Target frequent sites such as `candidates.append(...)` / `stack.append(...)` in sample/13.

In scope:
- `src/hooks/cpp/emitter/collection_expr.py`
- `src/hooks/cpp/emitter/stmt.py`
- `tools/unittest/test_py2cpp_codegen_issues.py`
- `sample/cpp/13_maze_generation_steps.cpp` (regeneration check)

Out of scope:
- Structured-binding conversion for tuple unpack (separate task)
- Changes to EAST3 type inference algorithms
- Tuple-representation changes in other backends

Acceptance criteria:
- `::std::tuple<T...>(::std::make_tuple(...))` is no longer re-emitted.
- Output is unified to equivalent shortest form (`::std::make_tuple(...)` or `emplace_back(...)`).
- `check_py2cpp_transpile.py` and related unit tests pass.
- Regenerated `sample/cpp/13` confirms reduced redundant wrapping in target fragments.

Verification commands (planned):
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check/check_py2cpp_transpile.py`
- `python3 tools/gen/regenerate_samples.py --langs cpp --stems 13_maze_generation_steps --force`

Decision log:
- 2026-03-02: Per user direction, filed sample/13 tuple double-wrap reduction as P0.
- 2026-03-02: Added a path in `src/hooks/cpp/emitter/call.py` that skips extra cast for `list<tuple[...]>.append(...)` when the argument is `::std::make_tuple(...)`, avoiding double wrapping `::std::tuple<...>(::std::make_tuple(...))`.
- 2026-03-02: Added non-emission checks for `tuple(make_tuple)` to sample/13 regressions in `test_py2cpp_codegen_issues.py` and locked recurrence detection.
- 2026-03-02: Ran `python3 tools/gen/regenerate_samples.py --langs cpp --stems 13_maze_generation_steps --force` / `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v` / `python3 tools/check/check_py2cpp_transpile.py`; confirmed all passed.

## Breakdown

- [x] [ID: P0-CPP-S13-TUPLE-CTOR-SLIM-01-S1-01] Inventory sample/13 tuple double-wrap sites and lock applicability boundaries.
- [x] [ID: P0-CPP-S13-TUPLE-CTOR-SLIM-01-S1-02] Define priority rules for direct `make_tuple` and `append/emplace` application.
- [x] [ID: P0-CPP-S13-TUPLE-CTOR-SLIM-01-S2-01] Update CppEmitter tuple-construction output and remove double wrapping.
- [x] [ID: P0-CPP-S13-TUPLE-CTOR-SLIM-01-S2-02] Add `emplace_back`-capable paths for `append` variants and reduce unnecessary temporary construction.
- [x] [ID: P0-CPP-S13-TUPLE-CTOR-SLIM-01-S2-03] Lock fallback behavior for non-applicable cases and preserve current semantics.
- [x] [ID: P0-CPP-S13-TUPLE-CTOR-SLIM-01-S3-01] Add unit tests to detect double-wrap recurrence.
- [x] [ID: P0-CPP-S13-TUPLE-CTOR-SLIM-01-S3-02] Verify no regressions with `sample/cpp/13` regeneration and transpile checks.
