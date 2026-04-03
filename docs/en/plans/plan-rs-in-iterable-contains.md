# Plan: Handle Rust `in` operator as generic iterable contains (P0-RS-IN-ITERABLE)

## Background

Python's `in` operator is a generic operator following the iterable protocol:

```python
x in [1, 2, 3]       # list __contains__
x in (1, 2, 3)        # tuple __contains__
x in {1, 2, 3}        # set __contains__
x in "abc"            # str __contains__
x in range(1000)      # range __contains__
x in my_iterable      # arbitrary iterable
```

The current Rust emitter / runtime handles tuple `in` using per-element-count `PyContains` trait implementations. Nearly identical code is written by hand for 2 through 12 elements, and tuples with more than 12 elements do not work.

This design is broken and is also prohibited by spec-emitter-guide §1.1.

## Design

### Principle

The `in` operator is handled as a **generic `contains` on an iterable**. The runtime absorbs differences between collection types; the emitter is unaware of the collection type.

### Rust Implementation

| Python collection | Rust representation | How `in` is implemented |
|---|---|---|
| `list[T]` | `Vec<T>` / `PyList<T>` | `.contains(&key)` |
| `tuple[T, ...]` | Convert to `Vec<T>` or slice | `.contains(&key)` |
| `set[T]` | `HashSet<T>` / `PySet<T>` | `.contains(&key)` |
| `dict[K, V]` | `HashMap<K, V>` / `PyDict<K, V>` | `.contains_key(&key)` |
| `str` | `String` | `.contains(&substring)` |
| `range(n)` | Arithmetic check | `start <= x && x < stop && (x - start) % step == 0` |

### Handling tuples

Tuples can hold different types at fixed positions, but when used with `in`, the elements are assumed to be the same type (in Pytra's type system, something like `tuple[int, int, int]` is assumed, where all elements are the same type). When the Rust emitter processes tuple `in`:

1. Convert `EAST3 Tuple.elements` to a slice literal `&[elem1, elem2, ...]`
2. Call `.contains(&key)`

```rust
// Python: x in (1, 2, 3)
// Rust:
[1, 2, 3].contains(&x)
```

This works regardless of element count. Per-element-count trait implementations are unnecessary.

### Handling range

`x in range(start, stop, step)` is checked arithmetically without generating an array:

```rust
// Python: x in range(0, 1000, 2)
// Rust:
x >= 0 && x < 1000 && (x - 0) % 2 == 0
```

Since `range` is already normalized to `RangeExpr` in EAST3, the emitter can emit the arithmetic check directly for the `Compare(In) + RangeExpr` pattern.

## Implementation Order

1. In the Rust emitter's `_emit_compare`, convert `In` / `NotIn` + `Tuple` to `[...].contains(&key)`
2. In the Rust emitter's `_emit_compare`, convert `In` / `NotIn` + `RangeExpr` to an arithmetic check
3. Remove the per-element-count tuple impl (2–12 elements) from `py_runtime.rs`
4. Confirm that the `in_membership_iterable` fixture passes compile + run parity in Rust
5. Confirm no regressions in full fixture + sample parity

## Related

- P0-EAST3-IN-EXPAND: EAST3 optimizer expansion of small literal counts to `||` (optimization). Independent of this task; both can be done. If the optimizer expansion applies first, the emitter only needs to render `BoolOp(Or)` and this task's `contains` path is not reached. When the optimizer does not expand (4+ elements, non-literals), this task's `contains` path is used.
