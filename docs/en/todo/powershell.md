<a href="../../ja/todo/powershell.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-2563EB?style=flat-square">
</a>

# TODO — PowerShell backend

> Domain-specific TODO. See [index.md](./index.md) for the full index.

Last updated: 2026-04-04

## Operating Rules

- **The old toolchain1 (`src/toolchain/emit/powershell/`) must not be modified.** All new development and fixes go in `src/toolchain2/emit/powershell/` ([spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1).
- Each task requires an `ID` and a context file (`docs/ja/plans/*.md`).
- Work in priority order (lower P number first).
- Progress notes and commit messages must include the same `ID`.
- **When a task is complete, change `[ ]` to `[x]` and append a completion note, then commit.**
- Completed tasks are periodically moved to `docs/en/todo/archive/`.
- **parity test completion criteria: emit + compile + run + stdout match.**
- **Always read the [emitter implementation guidelines](../spec/spec-emitter-guide.md).** It covers the parity check tool, prohibited patterns, and how to use mapping.json.

## References

- Old toolchain1 PowerShell emitter: `src/toolchain/emit/powershell/`
- toolchain2 TS emitter (reference implementation): `src/toolchain2/emit/ts/`
- Existing PowerShell runtime: `src/runtime/powershell/`
- emitter implementation guidelines: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json spec: `docs/ja/spec/spec-runtime-mapping.md`

## Incomplete Tasks

### P1-PS1-EMITTER: Implement a new PowerShell emitter in toolchain2

1. [x] [ID: P1-PS1-EMITTER-S1] Implement a new PowerShell emitter in `src/toolchain2/emit/powershell/` — CommonRenderer + override structure. Use the old `src/toolchain/emit/powershell/` and the TS emitter as reference.
   - Completed: Created `emitter.py`, `types.py`, `__init__.py`, `cli.py` from scratch. Standalone function-based structure.
2. [x] [ID: P1-PS1-EMITTER-S2] Create `src/runtime/powershell/mapping.json` — define `calls`, `types`, `env.target`, `builtin_prefix`, `implicit_promotions`.
   - Completed: `src/runtime/powershell/mapping.json` created from scratch.
3. [x] [ID: P1-PS1-EMITTER-S3] Confirm successful PowerShell emit for all fixture cases.
   - Completed: All 145 cases in test/fixture/east3/ emitted without errors.
4. [x] [ID: P1-PS1-EMITTER-S4] Align the PowerShell runtime with toolchain2 emit output.
   - Completed: Fixed `runtime_call`-based Attribute method dispatch; added 25 missing functions to py_runtime.ps1 (list_sort/reverse/clear, dict_pop/setdefault/clear, str_strip, etc.).
5. [x] [ID: P1-PS1-EMITTER-S5] Pass PowerShell run parity for fixtures (`pwsh -File`).
   - Completed: 146/146 pass (added callable_optional_none fixture, fixed callable variable dispatch, PodIsinstanceFoldPass optimizer, etc.)
   - Note: There was a bug where all cases would be SKIP unless `pwsh` was added to `_LOCAL_TOOL_FALLBACKS` (fixed).
6. [ ] [ID: P1-PS1-EMITTER-S6] Pass PowerShell parity for stdlib (`--case-root stdlib`)
   - Current state: 6/16 pass, 10/16 fail (argparse, json, math_path, os_glob, pathlib, re, sys, etc.)
7. [ ] [ID: P1-PS1-EMITTER-S7] Pass PowerShell parity for sample (`--case-root sample`)

### P2-PS1-LINT: Resolve emitter hardcode lint violations for PowerShell

1. [x] [ID: P2-PS1-LINT-S1] Confirm `check_emitter_hardcode_lint.py --lang ps1` reports 0 violations across all categories.
   - Completed: All 8 categories 🟩 PASS (0 violations)
