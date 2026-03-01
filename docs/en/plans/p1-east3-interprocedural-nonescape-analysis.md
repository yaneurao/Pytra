# P1: Introduce EAST3 interprocedural non-escape analysis (RAII candidate annotation)

Last updated: 2026-02-28

Related TODO:
- `ID: P1-EAST3-NONESCAPE-IPA-01` in `docs/ja/todo/index.md`

Background:
- To collapse `rc` / `object` paths in C++ output, we first need to determine whether values escape outside functions.
- A local-only, single-function analysis misses escapes that happen through callees.
- User policy prioritizes marking proven non-escape points as RAII-conversion candidates.

Goal:
- Add interprocedural non-escape analysis to EAST3 optimization layer, and store function summaries and value annotations in `meta`.
- Conservatively converge by fixed-point iteration per SCC over call graphs including recursion/mutual recursion.
- Provide annotation boundaries that downstream (`CppOptimizer` / `CppEmitter`) can use to decide RAII conversion applicability.

In scope:
- `src/pytra/compiler/east_parts/east3_optimizer.py`
- `src/pytra/compiler/east_parts/east3_opt_passes/*` (add new `NonEscapeInterproceduralPass`)
- `src/pytra/compiler/east_parts/east3_optimizer_cli.py` (extend trace/dump if needed)
- `test/unit/test_east3_optimizer*.py` (pin analysis-result regressions)
- If needed, minimal reflection in `docs/ja/spec/spec-east3-optimizer.md`

Out of scope:
- Actual `rc/object -> RAII` replacement on C++ side (separate task)
- Applying optimization to other backends
- Aggressive inference for dynamic calls with uncertain behavior

Analysis policy:
- Build function summaries first.
  - Examples: whether `arg_i` escapes, whether return values originate from escaped paths, whether locally created values flow out.
- Build a call graph and iterate per SCC.
  - Inside an SCC, update summaries together and repeat until no changes.
- Treat unresolved calls (dynamic dispatch / external / Any-object paths) as `escape=true` with fail-closed policy.
- After convergence, annotate EAST3 node `meta`.
  - Function nodes: `escape_summary`
  - Expression/assignment nodes: `non_escape_candidate`, etc.

Acceptance criteria:
- On fixtures containing interprocedural calls, non-escape candidates that local analysis could not detect are reflected in `meta`.
- Fixed-point computation converges for recursion/mutual-recursion cases and is deterministic (same result on rerun).
- Cases with unresolved calls fall to fail-closed (safe side).
- Existing `east3 optimizer` regressions are non-regressive.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_optimizer*.py' -v`
- `python3 tools/check_py2cpp_transpile.py`

Decision log:
- 2026-02-28: Per user instruction, fixed policy to introduce interprocedural non-escape analysis (SCC + fixed point) on EAST3 as a pre-stage to RAII replacement.
- 2026-02-28: Fixed implementation policy to introduce `non_escape_policy` in `PassContext`, normalize fail-closed defaults (`unknown_call_escape`, etc.), and distribute them to the pass.
- 2026-02-28: Added `non_escape_policy` output to `optimize_east3_document` reports, and pinned stability of default/override/reported values via unit tests.
- 2026-02-28: Added `non_escape_call_graph.py`, implementing call-graph utilities that extract function/method symbols from EAST3 modules and return resolved edges plus unresolved-call counts, along with deterministic Tarjan SCC decomposition.
- 2026-02-28: Added `test_east3_non_escape_call_graph.py` and pinned call graph/SCC regressions for top-level/class-method/mutual-recursion cases.
- 2026-02-28: Added `NonEscapeInterproceduralPass`, implementing fixed-point summary computation converging `arg_escape` / `return_from_args` / `return_escape` (including fail-closed unknown-call policy).
- 2026-02-28: In `test_east3_non_escape_interprocedural_pass.py`, pinned regressions for summary propagation (`sink->wrap`), return-origin propagation (`identity->wrap2`), and policy override.
- 2026-02-28: Added implementation that annotates converged summaries onto function-node `meta.escape_summary` and call-expression `meta.non_escape_callsite`, and added regression assertions for annotation payloads in unit tests.
- 2026-02-28: Added summary-propagation tests for mixed mutual-recursion + external-call cases (`a <-> b` with `unknown_sink`), plus determinism tests where second run yields `changed=False`.
- 2026-02-28: Re-ran `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_optimizer*.py' -v` (42 OK) and `python3 tools/check_py2cpp_transpile.py` (`checked=133 ok=133 fail=0 skipped=6`), confirming no regression.

## Breakdown

- [x] [ID: P1-EAST3-NONESCAPE-IPA-01-S1-01] Specify escape-judgment domain (arg escape / return escape / unknown-call policy) and hold it in `PassContext`.
- [x] [ID: P1-EAST3-NONESCAPE-IPA-01-S1-02] Extract call graph from EAST3 and add SCC decomposition utilities.
- [x] [ID: P1-EAST3-NONESCAPE-IPA-01-S2-01] Implement `NonEscapeInterproceduralPass` and make summary fixed-point updates converge.
- [x] [ID: P1-EAST3-NONESCAPE-IPA-01-S2-02] Annotate converged summaries into function/expression node `meta`.
- [x] [ID: P1-EAST3-NONESCAPE-IPA-01-S3-01] Add unit tests for recursion, mutual recursion, and mixed external calls to pin fail-closed behavior and determinism.
- [x] [ID: P1-EAST3-NONESCAPE-IPA-01-S3-02] Re-run existing `east3 optimizer` regressions and `check_py2cpp_transpile` to confirm non-regression.
