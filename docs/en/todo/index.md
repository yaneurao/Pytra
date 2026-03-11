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

### P1: lock representative relative-import transpile smoke for the second wave (`js/ts`) and prepare the remaining-backend handoff

Context: [docs/ja/plans/p1-relative-import-secondwave-smoke.md](../ja/plans/p1-relative-import-secondwave-smoke.md)

1. [ ] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-SMOKE-01] Lock representative relative-import transpile smoke for `js/ts` and update the coverage inventory / docs handoff to the next baseline.
2. [x] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-SMOKE-01-S1-01] Created the live plan / TODO and locked the `js/ts` second-wave smoke contract.
3. [x] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-SMOKE-01-S2-01] Added representative relative-import transpile cases to the `py2js` smoke suite.
4. [x] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-SMOKE-01-S2-02] Added representative relative-import transpile cases to the `py2ts` smoke suite.
5. [ ] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-SMOKE-01-S3-01] Sync the coverage inventory / backend-parity docs / handoff metadata to the `js/ts` baseline and leave the task close-ready.
- Progress memo: `js/ts` now have contract-driven representative transpile smoke locked; what remains is the `js/ts` coverage-baseline and handoff sync.

### P1: relative-import second-wave rollout planning

Context: [p1-relative-import-secondwave-planning.md](../plans/p1-relative-import-secondwave-planning.md)

1. [ ] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-PLANNING-01] Lock the live contract, docs handoff, and verification lane for second-wave relative-import rollout.
2. [x] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-PLANNING-01-S1-01] Added the live plan / TODO plus the second-wave rollout contract, checker, and docs handoff.
3. [ ] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-PLANNING-01-S2-01] Break the second-wave backend rollout order into backend-group bundles for representative smoke / fail-closed rollout.
4. [ ] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-PLANNING-01-S3-01] Sync coverage docs / support wording / archive handoff to the current second-wave state and close the task.

- Progress note: The second-wave backend set is now `go/java/js/kotlin/nim/scala/swift/ts`, the representative scenarios stay `parent_module_alias` / `parent_symbol_alias`, and the handoff now points to the live `p1-relative-import-secondwave-planning.md` plan.
