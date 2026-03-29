<a href="../../ja/spec/spec-east.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# EAST Specification (Implementation-Aligned)

This document is the unified source of truth for EAST, aligned with the current implementation in `src/toolchain/misc/east.py` and `src/toolchain/misc/east_parts/`.

It integrates the previous EAST2 spec and the stage responsibilities that had been split across EAST1 / EAST2 / EAST3 documents. Legacy stage-by-stage notes are archived. Linked-program details that are now owned by the linker are documented in `spec-linker.md`.

## 1. Objective

EAST is Pytra's implementation-oriented intermediate representation family.
It exists because Python's built-in `ast` cannot preserve the information Pytra needs for downstream compilation, especially comments, frontend-only normalization results, import binding metadata, and target-oriented lowering contracts.
To close that gap, Pytra introduced its own parser-side normalization and EAST as the canonical interchange format between analysis, lowering, linking, and emitters.

## 2. Top-Level Structure

Top-level modules use `kind=Module`.

Typical EAST2 module fields:

- `kind`: always `Module`
- `east_stage`: `2`
- `schema_version`
- `source_path`
- `source_span`
- `body`
- `main_guard_body`
- `renamed_symbols`
- `meta.import_bindings`
- `meta.qualified_symbol_refs`
- `meta.import_modules`
- `meta.import_symbols`
- `meta.dispatch_mode`

Linked EAST3 still uses `kind=Module`, but `east_stage=3`.
A linked program may additionally carry `meta.linked_program_v1`.
Synthetic helper modules emitted by the linker may additionally carry `meta.synthetic_helper_v1`.

### 2.1 Import metadata

`ImportBinding` records normalized import bindings.
Typical fields are:

- `local_name`
- `source_module`
- `source_symbol`
- `import_kind`
- `runtime_module_id` (optional)
- `runtime_symbol` (optional)

`QualifiedSymbolRef` records qualified references discovered during analysis.
Typical fields are:

- `module_name`
- `symbol_name`
- `runtime_module_id` (optional)
- `runtime_symbol` (optional)

## 3. Syntax Normalization Contract

EAST is not a direct dump of Python syntax. The frontend normalizes several Python constructs into a compilation-friendly shape.

Key normalizations:

- `if __name__ == "__main__": ...` is split into `main_guard_body`.
- Duplicate symbols and reserved names are renamed through `renamed_symbols`.
- The reserved-name set includes `main`, `py_main`, and `__pytra_main`.
- `for ... in range(...)` is normalized through `ForRange` / `RangeExpr`.
- Raw `Call(Name("range"), ...)` must not survive into downstream stages where range semantics are already normalized.
- `from __future__ import annotations` is accepted as a frontend-only directive.
- Other `__future__` imports fail closed unless they are explicitly supported.

## 4. Common Node Attributes

Expression-like nodes may include the following common attributes:

- `kind`
- `source_span`
- `resolved_type`
- `type_expr`
- `borrow_kind`
- `casts`
- `repr`

Function-like nodes may additionally include:

- `decorators`
- `meta.runtime_abi_v1`
- `meta.template_v1`
- `meta.template_specialization_v1`

Assignment-like nodes may additionally include:

- `meta.extern_var_v1`

Class-like nodes may additionally include:

- `meta.nominal_adt_v1`

### 4.1 Metadata lanes

- `runtime_abi_v1` describes the ABI contract after frontend resolution.
- `template_v1` describes template declarations.
- `template_specialization_v1` describes specialization metadata normalized for linker ownership.
- `extern_var_v1` marks extern-backed variable contracts.
- `nominal_adt_v1` marks closed nominal ADT families used by `match` analysis.

## 5. `leading_trivia` Pass-Through Directives

EAST preserves selected comment trivia that has compilation meaning.
The current pass-through directives are C++-oriented comment forms such as:

- `# Pytra::cpp ...`
- `# Pytra::pass ...`
- block begin/end variants of the same family

These survive as `leading_trivia` so downstream stages can preserve or interpret them without reparsing source comments.

## 6. Nominal ADT and `match` v1

The current nominal ADT / pattern-match contract uses the following node families:

- `Match`
- `MatchCase`
- `VariantPattern`
- `PatternBind`
- `PatternWildcard`

`meta.match_analysis_v1` carries the frontend analysis result.
Typical fields are:

- `schema_version`
- `family_name`
- `coverage_kind`
- `covered_variants`
- `uncovered_variants`
- `duplicate_case_indexes`
- `unreachable_case_indexes`

This metadata is the canonical source for exhaustiveness and reachability decisions at later stages.

## 7. Type System

EAST uses canonical semantic types rather than preserving arbitrary annotation spelling.
Normalization includes:

- `bytes` / `bytearray` -> `list[uint8]`
- `pathlib.Path` -> `Path`

### 7.1 `TypeExpr`

The canonical `TypeExpr` schema includes:

- `NamedType`
- `GenericType`
- `OptionalType`
- `UnionType`
  - `union_mode=general|dynamic`
- `DynamicType`
- `NominalAdtType`

When both are present, `type_expr` has higher authority than legacy `resolved_type` text.

### 7.2 `JsonValue`

`JsonValue` is treated as a nominal closed-ADT lane rather than an open dynamic blob.
The canonical semantic-tag families currently include:

- `json.loads`
- `json.loads_obj`
- `json.loads_arr`
- `json.value.as_obj`
- `json.value.as_arr`
- `json.value.as_str`
- `json.value.as_int`
- `json.value.as_float`
- `json.value.as_bool`
- `json.obj.get`
- `json.obj.get_obj`
- `json.obj.get_arr`
- `json.obj.get_str`
- `json.obj.get_int`
- `json.obj.get_float`
- `json.obj.get_bool`
- `json.arr.get`
- `json.arr.get_obj`
- `json.arr.get_arr`
- `json.arr.get_str`
- `json.arr.get_int`
- `json.arr.get_float`
- `json.arr.get_bool`

## 8. Type Inference and Resolution Rules

The implementation currently infers or normalizes types for at least these node families:

- `Name`
- `Constant`
- `List`
- `Set`
- `Dict`
- `Tuple`
- `BinOp`
- `Subscript`
- `Call`
- `ListComp`
- `BoolOp`

Additional current rules:

- `range`-derived constructs are normalized before backend-facing stages.
- Built-in lowered calls may use `lowered_kind: BuiltinCall`.
- Dynamic-producing helpers such as `dict.get`, `dict.pop`, `dict.setdefault`, and `list.pop` may mark `yields_dynamic`.

## 9. EAST3 Runtime-Resolution Boundary

EAST3 is the canonical boundary for runtime/stdlib call resolution.
The following fields belong to the EAST3 contract:

- `runtime_module_id`
- `runtime_symbol`
- `runtime_call`
- `resolved_runtime_call`
- `resolved_runtime_source`
- `semantic_tag`

Backends and emitters must not branch directly on ad hoc runtime implementation symbols once these canonical fields exist.
Resolution priority, backend API usage, and forbidden direct-symbol branching are enforced by policy and CI.

Guardrail commands:

- `python3 tools/check/check_emitter_runtimecall_guardrails.py`
- `python3 tools/check/check_emitter_forbidden_runtime_symbols.py`
- `python3 tools/check/check_noncpp_east3_contract.py`

## 10. Casts and Argument Usage

`casts` use the canonical JSON-friendly cast-spec shape defined by the implementation.
`arg_usage` records argument-consumption intent for later lowering and emitter decisions.
Both are compilation contracts, not presentation metadata.

## 11. Supported Statements and Pre-Collection

EAST supports the statement families needed by the current compiler, including class/function definitions, assignments, control flow, imports, match constructs, and frontend-normalized range loops.

Before full lowering, the compiler pre-collects class information needed for inheritance, nominal ADT interpretation, and dispatch normalization.

## 12. Error Contract

EAST-building stages fail closed.
Unsupported constructs or schema mismatches must be reported as explicit compiler errors rather than silently degraded IR.
Human-readable dumps are for diagnosis only and do not replace the JSON schema contract.

## 13. Known Constraints

- Comment fidelity is selective rather than universal; only semantically meaningful trivia is preserved.
- Some Python constructs are intentionally rejected before EAST3 if Pytra cannot assign a stable cross-target contract.
- Backend behavior must not depend on legacy pre-EAST3 symbol heuristics.

## 14. Validation Status

This document is implementation-aligned.
If code and documentation diverge, the implementation in `src/toolchain/misc/east.py` and `src/toolchain/misc/east_parts/` wins until the document is updated.

## 15. Current Stage Structure (2026-02-24)

Current pipeline:

- EAST1
- EAST2
- EAST3

Current CLI contract:

- `pytra-cli.py --target cpp` accepts only `--east-stage 3`.
- The eight non-C++ converters still keep `--east-stage 2` as a compatibility mode, with a warning.
- `meta.dispatch_mode` semantics are applied exactly once during `EAST2 -> EAST3`.

### 15.1 Stage responsibilities

Current implementation ownership is split as follows:

- EAST core structures: `src/toolchain/misc/east_parts/core.py`
- EAST1 build/normalization: `src/toolchain/misc/east_parts/east1.py`
- EAST2 shared IR shaping: `src/toolchain/misc/east_parts/east2.py`
- EAST2 -> EAST3 lowering: `src/toolchain/misc/east_parts/east2_to_east3_lowering.py`
- EAST3 finalized compiler-facing form: `src/toolchain/misc/east_parts/east3.py`
- CLI integration: `src/toolchain/misc/transpile_cli.py`

Canonical destination after migration:

- `src/toolchain/compile/core.py`
- `src/toolchain/compile/east1.py`
- `src/toolchain/compile/east2.py`
- `src/toolchain/compile/east2_to_east3_lowering.py`
- `src/toolchain/compile/east3.py`
- `src/toolchain/frontends/transpile_cli.py`

## 16. Invariants

- EAST modules always use stable schema-versioned JSON shapes.
- EAST2 is the shared depythonized IR boundary.
- EAST3 is the canonical runtime-resolution boundary.
- Linker-owned synthetic modules must be explicitly marked in module metadata.
- Backend code must consume canonical EAST fields rather than reconstructing semantics from source spelling.

## 17. Integrated Pipeline

The integrated pipeline is:

1. parse and frontend normalization
2. build EAST1
3. normalize into EAST2 shared IR
4. lower `EAST2 -> EAST3` where required
5. link linked-program metadata where applicable
6. emit target code from canonical EAST contracts

## 18. Linked-Module Metadata Contract

Linked modules may add `meta.linked_program_v1` and helper-specific synthetic metadata, but they do not change the top-level `Module` contract.
Linker-added metadata must be explicit, versioned, and non-ambiguous about ownership.

## 19. EAST1 Build Boundary

`core.py`, `east1_build.py`, `east1.py`, `pytra-cli.py --target cpp`, and `transpile_cli.py` together define the current EAST1 build boundary.
The source of truth for import-graph analysis is `src/toolchain/frontends/east1_build.py`, while the compiler-side `transpile_cli.py` acts as a wrapper entry.

Acceptance conditions for EAST1 are:

1. source spans are attached consistently
2. import bindings are normalized
3. `main_guard_body` is split
4. reserved-name renaming is deterministic
5. comments required for pass-through directives survive in `leading_trivia`
6. unsupported constructs fail closed before later stages depend on them

## 20. Migration Phases

Migration keeps current implementation paths authoritative while gradually moving the stable ownership boundary toward `src/toolchain/compile/*` and `src/toolchain/frontends/*`.
During migration, duplicated responsibility across old and new paths is not allowed to become semantically divergent.

## 21. EAST Acceptance Criteria

A stage is accepted only when:

- schema shape is stable and versioned
- required metadata is produced deterministically
- unsupported constructs fail closed
- downstream stages no longer need ad hoc source reconstruction
- canonical guardrails pass in CI

## 22. Minimum Verification Commands

Minimum verification commands for EAST boundary work:

- `python3 tools/check/check_emitter_runtimecall_guardrails.py`
- `python3 tools/check/check_emitter_forbidden_runtime_symbols.py`
- `python3 tools/check/check_noncpp_east3_contract.py`
- `python3 tools/check/check_east3_golden.py`

## 23. Future Extensions

Planned future extensions include richer depythonized contracts, further linker-owned specialization metadata, and continued reduction of legacy compatibility paths.
All additions must preserve fail-closed behavior and schema-version clarity.

## 24. EAST2 Shared IR Contract (Depythonization Draft)

EAST2 is the shared neutral IR boundary.
Its role is to carry cross-target semantics without leaking Python-surface details that later stages should not have to reinterpret.

Principles:

- node kinds must be target-neutral where practical
- operators, types, and metadata must use canonical names
- Python-only surface constructs that require target-specific reinterpretation must not cross the EAST2 boundary unchanged
- diagnostics must fail closed rather than silently accepting partially normalized IR
- `EAST2 -> EAST3` is responsible for one-way lowering into runtime-resolved contracts, not for preserving multiple competing interpretations

Forbidden at the EAST2 boundary:

- unresolved raw runtime implementation symbol branching
- backend-specific emitter assumptions encoded as frontend syntax leftovers
- unnormalized `range(...)` calls in places where `RangeExpr` / `ForRange` should exist
- ambiguous metadata ownership between frontend, linker, and emitter
