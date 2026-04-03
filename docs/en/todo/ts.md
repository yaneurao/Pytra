<a href="../../ja/todo/ts.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-2563EB?style=flat-square">
</a>

# TODO — TypeScript / JavaScript backend

> Domain-specific TODO. See [index.md](./index.md) for the full index.

Last updated: 2026-04-01 (P0-TS-REMOVE-TYPE-ID completed, P0-TS-NEW-FIXTURES completed, P0-TS-STDLIB completed, P0-TS-LINT-V2 completed, S1/S2/S3/S4/S5 completed, P0-TS-LINT-FIX completed, P0-TS-TYPE-MAPPING completed, P8-TS-EMITTER-S6/S7 completed, P0-JS-RUNTIME-ESM completed)

## Operating Rules

- **The old toolchain1 (`src/toolchain/emit/ts/`) must not be modified.** All new development and fixes go in `src/toolchain2/emit/ts/` ([spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1).
- Each task requires an `ID` and a context file (`docs/ja/plans/*.md`).
- Work in priority order (lower P number first).
- Progress notes and commit messages must include the same `ID`.
- **When a task is complete, change `[ ]` to `[x]` and append a completion note, then commit.**
- Completed tasks are periodically moved to `docs/en/todo/archive/`.
- **parity test completion criteria: emit + compile + run + stdout match.**
- **Always read the [emitter implementation guidelines](../spec/spec-emitter-guide.md).** It covers the parity check tool, prohibited patterns, and how to use mapping.json.

## Current Status

- No TS/JS emitter has been implemented in toolchain2 yet (`src/toolchain2/emit/ts/` and `src/toolchain2/emit/js/` do not exist)
- runtime exists in `src/runtime/ts/` and `src/runtime/js/` (implementations from the old toolchain1 era)
- The old toolchain1 TS/JS emitter exists at `src/toolchain/emit/ts/` and `src/toolchain/emit/js/`, but needs to be migrated to toolchain2

## Design Approach

Implement the TypeScript emitter first; handle JavaScript by suppressing type annotation output via a flag.

- EAST3 contains complete type information. The TS emitter outputs it straightforwardly with type annotations.
- JS mode simply omits type annotations using the same emitter (`--strip-types` or `--target js`).
- There is no need to build two separate emitters — one TS emitter + a flag covers both JS and TS.

## Incomplete Tasks

### P0-TS-SHIM-CLEANUP: Remove Python built-in shims from the runtime

Context: [docs/ja/plans/plan-ts-runtime-shim-cleanup.md](../plans/plan-ts-runtime-shim-cleanup.md)

`py_runtime.ts` exports Python built-in names as shims (e.g., `export const int = Number`, `export function match(...)`). The emitter should resolve these to TS-specific names via EAST3 `runtime_call` / `mapping.json`.

1. [x] [ID: P0-TS-SHIM-S1] Audit and enumerate the Python built-in name shims exported from `py_runtime.ts` (2026-04-02) — `int=Number`, `float=Number`, `bool=Boolean`, `str=String`, `match`/`sub`/`search`/`findall`/`split` (re functions), `perf_counter`, `sys`, `dict()`/`list()`/`set_()` are in scope. Type aliases (e.g., `type int = number`) are retained; value exports migrate to mapping.json resolution.
2. [ ] [ID: P0-TS-SHIM-S2] Fix the emitter to resolve via the mapping.json `calls` table and remove the shim exports.
3. [ ] [ID: P0-TS-SHIM-S3] Confirm no regressions in fixture + sample + stdlib TS/JS parity.

### P0-TS-REMOVE-TYPE-ID: Retire PYTRA_TYPE_ID and migrate to native TS `instanceof`

Spec: [docs/ja/spec/spec-adt.md](../spec/spec-adt.md) §3.4

The TS emitter mimics C++'s `type_id` approach by embedding a `[PYTRA_TYPE_ID]: number` field in all classes. Since TS has native `typeof` / `instanceof`, this is unnecessary. Unions should be output as `T1 | T2` directly, and isinstance should be checked with `instanceof`.

1. [x] [ID: P0-TS-TYPEID-S1] Remove `PYTRA_TYPE_ID` field insertion into classes from the TS emitter (2026-04-01)
2. [x] [ID: P0-TS-TYPEID-S2] Replace `pytra_isinstance` with native JS/TS `instanceof` (2026-04-01) — absorb post-link `pytra_isinstance(pyTypeId(...), *_TID)` patterns into native checks on the emitter side
3. [x] [ID: P0-TS-TYPEID-S3] Remove `PYTRA_TYPE_ID` export from `pytra_built_in_py_runtime` (2026-04-01) — retain the internal runtime constant, remove only the export
4. [x] [ID: P0-TS-TYPEID-S4] Confirm no regressions in fixture + sample + stdlib TS/JS parity (2026-04-01) — fixture TS/JS 136/136, sample TS/JS 18/18, stdlib TS/JS 16/16 PASS

### P0-TS-NEW-FIXTURES: Pass TS/JS parity for new fixtures

Parity check for fixtures added in this session. All pass in Python already.

1. [x] [ID: P0-TS-NEWFIX-S1] Confirm `tuple_unpack_variants` passes compile + run parity in TS/JS (2026-04-01)
2. [x] [ID: P0-TS-NEWFIX-S2] Confirm `typed_container_access` passes compile + run parity in TS/JS (2026-04-01)
3. [x] [ID: P0-TS-NEWFIX-S3] Confirm `in_membership_iterable` passes compile + run parity in TS/JS (2026-04-01)
4. [x] [ID: P0-TS-NEWFIX-S4] Confirm `callable_higher_order` passes compile + run parity in TS/JS (2026-04-01)
5. [x] [ID: P0-TS-NEWFIX-S5] Confirm `object_container_access` passes compile + run parity in TS/JS (2026-04-01) — 5/5 PASS with `runtime_parity_check_fast.py --targets ts,js --case-root fixture ...`

### P0-TS-STDLIB: Pass TS/JS stdlib parity

1. [x] [ID: P0-TS-STDLIB-S1] Confirm all cases pass with `runtime_parity_check_fast.py --targets ts --case-root stdlib` (fix emitter / runtime if failures occur) (2026-04-01) — 16/16 PASS
2. [x] [ID: P0-TS-STDLIB-S2] Confirm all cases pass with `runtime_parity_check_fast.py --targets js --case-root stdlib` (2026-04-01) — 16/16 PASS

### P0-TS-LINT-V2: Resolve remaining TS emitter hardcode lint violations

`check_emitter_hardcode_lint.py --lang ts` shows 4 categories FAIL (module_name, runtime_symbol, class_name, skip_pure_python). Once resolved to 0 by P0-TS-LINT-FIX, new code may have reintroduced them.

1. [x] [ID: P0-TS-LINT-V2-S1] Fix module_name / runtime_symbol / class_name violations (2026-04-01) — consolidated runtime symbol / exception mapping / builtin symbol tables into `types.py`
2. [x] [ID: P0-TS-LINT-V2-S2] Fix skip_pure_python violations — remove pure Python modules from mapping.json skip_modules (2026-04-01) — removed `pytra.std.random`
3. [x] [ID: P0-TS-LINT-V2-S3] Confirm `check_emitter_hardcode_lint.py --lang ts` reports 0 violations across all categories (2026-04-01) — 0 violations

### P0-JS-RUNTIME-ESM: Migrate JS runtime from `require()` to ESM imports

Review finding: The TS emitter changed JS output to ESM (`import` syntax), but `require("fs")` / `require("path")` remain in `src/runtime/js/built_in/py_runtime.js`. In ESM-mode `node`, `require` is undefined, causing `pyglob()` to silently return an empty array (`glob.glob()` breaks silently).

1. [x] [ID: P0-JS-RUNTIME-ESM-S1] Rewrite `require("fs")` / `require("path")` in `py_runtime.js` as ESM `import` statements (2026-03-30)
2. [x] [ID: P0-JS-RUNTIME-ESM-S2] Confirm `os_glob_extended` fixture passes compile + run parity in JS (2026-03-30)

### P0-TS-TYPE-MAPPING: Migrate TS emitter type mapping to mapping.json

Spec: [spec-runtime-mapping.md](../spec/spec-runtime-mapping.md) §7

1. [x] [ID: P0-TS-TYPEMAP-S1] Add a `types` table to `src/runtime/ts/mapping.json` — define full mappings for POD types (`int64` → `number`, etc.) and class types (`Exception` → `Error`, etc.)
2. [x] [ID: P0-TS-TYPEMAP-S2] Replace hardcoded type names in the TS emitter (including `types.py`) with `resolve_type()` calls — add a `mapping` parameter to `ts_type()` and update all call sites to pass `ctx.mapping`
3. [x] [ID: P0-TS-TYPEMAP-S3] Confirm no impact on fixture emit (2026-03-30) — maintained 146/146 PASS

### P0-TS-LINT-FIX: Fix hardcode violations in the TS emitter

Spec: [spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1, §7

Violation list (detected by `check_emitter_hardcode_lint.py`):
- module_name 1 violation: `"sys"` — hardcoded module name
- runtime_symbol 1 violation: `"perf_counter"` — hardcoded runtime function name
- class_name 4 violations: `"Path"`, `"ArgumentParser"`, `"Exception"` family — some to be resolved by P0-TS-TYPE-MAPPING; remainder to be removed from emitter logic

1. [x] [ID: P0-TS-LINT-S1] Fix module_name violation — remove the `"sys"` string literal and resolve from EAST3 `runtime_module_id` (renamed `sys` to `pySys` in py_runtime.ts, updated mapping.json)
2. [x] [ID: P0-TS-LINT-S2] Fix runtime_symbol violation — remove the `"perf_counter"` string match and use the mapping.json resolution result directly (handled via runtime_imports scan)
3. [x] [ID: P0-TS-LINT-S3] Fix class_name violations — move `"Path"`, `"ArgumentParser"`, `"Exception"` family to types.py (lint-excluded) and remove the literals from the emitter
4. [x] [ID: P0-TS-LINT-S4] Confirm 0 TS violations with `check_emitter_hardcode_lint.py` (2026-03-30) — maintained 146/146 PASS

### P8-TS-EMITTER: Implement a new TypeScript emitter in toolchain2

Prerequisite: Begin after the Go emitter (reference implementation) and CommonRenderer have stabilized.

1. [x] [ID: P8-TS-EMITTER-S1] Implement a new TypeScript emitter in `src/toolchain2/emit/ts/` — CommonRenderer + override structure. Leave only TS/JS-specific nodes (prototype chain, arrow function, destructuring, etc.) as overrides (142 fixtures OK)
2. [x] [ID: P8-TS-EMITTER-S2] Create `src/runtime/ts/mapping.json` and define runtime_call mappings
3. [x] [ID: P8-TS-EMITTER-S3] Confirm successful TS emit for 132 fixtures + 18 samples (147 fixtures OK, 18 samples OK)
4. [x] [ID: P8-TS-EMITTER-S4] Align the TS runtime with toolchain2 emit output
5. [x] [ID: P8-TS-EMITTER-S5] Pass fixture + sample TS compile + run parity (tsc + node execution) — 146/146 PASS (2026-03-30)
6. [x] [ID: P8-TS-EMITTER-S6] Add a type-annotation suppression flag (`--strip-types` or `--target js`) to cover JS output — fixed strip_types mode in the emitter (type declarations / as any / pytra_isinstance export), added missing functions to py_runtime.js (math/json/path/sys/re/argparse, etc.)
7. [x] [ID: P8-TS-EMITTER-S7] Pass fixture + sample JS run parity (node execution) — fixture 131/131 + stdlib 16/16 = 147/147 PASS (2026-03-30)

### P0-TS-RUNTIME-TYPE-ID-CLEANUP: Completely remove PYTRA_TYPE_ID from the TS/JS runtime

Spec: [docs/ja/spec/spec-adt.md](../spec/spec-adt.md) §6

P0-TS-REMOVE-TYPE-ID removed the emitter export, but the `PYTRA_TYPE_ID` Symbol definition and references remain internally in `src/runtime/ts/built_in/py_runtime.ts` and `src/runtime/js/built_in/py_runtime.js`. Since generated code no longer uses it, remove it completely from the runtime internals as well.

1. [x] [ID: P0-TS-RT-TYPEID-S1] Remove `PYTRA_TYPE_ID` definition and all references from `src/runtime/ts/built_in/py_runtime.ts` (2026-04-02)
2. [x] [ID: P0-TS-RT-TYPEID-S2] Do the same for `src/runtime/js/built_in/py_runtime.js` (2026-04-02)
3. [x] [ID: P0-TS-RT-TYPEID-S3] Confirm no regressions in fixture + sample + stdlib TS/JS parity (2026-04-02) — fixture 137/137, sample 18/18, stdlib 16/16 PASS

### P12-TS-SELFHOST: Transpile toolchain2 to TypeScript using the TS emitter and pass tsc build

Prerequisite: Begin after P8-TS-EMITTER is complete.

1. [ ] [ID: P12-TS-SELFHOST-S0] Add return type annotations to functions in the selfhost target code (`src/toolchain2/` all .py) that are missing them — bring resolve to a state where no `inference_failure` occurs (shared with P4/P6/P9; share results with whichever lane completes first)
2. [ ] [ID: P12-TS-SELFHOST-S1] Emit all toolchain2 .py files to TS and confirm tsc build passes
3. [ ] [ID: P12-TS-SELFHOST-S2] Resolve tsc build failures by fixing the emitter/runtime (no EAST workarounds)
4. [ ] [ID: P12-TS-SELFHOST-S3] Place selfhost TS golden files and maintain them as regression tests
5. [ ] [ID: P12-TS-SELFHOST-S4] `run_selfhost_parity.py --selfhost-lang ts --emit-target ts --case-root fixture` passes fixture parity
6. [ ] [ID: P12-TS-SELFHOST-S5] `run_selfhost_parity.py --selfhost-lang ts --emit-target ts --case-root sample` passes sample parity
