# P1: Remove Multiple Inheritance from `CppEmitter`

## Goal
Abolish multiple inheritance in `CppEmitter` and migrate to a single-inheritance design.
This reduces hierarchical type-check dependencies on the emitter side and simplifies `isinstance()`-equivalent branching.

## Background
- Current `CppEmitter` uses multiple inheritance over `CppCallEmitter`, `CppStatementEmitter`, `CppExpressionEmitter`, `CppBinaryOperatorEmitter`, `CppTriviaEmitter`, `CppTemporaryEmitter`, and `CodeEmitter`.
- While responsibility split helped, this also makes runtime `isinstance`-style checks and call-resolution paths more complex.
- To continue safe hooks reduction and `CppEmitter` size reduction, class design should converge to single inheritance plus explicit delegation (or function injection).

## Policy
1. `CppEmitter` should ultimately converge to single inheritance from `CodeEmitter`.
2. Additional responsibilities are moved to either:
   - dedicated helper instances like `self._call_emitter`, `self._statement_emitter`, `self._expression_emitter`, or
   - stateless helper functions built from current helper classes.
3. To minimize impact on external APIs (outside `cpp_emitter.py`), `CppEmitter` keeps a thin delegation API.
4. `isinstance`-like routing should move from type-hints/flags to explicit processing-kind identifiers.

## Acceptance criteria
- `CppEmitter` no longer uses multiple inheritance.
- The change stays consistent with responsibility split progress in `docs/ja/plans/p1-cpp-emitter-reduce.md`.
- `python3 test/unit/test_py2cpp_smoke.py` and `python3 tools/check_py2cpp_transpile.py` pass.
- Readability and regression quality of generated outputs are preserved.

## References
- `docs/ja/plans/p1-cpp-emitter-reduce.md`
- `src/hooks/cpp/emitter/cpp_emitter.py`

## TODO Granularity (proposed)
- Parent task `P1-CPP-EMIT-NOMI-01`
  - `P1-CPP-EMIT-NOMI-01-S1`: Decide data/lifecycle design for removing multiple inheritance.
  - `P1-CPP-EMIT-NOMI-01-S2`: Migrate initialization paths to delegation.
  - `P1-CPP-EMIT-NOMI-01-S3`: Extract delegation paths for `call/expr/stmt` method families.
  - `P1-CPP-EMIT-NOMI-01-S4`: Verify existing regression tests and no major performance regressions.

## Decision log

- [2026-02-25] [ID: P1-CPP-EMIT-NOMI-01-S1]
  - Work done: changed `src/hooks/cpp/emitter/cpp_emitter.py` to single inheritance (`CodeEmitter` only).
  - Implementation: injected delegation from `CppCallEmitter`/`CppStatementEmitter`/`CppExpressionEmitter`/`CppBinaryOperatorEmitter`/`CppTriviaEmitter`/`CppTemporaryEmitter` into `CppEmitter` via class-external attach wiring.
  - Validation: `PYTHONPATH=src python3 tools/check_py2cpp_transpile.py` verified `checked=132 ok=132 fail=0 skipped=6`.

- [2026-02-25] [ID: P1-CPP-EMIT-NOMI-01-S2]
  - Work done: explicitly classified `isinstance`/type-check-related type-id name-call branches with `_type_id_name_call_kind`, simplifying branching in `_build_type_id_expr_from_call_name` / `render_call` / `_render_repr_expr`.
  - Change details: unified flag-based classification of `isinstance/issubclass` and `py_*` type-id calls; clarified non-lowered-case detection routes and error construction.
  - Validation: `PYTHONPATH=src python3 tools/check_py2cpp_transpile.py` verified `checked=131 ok=131 fail=0 skipped=6`.
