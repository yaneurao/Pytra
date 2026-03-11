# P2: Split EAST core.py / test_east_core.py by responsibility

Last updated: 2026-03-11

Related TODO:
- `ID: P2-EAST-CORE-MODULARIZATION-01` in `docs/ja/todo/index.md`

Background:
- `src/toolchain/ir/core.py` has grown to around 10k lines after repeated selfhost parser feature work and helper splitting.
- `test/unit/ir/test_east_core.py` also concentrated source guards into one file, so even responsibility-local changes now expand the review surface.
- The recent P2 work made local cleanup progress, but it was too fine-grained: helper-by-helper commits accumulated while file-level modularization and progress cleanup lagged behind.

Objective:
- Re-split `core.py` and `test_east_core.py` by responsibility such as suffix parser / annotation / builder / source guard, so future compiler-internal work can proceed in cluster-sized slices.

Scope:
- `src/toolchain/ir/core.py`
- `src/toolchain/ir/core_expr_*.py`
- `test/unit/ir/test_east_core.py`
- `test/unit/ir/test_east_*.py` if needed
- `docs/ja/todo/index.md` / `docs/en/todo/index.md`
- `docs/ja/plans/p2-east-core-modularization.md` / `docs/en/plans/p2-east-core-modularization.md`

Out of scope:
- New EAST/EAST3 language features
- Nominal ADT / runtime / backend rollout itself
- Full frontend redesign beyond the selfhost parser

Acceptance Criteria:
- `core.py` is split further by responsibilities such as `call` / `attr` / `subscript` / builder / statement parser, so future changes can stay within module-sized boundaries.
- `test_east_core.py` source guards are reorganized at cluster level, and suitable parts move into dedicated test modules.
- TODO keeps only one-line progress summaries, while detailed notes move into this plan's `Decision Log`.
- Representative regressions continue to pass: `test_east_core.py`, `test_prepare_selfhost_source.py`, and `tools/build_selfhost.py`.

Validation Commands:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east_core.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/selfhost -p 'test_prepare_selfhost_source.py'`
- `python3 tools/build_selfhost.py`
- `python3 tools/check_todo_priority.py`
- `git diff --check`

Breakdown:
- [x] [ID: P2-EAST-CORE-MODULARIZATION-01-S1-01] Inventory remaining clusters in `core.py` / `test_east_core.py` and fix split boundaries as `suffix parser` / `annotation` / `builder` / `source guard`.
- [x] [ID: P2-EAST-CORE-MODULARIZATION-01-S2-01] Extract the `attr/subscript annotation` cluster into a dedicated mixin module and push state/build-dispatch helpers out of `core.py`.
- [x] [ID: P2-EAST-CORE-MODULARIZATION-01-S2-02] Move the remaining `call/attr/subscript` suffix parser clusters into dedicated modules and reduce `core.py` postfix parsing to orchestration.
- [x] [ID: P2-EAST-CORE-MODULARIZATION-01-S3-01] Split `test_east_core.py` source guards into feature-specific test modules so they track module boundaries one-to-one.
- [x] [ID: P2-EAST-CORE-MODULARIZATION-01-S3-02] Compress TODO/plan progress notes and keep detailed history only in the `Decision Log`.
- [x] [ID: P2-EAST-CORE-MODULARIZATION-01-S4-01] Re-run representative regressions, confirm no regression, and archive the completed task.

## S1-01 Inventory

As of 2026-03-11, the major remaining clusters are:

1. `call suffix / call args`
   - Partially moved into `core_expr_call_args.py` / `core_expr_call_suffix.py`.
   - Remaining issue: unify source-guard granularity.
2. `attr/subscript suffix`
   - token/state helpers are already in `core_expr_attr_subscript_suffix.py`.
   - annotation/build-dispatch still remain in `core.py`.
3. `call / attr / subscript annotation`
   - call annotation is partially extracted into `core_expr_call_annotation.py`.
   - attr/subscript annotation is still in `core.py` and is the next main cluster.
4. `builder / statement parser`
   - `_sh_make_*` helpers and the statement parser are still concentrated in `core.py`.
5. `source guard`
   - `test_east_core.py` still mixes guards for already-split modules and guards for unsplit parts.

Why start with `attr/subscript annotation`:
- There is already an adjacent `attr/subscript suffix` module, so the responsibility boundary is close and the diff can stay contained.
- On the `core.py` side, we can first move only state/build-dispatch helpers out while keeping the actual build bodies local.
- `test_east_core.py` can be cleanly reorganized around `core.py` plus the new module.

## Decision Log

- 2026-03-11: Based on user feedback, switched from helper-by-helper changes to cluster-sized splitting for `core.py`. Progress notes should also be compressed and moved out of TODO.
- 2026-03-11: As `S1-01`, inventoried the remaining clusters in `core.py` / `test_east_core.py` and fixed `attr/subscript annotation` as the first split target.
- 2026-03-11: As `S2-01`, extracted the `attr/subscript annotation` cluster into `core_expr_attr_subscript_annotation.py`. The split boundary intentionally leaves the build bodies and top-level `_sh_*`-heavy orchestration in `core.py`, while moving only the state/build-dispatch helpers out.
- 2026-03-11: By the time `P1-IR-CORE-DECOMPOSITION-01` closed, `core.py` was already reduced to 214 lines, `test_east_core.py` to 44 lines, the `call/attr/subscript` suffix and annotation clusters lived in dedicated modules, source-contract guards were split, progress notes were compressed, and representative IR/selfhost regressions passed. This plan is therefore fulfilled by the P1 end state and moves to archive to avoid duplicate tracking.
