<a href="../../ja/plans/p1-isinstance-narrowing.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-2563EB?style=flat-square">
</a>

# P1-ISINSTANCE-NARROWING: Automatic type narrowing after isinstance

Last updated: 2026-03-27
Status: Completed

## Background

Currently in Pytra, calling methods on union types or nominal ADTs (such as `JsonVal`) requires a manual `cast` after an `isinstance` check.

```python
# Current state: manual cast required
if isinstance(stmt, dict):
    d: dict[str, JsonVal] = cast(dict[str, JsonVal], stmt)
    d.get("key")
```

Similar to TypeScript's type guards and Kotlin's smart casts, we introduce automatic narrowing of `x`'s type to `T` inside an `if isinstance(x, T):` block.

```python
# Proposed: automatic narrowing inside the if block after isinstance
if isinstance(stmt, dict):
    stmt.get("key")  # stmt can be treated as dict[str, JsonVal]
```

## Design

### Where the responsibility lives

Implemented purely as a resolve-stage (EAST2) change.

| Layer | Responsibility |
|---|---|
| **EAST2 (resolve)** | Detect `if isinstance(x, T):` and update `x`'s type environment to `T` inside the if block |
| EAST3 | Retains narrowed type information as-is (no additional work) |
| emitter | Only maps the already-narrowed `resolved_type` (no additional work) |

### Implementation approach

1. The resolver analyzes the condition of an `If` statement and detects `isinstance(x, T)` patterns
2. In the if block's (`body`) type environment, overwrite `x`'s type with `T`
3. `elif isinstance(x, U):` is handled similarly
4. Early return guard: after `if not isinstance(x, T): return`, narrow `x` to `T` for the entire remainder of the function
5. Ternary isinstance: in `y = x if isinstance(x, T) else None`, narrow `x` to `T` on the true side
6. Narrowing is reflected as an implicit cast in EAST2's type information (updating `resolved_type` / `type_expr`)

### v1 scope

| Pattern | Example | v1 support |
|---|---|---|
| Narrowing inside if block | `if isinstance(x, T): x.method()` | Supported |
| elif narrowing | `elif isinstance(x, U): x.method()` | Supported |
| Early return guard | `if not isinstance(x, T): return` → x is T thereafter | Supported |
| Ternary isinstance | `y = x if isinstance(x, T) else None` | Supported |
| Block-level propagation (loops etc.) | `if isinstance(x, list): for item in x` | Supported (natural consequence of basic narrowing) |
| `isinstance` combined with `and` | `if isinstance(x, T) and len(x) > 0:` | Supported |
| `not isinstance(...) or ...: continue` guard | `if not isinstance(x, T) or pred(x): continue` | Supported |
| Excluded type inference in `else` block | `else: # x is not T` | Not supported |
| `x` is reassigned inside the if block | `x = other_value` | Invalidates narrowing (safe side) |

### Early return guard design

`if not isinstance(x, T): return` (or `raise` / `break` / `continue`) always exits the if block, so `x`'s type is fixed to `T` in subsequent statements.

```python
def process(val: JsonVal) -> str:
    if not isinstance(val, dict):
        return ""
    # From here on, val is dict[str, JsonVal]
    val.get("key")  # OK
```

The resolver detects "all branches of the if block exit (return/raise/break/continue)" and applies narrowing to the type environment of subsequent statements.

### Ternary isinstance design

In `y = x if isinstance(x, T) else default`, resolve `x` as `T` on the true side.

```python
owner_node = owner if isinstance(owner, dict) else None
# owner_node's type is dict[str, JsonVal] | None
```

### Alignment with existing specification

- `cast` can still be used explicitly (backward compatible)
- Narrowing is just the resolver updating the type environment; no new EAST nodes are needed
- The principle that `type_expr` is the source of truth is maintained

## Risks

- When the `T` in `isinstance(x, T)` is a generic type (e.g. `dict[str, JsonVal]`), type parameter inference is needed
- Alignment with nominal ADT variant narrowing (`isinstance(x, Cat)` narrows `Animal` → `Cat`)
- Handling nested `isinstance` (`if isinstance(x, A): if isinstance(x.field, B):`)

## Subtasks

1. [ID: P1-NARROW-S1] Implement isinstance condition detection + if/elif block type environment update in the resolver
2. [ID: P1-NARROW-S2] Support early return guard (`if not isinstance(x, T): return` fallthrough narrowing)
3. [ID: P1-NARROW-S3] Support ternary isinstance (`y = x if isinstance(x, T) else None`)
4. [ID: P1-NARROW-S4] Implement narrowing invalidation on reassignment detection
5. [ID: P1-NARROW-S5] Add fixtures (all narrowing patterns) + generate golden + confirm parity

## Acceptance Criteria

1. Inside an `if isinstance(x, T):` block, `x` is type-resolved as `T`
2. `elif isinstance(x, U):` also works the same way
3. After `if not isinstance(x, T): return`, `x` is type-resolved as `T`
4. On the true side of `y = x if isinstance(x, T) else None`, `x` is type-resolved as `T`
5. Narrowing propagates naturally into loops etc. within the if block
6. When `x` is reassigned inside the if block, narrowing is invalidated
7. Existing manual `cast` patterns continue to work (backward compatible)
8. Existing fixture / sample parity is maintained

## Decision Log

- 2026-03-27: Prompted by the issue of `JsonVal` → `dict` narrowing not reaching Go in call_graph.py for selfhost. Specified automatic type narrowing after isinstance. The design achieves this by updating the type environment in the resolve stage, without burdening the emitter.
- 2026-03-27: Based on go-selfhost contributor reports, expanded v1 scope. Early return guard, ternary isinstance, and block-level propagation are included in v1.
- 2026-03-27: The implementation centralizes narrowing source of truth in the resolver/EAST; guard-aware scope tracking in the emitter is not adopted. Canonical narrowing targets for `JsonVal` are `dict[str,JsonVal]` / `list[JsonVal]`.
- 2026-03-27: `and`-chained conditions and `not isinstance(...) or ...: continue` form fallthrough guards are included in v1. Any name that is reassigned is immediately removed from the narrowed type environment within the same block.
