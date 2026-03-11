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

1. [ ] [ID: P1-IR-CORE-DECOMPOSITION-01] Decompose `core.py` and `test_east_core.py` in cluster-sized slices so source-contract guards and parser behavior no longer share one file.
   Context: [docs/ja/plans/p1-ir-core-decomposition.md](../../ja/plans/p1-ir-core-decomposition.md)
- Progress memo: [ID: P1-IR-CORE-DECOMPOSITION-01-S1-01] Using `core.py=10081 lines` and `test_east_core.py=3912 lines` as the baseline, the split boundaries and bundle-sized work units for source-contract, parser behavior, and suffix/call clusters were fixed.
- Progress memo: [ID: P1-IR-CORE-DECOMPOSITION-01-S1-02] TODO now keeps only one-line cluster summaries, while detailed verification and rationale live in the plan decision log.
- Progress memo: [ID: P1-IR-CORE-DECOMPOSITION-01-S2-01] Added a shared support module and `test_east_core_source_contract_builders.py`, then moved 10 builder source-contract guards out of `test_east_core.py`.
- Progress memo: [ID: P1-IR-CORE-DECOMPOSITION-01-S2-02] Moved 51 source-contract guards into five `test_east_core_source_contract_*.py` files plus the existing builders/expr-suffix files, leaving `test_east_core.py` focused on parser behavior and representative regressions.
- Progress memo: [ID: P1-IR-CORE-DECOMPOSITION-01-S2-03] Parser behavior now lives in dedicated decorators / diagnostics / types / exprs / classes / runtime / statements files, leaving `test_east_core.py` as a residual regression shell.
- Progress memo: [ID: P1-IR-CORE-DECOMPOSITION-01-S3-01] Moved declaration / decorator / extern / string / text / stmt-analysis / type / import / signature / builder / entrypoint / parse-context clusters into dedicated modules.
- Progress memo: [ID: P1-IR-CORE-DECOMPOSITION-01-S3-01] Split expression parsing into parser-base / precedence / primary / lowered / resolution / call-args / call-annotation / attr-subscript-annotation / stmt-parser / module-parser clusters.
- Progress memo: [ID: P1-IR-CORE-DECOMPOSITION-01-S3-01] `core.py` now acts as a thin facade with only split-module imports plus the three wrappers `_sh_parse_stmt_block_mutable`, `_sh_parse_stmt_block`, and `convert_source_to_east_self_hosted`.
- Progress memo: [ID: P1-IR-CORE-DECOMPOSITION-01-S4-01] Added `test_east_core_source_contract_core_surface.py` to lock the thin-facade contract and representative IR/selfhost regressions.
- Progress memo: [ID: P1-IR-CORE-DECOMPOSITION-01-S4-01] Moved `_ShExprParser` / `_sh_parse_expr*` into `core_expr_shell.py` and locked the facade/parser-shell split in source-contract tests.

1. [ ] [ID: P2-EAST-CORE-MODULARIZATION-01] [p2-east-core-modularization.md](../plans/p2-east-core-modularization.md) Split `core.py` / `test_east_core.py` by responsibility so compiler-internal improvements can proceed in cluster-sized slices again.
