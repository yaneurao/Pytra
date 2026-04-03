<a href="../../en/todo/dart.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — Dart backend

> Domain-specific TODO. See [index.md](./index.md) for the full index.

Last updated: 2026-04-02

## Operating Rules

- **The old toolchain1 (`src/toolchain/emit/dart/`) must not be modified.** All new development and fixes go in `src/toolchain2/emit/dart/` ([spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1).
- Each task requires an `ID` and a context file (`docs/ja/plans/*.md`).
- Work in priority order (lower P numbers first).
- Progress notes and commit messages must always include the same `ID`.
- **When a task is complete, change `[ ]` to `[x]` and append a completion note, then commit.**
- Completed tasks are periodically moved to `docs/ja/todo/archive/`.
- **Completion criteria for parity tests: "emit + compile + run + stdout match".**
- **You must read the [emitter implementation guide](../spec/spec-emitter-guide.md).** It covers the parity check tool, prohibited patterns, and how to use mapping.json.

For completed tasks, see the [archive](archive/20260402.md).

## References

- Old toolchain1 Dart emitter: `src/toolchain/emit/dart/`
- toolchain2 TS emitter (reference implementation): `src/toolchain2/emit/ts/`
- Existing Dart runtime: `src/runtime/dart/`
- Emitter implementation guide: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json spec: `docs/ja/spec/spec-runtime-mapping.md`

## Incomplete Tasks

- None. The next Dart task is pending a new ticket.
