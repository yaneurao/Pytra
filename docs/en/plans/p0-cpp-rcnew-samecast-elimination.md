# P0: Remove Same-Type Cast Redundancy for C++ `rc_new` (highest priority)

Last updated: 2026-02-28

Related TODO:
- `ID: P0-CPP-RCNEW-SAMECAST-01` in `docs/en/todo/index.md`

Background:
- In generated C++ for sample/18, double-form output appears such as `tokens.append(rc<Token>(::rc_new<Token>(...)));`, reducing readability.
- By runtime definition, `::rc_new<T>(...)` already returns `rc<T>`, so outer `rc<T>(...)` is a redundant same-type cast.
- Current same-type cast omission relies on type inference of rendered expressions and cannot infer return types of `::rc_new<T>(...)` sufficiently.

Goal:
- Reduce `rc<T>(::rc_new<T>(...))` to `::rc_new<T>(...)` in C++ output and permanently eliminate same-type casts.
- Pin omission rules as a shared emitter contract instead of a local patch to prevent recurrence.

Scope:
- `src/pytra/compiler/east_parts/code_emitter.py` (strengthen rendered-expression type inference)
- `src/hooks/cpp/emitter/analysis.py` (same-type cast omission decision)
- `src/hooks/cpp/emitter/call.py` (cast application on append path)
- Regression tests in `test/unit/test_py2cpp_codegen_issues.py` / `test/unit/test_east3_cpp_bridge.py`
- `sample/cpp/18_mini_language_interpreter.cpp` (verify after regeneration)

Out of scope:
- Adding class static builder APIs such as `Token::rc_new()`
- Changing `rc`/runtime memory model
- Whole C++ backend readability optimization (separate task)

Acceptance criteria:
- `rc<Token>(::rc_new<Token>(` does not remain in sample/18.
- Add regression tests that treat return type of `::rc_new<T>(...)` as `rc<T>` so same-type casts do not recur.
- `python3 tools/check_py2cpp_transpile.py` and target unit/smoke pass.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2cpp_transpile.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_smoke.py' -v`
- `python3 tools/regenerate_samples.py --langs cpp --force`

Decision log:
- 2026-02-28: By user instruction, confirmed policy to prioritize removing redundant same-type cast in `rc<T>(::rc_new<T>(...))` at P0, rather than moving to `Token::rc_new` style.
- 2026-02-28: Added inference for `::rc_new<T>(...)` form to `infer_rendered_arg_type()`, and updated `should_skip_same_type_cast` to normalize `rc<T>` wrapper differences for same-type judgment.
- 2026-02-28: Applied same-type cast omission on typed `list.append` path, reducing `tokens.append(rc<Token>(::rc_new<Token>(...)))` in sample/18 to `tokens.append(::rc_new<Token>(...))`.
- 2026-02-28: Passed validation runs `test_py2cpp_codegen_issues.py` / `test_east3_cpp_bridge.py` / `tools/check_py2cpp_transpile.py` / `tools/regenerate_samples.py --langs cpp --force` / `tools/runtime_parity_check.py --targets cpp 18_mini_language_interpreter`.

## Breakdown

- [x] [ID: P0-CPP-RCNEW-SAMECAST-01-S1-01] Add a rule so `infer_rendered_arg_type()` can infer `::rc_new<T>(...)` as `rc<T>`.
- [x] [ID: P0-CPP-RCNEW-SAMECAST-01-S1-02] Update same-type cast omission (`should_skip_same_type_cast`) to use this inference and treat `rc<T>(::rc_new<T>(...))` as no-op.
- [x] [ID: P0-CPP-RCNEW-SAMECAST-01-S2-01] Pin with regression tests that same-type cast originating from `rc_new` is actually removed on C++ cast application paths (`apply_cast` vicinity).
- [x] [ID: P0-CPP-RCNEW-SAMECAST-01-S2-02] Regenerate `sample/cpp` and confirm the target fragment in sample/18 reduces to `::rc_new<Token>(...)`.
- [x] [ID: P0-CPP-RCNEW-SAMECAST-01-S3-01] Run `check_py2cpp_transpile` and smoke tests, verify non-regression, and record results in the decision log.
