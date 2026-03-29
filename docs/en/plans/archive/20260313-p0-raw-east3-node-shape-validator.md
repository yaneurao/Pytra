<a href="../../../ja/plans/archive/20260313-p0-raw-east3-node-shape-validator.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: fix raw EAST3 validator node-shape misclassification

Last updated: 2026-03-13

Related TODO:
- `ID: P0-RAW-EAST3-NODE-SHAPE-VALIDATOR-01` in `docs/ja/todo/index.md`

Background:
- In the current backend test matrix snapshot, `rs` fails on `any_dict_items` with `raw EAST3 $.body[1].meta.lifetime_analysis.def_use.defs.meta must be an object`, while `scala` and `cpp` fail on `18_mini_language_interpreter` with `raw EAST3 $.body[5].body[5].arg_index.kind must be non-empty string`.
- These are not backend-local bugs. The common cause is that `src/toolchain/link/program_validator.py` treats any dict key named `kind` or `meta` as if it were a node field.
- `lifetime_analysis.def_use.defs["meta"]` is a variable name inside a def-use map, not node metadata. Likewise, `arg_index["kind"]` is an auxiliary map entry, not an EAST node kind.
- Because the failure happens in the shared frontend path, fixing it once should remove the same raw-validator blocker across multiple backends including `rs/java/ruby/scala/cpp`.

Goal:
- Narrow raw EAST3 validation so `kind` / `meta` / `source_span` / `repr` invariants apply only to node-shaped dicts.
- Lock regressions so auxiliary analysis maps and index maps with keys named `meta` or `kind` no longer trigger false positives.
- Verify that `any_dict_items` and `18_mini_language_interpreter` now pass through the raw validator and reach backend transpile routes.

Scope:
- `src/toolchain/link/program_validator.py`
- `tools/unittest/common/test_frontend_type_expr.py`
- Representative smoke / docs / matrix notes only if needed

Out of scope:
- Backend-emitter-specific fixes
- Downstream compile/run quality fixes for `18_mini_language_interpreter`
- A full redesign of the raw EAST3 validator

Acceptance criteria:
- `validate_raw_east3_doc()` no longer misclassifies auxiliary-map entries such as `defs["meta"]` or `arg_index["kind"]` as node fields.
- Fail-closed checks on actual nodes for `kind` / `meta` / `source_span` / `dispatch_mode` drift remain intact.
- The repo has regression tests proving that `test/fixtures/typing/any_dict_items.py` and `sample/py/18_mini_language_interpreter.py` pass the raw validator.
- Targeted `py2x --target rs/java/ruby/scala/cpp` transpiles no longer stop at raw EAST3 validation.

Verification:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src:/workspace/Pytra/test/unit python3 -m unittest discover -s tools/unittest/common -p 'test_frontend_type_expr.py'`
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src:/workspace/Pytra/test/unit python3 src/py2x.py --target rs test/fixtures/typing/any_dict_items.py -o /tmp/any_dict_items.rs`
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src:/workspace/Pytra/test/unit python3 src/py2x.py --target java test/fixtures/typing/any_dict_items.py -o /tmp/AnyDictItems.java`
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src:/workspace/Pytra/test/unit python3 src/py2x.py --target ruby test/fixtures/typing/any_dict_items.py -o /tmp/any_dict_items.rb`
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src:/workspace/Pytra/test/unit python3 src/py2x.py --target scala sample/py/18_mini_language_interpreter.py -o /tmp/MiniLanguageInterpreter.scala`
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src:/workspace/Pytra/test/unit python3 src/py2x.py --target cpp sample/py/18_mini_language_interpreter.py -o /tmp/mini_language_interpreter.cpp`
- `git diff --check`

Implementation policy:
1. Do not broadly weaken validation. Fix the node-shape classifier instead.
2. Skipping auxiliary maps must not drop fail-closed coverage for actual body items or expression nodes.
3. Add regression tests first, then tighten the validator around those cases.
4. Confirm the matrix-visible failures with targeted transpile verification and synchronize the TODO / decision log afterward.

## Breakdown

- [x] [ID: P0-RAW-EAST3-NODE-SHAPE-VALIDATOR-01] Fix raw EAST3 validator node-shape misclassification so auxiliary `meta` / `kind` keys do not produce false positives.
- [x] [ID: P0-RAW-EAST3-NODE-SHAPE-VALIDATOR-01-S1-01] Lock `any_dict_items` / `18_mini_language_interpreter` and a synthetic auxiliary-map case into regression tests and the plan.
- [x] [ID: P0-RAW-EAST3-NODE-SHAPE-VALIDATOR-01-S2-01] Narrow raw EAST3 validation to node-shaped dicts while preserving fail-closed behavior for actual nodes.
- [x] [ID: P0-RAW-EAST3-NODE-SHAPE-VALIDATOR-01-S2-02] Sync targeted backend transpile verification plus the TODO / decision log and reduce the validator-origin matrix failures.

Decision log:
- 2026-03-13: After the active TODO became empty, a new P0 seed was chosen from the current backend test matrix red cells. The raw EAST3 validator false positives on `any_dict_items` and `18_mini_language_interpreter` are the first target because they are shared frontend failures, not backend-local issues.
- 2026-03-13: `S1-01` added a synthetic auxiliary-map regression plus actual fixture/sample load regressions to `test_frontend_type_expr.py`, locking the fact that `defs["meta"]` and `arg_index["kind"]` must not trigger raw-validator false positives.
- 2026-03-13: `S2-01` threaded `parent_key` through the object walk in `program_validator.py` and limited EAST3 node validation to dicts that sit under node containers such as `body/value/target` or carry node hint keys. `py2x --target rs/java/ruby any_dict_items` and `py2x --target scala/cpp 18_mini_language_interpreter` now reach output generation instead of stopping in raw validation.
- 2026-03-13: `S2-02` synchronized the targeted transpile verification with the TODO/decision log and treated the matrix-visible failures as closed from the raw-validator side. Any remaining red cells after this point belong to downstream backend-specific issues, not node-shape misclassification.
