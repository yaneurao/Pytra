<a href="../../docs-ja/plans/instruction-template.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# Instruction Template (Priority Override)

Last updated: 2026-02-22

Use this template when you need to override priorities for the current work while keeping `docs-ja/todo.md` as the source of truth.
Do not use `todo2.md`.

## Template

```md
Target IDs for this turn:
- P1-COMP-01
- P1-COMP-02

Completion conditions:
- Unit tests pass
- Update related descriptions in docs-ja

Out of scope:
- Translation updates under docs/
- Broad refactoring

Priority:
- Top priority for this turn only
```

## Operational rules

- Override priority through chat instructions (do not use `todo2.md`).
- Instructions must include at least: `target IDs`, `completion conditions`, and `out of scope`.
- Without explicit override instructions, follow the default priority order in `docs-ja/todo.md`.
