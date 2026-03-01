# P2: Reduce Excess Parentheses in Java Output

Last updated: 2026-02-28

Related TODO:
- `ID: P2-JAVA-PARENS-01` in `docs/ja/todo/index.md`

Background:
- Generated code in `sample/java` still contains excessive parentheses such as `double x2 = (x * x);`, reducing readability.
- Current Java emitter implementation always wraps entire binary expressions in parentheses, making even clearly prioritized expressions redundant.
- Removing parentheses uniformly risks changing semantics, so minimization must be based on operator precedence.

Objective:
- Move Java backend expression output toward "minimal parentheses with semantic preservation," improving readability of `sample/java`.

Scope:
- Expression output in `src/hooks/java/emitter/java_native_emitter.py` (especially around `BinOp`)
- `test/unit/test_py2java_smoke.py` and Java codegen regressions
- `sample/java` regeneration results

Out of scope:
- Large Java backend optimizations (speed improvements, runtime API redesign, etc.)
- Parenthesis-rule changes in other backends (`cpp/rs/cs/js/ts/go/swift/kotlin/ruby/lua`)
- Redesign of AST/EAST structure itself

Acceptance Criteria:
- Unnecessary whole-expression parentheses are removed in simple forms like `x * x` without changing semantics.
- Required parentheses are preserved in expressions involving precedence/associativity interactions.
- Existing Java smoke/transpile regressions pass, and excessive parentheses are reduced in regenerated `sample/java`.

Validation Commands (planned):
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2java_smoke.py' -v`
- `python3 tools/regenerate_samples.py --langs java --force`
- `rg -n "\\(x \\* x\\)" sample/java`

Decision Log:
- 2026-02-28: Per user instruction, filed P2 task to reduce excessive parentheses in Java generated code.
- 2026-03-01: Applied minimal-parentheses rules only to `BinOp`, and adopted fail-closed policy to always keep parentheses when RHS is a same-precedence `BinOp` (preserve grouping such as `a - (b - c)`).
- 2026-03-01: Switched `BinOp` output in `java_native_emitter.py` to precedence-based rendering and reduced unnecessary whole-expression parentheses.
- 2026-03-01: Added regressions in `test_py2java_smoke.py` for `BinOp` minimal-parentheses and RHS grouping preservation, and updated existing expected values to new notation.
- 2026-03-01: Ran `tools/regenerate_samples.py --langs java --force` and reflected changes into all 18 files in `sample/java`. Verified no residues of `"(x * x)"` and `"(2.0 * Math.PI)"` via `rg`.
- 2026-03-01: Confirmed `check_py2java_transpile.py` still fails only for known 4 unsupported `Try/Yield/Swap` cases (out of scope for this task).

## Breakdown

- [x] [ID: P2-JAVA-PARENS-01-S1-01] Document Java emitter parenthesis-output contract (minimal-parentheses rules and fail-closed conditions).
- [x] [ID: P2-JAVA-PARENS-01-S2-01] Change `BinOp` output to precedence-based rendering and reduce unnecessary whole-expression parentheses.
- [x] [ID: P2-JAVA-PARENS-01-S2-02] Add regressions covering semantic preservation in combinations with surrounding expressions (`Compare/BoolOp/IfExp`, etc.).
- [x] [ID: P2-JAVA-PARENS-01-S3-01] Regenerate `sample/java`, verify reduction results, and lock regression tests.
