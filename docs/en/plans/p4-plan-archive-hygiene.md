# P4 Plan Archive Hygiene

Last updated: 2026-03-11

Purpose:
- Reclassify the live plans left under `docs/ja/plans/` into `active`, `backlog`, and `stale-complete`.
- Restore consistency between `docs/ja/todo/index.md` and `docs/ja/plans/`, so completed tasks do not keep dangling live plans and active tasks do not lose their context files.
- Lock the archive handoff workflow so completed tasks stop accumulating under the live `plans/` directory.

Background:
- [TODO](/workspace/Pytra/docs/ja/todo/index.md) currently says there are no unfinished tasks, while the top level of [plans](/workspace/Pytra/docs/ja/plans/README.md) still contains many `p0-*`, `p1-*`, `p2-*`, `p3-*`, and `p4-*` files.
- The archive side already contains many completed plans, so live plans and archived plans are mixed in practice.
- In that state, looking at `plans/` alone is no longer enough to tell whether a plan is active, merely backlog, or already stale-complete, which breaks the intended TODO workflow.

Out of scope:
- Revising the technical contents of each plan.
- Redesigning task priorities themselves.
- Large-scale rewrites of already archived history bodies.

Acceptance criteria:
- The classification rules for `active`, `backlog`, and `stale-complete` are documented for `p*-*.md` files under `docs/ja/plans/`.
- Representative stale-complete plans are moved into the archive and the TODO/archive indexes stay consistent.
- Plans intentionally left as backlog can be recognized as backlog from the plan text or README instead of being mistaken for active work.
- The `docs/en/` mirror follows the same operating policy as the Japanese source.

## Child tasks

- [ ] [ID: P4-PLAN-ARCHIVE-HYGIENE-01-S1-01] Inventory live plans and record the classification rules plus representative counts for `active`, `backlog`, and `stale-complete`.
- [ ] [ID: P4-PLAN-ARCHIVE-HYGIENE-01-S2-01] Move representative stale-complete live plans into the archive and repair TODO/archive index links.
- [ ] [ID: P4-PLAN-ARCHIVE-HYGIENE-01-S3-01] Decide the placement or labeling rules for backlog plans so the top-level `plans/` directory becomes active-first again.
- [ ] [ID: P4-PLAN-ARCHIVE-HYGIENE-01-S4-01] Reflect the archive handoff workflow in README / operations docs and prevent future completed-plan drift.

## Decision log

- 2026-03-11: This task is important for docs hygiene but not urgent enough to block current compiler/runtime work, so it is tracked as `P4`.
- 2026-03-11: Start with explicit classification rules and representative stale-complete handoff, instead of trying to archive every remaining live plan in one pass.
