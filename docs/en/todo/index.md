# TODO (Open)

> `docs/ja/` is the source of truth. `docs/en/` is its translation.

<a href="../../ja/todo/index.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

Last updated: 2026-03-11

## Context Operation Rules

- Every task must include an `ID` and a context file (`docs/ja/plans/*.md`).
- To override priority, issue chat instructions in the format of `docs/ja/plans/instruction-template.md`; do not use `todo2.md`.
- The active target is fixed to the highest-priority unfinished ID (smallest `P<number>`, and the first one from the top when priorities are equal); do not move to lower priorities unless there is an explicit override instruction.
- If even one `P0` remains unfinished, do not start `P1` or lower.
- Before starting, check `Background` / `Out of scope` / `Acceptance criteria` in the context file.
- Progress memos and commit messages must include the same `ID` (example: `[ID: P0-XXX-01] ...`).
- Keep progress memos in `docs/ja/todo/index.md` to a one-line summary only; details such as decisions and verification logs must be recorded in the `Decision log` of the context file (`docs/ja/plans/*.md`).
- If one `ID` is too large, you may split it into child tasks in `-S1` / `-S2` format in the context file, but keep the parent checkbox open until the parent `ID` is completed.
- If uncommitted changes remain due to interruptions, do not start a different `ID` until you complete the same `ID` or revert the diff.
- When updating `docs/ja/todo/index.md` or `docs/ja/plans/*.md`, run `python3 tools/check_todo_priority.py` and verify that each progress `ID` added in the diff matches the highest-priority unfinished `ID` or one of its child IDs.
- Append in-progress decisions to the context file `Decision log`.
- For temporary output, use existing `out/` or `/tmp` only when necessary, and do not add new temporary folders under the repository root.

## Notes

- This file keeps unfinished tasks only.
- Completed tasks are moved to history via `docs/ja/todo/archive/index.md`.
- `docs/ja/todo/archive/index.md` keeps only the index, and the history body is stored by date in `docs/ja/todo/archive/YYYYMMDD.md`.

## Unfinished Tasks

### P1: Decompose large expression split modules by cluster

Context: [docs/en/plans/p1-ir-expr-module-decomposition.md](../plans/p1-ir-expr-module-decomposition.md)

1. [ ] [ID: P1-IR-EXPR-MODULE-DECOMPOSITION-01] Decompose the large expression-side split modules under `toolchain/ir` by cluster and make the `attr/subscript/call` responsibility boundaries explicit.
2. [x] [ID: P1-IR-EXPR-MODULE-DECOMPOSITION-01-S1-01] Lock the split boundary so `core_expr_attr_subscript_suffix.py` becomes `attr_suffix` / `subscript_suffix` / `shared_postfix_orchestration`, and `core_expr_call_annotation.py` becomes `named_call` / `attr_call` / `callee_call` / `shared_state_orchestration`.
3. [x] [ID: P1-IR-EXPR-MODULE-DECOMPOSITION-01-S1-02] Fix the progress-note rule for this task so TODO stays at one-line bundle summaries and helper-level detail lives in the plan.
4. [x] [ID: P1-IR-EXPR-MODULE-DECOMPOSITION-01-S2-01] Split the `attr suffix` / `subscript suffix` cluster into [core_expr_attr_suffix.py](../../src/toolchain/ir/core_expr_attr_suffix.py) / [core_expr_subscript_suffix.py](../../src/toolchain/ir/core_expr_subscript_suffix.py), and shrink [core_expr_attr_subscript_suffix.py](../../src/toolchain/ir/core_expr_attr_subscript_suffix.py) to a postfix facade.
5. [x] [ID: P1-IR-EXPR-MODULE-DECOMPOSITION-01-S2-02] Split the `named-call` / `attr-call` / `callee-call` annotation cluster into [core_expr_named_call_annotation.py](../../src/toolchain/ir/core_expr_named_call_annotation.py), [core_expr_attr_call_annotation.py](../../src/toolchain/ir/core_expr_attr_call_annotation.py), and [core_expr_callee_call_annotation.py](../../src/toolchain/ir/core_expr_callee_call_annotation.py), and shrink [core_expr_call_annotation.py](../../src/toolchain/ir/core_expr_call_annotation.py) to the shared call-orchestration facade.
6. [x] [ID: P1-IR-EXPR-MODULE-DECOMPOSITION-01-S3-01] Updated source-contract tests to the post-split layout and passed representative regressions.
7. [ ] [ID: P1-IR-EXPR-MODULE-DECOMPOSITION-01-S4-01] Update docs / TODO / archive and move the completed task to archive.
