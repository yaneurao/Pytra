# type_id Spec (Single Inheritance, Range Checks)

<a href="../../docs-ja/spec/spec-type_id.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-10B981?style=flat-square">
</a>

This document defines the semantics, allocation rules, and runtime contracts of `type_id` in Pytra.
The primary goal is to unify `isinstance` / `issubclass` behavior across all targets.

## 1. Goals

- Unify `isinstance` / `issubclass` on `type_id`-based runtime APIs.
- Keep results identical across C++ / JS / TS / Rust / C#.
- Avoid name-string-based checks that break under minification/renaming.
- Keep trait/protocol behaviors (`iterable`, `truthy`, `len`) separate from nominal inheritance.

## 2. Non-goals

- Full CPython compatibility for metaclass / ABC / virtual subclass.
- General support for multiple inheritance.
- One-shot migration of all targets at once.

## 3. Terminology

- `type_id`:
  Stable integer type identity at runtime.
- `TypeInfo`:
  Per-`type_id` metadata (`base_type_id`, range, name, traits).
- `trait_id`:
  Behavior capability id (`iterable`, `truthy`, `len`, ...), independent from inheritance.

## 4. Core Design

### 4.1 Single inheritance only

- Each type has `base_type_id: int | None` (0 or 1 base).
- Definitions that imply multiple bases must fail before execution.
- The inheritance graph is a tree/forest (no cycles).
- Parent/child relation is represented by ID range (`type_id_min` / `type_id_max`).

### 4.2 Separate nominal checks from trait checks

- `isinstance(x, T)` checks only nominal inheritance.
- Trait/protocol checks are handled by dedicated runtime slots.
- Trait status must not change nominal `isinstance` results.

### 4.3 No string-name-based dispatch

- Do not use `constructor.name` / RTTI name strings for type checks.
- Use `type_id` only.

## 5. TypeInfo Model

Each `type_id` keeps:

- `type_id: int`
- `name: str` (diagnostics/logging)
- `base_type_id: int | None`
- `type_id_min: int`
- `type_id_max: int`
- `mro_depth: int` (optional)
- `traits: bitset | set[trait_id]`

Notes:

- `type_id_min/max` enables O(1) subtype checks.
- `mro_depth` is optional diagnostic/optimization metadata.

## 6. Validation and Allocation

### 6.1 Validation

At registration time:

1. `base_type_id` must exist.
2. `base_type_id` must not form self/cyclic edges.
3. Single-inheritance constraints must hold.

### 6.2 Range allocation (linker stage)

- `type_id_min/max` is finalized in linker (or equivalent deterministic phase).
- Ordering:
  1. Topological order (base before derived)
  2. Lexicographic FQCN tie-break
- Assignment:
  - DFS from each root.
  - Assign `type_id_min = allocator.next()`.
  - Assign children continuously.
  - Finalize `type_id_max` after all descendants.

Result:

- For every descendant: `parent.min <= child_id <= parent.max`.
- `is_subtype` becomes interval comparison.

### 6.3 Optional debug cross-check

- Debug builds may verify with base-chain traversal.
- Runtime contract remains `type_id_min/max`.

## 7. Runtime API Contract

Targets must provide:

- `py_is_subtype(actual_type_id: int, expected_type_id: int) -> bool`
- `py_isinstance(obj: object, expected_type_id: int) -> bool`
- `py_issubclass(actual_type_id: int, expected_type_id: int) -> bool`

Dispatch mode contract:

- `--object-dispatch-mode=type_id`: these APIs are mandatory canonical path.
- `--object-dispatch-mode=native`: target-native mechanisms are allowed only if observable results match.

Rules:

- `py_isinstance` obtains `obj.type_id` then calls `py_is_subtype`.
- Unknown `expected_type_id`: fail-fast in dev; return `false` in runtime mode.

## 8. Check Algorithm

### 8.1 Default

- O(1) interval check:
  `expected_min <= actual_id <= expected_max`

### 8.2 Fallback

- Debug-only O(depth) base-chain traversal to validate equivalence.

## 9. Dispatch Mode Scope

Common CLI:

- `--object-dispatch-mode {type_id,native}` (default: `native`)

The switch applies to the full object boundary set:

- `isinstance` / `issubclass`
- boxing/unboxing
- iterable/truthy/len/str-related object dispatch

Hybrid mode (partially `type_id`, partially `native`) is not allowed.

## 10. Target Requirements

### 10.1 C++

- `PyObj` holds `type_id`.
- Runtime stores type range table.
- `py_is_subtype` uses range check.

### 10.2 JS/TS

- Objects store `pyTypeId` (symbol key recommended).
- Checks rely on `type_id` only.

### 10.3 Rust

- Runtime keeps `type_id` + range table.
- External behavior follows `py_is_subtype` contract.

## 11. Codegen Rules

- Lower `isinstance` / `issubclass` to runtime API calls.
- Avoid backend-local handwritten type semantics.
- In `EAST3`, type-check semantics are lowered once and backends only map lowered nodes.
- For strict `east_stage=3`, unlowered fallback routes are fail-fast.

## 12. Test Focus

1. Single inheritance: `A <- B <- C`, `isinstance(C(), A)` is true.
2. Non-related types: false.
3. Multiple-inheritance input (`class C(A, B)`) fails before runtime.
4. Interval consistency: `child_id` is inside parent range.
5. JS/TS minification does not change results.
6. Trait separation: trait implementation does not alter nominal `isinstance`.

## 13. Staged Adoption

1. Introduce single-inheritance `TypeInfo` + range checks in runtime.
2. Consolidate `isinstance` / `issubclass` to runtime APIs.
3. Finalize deterministic `type_id_min/max` in linker.
4. Remove backend-local direct type-check logic.
5. Lock cross-target regression tests.

## 14. Related

- `docs-ja/spec/spec-east.md`
- `docs-ja/spec/spec-linker.md`
- `docs-ja/spec/spec-dev.md`
- `docs-ja/spec/spec-boxing.md`
- `docs-ja/spec/spec-iterable.md`
- `docs-ja/plans/p0-typeid-isinstance-dispatch.md`
