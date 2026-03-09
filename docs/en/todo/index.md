# TODO (Open)

> `docs/ja/` is the source of truth. `docs/en/` is its translation.

<a href="../../ja/todo/index.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

Last updated: 2026-03-09

## Context Operation Rules

- Every task must include an `ID` and a context file (`docs/ja/plans/*.md`).
- To override priority, issue chat instructions in the format of `docs/ja/plans/instruction-template.md`; do not use `todo2.md`.
- The active target is fixed to the highest-priority unfinished ID (smallest `P<number>`, and the first one from the top when priorities are equal); do not move to lower priorities unless there is an explicit override instruction.
- If even one `P0` remains unfinished, do not start `P1` or lower.
- Before starting, check `Background` / `Out of scope` / `Acceptance criteria` in the context file.
- Progress memos and commit messages must include the same `ID` (example: `[ID: P0-XXX-01] ...`).
- Keep progress memos in `docs/ja/todo/index.md` to a one-line summary only; details (decisions and verification logs) must be recorded in the `Decision log` of the context file (`docs/ja/plans/*.md`).
- If one `ID` is too large, you may split it into child tasks in `-S1` / `-S2` format in the context file (keep the parent checkbox open until the parent `ID` is completed).
- If uncommitted changes remain due to interruptions, do not start a different `ID` until you complete the same `ID` or revert the diff.
- When updating `docs/ja/todo/index.md` or `docs/ja/plans/*.md`, run `python3 tools/check_todo_priority.py` and verify that each progress `ID` added in the diff matches the highest-priority unfinished `ID` (or its child `ID`).
- Append in-progress decisions to the context file `Decision log`.
- For temporary output, use existing `out/` (or `/tmp` only when necessary), and do not add new temporary folders under the repository root.

## Notes

- This file keeps unfinished tasks only.
- Completed tasks are moved to history via `docs/ja/todo/archive/index.md`.
- `docs/ja/todo/archive/index.md` keeps only the index, and the history body is stored by date in `docs/ja/todo/archive/YYYYMMDD.md`.

## Unfinished Tasks

### P0: Realign the C++ `py_runtime.h` core boundary and move remaining helpers back upstream / to dedicated lanes

Context: [docs/ja/plans/p0-cpp-pyruntime-core-boundary-realign.md](../plans/p0-cpp-pyruntime-core-boundary-realign.md)

1. [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01] Realign the `py_runtime.h` core boundary and move remaining helpers back upstream / to dedicated lanes.
2. [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S1-01] Inventory checked-in callers of `numeric_ops/zip_ops/contains`, typed helpers, tuple helpers, and `type_id` wrappers, then classify the end state.
3. [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S1-02] Record include ownership, upstream contracts, and non-goals in the decision log so they match `spec-runtime`.
4. [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S2-01] Extend helper-include collection in the C++ emitter / prelude / generated path so `zip`, `contains`, and numeric helpers are explicitly included.
5. [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S2-02] Remove transitive `numeric_ops` / `zip_ops` / `contains` includes from `py_runtime.h` and update the removed-include guards.
6. [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S3-01] Switch typed dict subscripts to `.at()` and remove checked-in `py_dict_get` callers.
7. [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S3-02] Move tuple constant-index access to `std::get<N>` even in generated/runtime paths, and slim or retire the tuple `py_at` helper.
8. [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S3-03] Shrink typed list/dict mutation helpers down to object-bridge-only surface, prioritizing direct emitter lowering for typed lanes.
9. [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S4-01] Move ownership of `type_id` registry / subtype / isinstance logic to `py_tid_*`, and slim the wrappers in `py_runtime.h`.
10. [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S4-02] Update `test_cpp_runtime_type_id.py` and generated runtime callers, and add a guard so cyclic ownership does not reappear.
11. [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S5-01] Clean up small remaining surfaces such as the `py_isinstance_of` fast path and the `PyFile` alias.
12. [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S5-02] Refresh representative tests / parity / docs / archive and close the task.
- Progress memo: [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S1-01] Reflected the runtime audit into an active plan. The first implementation step is to lock down explicit include contracts for `numeric_ops/zip_ops/contains`, then proceed in order through `py_dict_get`, tuple helpers, and `type_id` ownership.
