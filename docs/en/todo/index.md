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
- Progress memo: [ID: P1-IR-CORE-DECOMPOSITION-01-S2-03] Added `test_east_core_parser_behavior_decorators.py`, then moved 10 representative extern / abi / template parser-behavior tests out of `test_east_core.py`.
- Progress memo: [ID: P1-IR-CORE-DECOMPOSITION-01-S2-03] Added `test_east_core_parser_behavior_types.py`, then moved 10 representative decode-first / type-expr / typing-future parser-behavior tests out of `test_east_core.py`.
- Progress memo: [ID: P1-IR-CORE-DECOMPOSITION-01-S2-03] Moved 7 decorator/abi/template negative tests and 3 object-receiver diagnostics into `test_east_core_parser_behavior_decorators.py` / `test_east_core_parser_behavior_diagnostics.py`, removing the duplicate leading test and stray assertions from `test_east_core.py`.
- Progress memo: [ID: P1-IR-CORE-DECOMPOSITION-01-S2-03] Added `test_east_core_parser_behavior_exprs.py`, then moved 10 representative comprehension / lambda / fstring / yield / basic-parser-acceptance tests out of `test_east_core.py`.
- Progress memo: [ID: P1-IR-CORE-DECOMPOSITION-01-S2-03] Added `test_east_core_parser_behavior_classes.py`, then moved 7 representative class-storage / dataclass / nominal-ADT / enum parser-behavior tests out of `test_east_core.py`.
- Progress memo: [ID: P1-IR-CORE-DECOMPOSITION-01-S2-03] Added `test_east_core_parser_behavior_runtime.py`, then moved 12 representative runtime-annotation / builtin-call / pathlib / json / iter-lowering parser-behavior tests out of `test_east_core.py`.
- Progress memo: [ID: P1-IR-CORE-DECOMPOSITION-01-S2-03] Added `test_east_core_parser_behavior_statements.py`, then moved 6 representative identifier/import ambiguity, `super()`, bare `return`, arg-usage, and trailing-semicolon parser-behavior tests out of `test_east_core.py`, leaving only 3 residual source-contract regressions in the main file.
- Progress memo: [ID: P1-IR-CORE-DECOMPOSITION-01-S3-01] Moved the `attr/subscript annotation` cluster into `core_expr_attr_subscript_annotation.py` and updated `test_east_core_source_contract_expr_suffix.py` to the split locations.
- Progress memo: [ID: P1-IR-CORE-DECOMPOSITION-01-S3-01] Added `core_class_semantics.py`, then moved the decl-meta / nominal-ADT metadata / dataclass value-safe helper cluster out of `core.py`.

1. [ ] [ID: P2-EAST-CORE-MODULARIZATION-01] [p2-east-core-modularization.md](../plans/p2-east-core-modularization.md) Split `core.py` / `test_east_core.py` by responsibility so compiler-internal improvements can proceed in cluster-sized slices again.
