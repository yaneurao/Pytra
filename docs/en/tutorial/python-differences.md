<a href="../../ja/tutorial/python-differences.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# Differences from Python

Pytra uses Python syntax, but since it assumes static typing, not all Python patterns are available. This page explains the most common gotchas for Python users with concrete examples.

## Write Type Annotations

In Python, type annotations are optional. In Pytra, function arguments and return types need annotations.

```python
# NG: no type annotations
def add(a, b):
    return a + b

# OK: with type annotations
def add(a: int, b: int) -> int:
    return a + b
```

Variables can be inferred from literals, so annotations are optional for them.

```python
x = 42          # OK: inferred as int
name = "hello"  # OK: inferred as str

items: list[int] = []  # Empty containers need annotations
```

## Use `pytra.std.*` for Imports

Python standard library modules cannot be imported directly. Use `pytra.std.*` shims instead.

```python
# NG: direct standard library import
import json
import math
import os

# OK: import via pytra.std
from pytra.std import json
from pytra.std import math
from pytra.std.time import perf_counter
from pytra.std.pathlib import Path
```

See [pylib module list](../spec/spec-pylib-modules.md) for available modules.

Exception: `typing` and `dataclasses` can be imported directly (for annotations and decorators only).

```python
from typing import Optional    # OK
from dataclasses import field  # OK
```

## Integers Are Not Arbitrary Precision

Python's `int` has arbitrary precision, but Pytra converts it to `int64` (64-bit signed integer).

```python
# Python: handles huge integers
x = 2 ** 100  # OK in Python

# Pytra: may overflow beyond int64 range (-2^63 to 2^63-1)
x = 2 ** 100  # ⚠ potential overflow
```

You can specify integer types explicitly.

```python
small: int8 = 127       # -128 to 127
pixel: uint8 = 255      # 0 to 255
counter: int32 = 0      # -2^31 to 2^31-1
big: int64 = 0          # -2^63 to 2^63-1 (default)
```

## `if __name__ == "__main__":` Is Required

Pytra requires an `if __name__ == "__main__":` block as the entry point.

```python
# NG: writing directly at top level
print("hello")

# OK: inside main guard
if __name__ == "__main__":
    print("hello")
```

## No Multiple Inheritance

Python allows inheriting from multiple classes, but Pytra supports single inheritance only.

```python
# NG: multiple inheritance
class C(A, B):
    pass

# OK: single inheritance + trait
class C(A):
    @implements(Drawable)
    def draw(self) -> None: ...
```

Use [Traits](./trait.md) when you need multiple behavioral contracts.

## Cannot Call Methods on `object` / `Any`

Since Pytra is statically typed, you cannot call methods on values with unknown types.

```python
# NG: method call on object
def process(x: object) -> None:
    x.do_something()  # compile error

# OK: accept a concrete type
def process(x: MyClass) -> None:
    x.do_something()  # OK
```

For union types, narrow with `isinstance` first. See [Union Types and Narrowing](./union-and-narrowing.md).

## Empty Containers Need Type Annotations

```python
# NG: cannot infer type of empty container
items = []
data = {}

# OK: with type annotations
items: list[int] = []
data: dict[str, int] = {}
```

Non-empty containers are inferred.

```python
items = [1, 2, 3]           # OK: inferred as list[int]
data = {"a": 1, "b": 2}     # OK: inferred as dict[str, int]
```

## `*args` Needs Type Annotation

```python
# NG: no type annotation
def f(*args):
    pass

# OK: with type annotation
def f(*args: int) -> None:
    pass
```

`**kwargs` is not supported.

## Unsupported Syntax

| Syntax | Status |
|---|---|
| `**kwargs` | Not supported |
| `async` / `await` | Not supported |
| `with` statement | Supported |
| `lambda` | Supported |
| List comprehension | Supported (single generator only) |
| `for/else` | Not supported |
| `while/else` | Not supported |
| Decorators | `@property`, `@staticmethod`, `@trait`, `@implements`, `@extern`, `@abi`, `@template` |
| `global` / `nonlocal` | Not supported |
| `yield` / generators | Not supported |

## More Details

For a comprehensive compatibility table, see the [Python Compatibility Guide (spec)](../spec/spec-python-compat.md).
