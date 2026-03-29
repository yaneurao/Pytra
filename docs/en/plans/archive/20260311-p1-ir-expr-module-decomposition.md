<a href="../../../ja/plans/archive/20260311-p1-ir-expr-module-decomposition.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: Decompose large `toolchain.ir` expression modules by cluster

Last updated: 2026-03-11

Related TODO:
- `ID: P1-IR-EXPR-MODULE-DECOMPOSITION-01` in `docs/ja/todo/index.md`

Background:
- `P1-IR-CORE-DECOMPOSITION-01` and `P1-IR-ENTRYPOINT-FACADE-PRUNING-01` reduced `src/toolchain/ir/core.py` to a thin facade.
- However, large expression-side split modules still remain. At the start of this task, `core_expr_call_annotation.py` is still over 1000 lines and `core_expr_attr_subscript_suffix.py` is still over 600 lines.
- As long as those modules stay this large, small call/attr/subscript changes still have wide review scope, and source-contract tests do not map cleanly to the actual split boundaries.

Goal:
- Further decompose the heaviest expression split modules by cluster and make the responsibility boundaries around `attr suffix`, `subscript suffix`, `named-call`, `attr-call`, and `callee-call` explicit.
- Align source-contract tests so they map 1:1 to the split module structure.

Scope:
- `src/toolchain/ir/core_expr_attr_subscript_suffix.py`
- `src/toolchain/ir/core_expr_call_annotation.py`
- `src/toolchain/ir/core_expr_shell.py`
- `tools/unittest/ir/_east_core_test_support.py`
- `tools/unittest/ir/test_east_core_source_contract_expr_suffix.py`
- `tools/unittest/ir/test_east_core_source_contract_call_dispatch.py`
- `tools/unittest/ir/test_east_core_source_contract_call_metadata.py`
- `docs/ja/todo/index.md` / `docs/en/todo/index.md`
- `docs/ja/plans/p1-ir-expr-module-decomposition.md` / `docs/en/plans/p1-ir-expr-module-decomposition.md`

Out of scope:
- Parser / IR / runtime spec changes
- New nominal-ADT or typed-boundary feature work
- Backend implementation changes

Acceptance criteria:
- `attr suffix` and `subscript suffix` live in separate dedicated modules.
- `named-call`, `attr-call`, and `callee-call` annotation clusters are also split into dedicated modules in bundle-sized slices.
- `_ShExprParser` becomes mostly orchestration plus mixin imports after the split.
- Source-contract tests follow the split layout, and representative regressions (`test_east_core*.py`, `test_prepare_selfhost_source.py`, `build_selfhost.py`) pass.

Checks:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/ir -p 'test_east_core*.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/selfhost -p 'test_prepare_selfhost_source.py'`
- `python3 tools/build_selfhost.py`
- `python3 tools/check/check_transpiler_version_gate.py`
- `python3 tools/run/run_regen_on_version_bump.py --dry-run`
- `git diff --check`

Breakdown:
- [x] [ID: P1-IR-EXPR-MODULE-DECOMPOSITION-01-S1-01] Inventory the remaining clusters in `core_expr_call_annotation.py` and `core_expr_attr_subscript_suffix.py`, and lock split boundaries as `attr_suffix`, `subscript_suffix`, `named_call`, `attr_call`, `callee_call`, and `shared_state`.
- [x] [ID: P1-IR-EXPR-MODULE-DECOMPOSITION-01-S1-02] Fix the rule that TODO / plan progress notes stay compressed at bundle granularity for this task.
- [x] [ID: P1-IR-EXPR-MODULE-DECOMPOSITION-01-S2-01] Split the `attr suffix` / `subscript suffix` cluster into separate modules and update `core_expr_shell.py` imports.
- [x] [ID: P1-IR-EXPR-MODULE-DECOMPOSITION-01-S2-02] Split the `named-call` / `attr-call` / `callee-call` annotation cluster into dedicated modules in bundle-sized slices.
- [x] [ID: P1-IR-EXPR-MODULE-DECOMPOSITION-01-S3-01] Update source-contract tests to the post-split layout and pass representative regressions.
- [ ] [ID: P1-IR-EXPR-MODULE-DECOMPOSITION-01-S4-01] Update docs / TODO / archive and move the completed task to archive.

Decision log:
- 2026-03-11: Initial draft. At task start, `core_expr_call_annotation.py` and `core_expr_attr_subscript_suffix.py` are the remaining large expression modules, while `core.py` is already a thin facade, so the next split target is the expression-side split modules themselves.
- 2026-03-11: `core_expr_attr_subscript_suffix.py` will split into `attr_suffix` / `subscript_suffix` / `shared_postfix_orchestration`. The shared layer keeps only `_resolve_postfix_span_repr` and postfix dispatch.
- 2026-03-11: `core_expr_call_annotation.py` will split into `named_call` / `attr_call` / `callee_call` / `shared_state_orchestration`. The shared layer keeps call payload building, generic return inference, optional payload coalescing, and lookup facades.
- 2026-03-11: Progress notes for this task stay at one-line bundle summaries in TODO; helper-level detail is kept in plan decision logs or commit messages only.
- 2026-03-11: `S2-01` added `core_expr_attr_suffix.py` / `core_expr_subscript_suffix.py`, reduced `core_expr_attr_subscript_suffix.py` to `_ShExprPostfixSuffixParserMixin` plus a backward-compatible facade, and moved `core_expr_shell.py` to explicit split-mixin imports.
- 2026-03-11: As the first `S2-02` bundle, the `callee-call` cluster moved into `core_expr_callee_call_annotation.py`. `core_expr_call_annotation.py` now keeps the facade plus shared call-state helpers, while callee-specific return inference and dispatch live in the dedicated mixin.
- 2026-03-11: Treat `S2-02` as complete once `core_expr_named_call_annotation.py`, `core_expr_attr_call_annotation.py`, and `core_expr_callee_call_annotation.py` exist as the three dedicated bundles. `core_expr_call_annotation.py` is now down to `_build_call_expr_payload` plus the generic call-orchestration facade.
- 2026-03-11: `S3-01` completed once `_east_core_test_support.py` and the `test_east_core_source_contract_*` suite were aligned to the split module layout and `test_east_core*.py`, `test_prepare_selfhost_source.py`, and `build_selfhost.py` passed together.
