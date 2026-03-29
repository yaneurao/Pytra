<a href="../../ja/plans/p0-cpp-forcore-single-stmt-brace-omit.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Omit Unnecessary Braces for Single-Statement C++ `ForCore` Loops

Last updated: 2026-03-02

Related TODO:
- `ID: P0-CPP-FORCORE-BRACE-OMIT-01` in `docs/ja/todo/index.md`

Background:
- In current C++ emitter output for `ForCore`, braces `{}` are sometimes kept even when the loop body has only a single statement.
- In `sample/cpp/18_mini_language_interpreter.cpp` (`build_benchmark_source`), the single-statement `lines.append(...)` loop is also emitted with `{}`.
- `For`/`ForRange` already have single-statement brace-omission checks, but `ForCore` is not included in default omission logic.

Goal:
- Apply omission conditions equivalent to existing `For`/`ForRange` behavior to `ForCore`, reducing unnecessary `{}` on single-statement loops.
- Improve readability only, with no semantic changes (runtime behavior, scope, optimization results).

In scope:
- `src/hooks/cpp/emitter/cpp_emitter.py` (default brace-omission decision)
- `src/hooks/cpp/emitter/stmt.py` (`ForCore` emission path)
- `tools/unittest/test_py2cpp_codegen_issues.py` (regression)
- `sample/cpp/18_mini_language_interpreter.cpp` (regenerated diff check)

Out of scope:
- Changes to existing brace policy for `If` / `For` / `ForRange`
- Brace policy changes in other backends (Rust/Go/Scala, etc.)
- EAST3 optimizer / lowering spec changes

Acceptance criteria:
- For single-statement `ForCore` loops that satisfy omission conditions, emit `for (...) stmt;` format.
- For multi-statement, tuple-unpack, capture-rewrite, and other existing safety conditions, keep `{}` as before.
- `check_py2cpp_transpile.py` and relevant unit tests pass.
- Braces are omitted for single-statement loops (`lines.append(...)`) in `sample/cpp/18_mini_language_interpreter.cpp`.

Verification commands (planned):
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check/check_py2cpp_transpile.py`
- `python3 tools/gen/regenerate_samples.py --langs cpp --stems 18_mini_language_interpreter --force`

Decision log:
- 2026-03-02: Per user direction, filed `P0` to handle single-statement `ForCore` brace omission in `CppEmitter`.
- 2026-03-02: Finalized fail-closed omission conditions limited to `StaticRangeForPlan + NameTarget + no orelse + single statement`.
- 2026-03-02: Added a `ForCore` branch to `CppEmitter._default_stmt_omit_braces`, enabling brace omission only when the above conditions are met.
- 2026-03-02: Added `test_forcore_static_range_single_stmt_omits_braces`, and passed `sample/cpp/18` regeneration plus `check_py2cpp_transpile`.

## Breakdown

- [x] [ID: P0-CPP-FORCORE-BRACE-OMIT-01-S1-01] Finalize brace-omission conditions for `ForCore` (single statement, safety conditions, exclusion conditions).
- [x] [ID: P0-CPP-FORCORE-BRACE-OMIT-01-S2-01] Add `ForCore` to default brace decisions in `CppEmitter` and apply it to the emission path.
- [x] [ID: P0-CPP-FORCORE-BRACE-OMIT-01-S3-01] Add/update unit tests and lock in `ForCore` omission regressions.
- [x] [ID: P0-CPP-FORCORE-BRACE-OMIT-01-S3-02] Confirm no regressions through `sample/cpp/18` regeneration and transpile checks.
