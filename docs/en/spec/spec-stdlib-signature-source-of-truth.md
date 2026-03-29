<a href="../../ja/spec/spec-stdlib-signature-source-of-truth.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# Stdlib Signature Source-of-Truth Specification

This document defines the contract for `P0-STDLIB-SOT-01`: making `pytra/std` the single source of truth for type specifications.

## 1. Purpose

- Remove hardcoded standard-library specs scattered on the compiler side (`core.py`).
- Consolidate the source of truth for type specs into type annotations in `pytra/std/*.py`.
- Make the compiler operate as a "consumer" rather than a "spec owner".

## 2. Source-of-Truth and Reference Boundaries

- Source of truth: Return annotations of top-level functions and class methods in `src/pytra/std/*.py`.
- Reference layer: `src/toolchain/misc/stdlib/signature_registry.py`.
- Consumer side: `src/toolchain/misc/east_parts/core.py` retrieves types through the reference-layer API.

Required reference-layer responsibility:

- `signature_registry` is limited to reference concerns (return/method type lookup and import-resolution assistance).
- Final runtime dispatch decisions must be materialized in EAST3 (`runtime_call`, `resolved_runtime_call`, `semantic_tag`), and backends consume only those resolved fields.
- `signature_registry` must not contain backend-specific per-symbol runtime-dispatch rules.

Prohibited:

- Hardcoding return types in `core.py`, such as `perf_counter -> float64`.
- Keeping separate definitions for the same symbol in both `pytra/std` and compiler.
- Hardcoding backend runtime-dispatch strings in `signature_registry` for symbols such as `py_assert_*`, `perf_counter`, `json.loads`, or `write_rgb_png`.

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

- Pin reference-layer resolution results in `tools/unittest/common/test_stdlib_signature_registry.py`.
- Pin `resolved_type` of `perf_counter` calls in `tools/unittest/ir/test_east_core.py`.
