# TODO (Open)

> `docs/ja/` is the source of truth. `docs/en/` is its translation.

<a href="../../ja/todo/index.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

Last updated: 2026-03-14

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

### P2

1. [ ] [ID: P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01] Push typed fallback out of `py_runtime.h` and back into EAST3, the C++ emitter, and runtime SoT so the header shrinks without physical splitting.
Context: [docs/en/plans/p2-cpp-pyruntime-upstream-fallback-shrink.md](../plans/p2-cpp-pyruntime-upstream-fallback-shrink.md)
- Progress memo: The sixth `S2-02` bundle is done. `S2-01` is complete with the emitter reduced to a helper-only residual, and regenerating `iter_ops/gif` plus upstreaming the typed empty-bytes lane retires the generated boxed-list seed bucket. The sample `py_append` bucket is retired too, and `predicates` iterator lowering shrinks the generated generic-index baseline from `46 -> 44`. The typed-lane residuals are still 1 emitter bucket plus 2 generated-runtime buckets and 1 sample bucket. Next is shrinking the generated callers and the remaining sample generic-index bucket.
