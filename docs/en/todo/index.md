# TODO (Open)

> `docs/ja/` is the source of truth. `docs/en/` is its translation.

<a href="../../ja/todo/index.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

Last updated: 2026-03-12

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

### P1: move the next live relative-import rollout to the JVM package bundle and lock the representative `java/kotlin/scala` contract

Context: [docs/ja/plans/p1-relative-import-jvm-package-bundle.md](../plans/p1-relative-import-jvm-package-bundle.md)

1. [ ] [ID: P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01] Lock the live handoff and representative rollout contract for the `java/kotlin/scala` JVM package bundle.
2. [x] [ID: P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01-S1-01] Add the live plan / TODO / contract / checker and switch the coverage / second-wave handoff to the JVM package bundle.
3. [x] [ID: P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01-S2-01] Add representative package-style relative-import transpile smoke and wildcard fail-closed regressions for the `java/kotlin/scala` backends.
4. [ ] [ID: P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01-S2-02] Sync the coverage inventory / backend parity docs to the current JVM bundle state and spell out the long-tail handoff.
5. [ ] [ID: P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01-S3-01] Close the task after aligning focused docs / tests / handoff wording to the current state.
