<a href="../../docs-jp/plans/docs-translation-sync.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# TASK GROUP: TG-DOCS-SYNC

Last updated: 2026-02-22

Related TODO:
- `docs-jp/todo.md` `ID: DOCS-SYNC-01`

Background:
- `docs-jp` is the source of truth, but the synchronization workflow for `todo-history` English translation was not standardized and tended to be operator-dependent.

Objective:
- Define a repeatable routine to synchronize `docs-jp/todo-history/YYYYMMDD.md` to `docs/todo-history/YYYYMMDD.md`.

In scope:
- Documenting the sync workflow
- Clarifying update units (date/file) and ownership
- Establishing a minimal mechanical check path for missing sync

Out of scope:
- Bulk retranslation of all existing documents

Acceptance criteria:
- The daily sync flow can be reproduced from the documented steps.
- Differences between `docs-jp` and `docs` are easy to inspect.
- Date-file set parity between `docs-jp/todo-history` and `docs/todo-history` can be checked automatically.

Operational steps:
1. Run `python3 tools/sync_todo_history_translation.py` to create missing `docs/todo-history/YYYYMMDD.md` mirror files.
2. Translate generated `pending` files into English and update `<!-- translation-status: done -->`.
3. Run `python3 tools/sync_todo_history_translation.py --check` to confirm there are no missing/extra/index gaps.
4. Review granular diffs with `git diff -- docs-jp/todo-history docs/todo-history` and commit.

Validation commands:
- `python3 tools/sync_todo_history_translation.py --check`
- `git diff -- docs-jp/todo-history docs/todo-history`

Decision log:
- 2026-02-22: Initial draft created.
- 2026-02-22: Added `tools/sync_todo_history_translation.py` to automate date-file stub creation and index synchronization for `docs/todo-history`.
