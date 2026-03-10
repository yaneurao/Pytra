# P1: Decompose `core.py` and `test_east_core.py` in cluster-sized slices

Last updated: 2026-03-11

Related TODO:
- `docs/ja/todo/index.md` `ID: P1-IR-CORE-DECOMPOSITION-01`

Background:
- `src/toolchain/ir/core.py` is 10,081 lines and `test/unit/ir/test_east_core.py` is 3,912 lines, making review and navigation expensive.
- `P2-COMPILER-TYPED-BOUNDARY-01-S3-02` did make progress on helper extraction, but the work regressed into one-helper-per-commit micro-slices.
- `test_east_core.py` mixes source-contract guards and parser behavior tests, so the next split boundary is no longer obvious.

Goal:
- Decompose `core.py` and `test_east_core.py` into responsibility-focused modules and test files that can be advanced in cluster-sized slices.
- Separate source-contract guards, parser behavior, and suffix/call clusters into clearer ownership boundaries.
- Compress TODO / plan progress notes back to cluster-sized summaries.

In scope:
- `src/toolchain/ir/core.py`
- `src/toolchain/ir/core_expr_*.py`
- `test/unit/ir/test_east_core.py`
- `test/unit/ir/test_east_core*.py`
- `docs/ja/todo/index.md`, `docs/en/todo/index.md`
- `docs/ja/plans/*.md`, `docs/en/plans/*.md`

Out of scope:
- IR spec changes
- New typed-boundary or nominal-ADT features
- Backend-specific codegen quality work

Acceptance criteria:
- `core.py` becomes easier to read by separating responsibilities such as builder/core, suffix parser, and call annotation clusters.
- `test_east_core.py` is split so source-contract guards and parser behavior are no longer interleaved.
- Each slice handles roughly 5-10 helpers or test clusters instead of returning to micro-commits.
- TODO / plan progress notes are compressed to cluster-level summaries.

Validation commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east_core*.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/selfhost -p 'test_prepare_selfhost_source.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

## Breakdown

- [x] [ID: P1-IR-CORE-DECOMPOSITION-01-S1-01] Inventory split boundaries in `core.py` and `test_east_core.py`, then lock the split order for source-contract, parser-behavior, and suffix/call clusters.
- [x] [ID: P1-IR-CORE-DECOMPOSITION-01-S1-02] Record the cluster-level progress-note rule in this plan and align TODO wording with it.
- [x] [ID: P1-IR-CORE-DECOMPOSITION-01-S2-01] Extract the leading source-contract builder cluster from `test_east_core.py` into a shared support module plus a dedicated test file.
- [ ] [ID: P1-IR-CORE-DECOMPOSITION-01-S2-02] Split the remaining source-contract guards into cluster-specific `test_east_core_source_contract_*.py` files.
- [ ] [ID: P1-IR-CORE-DECOMPOSITION-01-S2-03] Split parser behavior, diagnostics, and representative nominal-ADT tests into dedicated test files.
- [ ] [ID: P1-IR-CORE-DECOMPOSITION-01-S3-01] Continue moving remaining `core.py` clusters into dedicated modules in bundle-sized slices.
- [ ] [ID: P1-IR-CORE-DECOMPOSITION-01-S4-01] Run representative IR/selfhost regressions and stabilize the split with compressed progress notes.

Decision log:
- 2026-03-11: Created this task using `core.py=10081 lines` and `test_east_core.py=3912 lines` as the baseline. The first slice will extract the leading source-contract builder cluster from `test_east_core.py` into a shared support module and a dedicated test file.
- 2026-03-11: Future splits should operate on bundles of roughly 5-10 helpers or test clusters, not one-helper-per-commit micro-slices. TODO / plan notes should stay at the same bundle-level granularity.
- 2026-03-11: Keep only one-line cluster-level progress notes in TODO, and record verification logs or rationale in this plan's decision log. All later `S2+` slices should keep that convention.
- 2026-03-11: Added `test/unit/ir/_east_core_test_support.py` plus `test/unit/ir/test_east_core_source_contract_builders.py`, then moved the leading 10 builder source-contract guards out of `test_east_core.py`.
- 2026-03-11: Added `test/unit/ir/test_east_core_source_contract_expr_suffix.py`, then moved 10 call/attr/subscript source-contract guards out of `test_east_core.py`. `S2-02` stays open because more source-contract clusters remain.
- 2026-03-11: Added `test/unit/ir/test_east_core_source_contract_call_metadata.py`, then moved 10 method/named-call metadata source-contract guards out of `test_east_core.py`. `S2-02` remains open because call-suffix, parser-helper, and tuple-destructure clusters are still in the main file.
