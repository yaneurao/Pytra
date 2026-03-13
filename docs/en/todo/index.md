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
### P0: Pytra-NES representative C++ mini repro contract

- [ ] [ID: P0-PYTRA-NES-CPP-MINI-REPRO-01] Lock a representative Pytra-NES multi-file package (parenthesized sibling relative import + `dataclass` + `deque[float]` field + `deque` methods) through build/run on the representative C++ lane.
  - Context: [docs/en/plans/p0-pytra-nes-cpp-mini-repro-contract.md](../plans/p0-pytra-nes-cpp-mini-repro-contract.md)
- [x] [ID: P0-PYTRA-NES-CPP-MINI-REPRO-01-S1-01] Added a representative package smoke and locked the current C++ multi-file build/run baseline that combines `from .controller import (...)` with `timestamps: deque[float] = field(init=False, repr=False)`.
  - Progress note: Added a 3-module `controller.py` / `pad_state.py` / `ppu.py` package to `test_py2cpp_features.py` and locked that `pad_state.h` emits `::std::deque<float64>` without leaking `field(...)`, while runtime output stays `3 / 1.5 / 1`.
- [ ] [ID: P0-PYTRA-NES-CPP-MINI-REPRO-01-S2-01] Turn the generated include / class layout / method-lowering surface exposed by the smoke into source guards so the representative Pytra-NES lane fails fast on drift.
- [ ] [ID: P0-PYTRA-NES-CPP-MINI-REPRO-01-S3-01] Sync TODO / plan / support docs to the representative Pytra-NES mini repro contract and close it.
