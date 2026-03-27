<a href="../../ja/spec/spec-cpp-list-reference-semantics.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# C++ List Reference Semantics (Ref-First Canonical Contract)

This document defines the final ref-first contract for mutable `list` in the C++ backend, and the only cases where it is allowed to fall back from that contract.

## 1. Objectives

- Fix `rc<list<T>>` as the canonical internal representation for mutable `list`.
- Limit generation of `list<T>` values to ABI-adapter boundaries or optimizer-proven cases.
- Make the aliasing, mutation, and boxing rules explicit for regression decisions.

## 2. Terms

- **ref-first**
  - preserve mutable lists as shared references first, then lower to values only when explicitly allowed
- **ABI adapter**
  - a boundary where `list<T>` values may be created temporarily, such as `@extern`, `Any`/`object`, or compatibility APIs
- **optimizer-only value lowering**
  - value lowering allowed only after proof over mutation, aliasing, escape, call graph, and SCC
- **legacy value model**
  - REMOVED. Was once available as a rollback compatibility mode via `--cpp-list-model value`.
- **alias**
  - sharing the same list object, such as `b = a`

## 3. Scope

This specification covers:

- typed mutable lists in backend internals
- argument/return paths
- attribute storage
- subscripting
- iteration
- helper/boxing boundaries

It does not cover `dict`, `set`, or `str` reference model migration (separate task).

## 4. Canonical Contract

- The canonical internal form for mutable `list` is `rc<list<T>>`.
- Alias sharing must be preserved first across assignment, destructive mutation, argument passing, returns, attribute storage, iteration, and subscripting.
- The backend must not generate `list<T>` as the default internal path.
- The emitter must not choose `list<T>` value form merely because:
  - the list is concretely typed
  - it is a local variable
  - aliases are not obvious
  - the sample output would look shorter

## 5. Allowed Exceptions for `list<T>` Values

### 5.1 ABI-adapter only

Keeping `list<T>` value helpers is allowed only at ABI boundaries such as:

- argument/return adapters for `@extern`
- `Any` / `object` boxing and unboxing boundaries
- narrowly scoped compatibility helpers at ABI boundaries

Even there, value helpers must not leak back into the backend's main internal path.

### 5.2 Optimizer-only value lowering

Value lowering is allowed only when the optimizer proves it safe.

Minimum proof requirements:

- mutation analysis
- alias analysis
- escape analysis
- fixed call graph / SCC

Correctness must still hold under ref-first semantics; value lowering is purely an optimization.

## 6. Alias / Mutation Contract

- `a = b` must preserve aliasing first.
- Destructive operations such as `append`, `extend`, `pop`, `insert`, `clear`, `sort`, and `reverse` must operate on the shared referenced list.
- Attribute fields storing mutable lists must preserve ref-first semantics.
- Returning a mutable list from a function must keep ref-first semantics unless the path is an ABI adapter or an optimizer-proven value-lowering path.

## 7. Subscript / Iteration Contract

- `xs[i]`, `xs[i:j]`, `for x in xs`, `enumerate(xs)`, and `reversed(xs)` must all treat `xs` as ref-first by default.
- Temporary call results such as `make()[0]` or `for x in make()` must not silently bypass the ref-first contract.
- If an adapter is required for a temporary handle, insert it explicitly and only at the required boundary.

## 8. PyListObj Lifetime / Iter Contract

- `PyListObj::py_iter_or_raise()` returns an iterator referencing the owner list object, not a snapshot of its values.
- The iterator holds the owner list's lifetime. If the owner reference expires, iteration stops.
- Elements appended via `py_append` during iteration are reflected in the iteration result as long as they fall within the unvisited range.
- `py_try_len` and `py_truthy` are evaluated against the current state of the owner list object.

## 9. Boxing / Dynamic Boundary Contract

- Converting typed lists into `object` / `Any` must be treated as a boundary.
- Boxing/unboxing helpers may construct value forms, but the emitter must not reuse those helpers as the default internal representation path.
- Crossing into unresolved or dynamically typed paths must fail closed and stay ref-first unless the boundary explicitly requires ABI normalization.

## 10. Fail-Closed Rules

Treat the following as fail-closed:

- unresolved aliasing
- unresolved mutation
- unresolved escape
- unresolved call targets
- `Any` / `object` / unknown helper boundaries

In these cases the backend must keep the list in the ref-first representation.

## 11. Boundary Helpers

Helpers such as:

- `make_object(const rc<list<T>>& values)`
- `obj_to_rc_list<T>`
- `obj_to_rc_list_or_raise<T>`
- `py_to_rc_list_from_object<T>`
- `py_to_typed_list_from_object<T>`

must remain boundary helpers only.

- Do not reuse them as the default internal representation choice inside the emitter.
- Designs that widely insert `rc_list_ref(...)` or `list<T>(...)` just for internal calls, returns, or locals are treated as incomplete implementation under this spec.

## 12. Legacy Rollback Contract (Removed)

- `--cpp-list-model value` has been removed. `pyobj` (ref-first) is the only mode.
- The old legacy value model (`list<T>` as a value type, copy-on-assignment) has been fully deleted.

## 13. Acceptance Criteria

The C++ backend satisfies this specification only if:

- representative aliasing/mutation fixture cases (`a = b` followed by `append`/`pop`) produce results matching Python
- `check_py2cpp_transpile` / C++ smoke / sample parity all pass
- differences remaining during transition are recorded in the decision log of the plan document as "case name + difference detail"

## 14. Future Extension

This ref-first principle is not `list`-specific; the same approach will eventually be applied to `dict`, `set`, and `bytearray`. However, the concrete contracts and regression criteria in this document are limited to `list`.
