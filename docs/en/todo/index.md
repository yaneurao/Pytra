# TODO (Open)

> `docs/ja/` is the source of truth. `docs/en/` is its translation.

<a href="../../ja/todo/index.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

Last updated: 2026-03-18 (P5-CPP-PY-IS-TYPE-DEAD-CODE-REMOVE-01 added)

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

### P5: py_runtime.h Shrink

#### P5-1: Remove py_is_type Dead Code

Context: [docs/ja/plans/p5-cpp-py-is-type-dead-code-remove.md](../../ja/plans/p5-cpp-py-is-type-dead-code-remove.md)

1. [ ] [ID: P5-CPP-PY-IS-TYPE-DEAD-CODE-REMOVE-01] Remove `py_is_dict` / `py_is_list` / `py_is_set` / `py_is_str` / `py_is_bool` / `py_is_int` / `py_is_float` from `py_runtime.h`. The emitter has already migrated to the `PYTRA_TID_*` + `py_runtime_value_isinstance` system; these functions are dead code.

#### P5-2: FloorDiv / Mod EAST3 IR Node

Context: [docs/ja/plans/p5-east3-floordiv-mod-node.md](../../ja/plans/p5-east3-floordiv-mod-node.md)

2. [ ] [ID: P5-EAST3-FLOORDIV-MOD-NODE-01] Convert `py_floordiv` / `py_mod` to C++ inline emit via EAST3 IR nodes and remove from `py_runtime.h`. Lays the groundwork for each language backend to generate floor-division and modulo natively.

### P6: py_runtime.h Shrink / Multi-language Support

#### P6-1: Fix C++ Emitter List-Mutation IR Bypass

Context: [docs/ja/plans/p6-cpp-list-mut-ir-bypass-fix.md](../../ja/plans/p6-cpp-list-mut-ir-bypass-fix.md)

1. [ ] [ID: P6-CPP-LIST-MUT-IR-BYPASS-FIX-01] Route all `py_list_*_mut()` direct-emit paths in `cpp_emitter.py` through IR nodes (ListAppend, etc.) and remove the 6 functions from `py_runtime.h`.

#### P6-2: py_len / py_slice EAST3 IR Nodes

Context: [docs/ja/plans/p6-east3-len-slice-node.md](../../ja/plans/p6-east3-len-slice-node.md)

2. [ ] [ID: P6-EAST3-LEN-SLICE-NODE-01] Add EAST3 IR nodes for `py_len` / `py_slice`, update the C++ emitter to generate inline expressions, and remove both from `py_runtime.h`.
