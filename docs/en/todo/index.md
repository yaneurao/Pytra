# TODO (Open)

> `docs/ja/` is the source of truth. `docs/en/` is its translation.

<a href="../../ja/todo/index.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

Last updated: 2026-03-11

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

### P0: relative import support

Context: [docs/ja/plans/p0-relative-import-support.md](../plans/p0-relative-import-support.md)

1. [ ] [ID: P0-RELATIVE-IMPORT-SUPPORT-01] Officially support `from .m import x` / `from ..pkg import y` in multi-file transpilation.
2. [x] [ID: P0-RELATIVE-IMPORT-SUPPORT-01-S1-01] Fix the syntax / diagnostics / root-escape policy for relative imports in plan and spec.
3. [ ] [ID: P0-RELATIVE-IMPORT-SUPPORT-01-S2-01] Make the self-hosted parser accept relative `from-import` while preserving raw module text.
4. [ ] [ID: P0-RELATIVE-IMPORT-SUPPORT-01-S2-02] Normalize relative modules to absolute `module_id`s during frontend module-map construction and rewrite EAST / import metadata.
5. [ ] [ID: P0-RELATIVE-IMPORT-SUPPORT-01-S2-03] Update import-graph diagnostics to distinguish root escape from missing modules and fail closed.
6. [ ] [ID: P0-RELATIVE-IMPORT-SUPPORT-01-S3-01] Add representative CLI / unit regressions for success, missing, duplicate, root escape, and wildcard cases.
7. [ ] [ID: P0-RELATIVE-IMPORT-SUPPORT-01-S3-02] Sync the import wording in `spec-user.md`, `spec-import.md`, and tutorial docs.

### P4: `py_runtime.h` final thin compat removal

Context: [docs/ja/plans/p4-crossruntime-pyruntime-final-thincompat-removal.md](../plans/p4-crossruntime-pyruntime-final-thincompat-removal.md)

1. [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-FINAL-THINCOMPAT-REMOVAL-01] Remove the final two `py_runtime.h` thin compat helpers across runtimes.
2. [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-FINAL-THINCOMPAT-REMOVAL-01-S1-01] Classify the residuals into `cpp_header_final_thincompat_defs` / `cpp_generated_final_thincompat_blocker` / `rs_runtime_generic_alias_surface` / `cs_runtime_generic_alias_surface`, and add inventory/tests.
3. [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-FINAL-THINCOMPAT-REMOVAL-01-S1-02] Fix the target end state and bundle order in docs/source guards.
4. [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-FINAL-THINCOMPAT-REMOVAL-01-S2-01] Move checked-in generated/native C++ callers to thin helpers and empty `cpp_generated_final_thincompat_blocker`.
5. [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-FINAL-THINCOMPAT-REMOVAL-01-S2-02] Shrink the Rust/C# runtime alias surface to internal/private seams.
6. [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-FINAL-THINCOMPAT-REMOVAL-01-S3-01] Remove template `py_runtime_type_id` / `py_isinstance` from `py_runtime.h` and refresh representative regressions/docs/archive.
