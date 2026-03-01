# Stdlib Signature Source-of-Truth Specification

This document defines the contract for `P0-STDLIB-SOT-01`: making `pytra/std` the single source of truth for type specifications.

## 1. Purpose

- Remove hardcoded standard-library specs scattered on the compiler side (`core.py`).
- Consolidate the source of truth for type specs into type annotations in `pytra/std/*.py`.
- Make the compiler operate as a "consumer" rather than a "spec owner".

## 2. Source-of-Truth and Reference Boundaries

- Source of truth: Return annotations of top-level functions and class methods in `src/pytra/std/*.py`.
- Reference layer: `src/pytra/compiler/stdlib/signature_registry.py`.
- Consumer side: `src/pytra/compiler/east_parts/core.py` retrieves types through the reference-layer API.

Prohibited:

- Hardcoding return types in `core.py`, such as `perf_counter -> float64`.
- Keeping separate definitions for the same symbol in both `pytra/std` and compiler.

## 3. Retrieval Unit

Initial retrieval units are as follows.

- Function return type: `lookup_stdlib_function_return_type(function_name)`
- Method return type: `lookup_stdlib_method_return_type(owner_type, method_name)`

Type representations are normalized in EAST-compatible form (e.g., `float -> float64`, `int -> int64`, `list[int] -> list[int64]`).

## 4. Fail-Closed

- If the reference layer cannot retrieve a type, callers must not fallback to implicit defaults and must keep it as `unknown`.
- When adding new support, always update annotations on the `pytra/std` side first.

## 5. Initial Target Scope

- Resolving return type of `perf_counter` (`pytra/std/time.py`).
- Retrieving major method return types of `Path` class (`pytra/std/pathlib.py`).

## 6. Verification

- Pin reference-layer resolution results in `test/unit/test_stdlib_signature_registry.py`.
- Pin `resolved_type` of `perf_counter` calls in `test/unit/test_east_core.py`.
