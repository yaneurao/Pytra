# Python Compatibility Guide

<a href="../../ja/spec/spec-python-compat.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

This page is a guide for **users who know Python**, showing side-by-side comparisons of "how Python behaves / how Pytra behaves".
For normative details on input constraints, see the [User Specification](./spec-user.md).

## General Policy

Pytra uses "type-annotated Python subset" as its source language. The syntax is identical to Python, but **static typing is assumed**, and some of Python's dynamic features are unavailable.

Legend for the tables below:
- ✅ Supported
- ⚠️ Partially supported / behaves differently from Python
- ❌ Not supported (transpilation error)

---

## Type Annotations

| Syntax / Feature | Python | Pytra |
|---|---|---|
| Variable type annotation (`x: int = 1`) | Optional | ✅ Optional (literals are inferred) |
| Function argument / return type annotation | Optional | ⚠️ Omitting gives `unknown` type; may cause errors where inference does not apply |
| `from typing import cast` | Returns value as-is at runtime | ✅ Available via `from pytra.typing import cast`. Direct `from typing import ...` is an error |
| Generics via `typing.TypeVar` | Functions as a type variable | ⚠️ Allowed only as an annotation. Use Pytra's own `@template` to define generic functions |
| `type X = A \| B` (PEP 695 type alias) | Works as a type alias since Python 3.12 | ✅ Supported as a tagged union declaration. Converted to each target language's native tagged union |

---

## Functions and Arguments

| Syntax / Feature | Python | Pytra |
|---|---|---|
| Regular arguments and default values | Works | ✅ Works |
| Keyword argument calls (`f(a=1, b=2)`) | Passed by keyword name | ✅ Supported. For languages with positional-only arguments (e.g. C++), arguments are reordered by signature lookup |
| Calls with reordered arguments (`f(b=2, a=1)`) | Resolved by name, order is free | ✅ Supported. Reordered to definition order on output |
| `*args` (with type annotation) | Accepts any number of positional args | ✅ Supported as `def f(*args: int)`. Only one vararg is allowed |
| `*args` (without type annotation) | Works | ⚠️ Treated as `unknown` type |
| `**kwargs` | Accepts any number of keyword args | ❌ Explicit parser error |
| `f(**some_dict)` calls | Unpacks dict as keyword arguments | ❌ Not supported |
| `*` (keyword-only separator) | Forces arguments after `*` to keyword-only | ⚠️ Syntax can be parsed, but keyword-only enforcement is not implemented (`b` is treated as a normal positional argument) |
| `/` (positional-only separator) | Forces arguments before `/` to positional-only | ❌ Explicit parser error |
| `lambda` | Works | ✅ Supported. Includes captures, argument passing, immediate calls, and ternary expressions |
| Generic function definition via `@template("T")` | ❌ | ✅ Pytra-specific. Defines functions with type parameters |
| External function / class declaration via `@extern` | ❌ | ✅ Pytra-specific. Declares bindings for external library functions and classes |

---

## Classes, Inheritance, and OOP

| Syntax / Feature | Python | Pytra |
|---|---|---|
| `class` definition | Works | ✅ Works |
| Single inheritance | Works | ✅ Works |
| Multiple inheritance (`class C(A, B)`) | Works (resolved by MRO) | ❌ Explicit error |
| Mix-in (method injection via multiple inheritance) | Achieved via multiple inheritance | ❌ Unavailable because multiple inheritance is unsupported |
| Instance member definition in `__init__` | Works | ✅ Works via `self.x = ...` |
| Member declaration in class body | Treated as a class variable | ⚠️ Converted to `inline static` in C++ and `static` in C# |
| `super().__init__()` | Works | ✅ Works |
| `@dataclass` | Works | ✅ Supports the representative usages of `field(default=...)` / `field(default_factory=...)` |
| `isinstance(x, T)` | Works | ✅ Works |
| `@sealed` for sealed family declaration | ❌ | ✅ Pytra-specific. A decorator that declares the family class of a nominal ADT |
| `getattr(obj, "name")` | Dynamically retrieves attribute | ❌ Unsupported by design. Dynamic attribute access is not supported |
| `setattr(obj, "name", val)` | Dynamically sets attribute | ❌ Unsupported by design |
| Method call on `object`-typed variable | Works (resolved at runtime) | ❌ Explicit error. Resolve the type before accessing |

---

## Control Flow

| Syntax / Feature | Python | Pytra |
|---|---|---|
| `if / elif / else` | Works | ✅ Works |
| `for` / `while` | Works | ✅ Works |
| `match / case` | Works since Python 3.10 | ⚠️ Only exhaustive matching against `@sealed` families is supported. Guard patterns, nested patterns, and match expressions are not supported |
| `try / except / finally` | Works | ✅ Basic usage works. Details of multi-except type patterns are not yet finalized |
| `yield` / generators | Works | ⚠️ Not yet finalized (no dedicated tests) |
| Trailing semicolons (`x = 1; y = 2`) | Works | ❌ Parser input error |

---

## Built-in Types and Numbers

| Type / Feature | Python | Pytra |
|---|---|---|
| `int` | Arbitrary precision (bigint) | ⚠️ `int64` (64-bit integer). Overflow is not detected |
| `int64`, `int32`, `int16`, `int8` | ❌ | ✅ Pytra-specific signed fixed-width integer types. Available via `from pytra.types import int64` etc. |
| `uint64`, `uint32`, `uint16`, `uint8` | ❌ | ✅ Pytra-specific unsigned fixed-width integer types |
| `float` | 64-bit floating point | ✅ Works as `float64` |
| `float32` | ❌ | ✅ Pytra-specific 32-bit floating point type. Available via `from pytra.types import float32` |
| `bool` | Works | ✅ Works |
| `str` | Works | ✅ Supports slicing, for-each, f-strings, etc. |
| `list[T]` | Works | ✅ Works |
| `dict[K, V]` | Works | ✅ Works |
| `set[T]` | Works | ✅ Works |
| `tuple` | Works | ✅ Works |
| `bytes` / `bytearray` | Works | ✅ Supports basic operations |
| `None` | Works | ✅ Works |
| `Any` | Works | ✅ Supports basic usage |

---

## Collections and Comprehensions

| Syntax / Feature | Python | Pytra |
|---|---|---|
| List comprehension | Can have multiple `for` clauses | ⚠️ Assumes one generator (nested is separately supported) |
| Set comprehension | Can have multiple `for` clauses | ⚠️ Assumes one generator |
| Dict comprehension | Can have multiple `for` clauses | ⚠️ Assumes one generator |
| `if` condition in comprehension | Works | ✅ Works |
| Nested comprehension | Works | ✅ Works |
| `collections.deque[T]` | Available via `from collections import deque` | ✅ Available via `from pytra.std.collections import deque`. Representative operations (`append`, `popleft`, etc.) are supported |

---

## Modules and Imports

| Syntax / Feature | Python | Pytra |
|---|---|---|
| `import M` / `from M import S` | Works | ✅ Works |
| `from M import S as A` / `import M as A` | Works | ✅ Works |
| `from M import *` | Works | ⚠️ Passes only when exported symbols can be statically resolved |
| Relative imports (`from .m import x`) | Works | ✅ Supports sibling / parent |
| Direct import of Python standard library | Works | ❌ Explicit error. Use `pytra.std.*` (see table below) |
| Import of user-created modules | Works | ✅ Supported. Multi-file dependency resolution is being incrementally implemented |

### Standard Library Replacement Imports

Modules that can be imported directly in Python must go through `pytra.*` in Pytra.

| Python style | Pytra style |
|---|---|
| `from typing import cast` | `from pytra.typing import cast` |
| `from enum import Enum, IntEnum` | `from pytra.enum import Enum, IntEnum` |
| `from dataclasses import dataclass, field` | `from pytra.dataclasses import dataclass, field` |
| `from collections import deque` | `from pytra.std.collections import deque` |
| `import math` / `from math import sqrt` | `from pytra.std.math import sqrt` etc. |
| `from pathlib import Path` | `from pytra.std.pathlib import Path` |
| `import re` / `from re import compile` | `from pytra.std.re import compile` etc. |
| `import sys` | `from pytra.std.sys import ...` |
| `import os` | `from pytra.std.os import ...` |
| `import json` | `from pytra.std.json import ...` |

> `pytra.typing` / `pytra.enum` / `pytra.dataclasses` — the transpiler ignores these import statements (the parser already recognizes `cast` / `Enum` / `dataclass`). At Python runtime they re-export from the standard module, so the code runs unchanged.

---

## Pytra-Specific Features (not in standard Python)

The following are features that Pytra provides and that do not exist in standard Python. Each is also described in its relevant section above.

| Feature | Pytra syntax | Details |
|---|---|---|
| Fixed-width integer types | `int64`, `int32`, `int16`, `int8`, `uint64`, `uint32`, `uint16`, `uint8` | See built-in types section |
| 32-bit floating point type | `float32` | See built-in types section |
| Union type declaration (tagged union) | `type X = A \| B` (PEP 695 syntax) | See type annotation section |
| Nominal ADT (sealed family) | `@sealed` class + variant class | See classes section |
| Generic function template definition | `@template("T")` decorator | See functions section |
| External function / class binding declaration | `@extern` decorator | See functions section |
| Direct C++ code embedding | `# Pytra::cpp ...` comment | C++ target only |

---

## Related Documentation

- Normative input constraints: [User Specification](./spec-user.md)
- Tagged union details: [Tagged Union Specification](./spec-tagged-union.md)
- C++ backend support matrix: [py2cpp Support Matrix](../language/cpp/spec-support.md)
- Usage and execution guide: [Tutorial](../tutorial/README.md)
