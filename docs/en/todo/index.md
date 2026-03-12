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

1. [ ] [ID: P1-DATACLASS-FIELD-STATIC-SUBSET-01] Treat `dataclasses.field(...)` as a static dataclass metadata subset rather than a runtime call, with representative lanes locked by fail-closed contracts.
   Context: [p1-dataclass-field-static-subset.md](/workspace/Pytra/docs/en/plans/p1-dataclass-field-static-subset.md)
   Summary: representative Pytra-NES cases such as `timestamps: deque[float] = field(init=False, repr=False)` currently leak `field(...)` as a normal expression into backend output and generate broken code. In v1, `default` / `default_factory` / `init` / `repr` / `compare` will be handled as a static metadata subset and unsupported options will fail closed. Progress: `S3-01` now locks representative regressions for `repr` / `compare` metadata and the fail-closed policy for unsupported options, duplicate options, and `default` + `default_factory` conflicts.

2. [ ] [ID: P5-CPP-PYRUNTIME-RESIDUAL-THIN-SEAM-SHRINK-01] Minimize the remaining object-bridge mutation seam and shared `type_id` thin seam in `py_runtime.h` after the cross-runtime contracts are fully classified.
   Context: [p5-cpp-pyruntime-residual-thin-seam-shrink.md](/workspace/Pytra/docs/en/plans/p5-cpp-pyruntime-residual-thin-seam-shrink.md)
   Summary: the current `py_runtime.h` has already been reduced substantially, but `py_append(object&)` and the `py_runtime_value_*` / `py_runtime_object_*` / `py_runtime_type_id_*` thin seams still remain. These cannot be removed by editing the header alone, so this `P5` task fixes the later-stage shrink plan and bundle order across the C++ / Rust / C# emitters and runtimes.

3. [ ] [ID: P5-POWERSHELL-CS-HOST-01] define a PowerShell host profile that builds and runs C# backend output from `pwsh` instead of adding a pure PowerShell backend.
   Context: [p5-powershell-csharp-host-profile.md](/workspace/Pytra/docs/en/plans/p5-powershell-csharp-host-profile.md)
   Summary: this task fixes a representative `pwsh + py2cs` host profile, including generated `.cs` plus bundled runtime layout, build-driver priority across `dotnet` / `csc` / `Add-Type`, and explicit fail-closed conditions. A pure PowerShell target backend stays out of scope.

4. [ ] [ID: P6-BACKEND-PARITY-MATRIX-CELL-FILL-01] turn the cross-backend parity matrix into a real `feature × backend` support-state table and make it the canonical source across all backends.
   Context: [p6-backend-parity-matrix-cell-fill.md](/workspace/Pytra/docs/en/plans/p6-backend-parity-matrix-cell-fill.md)
   Summary: the current parity matrix already has the row seed and the state taxonomy, but it does not yet populate per-cell support states. This `P6` turns the cross-backend matrix into the canonical 2D table with `support_state` / `evidence_kind`, while keeping the C++ table as drill-down documentation.
