# `Any` Annotation Prohibition Guide

Last updated: 2026-03-18 (S6 complete: PyObj removed)

> Source of truth: [docs/ja/spec/spec-any-prohibition.md](../../ja/spec/spec-any-prohibition.md)

## Overview

The Pytra transpiler prohibits `Any` type annotations in transpile-target Python code.
When an `Any` annotation is detected, `AnyAnnotationProhibitionPass` raises a compile error and stops.

## Why `Any` is Prohibited

1. `Any` annotations leave types unresolved for the C++ emitter. The `PyObj` boxing hierarchy was removed in S6; `object` is now redefined as `rc<RcObject>` (the reference-counted base), but using `Any` would trigger attempted boxing into this type, causing compile errors.
2. Pytra's type system requires type resolution by design; `Any` disables type inference.
3. Eliminating `Any` enables generation of statically type-safe C++ code.

## Error Message

```
AnyAnnotationProhibitionPass: `Any` type annotations are prohibited.
Use a concrete type (e.g. `str`, `int`, `list[str]`), a union type
(e.g. `str | int`), or a user-defined class instead of `Any`.
Violations:
  [line N, col C] parameter `x` of `foo`: annotation `Any` contains `Any`
  [line M, col D] variable `val`: annotation `dict[str, Any]` contains `Any`
```

## Migration Guide

### Variable Annotations

```python
# Before (prohibited)
x: Any = compute()

# After: use a concrete type
x: int = compute()

# After: use a union type (when multiple types are possible)
x: str | int | None = compute()
```

### Function Parameters

```python
# Before (prohibited)
def process(data: Any) -> str:
    ...

# After: concrete type
def process(data: str) -> str:
    ...

# After: union type
def process(data: str | int) -> str:
    ...

# After: user-defined class
def process(data: MyClass) -> str:
    ...
```

### Return Types

```python
# Before (prohibited)
def get_value() -> Any:
    ...

# After
def get_value() -> str | int | None:
    ...
```

### Container Types

```python
# Before (prohibited)
values: dict[str, Any] = {}
items: list[Any] = []

# After: concrete element type
values: dict[str, str] = {}
items: list[int] = []

# After: union type
values: dict[str, str | int | bool] = {}
```

### extern Variables

```python
# Before (prohibited; `object` also deprecated)
stderr: object = extern(__s.stderr)

# After (S5-01): omit annotation
stderr = extern(__s.stderr)  # C++ side infers type via auto
```

## About `from typing import Any`

The import statement `from typing import Any` is **not** prohibited. Imports are treated as annotation-only no-ops.
However, using `Any` as an actual type annotation will cause an error.

## Enabling the Pass

`AnyAnnotationProhibitionPass` is disabled by default.
To enable explicitly:

```
python3 src/py2x.py --target cpp input.py --east3-opt-pass +AnyAnnotationProhibitionPass
```

After stdlib (`pytra.std.*`) `Any` migration (P5-ANY-ELIM-OBJECT-FREE-01-S2-02) is complete,
this pass will be added to the default pass list (`build_local_only_passes()`).

## Related Tasks

- `P5-ANY-ELIM-OBJECT-FREE-01-S2-01`: Pass implementation
- `P5-ANY-ELIM-OBJECT-FREE-01-S2-02`: stdlib migration
- `P5-ANY-ELIM-OBJECT-FREE-01-S5-01`: `extern` variable transparent handling
- `P5-ANY-ELIM-OBJECT-FREE-01-S6-01/02`: PyObj boxing hierarchy removal
