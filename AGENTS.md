# Agent Collaboration Rules

## docs-jp Policy

- `docs-jp/` is the source of truth, and `docs/` is only a translation mirror.
- Do not create new files under `docs-jp/` unless the user explicitly requests it in the same turn.
- Keep unfinished work only in `docs-jp/todo.md`.
- Move completed items to `docs-jp/todo-old.md` and `docs-jp/todo-history/YYYYMMDD.md`.

## Long-Term Planning Notes

- Store long-term plans and design drafts in `plans/`.
- Do not keep long-term planning notes as standalone files under `docs-jp/`.
- When a plan item becomes actionable, copy only the unfinished task into `docs-jp/todo.md`.

## Guardrail

- Run `python3 tools/check_docs_jp_guard.py` before committing when touching docs.
- `tools/check_docs_jp_guard.py` fails if unmanaged files exist under `docs-jp/`.
