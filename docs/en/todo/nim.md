<a href="../../en/todo/nim.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — Nim backend

> Domain-specific TODO. See [index.md](./index.md) for the full index.

Last updated: 2026-04-02

## Operating Rules

- **The old toolchain1 (`src/toolchain/emit/nim/`) must not be modified.** All new development and fixes go in `src/toolchain2/emit/nim/` ([spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1).
- Each task requires an `ID` and a context file (`docs/ja/plans/*.md`).
- Work in priority order (lower P numbers first).
- Progress notes and commit messages must always include the same `ID`.
- **When a task is complete, change `[ ]` to `[x]` and append a completion note, then commit.**
- Completed tasks are periodically moved to `docs/ja/todo/archive/`.
- **Completion criteria for parity tests: "emit + compile + run + stdout match".**
- **You must read the [emitter implementation guide](../spec/spec-emitter-guide.md).** It covers the parity check tool, prohibited patterns, and how to use mapping.json.

## References

- Old toolchain1 Nim emitter: `src/toolchain/emit/nim/`
- toolchain2 TS emitter (reference implementation): `src/toolchain2/emit/ts/`
- Existing Nim runtime: `src/runtime/nim/`
- Emitter implementation guide: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json spec: `docs/ja/spec/spec-runtime-mapping.md`

## Incomplete Tasks

### P1-NIM-EMITTER: Implement a new Nim emitter in toolchain2

Context: [docs/ja/plans/p1-nim-emitter.md](../plans/p1-nim-emitter.md)

1. [x] [ID: P1-NIM-EMITTER-S1] Implement a new Nim emitter in `src/toolchain2/emit/nim/` — CommonRenderer + override structure. Create emitter.py, types.py, __init__.py, profiles/nim.json. Completed: 2026-03-31
2. [x] [ID: P1-NIM-EMITTER-S2] Create `src/runtime/nim/mapping.json` — define `calls`, `types`, `env.target`, `builtin_prefix`, `implicit_promotions`, `skip_modules`. Completed: 2026-03-31
3. [x] [ID: P1-NIM-EMITTER-S3] Confirm Nim emit success for all fixtures — 129/131 success (remaining 2 are due to trait not yet supported on the parser side). Completed: 2026-03-31
4. [x] [ID: P1-NIM-EMITTER-S4] Align the Nim runtime with toolchain2 emit output — added py_print, str methods, container helpers, assert framework, etc. Completed: 2026-03-31
5. [ ] [ID: P1-NIM-EMITTER-S5] Pass fixture + sample Nim compile + run parity (`nim c -r`) — requires Nim compiler
6. [ ] [ID: P1-NIM-EMITTER-S6] Pass stdlib Nim parity (`--case-root stdlib`) — requires Nim compiler

### P2-NIM-LINT-FIX: Fix hardcode violations in the Nim emitter

1. [x] [ID: P2-NIM-LINT-S1] Confirm 0 Nim violations in `check_emitter_hardcode_lint.py` — Completed: 2026-04-02 (0 violations with `--lang nim --include-runtime --no-write`)

### P20-NIM-SELFHOST: Convert toolchain2 to Nim via the Nim emitter and run it

1. [ ] [ID: P20-NIM-SELFHOST-S0] Complete type annotation for selfhost target code (shared with other languages)
2. [ ] [ID: P20-NIM-SELFHOST-S1] Emit all toolchain2 .py files to Nim and confirm compile + execution
3. [ ] [ID: P20-NIM-SELFHOST-S2] Place Nim selfhost golden files
4. [ ] [ID: P20-NIM-SELFHOST-S3] Confirm fixture parity PASS with `run_selfhost_parity.py --selfhost-lang nim --emit-target nim --case-root fixture`
5. [ ] [ID: P20-NIM-SELFHOST-S4] Confirm sample parity PASS with `run_selfhost_parity.py --selfhost-lang nim --emit-target nim --case-root sample`
