<a href="../../ja/spec/spec-cpp-list-reference-semantics.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
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
  - rollback/comparison mode enabled by `--cpp-list-model value`
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

It does not redefine the rollback-only legacy mode except as an explicit exception.

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
- narrowly scoped helpers required for rollback compatibility

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

## 8. Boxing / Dynamic Boundary Contract

- Converting typed lists into `object` / `Any` must be treated as a boundary.
- Boxing/unboxing helpers may construct value forms, but the emitter must not reuse those helpers as the default internal representation path.
- Crossing into unresolved or dynamically typed paths must fail closed and stay ref-first unless the boundary explicitly requires ABI normalization.

## 9. Fail-Closed Rules

Treat the following as fail-closed:

- unresolved aliasing
- unresolved mutation
- unresolved escape
- unresolved call targets
- `Any` / `object` / unknown helper boundaries

In these cases the backend must keep the list in the ref-first representation.

## 10. Boundary Helpers

Helpers such as:

- `make_object(const rc<list<T>>& values)`
- `obj_to_rc_list<T>`
- `obj_to_rc_list_or_raise<T>`
- `py_to_rc_list_from_object<T>`
- `py_to_typed_list_from_object<T>`

must remain boundary helpers only.

- Do not reuse them as the default internal representation choice inside the emitter.
- Designs that widely insert `rc_list_ref(...)` or `list<T>(...)` just for internal calls, returns, or locals are treated as incomplete implementation under this spec.

## 11. Legacy Rollback Contract

- `--cpp-list-model value` exists only for rollback/comparison.
- In the legacy value model, `list<T>` behaves as a value type and `b = a` creates a copy.
- This mode is not the mainline semantic baseline; it is an escape hatch only.

## 12. Acceptance Criteria

The C++ backend satisfies this specification only if:

- representative aliasing/mutation regressions preserve shared list semantics
- helper/boxing boundaries are explicit and limited
- call-returned list paths (`make()[0]`, `make().append(...)`, `for x in make()`) still follow ref-first semantics
- field storage and typed call boundaries preserve handle semantics
- `--cpp-list-model value` remains a clearly separated rollback path

## 13. Future Extension

This specification allows future optimizer-driven value lowering, but only as a proven optimization layered on top of ref-first semantics. It does not permit reintroducing value-first internals as the default backend contract.
