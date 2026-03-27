<a href="../../ja/plans/p2-runtime-helper-generics-under-linked-program.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P2 Proposal: Introduce Helper Generics for Linked Runtime

Last updated: 2026-03-08

Related:
- [p2-runtime-sot-linked-program-integration.md](./p2-runtime-sot-linked-program-integration.md)
- [p1-runtime-abi-decorator-for-generated-helpers.md](./archive/20260308-p1-runtime-abi-decorator-for-generated-helpers.md)
- [p1-cpp-py-runtime-core-slimming.md](./archive/20260308-p1-cpp-py-runtime-core-slimming.md)
- [../spec/spec-template.md](../spec/spec-template.md)

Notes:

- This is an unscheduled design memo and is not yet queued in `docs/ja/todo/index.md`.
- Its purpose is to preserve the design context for “how to handle generic helpers after linked-runtime integration.”
- It is not an instruction to implement immediately.

Background:
- As long as runtime SoT is emitted as pre-generated artifacts, practical work needs `@abi` to give helper boundaries a fixed ABI.
- If runtime SoT can instead be integrated into a linked program as ordinary modules, helpers can be optimized on the same footing as user code.
- In that model, writing helpers such as `str.join`, `dict.keys`, or `take` as pure-Python generic helpers becomes much more attractive because it reduces `object` fallback and target-specific handwritten helpers.
- In the current spec, `typing.TypeVar` is annotation-only and does not provide generic/template functionality.
- Therefore this proposal should be treated as “small, runtime-helper-only function generics” rather than a full language-wide template design.

Goal:
- Make linked runtime helpers easier to write in pure Python by allowing generic helpers over `list[T]`, `dict[K, V]`, `tuple[T, U]`, and similar shapes.
- Keep those helpers as ordinary linked-program modules while still allowing monomorphization/specialization based on concrete use sites.
- Further reduce the need for `@abi` and remove handwritten value/ref adapters where whole-program reasoning is sufficient.
- Make it easier to move collection/string helpers out of `py_runtime` and back into SoT.

Scope:
- Generic syntax for runtime/internal helper modules
- Generic helper instantiation at the linked-program stage
- Specialized helper output for the C++ backend
- Type-parameter analysis limited to runtime helpers
- Responsibility boundaries in docs/spec

Out of scope:
- Exposing general-purpose generics/templates to user programs
- Generic classes, protocols, or higher-kinded types
- Generic methods or nested generic functions
- General compile-time branching features
- Simultaneous support across all backends
- Full implementation of the older `spec-template` draft

Acceptance criteria for future implementation:
- Rank-1 generic functions can be written for linked runtime helpers.
- Concrete type tuples are collected from runtime-helper use sites and deterministically materialized at the linked-program stage.
- The C++ backend can emit specialized helpers without collapsing to `object`.
- Representative helpers over `list[T]`, `dict[K, V]`, and `tuple[T, U]` can live in pure-Python SoT.
- `@abi` is no longer mandatory for generic helpers in general and is reduced to external/public/prebuilt boundaries.

## 1. The Core Problem

Even if runtime helpers are integrated into the linked program, the design is still awkward without generics:

- Writing helpers over `list[T]` with `object` loses type precision.
- Handwriting one helper per concrete type (`list[str]`, `list[int]`, `list[Token]`, ...) makes SoT noisy.
- That pressure pushes collection helpers back into `native/core`.

In other words, moving runtime helpers back into pure-Python SoT really needs both:

- linked runtime integration
- helper-limited generics

## 2. Intended Scope

This proposal deliberately targets only “small generics.”

### 2.1 Allowed initially

- top-level function generics
- rank-1 type parameters
- simple type parameters such as `T`, `K`, `V`, `U`
- `list[T]`, `dict[K, V]`, `set[T]`, `tuple[T, U]`
- monomorphization at the linked-program stage

### 2.2 Not allowed initially

- generic classes
- constrained `TypeVar`
- variance
- protocol / trait bounds
- advanced inference for generic recursion
- direct native-template emission per backend

## 3. What Kind of Helpers Benefit

Examples:

```python
@template("T")
def py_head(xs: list[T]) -> T:
    return xs[0]
```

```python
@template("T")
def py_take(xs: list[T], n: int) -> list[T]:
    out: list[T] = []
    i = 0
    while i < n and i < len(xs):
        out.append(xs[i])
        i += 1
    return out
```

```python
@template("K", "V")
def py_dict_keys(d: dict[K, V]) -> list[K]:
    out: list[K] = []
    for k in d:
        out.append(k)
    return out
```

If the linked-program stage can specialize these per concrete type tuple, they become straightforward specialized helpers for C++.

## 4. Relationship to `@abi`

This proposal does not reject `@abi`, but it changes its role.

### 4.1 Where `@abi` becomes less necessary

- pure-Python runtime helpers
- helper calls over `list/dict/set/bytearray`
- ordinary user-code-to-helper calls

These become ordinary intra-program calls, so whole-program optimization can decide ref/value lowering instead of forcing a helper ABI first.

### 4.2 Where `@abi` still remains useful

- prebuilt runtime artifacts
- external/native helpers
- public helper APIs whose boundary must remain fixed

So `@abi` naturally shrinks into an escape hatch for fixed-boundary cases instead of the primary way to express generic helpers.

## 5. Where to Instantiate

The most important design point is this: specialization should happen at the linked-program stage, not before `emit-runtime-*`.

Reasons:

- concrete type tuples are visible only once user-code call sites are known
- runtime helpers and user modules can be analyzed in the same call graph
- unused specializations do not need to be emitted
- C++ decisions such as ref-first versus value-lowering can be delayed until after specialization

Conceptually:

```text
runtime helper generic definition
user module call sites
  -> LinkedProgramLoader
  -> generic helper specialization collector
  -> helper monomorphization
  -> global optimizer
  -> backend lower / emit
```

## 6. Syntax Direction

Longer term this must align with `spec-template`, but for helper-only v1 the canonical direction is:

### 6.1 `@template("T")` family (canonical)

```python
@template("T")
def py_head(xs: list[T]) -> T:
    return xs[0]
```

Pros:

- aligns with the template-spec direction
- extends naturally to user-facing templates later

Cons:

- slightly heavier than ideal for tiny runtime helpers

### 6.2 `TypeVar`-only notation (rejected)

```python
T = TypeVar("T")

def py_head(xs: list[T]) -> T:
    return xs[0]
```

Pros:

- more Python-like
- convenient for small helper code

Cons:

- `TypeVar` is currently annotation-only in the spec
- declaration-site generic intent is too implicit
- it blurs the line between runtime-only generics and future user-facing generics

As of 2026-03-08 this option is rejected. For helper v1, the key requirement is an explicit function-scoped type-parameter declaration, so the canonical syntax is `@template("T", ...)`. If explicit instantiation is added later, it should extend the same decorator family with `@instantiate(...)`.

## 7. Required Linked-Program Mechanisms

### 7.1 Specialization collector

- find helper-generic definitions
- collect concrete type tuples per call site
- build a deterministic specialization list
- treat `FunctionDef.meta.template_v1` as the canonical entry point instead of raw decorators

### 7.2 Monomorphization rule

- `py_head[T]` + `list[str]` -> `py_head__str`
- `py_dict_keys[K, V]` + `dict[str, int]` -> `py_dict_keys__str__int64`

The names do not need to be user-facing, but they must be deterministic and diff-friendly.

### 7.3 Optimization integration

- include specialized helper bodies in the global optimizer input
- treat helper specializations as ordinary nodes for `type_id`, call graph, non-escape, and ownership reasoning

## 8. What This Buys for C++

### 8.1 Benefits

- less `object` fallback
- `list[T]` / `dict[K, V]` helpers can move back into pure-Python SoT
- fewer collection helpers need to remain in `py_runtime`
- list ref-first optimization can be applied to specialized helpers too

### 8.2 Cautions

- even after specialization, mutable-container internals should remain ref-first
- the mere existence of `list[T]` helpers is not a reason to force value helpers
- it is too early to bias the design toward direct native-template output just because C++ could support it

## 9. Staged Rollout

### Phase 1: design only

- settle the syntax direction for helper-limited generics
- choose `@template` versus `TypeVar`
- define the boundary with linked-runtime integration

### Phase 2: helper-only monomorphization

- add collector + monomorphization only for runtime-helper modules
- smoke it first in C++

### Phase 3: optimizer integration

- treat helper specializations as ordinary global-optimizer nodes
- lock in “no `object` fallback” for representative helpers

### Phase 4: expand generic runtime helpers

- move `list`, `dict`, and `tuple` helpers back into SoT
- audit which helpers no longer need `@abi`
