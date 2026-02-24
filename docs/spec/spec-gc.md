<a href="../../docs-ja/spec/spec-gc.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# GC Specification

When converting Python code to C++, memory management is required.
This project adopts **reference counting (RC)**.

## Preconditions

- Multithread support is required.
- Circular references are prohibited (prohibited by language specification).
- Weak references are not supported.
- `__del__` is not supported.

## Adopted Strategy

- Management strategy is **RC only** (no tracing GC).
- Each heap object has `ref_count`.
- When `ref_count` reaches 0, release immediately.

## Object Model

- GC targets are reference-type objects (string, list, dict, class instance, etc.).
- Value types (`int`, `double`, `bool`, etc.) are outside RC management.
- All reference types share a common header:
  - `std::atomic<uint32_t> ref_count`
  - `type_id` (for debugging/type checks)

## Basic Operations

- `incref(obj)`:
  - If `obj != nullptr`, do `ref_count.fetch_add(1, std::memory_order_relaxed)`.
- `decref(obj)`:
  - If `obj != nullptr`, do `old = ref_count.fetch_sub(1, std::memory_order_acq_rel)`.
  - Proceed to release only when `old == 1`.
- On release:
  - `decref` each reference field in order (recursive release propagation).
  - Finally `delete` the object itself.

## Rules For Assignment and Container Updates

- Variable assignment `a = b`:
  1. obtain `tmp = b`
  2. `incref(tmp)`
  3. `old = a`
  4. `a = tmp`
  5. `decref(old)`
- Apply the same order for field assignment `obj.x = v` and array/dict element updates.
- Generated code must always apply the same rule so no `decref` leak appears even on exception paths.

## Multithread Specification

- Manage `ref_count` with `std::atomic`.
- RC operations (`incref/decref`) are lock-free atomic updates.
- Structural updates to container internals (list/dict) are protected with separate locks.
- Recommended policies:
  - per-object `std::mutex`, or
  - fine-grained locks in runtime layer (for list and dict)
- Separate responsibilities as: "reference counting with atomics" and "container structure with mutexes".

## Generated-Code API

- `template<class T, class... Args> T* rc_new(Args&&...)`
  - Construct with `ref_count = 1`.
- `void incref(PyObj* obj)`
- `void decref(PyObj* obj)`
- `template<class T> class RcHandle`
  - RAII helper for automatic `incref/decref`.

## Prohibited Items (Detected By Transpiler)

- Assignment patterns creating circular references must be compile errors.
  - e.g., parent-child mutual references, self-references, container insertions that create cycles.
- Direct retention of raw pointers is prohibited; generated code must use RC-managed types only.

## Debug Support

- Enable the following in debug builds:
  - lower-bound checks for `ref_count` (detect invalid negative-direction destruction)
  - double-free detection
  - leak list output at shutdown

## Non-Goals (This Specification)

- tracing GC (mark-sweep, generational, incremental)
- weak references
- `__del__`
- automatic collection of circular references
