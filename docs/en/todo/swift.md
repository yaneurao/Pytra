<a href="../../ja/todo/swift.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-2563EB?style=flat-square">
</a>

# TODO — Swift backend

> Domain-specific TODO. See [index.md](./index.md) for the full index.

Last updated: 2026-04-03

## Operating Rules

- **The old toolchain1 (`src/toolchain/emit/swift/`) must not be modified.** All new development and fixes go in `src/toolchain2/emit/swift/` ([spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1).
- Each task requires an `ID` and a context file (`docs/ja/plans/*.md`).
- Work in priority order (lower P number first).
- Progress notes and commit messages must include the same `ID`.
- **When a task is complete, change `[ ]` to `[x]` and append a completion note, then commit.**
- Completed tasks are periodically moved to `docs/en/todo/archive/`.
- **parity test completion criteria: emit + compile + run + stdout match.**
- **Always read the [emitter implementation guidelines](../spec/spec-emitter-guide.md).** It covers the parity check tool, prohibited patterns, and how to use mapping.json.

## References

- Old toolchain1 Swift emitter: `src/toolchain/emit/swift/`
- toolchain2 TS emitter (reference implementation): `src/toolchain2/emit/ts/`
- Existing Swift runtime: `src/runtime/swift/`
- emitter implementation guidelines: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json spec: `docs/ja/spec/spec-runtime-mapping.md`

## Incomplete Tasks

### P1-SWIFT-EMITTER: Implement a new Swift emitter in toolchain2

1. [x] [ID: P1-SWIFT-EMITTER-S1] Implement a new Swift emitter in `src/toolchain2/emit/swift/` — CommonRenderer + override structure. Use the old `src/toolchain/emit/swift/` and the TS emitter as reference.
   Completion note: Added `src/toolchain2/emit/swift/` and connected `emit_swift_module()` to the Swift parity harness entry point. Confirmed emit + compile + run for representative fixtures (`add`, `assign`, `alias_arg`, `class`, `class_instance`). Context: `docs/ja/plans/p1-swift-toolchain2-bootstrap.md`
2. [x] [ID: P1-SWIFT-EMITTER-S2] Create `src/runtime/swift/mapping.json` — define `calls`, `types`, `env.target`, `builtin_prefix`, `implicit_promotions`.
   Completion note: Added `src/runtime/swift/mapping.json` and, together with the `runtime_parity_check_fast.py` Swift path, made the Swift target launchable from toolchain2. Context: `docs/ja/plans/p1-swift-toolchain2-bootstrap.md`
3. [x] [ID: P1-SWIFT-EMITTER-S3] Confirm successful Swift emit for all fixture cases.
   Completion note: Expanded Swift emitter support for expression / statement / class / exception / collection / lambda / enum / bytes and confirmed all fixture emits succeed. Context: `docs/ja/plans/p1-swift-toolchain2-bootstrap.md`
4. [x] [ID: P1-SWIFT-EMITTER-S4] Align the Swift runtime with toolchain2 emit output.
   Completion note: Extended `src/runtime/swift/built_in/py_runtime.swift` and handwritten stdlib shims to provide helpers required by emitter output: `gif/png/json/pathlib/sys/re`, container mutation, `min/max`, bytes/bytearray, Python-compatible repr, etc. Context: `docs/ja/plans/p1-swift-toolchain2-bootstrap.md`
5. [x] [ID: P1-SWIFT-EMITTER-S5] Pass Swift run parity for fixtures (build with `swiftc` then run).
   Completion note: Completed Swift fixture parity with `python3 tools/check/runtime_parity_check_fast.py --targets swift --case-root fixture`. Context: `docs/ja/plans/p1-swift-toolchain2-bootstrap.md`
6. [x] [ID: P1-SWIFT-EMITTER-S6] Pass Swift parity for stdlib (`--case-root stdlib`).
   Completion note: Confirmed `16/16 PASS` with `python3 tools/check/runtime_parity_check_fast.py --targets swift --case-root stdlib`. Context: `docs/ja/plans/p1-swift-toolchain2-bootstrap.md`
7. [x] [ID: P1-SWIFT-EMITTER-S7] Pass Swift parity for sample (`--case-root sample`).
   Completion note: Confirmed `18/18 PASS` with `python3 tools/check/runtime_parity_check_fast.py --targets swift --case-root sample` and synced sample golden to the current Python baseline. Context: `docs/ja/plans/p1-swift-toolchain2-bootstrap.md`

### P2-SWIFT-LINT: Resolve emitter hardcode lint violations for Swift

1. [ ] [ID: P2-SWIFT-LINT-S1] Confirm `check_emitter_hardcode_lint.py --lang swift` reports 0 violations across all categories.

### P20-SWIFT-SELFHOST: Transpile toolchain2 to Swift using the Swift emitter and pass the build

1. [ ] [ID: P20-SWIFT-SELFHOST-S0] Add type annotations to selfhost target code (shared with other languages)
2. [ ] [ID: P20-SWIFT-SELFHOST-S1] Emit all toolchain2 .py files to Swift and confirm the build passes
3. [ ] [ID: P20-SWIFT-SELFHOST-S2] Place selfhost Swift golden files
4. [ ] [ID: P20-SWIFT-SELFHOST-S3] `run_selfhost_parity.py --selfhost-lang swift --emit-target swift --case-root fixture` passes fixture parity
5. [ ] [ID: P20-SWIFT-SELFHOST-S4] `run_selfhost_parity.py --selfhost-lang swift --emit-target swift --case-root sample` passes sample parity
