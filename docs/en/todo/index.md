# TODO (Open)

> `docs/ja/` is the source of truth. `docs/en/` is its translation.

<a href="../../ja/todo/index.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

Last updated: 2026-03-13

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
### P0: align `py2x` entrypoint imports to the `toolchain.frontends` facade

- [ ] [ID: P0-FRONTENDS-FACADE-PY2X-ENTRYPOINTS-IMPORT-01] Move the frontend imports in `py2x.py` / `py2x-selfhost.py` from `toolchain.compiler.transpile_cli` over to the `toolchain.frontends` facade so entrypoint consumers stop reaching through the compat shim.
  - Context: [docs/en/plans/p0-frontends-facade-py2x-entrypoints-import.md](../plans/p0-frontends-facade-py2x-entrypoints-import.md)
- [ ] [ID: P0-FRONTENDS-FACADE-PY2X-ENTRYPOINTS-IMPORT-01-S1-01] Lock the stale import surface and close condition in the plan / TODO.
- [ ] [ID: P0-FRONTENDS-FACADE-PY2X-ENTRYPOINTS-IMPORT-01-S2-01] Update the `toolchain.frontends` facade exports plus the entrypoint imports and bring the source contract / focused tests back to green.
- [ ] [ID: P0-FRONTENDS-FACADE-PY2X-ENTRYPOINTS-IMPORT-01-S3-01] Sync TODO / plan / archive and lock the close condition.
