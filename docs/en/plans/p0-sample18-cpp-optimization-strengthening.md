# P0: Strengthen C++ output optimization for sample/18 (runtime hot path)

Last updated: 2026-03-01

Related TODO:
- `ID: P0-CPP-S18-OPT-01` in `docs/ja/todo/index.md`

Background:
- `sample/cpp/18_mini_language_interpreter.cpp` still contains `object`-path handling left in place for behavioral compatibility.
- In particular, there are still non-collapsed sections in hot paths (`tokenize / parse / execute`) where typed paths should be possible.
- Existing readability work (`P1-CPP-S18-READ-01`) improved part of this, but the current output still has dynamic paths reintroduced.

Goal:
- In C++ output for `sample/18`, progressively collapse `object` paths and string-comparison costs to reduce runtime overhead.
- Prefer typed loop / typed container / typed access for paths where EAST3 already has type information.

In scope:
- `src/pytra/compiler/east_parts/east3_opt_passes/*` (if needed)
- `src/hooks/cpp/emitter/*.py` (for/call/stmt/expr/type_bridge)
- `test/unit/test_east3_cpp_bridge.py`
- `test/unit/test_py2cpp_codegen_issues.py`
- `sample/cpp/18_mini_language_interpreter.cpp` (regeneration check)

Out of scope:
- Mini-language spec changes
- Full runtime ABI changes
- Bulk optimization outside sample/18

Acceptance criteria:
- The following 6 points are confirmed in `sample/18`:
  1. `enumerate(lines)` becomes typed tuple iteration, not `object` + `py_at`.
  2. `tokens` are held in typed containers, not `object(list<object>)`.
  3. Repeated retrieval (`py_at + obj_to_rc_or_raise`) in `Parser` is reduced.
  4. Runtime string comparisons for `ExprNode.kind` / `StmtNode.kind` / `op` are collapsed to enum/integer tags.
  5. `NUMBER` tokens no longer call `py_to_int64` on every parse step, and instead use values pre-decoded at lexical analysis.
  6. `execute` statement iteration is collapsed into a typed loop (non-`object`).
- `check_py2cpp_transpile.py`, `test_east3_cpp_bridge.py`, and `test_py2cpp_codegen_issues.py` pass.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2cpp_transpile.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 src/py2cpp.py sample/py/18_mini_language_interpreter.py -o sample/cpp/18_mini_language_interpreter.cpp`

Decision log:
- 2026-03-01: Per user instruction, we decomposed the 6 optimization opportunities for sample/18 C++ at P0 and created the implementation plan.
- 2026-03-01: Under `cpp_list_model=pyobj`, `enumerate(lines)` resolves to `py_enumerate(object)` and cannot proceed to typed direct unpack. Adopted policy: choose typed enumerate only when `iter_item_type=tuple[int64, str]` and `lines:list[str]`, via `py_to_str_list_from_object(lines)`.
- 2026-03-01: Added sample/18 regression under `cpp_list_model="pyobj"` in `test_py2cpp_codegen_issues.py`, pinning `for (const auto& [line_index, source] : py_enumerate(py_to_str_list_from_object(lines)))`.
- 2026-03-01: Passed `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v` (75), `test_east3_cpp_bridge.py` (90), and `python3 tools/check_py2cpp_transpile.py` (`checked=134 ok=134 fail=0 skipped=6`).
- 2026-03-01: Confirmed that the main cause of `tokens` degradation is a type boundary where `_cpp_type_text(list[T]) -> object` under `cpp_list_model=pyobj`. Since `tokenize()` return and `Parser.tokens` are lists crossing function boundaries, they are outside current stack-list (non-escape) collapse scope.
- 2026-03-01: Fixed `S2-02` policy to add a sample/18-first `list[Token]` specialized unbox-once path (`tokenize -> Parser` boundary), and progressively collapse `py_append(make_object(...))` and chained `py_at + obj_to_rc_or_raise`.
- 2026-03-01: Inventoried token access in `Parser`, confirming repeated `py_at(this->tokens, this->pos)` at `peek_kind` (1), `expect` (2), and `parse_primary` (1). Fixed `S3-02` policy: synthesize `_current_token()` / `_previous_token()` helpers on the emitter side to reduce duplicate unboxing at the same index.
- 2026-03-01: Pinned current string-comparison points (`node->kind` x4, `node->op` x4, `stmt->kind` x2). For `S4-02`, policy is to keep string fields for `kind/op` while adding `uint8` tags in parallel so comparisons use integers, and existing strings are used only for error messages.
- 2026-03-01: Since `NUMBER` already slices `text` in tokenize, fixed `S5-02` policy to add `int64 number_value` to `Token` (`0` for non-NUMBER), convert once with `py_to_int64` in lexical phase, and eliminate reconversion in parse phase.
- 2026-03-01: To connect to typed loop in `execute`, fixed `S6-02` policy to change `parse_program`/`execute` boundary to prefer `list<rc<StmtNode>>`, allowing `object` boxing only at external boundaries (main call, and runtime API only if needed).
- 2026-03-01: Implemented `S6-02` by adding `py_to_rc_list_from_object<T>()` to runtime, restoring typed iteration fastpath in `list[RefClass]` iteration for `ForCore(NameTarget)` where `pyobj` would otherwise force runtime path. Confirmed sample/18 `execute` collapses to `for (rc<StmtNode> stmt : py_to_rc_list_from_object<StmtNode>(stmts, ...))`.
- 2026-03-01: Re-ran `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v` (76) / `test_east3_cpp_bridge.py` (90) / `python3 tools/check_py2cpp_transpile.py` (`checked=134 ok=134 fail=0 skipped=6`) and confirmed no regression.
- 2026-03-01: Ran `python3 tools/runtime_parity_check.py --case-root sample --targets cpp 18_mini_language_interpreter --ignore-unstable-stdout` and confirmed `[PASS] 18_mini_language_interpreter`.
- 2026-03-01: Implemented `S3-02` by reorganizing sample/18 `Parser` through helper methods `current_token()/previous_token()`, reducing same-index token retrieval in generated C++ `expect` to once. Added regression in `test_py2cpp_codegen_issues.py` and confirmed behavior parity in `runtime_parity_check`.
- 2026-03-01: Implemented `S5-02` by adding `number_value` to sample/18 `Token`, predecoding `int(text)` for NUMBER in `tokenize`, and switching `parse_primary` to use `token_num.number_value`. Confirmed no regression with `test_py2cpp_codegen_issues.py`, `runtime_parity_check`, and `check_py2cpp_transpile`.
- 2026-03-01: Implemented `S4-02` by adding `kind_tag/op_tag` to `ExprNode/StmtNode` and moving eval/execute branches to integer comparison. To avoid top-level constant initialization being shadowed during module init, tag values were fixed as literals.
- 2026-03-01: Implemented `S2-02` by extending policy so `list[RefClass]` uses typed containers even with `cpp_list_model=pyobj`, and updated emitter to keep `Token/ExprNode/StmtNode` lists as `list<rc<...>>`. In sample/18, `tokenize`/`Parser.tokens`/`parse_program`/`execute` moved from `object` path to typed-container path.
- 2026-03-01: Implemented `S7-01` by adding sample/18 typed-token-container regressions in `test_py2cpp_codegen_issues.py` (`tokenize` signature / `Parser.tokens` field / `current_token` access), and pinned regenerated diffs of `sample/cpp/18_mini_language_interpreter.cpp`.
- 2026-03-01: Re-ran `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v` (80) / `test_east3_cpp_bridge.py` (90) / `python3 tools/check_py2cpp_transpile.py` (`checked=134 ok=134 fail=0 skipped=6`) / `runtime_parity_check` (sample/18 cpp PASS), and marked parent `P0-CPP-S18-OPT-01` complete.

## Breakdown

- [ ] [ID: P0-CPP-S18-OPT-01] Implement sample/18 C++ hot-path items in stages (typed enumerate / typed container / parser access / enum tag / number predecode / typed execute loop).

- [x] [ID: P0-CPP-S18-OPT-01-S1-01] Organize EAST3 and C++ emitter for-header generation conditions to collapse `enumerate(lines)` into typed tuple iteration.
- [x] [ID: P0-CPP-S18-OPT-01-S1-02] Add regression that pins `for (::std::tuple<int64, str> ...)`-equivalent output in sample/18 tokenize loop.

- [x] [ID: P0-CPP-S18-OPT-01-S2-01] Preserve type info for `tokens` (`list[Token]` equivalent) across parse->EAST3->emitter and identify degradation conditions into `object(list<object>)`.
- [x] [ID: P0-CPP-S18-OPT-01-S2-02] Migrate `tokenize` / `Parser` `tokens` to typed-container output and reduce excess boxing from `py_append(make_object(...))`.

- [x] [ID: P0-CPP-S18-OPT-01-S3-01] Detect repeated `py_at + obj_to_rc_or_raise` patterns in `Parser.peek_kind/expect/parse_primary` and design a shared helper (token cache) policy.
- [x] [ID: P0-CPP-S18-OPT-01-S3-02] Change emitter output to one-time token retrieval use and reduce duplicate dynamic access at the same index.

- [x] [ID: P0-CPP-S18-OPT-01-S4-01] Inventory comparison sites of `ExprNode.kind` / `StmtNode.kind` / `op` and define minimal enum/integer tag rollout surface (sample/18 first).
- [x] [ID: P0-CPP-S18-OPT-01-S4-02] Emit tag-based branches in C++ emitter and collapse `if (node->kind == "...")` chains.

- [x] [ID: P0-CPP-S18-OPT-01-S5-01] Verify current string-retention path for `NUMBER` tokens (`tokenize->parse_primary->py_to_int64`) and finalize lexical-stage predecode policy.
- [x] [ID: P0-CPP-S18-OPT-01-S5-02] Migrate to `Token` numeric-field use and reduce `py_to_int64(token->text)` in `parse_primary`.

- [x] [ID: P0-CPP-S18-OPT-01-S6-01] Design alignment between `parse_program` return type and downstream use to type-loop statement iteration in `execute`.
- [x] [ID: P0-CPP-S18-OPT-01-S6-02] Replace `for (object ... : py_dyn_range(stmts))` with typed iteration and reduce in-loop conversion `obj_to_rc_or_raise<StmtNode>`.

- [x] [ID: P0-CPP-S18-OPT-01-S7-01] Add golden regressions pinning regenerated sample/18 diffs for the 6 items above.
- [x] [ID: P0-CPP-S18-OPT-01-S7-02] Confirm no regression via `check_py2cpp_transpile.py` / unit tests / sample execution.
