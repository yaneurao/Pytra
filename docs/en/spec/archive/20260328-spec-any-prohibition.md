<a href="../../../ja/spec/archive/20260328-spec-any-prohibition.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# `Any` Annotation Prohibition Guide

Last updated: 2026-03-18 (S6 complete: PyObj removal)

## Overview

The Pytra transpiler prohibits `Any` type annotations in transpile-target Python code.
When an `Any` annotation is detected, `AnyAnnotationProhibitionPass` raises a compile error and halts.

## Why `Any` Is Prohibited

1. `Any` annotations produce variables of unknown type in the C++ emitter. The `PyObj` boxing hierarchy was removed in S6, and `object` is now redefined as `rc<RcObject>` (reference-counted base), but using `Any` causes an attempt to box against that type, resulting in a compile error.
2. Pytra's type system is designed to require type determination, and `Any` disables type inference.
3. By eliminating `Any`, statically type-safe C++ code can be generated.

## Error Message

```
AnyAnnotationProhibitionPass: `Any` type annotations are prohibited.
Use a concrete type (e.g. `str`, `int`, `list[str]`), a union type
(e.g. `str | int`), or a user-defined class instead of `Any`.
Violations:
  [line N, col C] parameter `x` of `foo`: annotation `Any` contains `Any`
  [line M, col D] variable `val`: annotation `dict[str, Any]` contains `Any`
```

## Migration Steps

### Variable Annotations

```python
# Before (prohibited)
x: Any = compute()

# After: use a concrete type
x: int = compute()

# After: use a union type (when multiple types may be returned)
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

### Function Return Values

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

# After: concrete element types
values: dict[str, str] = {}
items: list[int] = []

# After: union types
values: dict[str, str | int | bool] = {}
```

### extern Variables

```python
# Before (prohibited; object is also now deprecated)
stderr: object = extern(__s.stderr)

# After (once S5-01 is complete): omit the annotation
stderr = extern(__s.stderr)  # C++ side infers type via auto
```

## About `from typing import Any`

The import statement `from typing import Any` is not prohibited. Imports are permitted as annotation-only no-ops.
However, actually using `Any` as a type annotation will result in an error.

## Enabling the Pass

`AnyAnnotationProhibitionPass` is disabled by default.
To enable it explicitly:

```
python3 src/pytra-cli.py --target cpp input.py --east3-opt-pass +AnyAnnotationProhibitionPass
```

After migration of `Any` in the stdlib (`pytra.std.*`) is complete (P5-ANY-ELIM-OBJECT-FREE-01-S2-02),
it is planned to be added to the default pass list (`build_local_only_passes()`).

## Related Tasks

- `P5-ANY-ELIM-OBJECT-FREE-01-S2-01`: Pass implementation
- `P5-ANY-ELIM-OBJECT-FREE-01-S2-02`: stdlib migration
- `P5-ANY-ELIM-OBJECT-FREE-01-S5-01`: Transparent handling of `extern` variables
