<a href="../../ja/todo/rust.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-2563EB?style=flat-square">
</a>

# TODO — Rust backend

> Domain-specific TODO. See [index.md](./index.md) for the full index.

Last updated: 2026-05-03

## Operating Rules

- **The old toolchain1 (`src/toolchain/emit/rs/`) must not be modified.** All new development and fixes go in `src/toolchain2/emit/rs/` ([spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1).
- Each task requires an `ID` and a context file (`docs/ja/plans/*.md`).
- Work in priority order (lower P number first).
- Progress notes and commit messages must include the same `ID`.
- **When a task is complete, change `[ ]` to `[x]` and append a completion note, then commit.**
- Completed tasks are periodically moved to `docs/en/todo/archive/`.
- **parity test completion criteria: emit + compile + run + stdout match.**
- **Always read the [emitter implementation guidelines](../spec/spec-emitter-guide.md).** It covers the parity check tool, prohibited patterns, and how to use mapping.json.

## Current Status

- The toolchain2 Rust emitter is implemented in `src/toolchain2/emit/rs/` (fixture 131/131 + sample 18/18 emit successful)
- runtime exists in `src/runtime/rs/` (being extended for toolchain2)
- compile + run parity passes for some fixtures (class_instance, dataclass, class_tuple_assign, nested_types, str_index_char_compare, etc.)
- Remaining blockers: EAST3-side issue with inheritance + ref semantics (P0-EAST3-INHERIT)

## Incomplete Tasks

### P1-HOST-CPP-EMITTER-RS: Host the C++ emitter with rs

Convert the C++ emitter (`toolchain.emit.cpp.cli`, 16 modules) to rs and confirm that the converted emitter can generate C++ code correctly. The C++ emitter source is already selfhost-safe.

1. [x] [ID: P1-HOST-CPP-EMITTER-RS-S1] Run `python3 src/pytra-cli.py -build src/toolchain/emit/cpp/cli.py --target rs -o work/selfhost/host-cpp/rs/` and pass conversion + build.
   - Completed: On 2026-05-03, `python3 src/pytra-cli.py -build src/toolchain/emit/cpp/cli.py --target rs -o work/selfhost/emitter-host/rs_cpp/host_emit` and `rustc --edition=2021 -Awarnings work/selfhost/emitter-host/rs_cpp/host_emit/toolchain_emit_cpp_cli.rs -o work/selfhost/emitter-host/rs_cpp/host_emit/emitter_cpp_rs` passed.
2. [x] [ID: P1-HOST-CPP-EMITTER-RS-S2] Run `python3 tools/run/run_emitter_host_parity.py --host-lang rs --hosted-emitter cpp --case-root fixture` and confirm C++ emitter host parity PASS. The result is written automatically to `.parity-results/emitter_host_rs.json`.
   - Completed: On 2026-05-03, `python3 tools/run/run_emitter_host_parity.py --host-lang rs --hosted-emitter cpp --case-root fixture --timeout-sec 3600` passed. `.parity-results/emitter_host_rs.json` has `parity_status: ok` and `detail: matched work/selfhost/emitter-host/rs_cpp/linked/manifest.json`.

### P5-RS-CLI-COMMON: Migrate Rust cli.py to the common runner

Context: [docs/ja/plans/p5-rs-cli-common-runner.md](../plans/p5-rs-cli-common-runner.md)

Of all 17 languages, only Rust has its own cli.py (235 lines). Migration to the common runner is possible after the type_id table is retired (P0-RS-TYPEID-CLN).

Prerequisite: P0-RS-TYPEID-CLN completed (type_id table no longer needed)

1. [x] [ID: P5-RS-CLI-S1] Migrate the Rust emitter to `expected_type_name`-based dispatch.
   - Completed: The Rust emitter's `isinstance` / class hierarchy checking has been restructured around `expected_type_name` fallback and `PyAny::TypeId` / downcast, eliminating dependence on the manifest type-id table.
2. [x] [ID: P5-RS-CLI-S2] Remove `_generate_type_id_table_rs` and `_manifest_type_id_table`.
   - Completed: Removed Rust-specific type-id table generation from [cli.py](../../src/toolchain2/emit/rs/cli.py).
3. [x] [ID: P5-RS-CLI-S3] Move runtime copy and package mode to `post_emit` and delegate to the common runner.
   - Completed: Migrated Rust `cli.py` to `run_emit_cli(...)`-based approach; moved runtime copy and `--package` `Cargo.toml` / `src/lib.rs` / `src/main.rs` generation to the `post_emit` side. Confirmed emit success with both `pytra-cli -build ... --target rs` and `--rs-package`.
4. [x] [ID: P5-RS-CLI-S4] Confirm no regressions in Rust parity.
   - Completed: Broad parity confirmed in `P0-RS-TYPEID-CLN-S3` as `stdlib 16/16 PASS`, `sample 18/18 PASS`, `fixture 145/145 PASS`. After CLI unification, `runtime_parity_check_fast --case-root fixture --targets rs top_level union_basic optional_none` passed `3/3 PASS` with no spot-check regressions.

### P9-RS-SELFHOST: Transpile toolchain2 to Rust using the Rust emitter and pass cargo build

Prerequisite: Begin after P7-RS-EMITTER is complete.

1. [x] [ID: P9-RS-SELFHOST-S0] Add return type annotations to functions in the selfhost target code (`src/toolchain2/` all .py) that are missing them — bring resolve to a state where no `inference_failure` occurs (shared with P4/P6/P20; share results with whichever lane completes first)
   - Completed: Confirmed 0 missing return annotations in `src/toolchain2/` via `python3 -m unittest tools.unittest.selfhost.test_selfhost_return_annotations`.
2. [ ] [ID: P9-RS-SELFHOST-S1] Replace flat `include!` with Rust `mod` + `use` structure — context: [plan-rs-selfhost-mod-structure.md](../plans/plan-rs-selfhost-mod-structure.md)
   - [ ] [ID: P9-RS-MOD-S1] Add a mod-structure output mode to the Rust emitter's multifile_writer (1 EAST module = 1 Rust mod)
   - [ ] [ID: P9-RS-MOD-S2] Implement automatic generation of `lib.rs` / `Cargo.toml`
   - [ ] [ID: P9-RS-MOD-S3] Implement emit of cross-module `use crate::` paths
3. [ ] [ID: P9-RS-SELFHOST-S2] Emit all toolchain2 .py files to Rust and confirm cargo build passes
4. [ ] [ID: P9-RS-SELFHOST-S3] Resolve cargo build failures by fixing the emitter/runtime (no EAST workarounds)
5. [ ] [ID: P9-RS-SELFHOST-S4] Place selfhost Rust golden files and maintain them as regression tests
6. [ ] [ID: P9-RS-SELFHOST-S5] `run_selfhost_parity.py --selfhost-lang rs --emit-target rs --case-root fixture` passes fixture parity
7. [ ] [ID: P9-RS-SELFHOST-S6] `run_selfhost_parity.py --selfhost-lang rs --emit-target rs --case-root sample` passes sample parity
