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

- [ ] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01] Re-layout the non-C++ runtimes into a `generated/native` tree that can be compared against C++ at file level (context: [p0-noncpp-runtime-layout-alignment.md](../plans/p0-noncpp-runtime-layout-alignment.md)). Progress: the first-wave `rs/cs` trees are already cut over to `native/generated` and `png/gif` have been regenerated there. The remaining work is std-lane generation for modules such as `json/pathlib` and the rollout to other backends.
- [ ] [ID: P5-BACKEND-PARITY-SECONDARY-ROLLOUT-01] Fill the remaining unsupported support-matrix cells for the secondary tier (`go/java/kt/scala/swift/nim`) as a live implementation rollout task (context: [p5-backend-parity-secondary-rollout.md](../plans/p5-backend-parity-secondary-rollout.md))
- [ ] [ID: P6-BACKEND-PARITY-LONGTAIL-ROLLOUT-01] Fill the remaining unsupported support-matrix cells for the long-tail tier (`js/ts/lua/rb/php`) as a live implementation rollout task (context: [p6-backend-parity-longtail-rollout.md](../plans/p6-backend-parity-longtail-rollout.md))
