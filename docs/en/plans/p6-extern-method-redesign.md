<a href="../../ja/plans/p6-extern-method-redesign.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-2563EB?style=flat-square">
</a>

# P6-EXTERN-METHOD-REDESIGN: Redesigning @extern_method / @abi

Last updated: 2026-03-29
Status: Draft

## Background

Currently, built_in declarations such as those in `containers.py` use two decorators, `@extern_method` + `@abi`, but:

- `@extern_method` arguments are redundant (three arguments: module, symbol, tag)
- `@abi` is unused (no implementation or tests)
- module / symbol / tag contain duplicate information

## Conclusion

### Consolidate into two decorators

| Decorator | Target | Meaning |
|---|---|---|
| `@extern` | Opaque types | An opaque type defined externally. No rc, no boxing. Treated as a handle. |
| `@runtime("namespace")` | Runtime-implemented classes | A class built into Pytra's type system. Has rc. Implementation exists in runtime. |

### Class declaration with `@runtime`

```python
@runtime("pytra.core")
class list(Generic[T]):
    def append(self, x: T) -> None: ...
    def extend(self, x: list[T]) -> None: ...
    def pop(self, index: int = -1) -> T: ...
    def sort(self) -> None: ...
    def clear(self) -> None: ...

@runtime("pytra.core")
class dict(Generic[K, V]):
    def get(self, key: K) -> V: ...
    def items(self) -> list[tuple[K, V]]: ...
```

- `@runtime("pytra.core")` declares the namespace the class belongs to
- No individual decorators needed for methods (`@runtime` class methods are all runtime-implemented)
- `@namespace` is not needed (included in `@runtime`'s argument)
- `@method` is not needed (methods inside a `@runtime` class are implicitly all extern)

### Opaque type declaration with `@extern`

```python
@extern
class Window:
    def set_title(self, title: str) -> None: ...
    def close(self) -> None: ...

@extern
class App:
    def create_window(self) -> Window: ...
    def destroy_window(self, win: Window) -> None: ...
```

- Not wrapped in rc (see spec-opaque-type.md)
- All methods are externally implemented

### Auto-derivation rules

For the `extend` method of `class list` decorated with `@runtime("pytra.core")`:

- module: `pytra.core.list` (namespace + class name)
- symbol: `list.extend` (class name + method name)
- tag: `stdlib.method.extend` (auto-derived)
- runtime function name: converted via mapping.json (`list.extend` → `py_list_extend_mut`, etc.)

### Deprecating `@abi`

`@abi` is deprecated. Reasons:

- No implementation or usage, so zero impact
- arg modes (`ref` / `ref_readonly` / `value` / `value_readonly`) are all deemed unnecessary

### Why arg modes are not needed

- All arguments are passed with rc as-is (`ref` only)
- `ref_readonly` is not useful for escape analysis (once passed to a function, tracking is impossible)
- `value` / `value_readonly` were considered for external FFI, but the runtime wrapper can simply deref
- The aliasing problem (`a.extend(a)`) means stripping rc would cause dangling references

### All runtime helper arguments are rc-based

Runtime helpers all take rc-wrapped arguments (`Object<list<T>>` / `*PyList[T]`). Only one pattern needs to be implemented.

### Difference between `@extern` and `@runtime`

| | `@extern` | `@runtime` |
|---|---|---|
| Purpose | External libraries (SDL3, etc.) | Pytra built_in / std |
| rc | None (opaque handle) | Yes (Pytra's type system) |
| boxing | None | Yes |
| type_id | None | Yes |
| isinstance | Not possible | Possible |
| Type category | OpaqueType | Normal class |

## Comparison with current state

| | Current | New design |
|---|---|---|
| list.append | `@extern_method(module="pytra.core.list", symbol="list.append", tag="stdlib.method.append")` | Simply write `def append(...)` inside a `@runtime` class |
| list.extend | Above + `@abi(args={"x": "value"})` | Same (arg mode not needed) |
| Window | `@extern class Window` | `@extern class Window` (unchanged) |

## Subtasks

1. [ID: P6-REDESIGN-S1] Implement `@runtime` decorator in the parser and incorporate auto-derivation rules
2. [ID: P6-REDESIGN-S2] Rewrite `containers.py` using `@runtime` notation
3. [ID: P6-REDESIGN-S3] Deprecate `@extern_method` (stop accepting it in the parser)
4. [ID: P6-REDESIGN-S4] Deprecate `@abi`
5. [ID: P6-REDESIGN-S5] Deprecate `meta.runtime_abi_v1` in spec-east.md
6. [ID: P6-REDESIGN-S6] Remove `@abi` references from tutorials and guides
7. [ID: P6-REDESIGN-S7] Update the emitter guide to document runtime implementation rules for `@runtime` class methods

## Open questions

- Should the function variant of `@extern` (`@extern def native_sqrt(x: float) -> float: ...`) be kept as-is?
- Are there cases of declaring functions (not methods) with `@runtime`?
- Estimate of rewrite volume in existing `containers.py`

## Decision Log

- 2026-03-28: Considered proposals A–D. Recommended proposal D (`@namespace` + `@method` minimal notation, auto-derivation).
- 2026-03-28: Considered 4 arg mode kinds (ref / ref_readonly / value / value_readonly).
- 2026-03-28: Discovered the aliasing problem (`a.extend(a)`). Confirmed that rc cannot be stripped.
- 2026-03-29: Concluded that `ref_readonly` is not useful for escape analysis. All arg modes are deemed unnecessary.
- 2026-03-29: Concluded that for external FFI as well, the runtime wrapper can deref, so `value` / `value_readonly` are also unnecessary.
- 2026-03-29: Decided to deprecate `@abi` and all arg modes.
- 2026-03-29: Discovered that `@method` is indistinguishable from `@extern`. Consolidated into two: `@runtime("namespace")` and `@extern`. Both `@namespace` and `@method` are now unnecessary.
