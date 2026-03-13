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

- [ ] [ID: P0-NONCPP-RUNTIME-GENERATED-CPP-BASELINE-01] Align non-C++ generated runtime lanes to the `cpp/generated/{built_in,std,utils}` baseline. Progress: `S2-01` is complete; `rs/cs` now materialize `generated/std/{argparse,json,random,re,sys,timeit}` and `generated/utils/assertions`. In addition, `S2-02` is now complete: the static family (`go/java/kotlin/scala/swift/nim`) materializes the full 25-module `generated/{built_in,std,utils}` baseline, and Kotlin / Scala / Swift / Nim `utils/{gif,png}` helper-shaped outputs have been renamed to canonical basenames. The first `S2-03` bundle materialized PHP `generated/std/{argparse,glob,os,os_path,random,re,sys,timeit}` and `generated/utils/assertions`, fixed the PHP keyword / `\\r` literal emitter bugs, and promoted PHP to a materialized backend in the baseline checker. The second `S2-03` bundle materialized the 9 missing `js/ts` modules (`std/{argparse,glob,os,os_path,random,re,sys,timeit}` and `utils/assertions`) into `generated/`, synchronized the script-family compare baseline plus current/target inventory, module buckets, manifest unit tests, and backend smoke to the full 25-module expectation, and fixed JS `JoinedStr` lowering so generated `argparse/re/assertions` stay parse-safe. Next: eliminate the remaining `lua/ruby` helper-shaped gap and bring them up to the full baseline. Context: [p0-noncpp-runtime-generated-cpp-baseline.md](../plans/p0-noncpp-runtime-generated-cpp-baseline.md)
- [ ] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01] Remove checked-in `src/runtime/<lang>/pytra/**` from every non-C++ / non-C# backend and converge the permanent repo-owned runtime layout on `generated/native` only. Context: [p0-noncpp-runtime-pytra-deshim.md](../plans/p0-noncpp-runtime-pytra-deshim.md)
- [x] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S1-01] Locked the current 12-backend `pytra/**` directory/file inventory, delete blocker references, and current->target mapping in plan / contract / checker / test form.
- [ ] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S1-02] Switch active contracts / checkers / spec wording to `generated/native only` and make checked-in `pytra/**` re-entry fail fast. Progress: first bundle synced `spec-folder/spec-dev` wording and the doc-policy checker.
- [ ] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S2-01] Resolve the Rust (`rs`) `pytra/**` compat residual and remove repo-tree `pytra/**` assumptions from `py2rs`, selfhost, runtime guards, and smoke.
- [ ] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S2-02] Switch the static family (`go/java/kotlin/scala/swift/nim`) registry / packaging / smoke / tooling to direct `generated/native` references and remove repo-tree `pytra/**` dependencies.
- [ ] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S2-03] Physically delete checked-in `src/runtime/<lang>/pytra/**` for the static family and sync allowlists / inventory / representative smoke to the deletion end state.
- [ ] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S3-01] Rework JS/TS import paths, shim writers, selfhost, and smoke so repo-tree `src/runtime/{js,ts}/pytra/**` direct-load and compat contracts disappear.
- [ ] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S3-02] Move Lua/Ruby/PHP packaging / runtime copy / loader contracts to `generated/native` or output-side staging and remove checked-in `pytra/**` assumptions.
- [ ] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S3-03] Physically delete checked-in `src/runtime/<lang>/pytra/**` for the script family and update representative smoke plus contract baselines to the deletion end state.
- [ ] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S4-01] Sync docs / TODO / archive references / inventory and close with the invariant that no checked-in non-C++ / non-C# backend owns `pytra/`.
