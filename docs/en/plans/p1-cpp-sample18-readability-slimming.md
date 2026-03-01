# P1: Collapse readability overhead in sample/18 C++ generated code (selected: #2,#7,#8,#5,#1)

Last updated: 2026-02-27

Related TODO:
- `ID: P1-CPP-S18-READ-01` in `docs/ja/todo/index.md`

Background:
- C++ generated code for `sample/18_mini_language_interpreter` has low readability because behavior-priority fallbacks pile up, with many `object` paths and redundant conversions.
- User-selected improvement items #2, #7, #8, #5, #1 are priority targets (`cast collapse`, `map key conversion collapse`, `timing conversion simplification`, `type decay suppression`, `typed loop header`).
- Existing `P0-FORCORE-TYPE-01` handles base task #1, so this task connects those outcomes into the readability-improvement set.

Goal:
- In sample/18 C++ generated code, reduce redundancy step by step for the selected 5 items.
- Improve readability of generated code while preserving compilability and parity.

In scope:
- `src/hooks/cpp/emitter/stmt.py`
- `src/hooks/cpp/emitter/expr.py`
- `src/hooks/cpp/emitter/*` (as needed)
- `test/unit/test_east3_cpp_bridge.py`
- `test/unit/test_py2cpp_smoke.py`
- `sample/cpp/18_mini_language_interpreter.cpp` (regeneration result check)

Out of scope:
- Full redesign of C++ runtime
- Introducing a new EAST3 optimization layer
- Global output optimization outside `sample/18`

Acceptance criteria:
- Improvement items #2, #7, #8, #5, #1 are implemented in a form verifiable independently.
- Redundant patterns at target sites are reduced in regenerated `sample/18` output.
- `check_py2cpp_transpile.py` / related unit tests / `sample/18` compile pass.
- No conflict with `P0-FORCORE-TYPE-01-S3-01`, and #1 application status is traceable in docs.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_smoke.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 src/py2cpp.py sample/py/18_mini_language_interpreter.py -o /tmp/18.cpp`

Decision log:
- 2026-02-27: Opened `P1-CPP-S18-READ-01` for sample/18 C++ readability improvements according to user selection (`2,7,8,5,1`).
- 2026-02-27: Finalized policy that improvement #1 is managed consistently with existing `P0-FORCORE-TYPE-01-S3-01` to avoid duplicate implementation.
- 2026-02-28: Added a typed-iterable path for `ForCore(RuntimeIterForPlan)+NameTarget`; when `list[T]` is known, choose typed loop header instead of `py_dyn_range + Unbox`, reducing redundant casts in sample/18 `for stmt in stmts`.
- 2026-02-28: Confirmed regressions with `test_east3_cpp_bridge.py` (85), `check_py2cpp_transpile.py` (`checked=133 ok=133 fail=0 skipped=6`), and `runtime_parity_check.py --case-root sample 18_mini_language_interpreter --targets cpp` (pass).
- 2026-02-28: Added dict load/store path for `dict_key_verified` to `test_east3_cpp_bridge.py`, and confirmed `env[stmt->name]` is preserved in regenerated sample/18 output to prevent recurrence of key-conversion chains.
- 2026-02-28: Fixed `BuiltinCall(perf_counter)` in `core.py` to `resolved_type=float64`, and confirmed unnecessary `py_to<float64>` is removed around `start/elapsed` in sample/18 via `test_py2cpp_codegen_issues.py` / parity.
- 2026-02-28: Added empty-collection-literal type-alignment rewrite (`_rewrite_empty_collection_literal_for_typed_target`) on return paths, and pinned regression so `new_expr_nodes() -> list[ExprNode]` does not decay to `list<object>{}`.
- 2026-02-28: Confirmed tuple direct unpack (`for (const auto& [line_index, source] : py_enumerate(lines))`) and NameTarget typed loop (`for (rc<StmtNode> stmt : stmts)`) are integrated into sample/18, and marked improvement item #1 complete.

## Breakdown

- [x] [ID: P1-CPP-S18-READ-01-S1-02] Improvement item #2: reduce redundant casts around tuple unpack / temporary variables.
- [x] [ID: P1-CPP-S18-READ-01-S1-07] Improvement item #7: collapse unnecessary key-conversion chains for `map` key access.
- [x] [ID: P1-CPP-S18-READ-01-S1-08] Improvement item #8: simplify numeric conversion chains around timing/elapsed calculations.
- [x] [ID: P1-CPP-S18-READ-01-S1-05] Improvement item #5: suppress excessive default initialization and type decay originating from `unknown`.
- [x] [ID: P1-CPP-S18-READ-01-S1-01] Improvement item #1: integrate typed loop header outcomes into `sample/18` output (depends on `P0-FORCORE-TYPE-01-S3-01`).
