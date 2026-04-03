<a href="../../en/todo/cs.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — C# backend

> Domain-specific TODO. See [index.md](./index.md) for the full index.

Last updated: 2026-03-31

## Operating Rules

- **The old toolchain1 (`src/toolchain/emit/cs/`) must not be modified.** All new development and fixes go in `src/toolchain2/emit/cs/` ([spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1).
- Each task requires an `ID` and a context file (`docs/ja/plans/*.md`).
- Work in priority order (lower P numbers first).
- Progress notes and commit messages must always include the same `ID`.
- **When a task is complete, change `[ ]` to `[x]` and append a completion note, then commit.**
- Completed tasks are periodically moved to `docs/ja/todo/archive/`.
- **Completion criteria for parity tests: "emit + compile + run + stdout match".**
- **You must read the [emitter implementation guide](../spec/spec-emitter-guide.md).** It covers the parity check tool, prohibited patterns, and how to use mapping.json.

## References

- Old toolchain1 C# emitter: `src/toolchain/emit/cs/`
- toolchain2 TS emitter (reference implementation): `src/toolchain2/emit/ts/`
- Existing C# runtime: `src/runtime/cs/`
- Emitter implementation guide: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json spec: `docs/ja/spec/spec-runtime-mapping.md`

## Incomplete Tasks

### P3-CS-SELFHOST: Convert toolchain2 to C# via the C# emitter and pass build

Context: [docs/ja/plans/p3-cs-selfhost.md](../plans/p3-cs-selfhost.md)

1. [ ] [ID: P3-CS-SELFHOST-S0] Add return type annotations to functions in the selfhost target code (`src/toolchain2/` all .py) that are missing them — get resolve to a state with no `inference_failure` (shared with other languages; share results from whichever side completes first)
2. [ ] [ID: P3-CS-SELFHOST-S1] Emit all toolchain2 .py files to C# and confirm the build passes
3. [ ] [ID: P3-CS-SELFHOST-S2] Resolve build failures by fixing the emitter/runtime (no EAST workarounds)
4. [ ] [ID: P3-CS-SELFHOST-S3] Place C# selfhost golden files and maintain them as regression tests
5. [ ] [ID: P3-CS-SELFHOST-S4] Confirm fixture parity PASS with `run_selfhost_parity.py --selfhost-lang cs --emit-target cs --case-root fixture`
6. [ ] [ID: P3-CS-SELFHOST-S5] Confirm sample parity PASS with `run_selfhost_parity.py --selfhost-lang cs --emit-target cs --case-root sample`
