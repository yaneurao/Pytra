<a href="../../ja/todo/zig.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-2563EB?style=flat-square">
</a>

# TODO — Zig backend

> Domain-specific TODO. See [index.md](./index.md) for the full index.

Last updated: 2026-04-04

## Operating Rules

- **The old toolchain1 (`src/toolchain/emit/zig/`) must not be modified.** All new development and fixes go in `src/toolchain2/emit/zig/` ([spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1).
- Each task requires an `ID` and a context file (`docs/ja/plans/*.md`).
- Work in priority order (lower P number first).
- Progress notes and commit messages must include the same `ID`.
- **When a task is complete, change `[ ]` to `[x]` and append a completion note, then commit.**
- Completed tasks are periodically moved to `docs/en/todo/archive/`.
- **parity test completion criteria: emit + compile + run + stdout match.**
- **Always read the [emitter implementation guidelines](../spec/spec-emitter-guide.md).** It covers the parity check tool, prohibited patterns, and how to use mapping.json.

## References

- Old toolchain1 Zig emitter: `src/toolchain/emit/zig/`
- toolchain2 TS emitter (reference implementation): `src/toolchain2/emit/ts/`
- Existing Zig runtime: `src/runtime/zig/`
- emitter implementation guidelines: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json spec: `docs/ja/spec/spec-runtime-mapping.md`

## Incomplete Tasks

### P1-ZIG-EMITTER: Implement a new Zig emitter in toolchain2

1. [x] [ID: P1-ZIG-EMITTER-S1] Implement a new Zig emitter in `src/toolchain2/emit/zig/` — CommonRenderer + override structure. Use the old `src/toolchain/emit/zig/` and the TS emitter as reference.
   - Completion note (2026-04-04): Implemented the emitter body and CLI/runtime copier in `src/toolchain2/emit/zig/`; Zig can now be emitted from toolchain2 without any dependency on the old toolchain1.
2. [x] [ID: P1-ZIG-EMITTER-S2] Create `src/runtime/zig/mapping.json` — define `calls`, `types`, `env.target`, `builtin_prefix`, `implicit_promotions`.
   - Completion note (2026-04-04): `src/runtime/zig/mapping.json` and `src/toolchain2/emit/profiles/zig.json` are in place; the Zig target can now be selected via the toolchain2 profile/mapping path.
3. [x] [ID: P1-ZIG-EMITTER-S3] Confirm successful Zig emit for all fixture cases.
   - Completion note (2026-04-04): All 146 fixture cases successfully emit/compile/run with `python3 tools/check/runtime_parity_check_fast.py --targets zig`.
4. [x] [ID: P1-ZIG-EMITTER-S4] Align the Zig runtime with toolchain2 emit output.
   - Completion note (2026-04-04): Updated `src/runtime/zig/built_in/py_runtime.zig` and the Zig runtime copier to align with the toolchain2 emitter's union/container/callable/exception/property/super lowering.
5. [x] [ID: P1-ZIG-EMITTER-S5] Pass Zig run parity for fixtures (`zig build-exe -OReleaseFast`).
   - Completion note (2026-04-04): `python3 tools/check/runtime_parity_check_fast.py --targets zig` reports `SUMMARY cases=146 pass=146 fail=0`; fixture parity is complete.
6. [ ] [ID: P1-ZIG-EMITTER-S6] Pass Zig parity for stdlib (`--case-root stdlib`)
7. [ ] [ID: P1-ZIG-EMITTER-S7] Pass Zig parity for sample (`--case-root sample`)

### P2-ZIG-LINT: Resolve emitter hardcode lint violations for Zig

1. [ ] [ID: P2-ZIG-LINT-S1] Confirm `check_emitter_hardcode_lint.py --lang zig` reports 0 violations across all categories.
