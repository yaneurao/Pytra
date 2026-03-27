<a href="../../../ja/plans/archive/20260312-p4-plan-archive-hygiene.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

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

## Classification Rules And Inventory Snapshot

- Count only tracked `p*-*.md` files directly under `docs/ja/plans/`; ignore untracked plan drafts.
- `active`: a live plan that is directly referenced by an unfinished task in `docs/ja/todo/index.md`.
- `stale-complete`: a live plan that is no longer referenced by TODO, has every checklist item marked `[x]`, and is not used as a live status/report sink or tool default output path.
- `backlog`: a live plan that is no longer referenced by TODO and is either unfinished backlog or an intentionally live status/report plan.

Tracked inventory as of 2026-03-12 (corrected criteria):
- before handoff, live `p*-*.md`: 146
- `active=6 / stale-complete=129 / backlog=11`
- after `S2-01` moved six representative stale-complete plans into archive, `live=140 / active=6 / stale-complete=123 / backlog=11`

Representative active:
- `p4-plan-archive-hygiene.md`
- `p4-crossruntime-pyruntime-emitter-shrink.md`
- `p4-crossruntime-pyruntime-residual-caller-shrink.md`

Representative stale-complete (archived in `S2-01`):
- `p1-multilang-selfhost-status.md`
- `p1-multilang-selfhost-multistage-status.md`
- `p0-backends-common-foundation.md`
- `p1-ruby-benchmark-readme-fix.md`
- `p1-go-sample01-quality-uplift.md`
- `p1-test-unit-layout-and-pruning.md`

Representative backlog / live-status:
- `p0-cpp-backend-dir-realign.md`
- `p1-pytra-cli-rs-target.md`
- `p2-wildcard-import-support.md`

## Child tasks

- [x] [ID: P4-PLAN-ARCHIVE-HYGIENE-01-S1-01] Inventory live plans and record the classification rules plus representative counts for `active`, `backlog`, and `stale-complete`.
- [x] [ID: P4-PLAN-ARCHIVE-HYGIENE-01-S2-01] Move representative stale-complete live plans into the archive and repair TODO/archive index links.
- [x] [ID: P4-PLAN-ARCHIVE-HYGIENE-01-S3-01] Decide the placement or labeling rules for backlog plans so the top-level `plans/` directory becomes active-first again.
- [x] [ID: P4-PLAN-ARCHIVE-HYGIENE-01-S4-01] Reflect the archive handoff workflow in README / operations docs and prevent future completed-plan drift.

## Decision log

- 2026-03-11: This task is important for docs hygiene but not urgent enough to block current compiler/runtime work, so it is tracked as `P4`.
- 2026-03-11: Start with explicit classification rules and representative stale-complete handoff, instead of trying to archive every remaining live plan in one pass.
- 2026-03-12: The first inventory used `archive twin exists` as a stale-complete signal, which misclassified the selfhost status files as representative stale-complete cases.
- 2026-03-12: Under the corrected criteria, `stale-complete` means `not in TODO + checklist complete + not a live status/report sink`, which changes the tracked live inventory to `active=6 / stale-complete=129 / backlog=11`.
- 2026-03-12: `S2-01` archived the representative stale-complete set (`p0-backends-common-foundation.md`, `p1-ruby-benchmark-readme-fix.md`, `p1-go-sample01-quality-uplift.md`, `p1-test-unit-layout-and-pruning.md`) in addition to the two earlier selfhost status files, reducing the live inventory to `140`.
- 2026-03-12: `plans/README.md` is now the canonical entrypoint for live `plans/`, listing the 6 active plans explicitly and documenting the backlog/stale-complete rules there. New backlog drafts may use `Related TODO: none (backlog draft / not yet promoted)`.
- 2026-03-12: `S4-01` added an archive handoff checklist to `plans/README.md` and the archive-operation docs, and synchronized the corrected classification rules into the README. That makes this hygiene task itself eligible for the same archive handoff path.
