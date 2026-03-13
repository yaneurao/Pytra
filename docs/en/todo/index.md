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
### P0: align `LinkedProgramModule` imports to the `toolchain.link` facade

- [ ] [ID: P0-LINK-FACADE-LINKED-PROGRAM-MODULE-IMPORT-01] Align the `LinkedProgramModule` import in `test_py2x_cli.py` to the `src.toolchain.link` facade so the tooling consumer no longer reaches through `program_model` directly.
  - Context: [docs/en/plans/p0-link-facade-linked-program-module-import.md](../plans/p0-link-facade-linked-program-module-import.md)
- [ ] [ID: P0-LINK-FACADE-LINKED-PROGRAM-MODULE-IMPORT-01-S1-01] Add the facade-import source contract plus TODO/plan baseline.
- [ ] [ID: P0-LINK-FACADE-LINKED-PROGRAM-MODULE-IMPORT-01-S2-01] Switch the `test_py2x_cli.py` import to the facade path and bring the focused unit suite back to green.
- [ ] [ID: P0-LINK-FACADE-LINKED-PROGRAM-MODULE-IMPORT-01-S3-01] Sync TODO / plan / archive and lock the close condition.
### P0: align the `transpile_cli` typed C++ contract to the direct-ownership header/source layout

- [ ] [ID: P0-CPP-TRANSPILE-CLI-DIRECT-HEADER-CONTRACT-01] Remove the checked-in `cpp/pytra` wrapper assumption from the `transpile_cli` typed C++ contract and align it to the `generated/native` direct-ownership header/source layout.
  - Context: [docs/en/plans/p0-cpp-transpile-cli-direct-header-contract.md](../plans/p0-cpp-transpile-cli-direct-header-contract.md)
- [x] [ID: P0-CPP-TRANSPILE-CLI-DIRECT-HEADER-CONTRACT-01-S1-01] Lock the stale contract surface and close condition in the plan / TODO.
  - Progress note: Locked the current contract in the plan as “`generated/compiler/transpile_cli.{h,cpp}` are the live owners, while checked-in `cpp/pytra/compiler/transpile_cli.h` is already deleted.”
- [x] [ID: P0-CPP-TRANSPILE-CLI-DIRECT-HEADER-CONTRACT-01-S2-01] Update the focused contract test to match the live tree and bring the targeted test back to green.
- [ ] [ID: P0-CPP-TRANSPILE-CLI-DIRECT-HEADER-CONTRACT-01-S3-01] Sync TODO / plan / archive and lock the close condition.
