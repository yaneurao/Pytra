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

### P1: Split the remaining `east2_to_east3_lowering.py` clusters in a second wave

Context: [docs/en/plans/p1-east23-lowering-orchestration-split.md](../plans/p1-east23-lowering-orchestration-split.md)

1. [ ] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01] Move the remaining `east2_to_east3_lowering.py` clusters into dedicated modules and reduce the main file to orchestration / dispatch logic.
2. [x] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S1-01] Inventory the remaining clusters as `call_metadata`, `stmt_lowering`, and `dispatch_orchestration`, then lock the split order.
3. [x] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S1-02] Keep progress notes at bundle level and fix the main-file end state as `dispatch + lifecycle`.
4. [ ] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S2-01] Split the `call metadata` / `json decode fastpath` cluster into a dedicated module.
5. [ ] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S2-02] Split the `Assign` / `For` / `ForRange` lowering cluster into a dedicated module.
6. [ ] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S2-03] Split `Attribute` / `Match` / `ForCore` lowering plus node-dispatch orchestration into dedicated modules.
7. [ ] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S3-01] Update source-contract tests and representative regressions to the second-wave split layout.
8. [ ] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S4-01] Update docs / TODO / archive and close the task.
- Progress note: [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S1-01] The remaining 833-line main file was reduced to three second-wave clusters: `call metadata/json decode`, `stmt lowering`, and `dispatch/orchestration`.
