<a href="../../ja/plans/p0-east3-cpp-empty-init-shorthand.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Reduce C++ Empty Initialization to `= {};` via EAST3 Markers

Last updated: 2026-03-02

Related TODO:
- `ID: P0-EAST3-CPP-EMPTY-INIT-SHORTHAND-01` in `docs/ja/todo/index.md`

Background:
- Current C++ output can emit redundant empty initialization where the left-hand type is repeated, such as `dict<str, int64> env = dict<str, int64>{};`.
- In C++, equivalent forms like `dict<str, int64> env = {};` (or `env{}`) are more readable.
- But naive replacement risks semantic changes at `Any/object` boundaries or ambiguous typing cases, so EAST3 must determine safe conditions first.

Goal:
- Add explicit markers in EAST3 for assignments/declarations where empty-initialization shorthand is safe, and let the C++ emitter output `= {};` based on those markers.
- If markers are missing or inconsistent, preserve current output to maintain fail-closed behavior.

In scope:
- `src/pytra/compiler/east_parts/east3_opt_passes/*` (add new pass or extend existing pass)
- `src/hooks/cpp/emitter/stmt.py` / `src/hooks/cpp/emitter/collection_expr.py`
- `tools/unittest/test_east3_cpp_bridge.py` / `tools/unittest/test_py2cpp_codegen_issues.py`
- `sample/cpp/18_mini_language_interpreter.cpp` (regeneration check)

Out of scope:
- Expression reductions other than empty initialization (parenthesis reduction, cast reduction, etc.)
- Output changes in other backends (Rust/Scala/Java, etc.)
- Spec changes to C++ runtime container types

Acceptance criteria:
- EAST3 marks empty `List/Dict/Set` initialization in `AnnAssign/Assign` when safety conditions are met.
- C++ emitter outputs `= {};` only for marked cases with matching types.
- Existing explicit typed initialization (for example `dict<...>{}` / `make_object(...)`) is preserved in `Any/object`, union, and runtime-boxing paths.
- `check_py2cpp_transpile.py` and relevant unit tests pass, and reduction is confirmed at target points in `sample/cpp/18`.

Verification commands (planned):
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check/check_py2cpp_transpile.py`
- `python3 tools/gen/regenerate_samples.py --langs cpp --stems 18_mini_language_interpreter --force`

Decision log:
- 2026-03-02: Per user direction, filed `P0` for adding EAST3 safety markers and reducing to `= {};` in the C++ emitter.
- 2026-03-02: Added `EmptyInitShorthandPass` and finalized implementation to attach `cpp_empty_init_shorthand_v1` (`version/target_type/rhs_kind`) only when `Assign/AnnAssign` has empty `List/Dict/Set`, `target_type` is `list/dict/set[...]`, and not `Any/object/union` (on mismatch, marker is removed to fail closed).
- 2026-03-02: Added marker-reference flow to `CppEmitter`; now `rendered_value` is reduced to `{}` only when hints match. Existing `T{}` output is preserved for missing hints, inconsistent hints, or non-empty initialization.
- 2026-03-02: Ran unit + sample + transpile checks, and confirmed empty initialization in `sample/cpp/18` reduced to `= {};`.
  - `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_optimizer.py' -v` (51 tests, OK)
  - `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -v` (92 tests, OK)
  - `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v` (98 tests, OK)
  - `python3 tools/gen/regenerate_samples.py --langs cpp --stems 18_mini_language_interpreter --force` (regen=1 fail=0)
  - `python3 tools/check/check_py2cpp_transpile.py` (checked=136 ok=136 fail=0 skipped=6)

## Breakdown

- [x] [ID: P0-EAST3-CPP-EMPTY-INIT-SHORTHAND-01-S1-01] Specify applicability conditions (LHS type = RHS empty container type, non-Any/object, non-boxing).
- [x] [ID: P0-EAST3-CPP-EMPTY-INIT-SHORTHAND-01-S1-02] Define EAST3 marker schema (for example `cpp_empty_init_shorthand_v1`) and fail-closed conditions.
- [x] [ID: P0-EAST3-CPP-EMPTY-INIT-SHORTHAND-01-S2-01] Add markers to target nodes in an EAST3 optimizer pass.
- [x] [ID: P0-EAST3-CPP-EMPTY-INIT-SHORTHAND-01-S2-02] Switch C++ emitter to marker-driven output and reduce `T x = T{};` to `T x = {};`.
- [x] [ID: P0-EAST3-CPP-EMPTY-INIT-SHORTHAND-01-S2-03] Implement fallback for missing/inconsistent markers and return to existing output.
- [x] [ID: P0-EAST3-CPP-EMPTY-INIT-SHORTHAND-01-S3-01] Add unit tests to detect misapplication (`Any/object` paths) and recurrence.
- [x] [ID: P0-EAST3-CPP-EMPTY-INIT-SHORTHAND-01-S3-02] Verify no regressions with `sample/cpp/18` regeneration and transpile checks.
