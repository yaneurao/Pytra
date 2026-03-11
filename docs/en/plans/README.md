<a href="../../ja/plans/README.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# plans

This folder stores long-term plans, design drafts, and investigation notes.

## How To Read Live Plans

- The canonical entrypoint for live `plans/` is this `README.md`, not the raw file listing.
- `active` means only live plans referenced directly by unfinished tasks in `docs/ja/todo/index.md`.
- `backlog` means live `p*-*.md` files that are not registered in TODO yet and are either still unfinished backlog drafts or intentional live status/report sinks.
- `stale-complete` means live `p*-*.md` files that are no longer referenced by TODO, have every checklist item complete, and are not live status/report sinks. These should be moved out of live `plans/`.

Active live plans as of 2026-03-12:
- `p4-crossruntime-pyruntime-emitter-shrink.md`
- `p6-backend-conformance-suite.md`
- `p7-backend-parity-rollout-and-matrix.md`

## Rules

- `docs/ja/` is the source of truth. This `docs/en/` tree is the English mirror.
- Keep planning documents under discussion in this folder; formal tracking of unfinished tasks stays in `docs/ja/todo/index.md`.
- Move only concrete, actionable items into `docs/ja/todo/index.md`.
- Each plan should map one-to-one with a TODO task ID (for example: `P1-COMP-01`).
- In TODO entries, always list both the task ID and the corresponding plan file path.
- If you place supporting reports such as readiness reports under `plans/`, always link them from the corresponding plan.
- For priority-override instructions, use `docs/ja/plans/instruction-template.md`.
- If a draft remains under live `plans/` before it is promoted into TODO, treat it as backlog through this README instead of the raw file listing.
- New backlog drafts may write `Related TODO: none (backlog draft / not yet promoted)` and should replace that line with the real TODO ID once promoted.

## Completion Handoff Checklist

- Once the parent TODO task and all child tasks are marked `[x]` in `docs/ja/todo/index.md`, move the live plan to `docs/ja/plans/archive/YYYYMMDD-<slug>.md`.
- Remove the completed task from `docs/ja/todo/index.md` and add a completion section to `docs/ja/todo/archive/YYYYMMDD.md`.
- Add the archived plan link to `docs/ja/todo/archive/index.md`.
- Mirror the same plan / TODO / archive handoff under `docs/en/`.
- Remove the completed plan from the active live plan list in `plans/README.md` and verify that the backlog / stale-complete classification still holds.
- Run `python3 tools/check_todo_priority.py` and `git diff --check` after the handoff.

## Recommended Template

```md
# TASK GROUP: <GROUP-ID>

Last updated: YYYY-MM-DD

Related TODO:
- `docs/ja/todo/index.md` `ID: ...`

Background:
Objective:
In scope:
- ...
Out of scope:
- ...
Acceptance criteria:
- ...
Validation commands:
- ...
Decision log:
- YYYY-MM-DD: Initial draft.
```
