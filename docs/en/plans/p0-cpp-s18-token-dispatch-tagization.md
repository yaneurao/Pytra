# P0: Tag-ify tokenizer string dispatch in sample/18 (if-chain collapse)

Last updated: 2026-03-01

Related TODO:
- `ID: P0-CPP-S18-TOKEN-DISPATCH-TAG-01` in `docs/ja/todo/index.md`

Background:
- The tokenizer in sample/18 determines token kinds with a string-comparison chain like `if (ch == "+") ...`.
- As branches increase, both comparison cost and generated-code verbosity increase.

Goal:
- Phase tokenizer token decisions toward a tag/enum-based approach and collapse long string-comparison chains.

Scope:
- `src/hooks/cpp/emitter/*` (tokenize emission)
- `sample/py/18_mini_language_interpreter.py` (only if minimal type-annotation adjustment is necessary)
- `test/unit/test_py2cpp_codegen_issues.py`
- `sample/cpp/18_mini_language_interpreter.cpp`

Out of scope:
- Mini-language grammar expansion
- Full parser/evaluator redesign

Acceptance criteria:
- In sample/18 tokenizer, token-kind selection is centered on tag lookup, and long string `if` chains are collapsed.
- Kind strings for error-message purposes are preserved only where necessary.
- Non-regression is confirmed via transpile/unit/parity checks.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/runtime_parity_check.py --case-root sample --targets cpp 18_mini_language_interpreter --ignore-unstable-stdout`

Decision log:
- 2026-03-01: Filed as P0 for additional sample/18 optimization to tag-ify tokenizer branches.
- 2026-03-01: Changed single-char token decisions in `sample/18` to `dict[str,int]` tag lookup + kind array lookup, and collapsed the `if (ch == "+")` chain.
- 2026-03-01: Confirmed a regression where `=` detection failed because of module-level constant initialization order (uninitialized global + shadowing inside `__pytra_main`), and resolved it by moving tag/kind constants into tokenize-local scope.
- 2026-03-01: Added tokenizer tag-dispatch regression coverage to `test_py2cpp_codegen_issues.py` to prevent reintroduction of single-char branch chains.
- 2026-03-01: Confirmed non-regression with `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v` (82 tests), `python3 tools/check_py2cpp_transpile.py` (`checked=134 ok=134 fail=0 skipped=6`), and `runtime_parity_check` (sample/18 cpp PASS).

## Breakdown

- [x] [ID: P0-CPP-S18-TOKEN-DISPATCH-TAG-01] Shift tokenizer kind decisions from string-comparison chains to a tag/enum-centered approach.
- [x] [ID: P0-CPP-S18-TOKEN-DISPATCH-TAG-01-S1-01] Inventory the current branch sequence and fix the tag-map spec (single char -> kind_tag).
- [x] [ID: P0-CPP-S18-TOKEN-DISPATCH-TAG-01-S2-01] Change emitter output to prioritize tag-based decisions and keep equivalent kind strings only where needed.
- [x] [ID: P0-CPP-S18-TOKEN-DISPATCH-TAG-01-S2-02] Add sample/18 regression coverage to prevent reintroduction of `if (ch == "...")` chains.
- [x] [ID: P0-CPP-S18-TOKEN-DISPATCH-TAG-01-S3-01] Confirm non-regression via transpile/unit/parity.
