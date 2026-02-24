<a href="../../docs-ja/plans/README.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# plans

This folder stores long-term plans, design drafts, and investigation notes.

## Rules

- `docs-ja/` is the source of truth. This `docs/` tree is the English mirror.
- Keep planning documents under discussion in this folder; formal tracking of unfinished tasks stays in `docs-ja/todo.md`.
- Move only concrete, actionable items into `docs-ja/todo.md`.
- Each plan should map one-to-one with a TODO task ID (for example: `P1-COMP-01`).
- In TODO entries, always list both the task ID and the corresponding plan file path.
- For priority-override instructions, use `docs-ja/plans/instruction-template.md`.

## Recommended Template

```md
# TASK GROUP: <GROUP-ID>

Last updated: YYYY-MM-DD

Related TODO:
- `docs-ja/todo.md` `ID: ...`

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
