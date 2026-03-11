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

### P1: Hardening multi-file runtime smoke for relative imports

Context: [p1-relative-import-multifile-runtime-hardening.md](../plans/p1-relative-import-multifile-runtime-hardening.md)

1. [ ] [ID: P1-RELATIVE-IMPORT-MULTIFILE-RUNTIME-HARDENING-01] Lock the already-implemented relative import behavior using multi-file build/run smoke on a Pytra-NES-style nested package layout.
2. [x] [ID: P1-RELATIVE-IMPORT-MULTIFILE-RUNTIME-HARDENING-01-S1-01] Fixed the current gap in plan / TODO and chose representative nested-package runtime smoke cases.
3. [ ] [ID: P1-RELATIVE-IMPORT-MULTIFILE-RUNTIME-HARDENING-01-S2-01] Add a multi-file C++ build/run regression for a nested-package relative import chain.
4. [ ] [ID: P1-RELATIVE-IMPORT-MULTIFILE-RUNTIME-HARDENING-01-S2-02] Add a multi-file C++ build/run regression for a bare parent relative import.
5. [ ] [ID: P1-RELATIVE-IMPORT-MULTIFILE-RUNTIME-HARDENING-01-S3-01] Sync docs / plan / TODO and focused regressions to the current contract, then close the task.

- Progress note: Relative imports are already supported in the current source, so this task focuses on strengthening representative nested-package multi-file build/run smoke rather than adding a new language feature.
