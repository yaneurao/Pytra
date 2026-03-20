<a href="../../ja/spec/spec-linker.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# Linked Program / Linker Specification

This document defines the linked-program stage that receives multiple raw `EAST3` modules, validates them as one program, materializes whole-program summaries, and hands linked `EAST3` modules plus `link-output.v1` to toolchain.emit.

## 1. Background

The single-module `EAST3` optimizer alone cannot decide program-wide facts such as:

- final `type_id` assignment
- call graph / SCC
- interprocedural non-escape summaries
- container ownership hints

Therefore Pytra introduces a linked-program stage between raw `EAST3` and backend emission.

## 2. Non-goals

- introducing a new EAST stage number beyond `east_stage=3`
- making the linker render target-language syntax
- letting backends reconstruct whole-program summaries on their own

## 3. Terms

- **link unit**
  - one raw `EAST3` module document before linking
- **LinkedProgram**
  - validated in-memory model bundling multiple link units and program-wide options
- **link-input.v1**
  - input manifest used to build a `LinkedProgram`
- **link-output.v1**
  - output manifest containing global summaries and linked-module outputs
- **linked module**
  - `EAST3` after linker / linked-program optimization; it keeps `kind=Module` and `east_stage=3`, and adds `meta.linked_program_v1`

## 4. Core Pipeline

### 4.1 Default (fast path)

```text
parser
  -> EAST1
  -> EAST2
  -> EAST3 (raw module)
  -> LinkedProgramLoader
  -> LinkedProgramOptimizer
  -> linked module (EAST3)
  -> backend
```

### 4.2 Debug / Repro Mode

Persist only when needed:

1. raw `EAST3` module set
2. `link-input.json`
3. `link-output.json`
4. linked modules

Recommended flow:

1. `py2x.py` writes raw `EAST3` modules plus `link-input.json`
2. `eastlink.py` reads `link-input.json` and writes `link-output.json` plus linked modules
3. `east2cpp.py` (for C++) or `east2x.py` (generic) reads `link-output.json` and emits target code

Recommended filenames:

- `*.east3.json`
- `link-input.json`
- `link-output.json`

## 5. Linker Responsibilities

The linked-program stage receives raw `EAST3` modules and must finalize:

1. **module-set validation**
   - validate `kind=Module`, `east_stage=3`, `schema_version`, and `meta.dispatch_mode`
   - fail fast on program-wide inconsistency
2. **module-id normalization and deterministic order**
   - normalize `module_id`
   - detect duplicates
   - construct the same `LinkedProgram` order for the same input set
3. **global summary construction**
   - program-wide call graph
   - SCCs
   - `type_id_table`
   - non-escape summary
   - container ownership hints
4. **materialization into linked modules**
   - copy each required slice into `meta.linked_program_v1`
   - finalize function/call summaries such as `FunctionDef.meta.escape_summary` and `Call.meta.non_escape_callsite`
5. **program-manifest output**
   - write `link-output.v1` as the canonical output manifest

Backends are forbidden from:

- recomputing `type_id`
- reloading module sets to rebuild whole-program summaries
- filling in missing global information ad hoc inside emitters or hooks

## 6. `type_id` Assignment Rules

### 6.1 Basics

- built-in/runtime types keep their existing fixed IDs
- user classes receive IDs from the linker via a deterministic rule
- the backend only consumes the final linker result

### 6.2 Determinism (mandatory)

- identical input module sets and options must produce identical `type_id_table`
- order must not depend on filesystem traversal order or hash-map iteration order

### 6.3 Validation

- duplicate FQCN assignment is an error
- missing referenced class IDs in linked output are an error

## 7. Input / Output Contract

### 7.1 Raw `EAST3` Document Requirements

Each raw document accepted by the linker must contain at least:

- `kind = "Module"`
- `east_stage = 3`
- `schema_version`
- `meta.dispatch_mode = "native" | "type_id"`
- `meta.transpiler_version` (recommended)

### 7.2 `link-input.v1`

`link-input.v1` is the input manifest used before constructing `LinkedProgram`.

Required top-level keys:

- `schema`
  - fixed value: `pytra.link_input.v1`
- `target`
- `dispatch_mode`
  - `native | type_id`
- `entry_modules`
- `modules`

Optional top-level key:

- `options`
  - target/optimizer-specific object; unknown keys may be preserved transparently

Required keys in `modules[*]`:

- `module_id`
- `path`
- `source_path`
- `is_entry`

Path contract:

- `path` and `source_path` are canonically POSIX-relative to the manifest directory
- loaders may accept absolute paths for compatibility, but generators output relative paths canonically

Validation rules:

1. `module_id` must be unique
2. `entry_modules` must be a subset of `modules[*].module_id`
3. every `path` must point to a raw `EAST3` document with `kind=Module` and `east_stage=3`
4. raw `meta.dispatch_mode` must match manifest `dispatch_mode`
5. validator normalizes module order by sorted `module_id` to ensure determinism

### 7.3 `link-output.v1`

`link-output.v1` is the canonical output manifest of linker / linked-program optimization.

Required top-level keys:

- `schema`
  - fixed value: `pytra.link_output.v1`
- `target`
- `dispatch_mode`
- `entry_modules`
- `modules`
- `global`
- `diagnostics`

Required keys in `modules[*]`:

- `module_id`
- `input`
- `output`
- `source_path`
- `is_entry`

Required keys in `global`:

- `type_id_table`
- `call_graph`
- `sccs`
- `non_escape_summary`
- `container_ownership_hints_v1`

Required keys in `diagnostics`:

- `warnings`
- `errors`

Rules:

1. `modules[*].output` points to linked-module output
2. tables under `global` are required even when empty
3. `link-output.v1` is the canonical source of global tables for backends and `ProgramWriter`

### 7.4 Linked Module Schema

A linked module still uses `kind=Module` and `east_stage=3`.
The added canonical metadata is `meta.linked_program_v1`.

Required keys in `meta.linked_program_v1`:

- `program_id`
- `module_id`
- `entry_modules`
- `type_id_resolved_v1`
- `non_escape_summary`
- `container_ownership_hints_v1`

Supplemental rules:

1. `meta.dispatch_mode` remains required and must not conflict with `meta.linked_program_v1`
2. function/call-level materialized summaries may reuse existing `meta` contracts
3. `meta.linked_program_v1` is required in linked modules and forbidden in raw `EAST3`

## 8. CLI / Route Policy

Canonical route:

- `py2x.py`
  - can output raw `EAST3` modules plus `link-input.json`
- `eastlink.py`
  - reads `link-input.json` and writes `link-output.json` plus linked modules
- `east2x.py`
  - accepts either a raw single `Module` or `link-output.json`

Minimum behavior rules:

1. `--link-only` writes only `link-output.json` plus linked modules
2. `--object-dispatch-mode` is fixed before raw `EAST3`, and the linker only validates consistency
3. debug/restart routes also treat `link-input.v1` / `link-output.v1` as canonical
4. global passes may only use the modules enumerated in `link-input.v1` / `link-output.v1`; they must not extend closure by rereading `source_path` or import statements
5. `NonEscapeInterproceduralPass` may only use closure information provided by linker/materializer metadata such as `meta.non_escape_import_closure`; if absent, treat it as unresolved fail-closed

## 9. Implementation-Mode Guidance

### 9.1 Daily operation

- use in-memory `LinkedProgramLoader + LinkedProgramOptimizer`
- do not write raw/linked artifacts on every run

### 9.2 Debug / CI

- materialize raw `EAST3`, `link-input.v1`, `link-output.v1`, and linked modules when reproducibility matters

## 10. Error Contract

Fail with an explicit error when:

- `module_id` is duplicated
- `dispatch_mode` is inconsistent
- raw input is not `kind=Module` / `east_stage=3`
- linked output is missing required global tables
- unresolved whole-program requirements remain for backend consumption

## 11. Acceptance Criteria

- same input set yields the same `link-output.v1`
- linked modules remain `east_stage=3`
- global summaries live in `link-output.v1` and `meta.linked_program_v1`
- backends can emit from linked modules without rebuilding whole-program state
- restart/debug flow works through `py2x -> eastlink -> east2x`

## 12. Related

- [spec-east.md](./spec-east.md)
- [spec-east3-optimizer.md](./spec-east3-optimizer.md)
- [spec-make.md](./spec-make.md)
- [spec-runtime.md](./spec-runtime.md)
