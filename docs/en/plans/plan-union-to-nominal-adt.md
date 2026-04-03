# Plan: Migrate union types to nominal ADT-based representation

## Background

The current EAST3 lowering degrades union types like `int | str` to `object` and processes them via boxing / unboxing / type_id dispatch. This came from using C++'s `object` implementation (`{type_id, rc<RcObject>}`) as the standard for all languages, and it causes the following problems:

- Massive generation of box/unbox nodes
- Complex auxiliary mechanisms: `yields_dynamic` / `Unbox` / `OBJ_ITER_INIT`, etc.
- Emitter collapses every time `JsonVal` (= `Any` = `object`) appears in selfhost
- Side effects such as hacking the return type of `dict.items()` to `list[tuple[K,V]]`

## Approach

**Do not degrade union types to `object`; use the optimal representation for each language.**

### Union representation by language

| Language group | Union representation | Notes |
|---|---|---|
| **Rust, Swift, Kotlin, Scala, Nim** | enum / tagged union | Native support |
| **Zig** | tagged union | Recursive types require pointers. RC management for recursive ADTs is a challenge, same as C++ |
| **C++** | `std::variant` (non-recursive only) or inheritance | Recursive types break RC management with `std::variant` + pointers. Recursive ADTs use inheritance-based or the existing `object` implementation |
| **TS/JS** | union type directly | Language supports union natively |
| **C#, Java, Dart** | sealed class / abstract record | Exhaustiveness check possible via pattern matching |
| **Go** | interface + struct | Boilerplate-heavy but expressible |
| **Ruby, Lua, PHP, PowerShell, Julia** | Dynamic types (as-is) | All variables are already equivalent to object, so no problem |

### EAST3 handling

- EAST3 already preserves `UnionType` / `NominalAdtType` (and continues to do so)
- **Stop** having lowering degrade them to `object`
- The emitter reads `UnionType` and generates the language-specific representation
- boxing / unboxing only occurs at `object` boundaries (only when `Any` type annotation is present)

### anonymous union → nominal ADT conversion

An anonymous union like `int | str` can be converted to a nominal ADT in the EAST3 optimizer or linker:

```python
# Code written by the user
x: int | str = ...

# Internally generated ADT
# (not visible to the user)
enum __Union_int_str {
    Int(int64),
    Str(str),
}
```

However, this is not needed for all languages (TS can use anonymous union directly). Give the language profile a `union_strategy: "nominal_adt" | "native_union" | "object_fallback"` that the emitter references.

### Constraint for recursive types

Recursive ADTs like `JsonVal` that contain themselves require pointers in C++ and Zig:

- C++: Using `std::variant<..., std::unique_ptr<JsonVal>>` breaks RC management (`unique_ptr` cannot be shared; `shared_ptr` requires indirect access, making the emitter cumbersome)
- Zig: Same pointer requirement; poor compatibility with RC
- Rust: `Box<JsonVal>` is fine (ownership is clear)

Options for C++ / Zig with recursive ADTs:

1. **Inheritance-based**: `class JsonVal { virtual ~JsonVal(); }` + derived classes. dispatch via vtable. RC uses `shared_ptr<JsonVal>` uniformly
2. **Keep the existing `object` implementation**: Process only recursive ADTs with the `object`-based approach (`type_id` + `rc<RcObject>`)
3. **Emulate Rust's approach**: `std::variant<..., std::unique_ptr<JsonVal>>` + arena allocator for lifetime management

In practice, the pragmatic approach is: use `std::variant` for non-recursive unions (`int | str`, `str | None`), and use inheritance-based or the existing `object` for recursive ADTs (`JsonVal`). The reason `std::variant` could not be adopted wholesale in the previous analysis was this RC problem with recursive types.

## Relationship to the dict.items() iterable problem

The problem of `dict.items()` being hacked to `list[tuple[K,V]]` is orthogonal to this approach:

- union / ADT improvement: stop degrading `int | str` to `object` → fewer box/unbox
- iterable improvement: treat `dict.items()` as the correct iterable → `list` hack disappears

Both are necessary but can proceed independently.

## Incremental Migration

### Phase 1: Confirm EAST3 union preservation

- EAST3 correctly preserving `UnionType` has been confirmed
- `dict[str, str | int | None]` becomes `UnionType([str, int64, None])` (confirmed)
- Identify where lowering degrades to `object` (lower.py line 597, lines 2042-2075)

### Phase 2: Incrementally remove `object` degradation from lowering

- First, stop treating `JsonVal` nominal ADT as equivalent to `object` (lower.py:910)
- Next, change boxing's `resolved_type="object"` to preserve the union type
- Address iter boundary's `object` together with the iterable improvement

### Phase 3: Emitter union support

- C++ emitter: generate `std::variant<T1, T2, ...>` for `UnionType`
- Rust emitter: generate `enum` for `UnionType`
- TS emitter: output `T1 | T2` directly for `UnionType`
- Go emitter: interface + type switch for `UnionType`
- Dynamically typed languages: no change

### Phase 4: `@template` class support + Iterable

- Implement class templates and enable defining generic iterables like `dict_items<K,V>`
- Define an `Iterable[T]` trait and unify the `for` iteration protocol
- Independent of union/ADT but advancing together further reduces remaining `object` usage

## Acceptance Criteria

- Non-recursive unions are represented by nominal ADTs such as `std::variant` / enum
- Recursive ADTs are also represented as ADTs in each language using pointers / RC / GC (C++ uses `struct { variant<..., rc<vector<Self>>> }`)
- Degradation to `object` is fully prohibited (no entry point because `Any` type annotations are themselves prohibited in Pytra)
- boxing / unboxing nodes disappear
- Fixtures using union types pass compile + run parity in all languages
- Selfhost's `JsonVal` is processed as a nominal ADT rather than `object`
- box/unbox nodes are no longer generated for cases caused by union → object degradation
