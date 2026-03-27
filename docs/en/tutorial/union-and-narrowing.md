<a href="../../ja/tutorial/union-and-narrowing.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# Union Types and isinstance Narrowing

This page explains how to work with **union types** (values that can hold multiple types) and **isinstance narrowing** (automatic type refinement in conditional branches) in Pytra.

## What is a Union Type?

A Python variable usually holds one type, but sometimes you need "this variable can be either int or str." In Pytra, you declare union types with the `type` statement.

```python
type Result = int | str | None
```

This means "a variable of type `Result` can hold an `int`, `str`, or `None`."

### Example: JSON Parser

A JSON value can be a number, string, boolean, null, array, or object. In Pytra, this is expressed as a single union type.

```python
type JsonVal = None | bool | int | float | str | list[JsonVal] | dict[str, JsonVal]
```

Recursive definitions (where `JsonVal` appears inside `list[JsonVal]`) are supported.

### Optional Type

The two-option pattern "either a value or None" can be written with `Optional`.

```python
from typing import Optional

def find(items: list[str], key: str) -> Optional[str]:
    for item in items:
        if item == key:
            return item
    return None
```

Internally, `Optional[str]` is the same as `str | None`.

### Ternary Expression Type Inference

The type of a ternary expression (`x if cond else y`) is automatically inferred from the types of both sides.

If both sides are the same type, the result is that type:

```python
# label is inferred as str
label = "yes" if flag else "no"
```

If one side is `None`, the result is `Optional[T]`:

```python
# name is inferred as str | None
name = user.get("name") if "name" in user else None
```

If both sides are different types, the result is a union type:

```python
# result is inferred as int | str
result = parse_int(s) if is_number else parse_str(s)
```

## Using isinstance to Check Types, and cast to Narrow

Since Pytra assumes static typing, you cannot call methods directly on a union-typed variable. First check the type with `isinstance`, then convert to a specific type with `cast` before calling methods.

```python
from pytra.typing import cast

def process(val: JsonVal) -> None:
    if isinstance(val, dict):
        d: dict[str, JsonVal] = cast(dict[str, JsonVal], val)
        d.get("key")        # OK: d is a dict, so methods are available

    elif isinstance(val, list):
        items: list[JsonVal] = cast(list[JsonVal], val)
        for item in items:   # OK: items is a list, so looping works
            print(item)
```

`cast` is imported from `pytra.typing`. At runtime, it does nothing (it serves as a hint for the type checker).

A larger example:

```python
def describe(val: JsonVal) -> str:
    if isinstance(val, dict):
        d: dict[str, JsonVal] = cast(dict[str, JsonVal], val)
        return "object with " + str(len(d)) + " keys"
    elif isinstance(val, list):
        items: list[JsonVal] = cast(list[JsonVal], val)
        return "array with " + str(len(items)) + " items"
    elif isinstance(val, str):
        return val
    elif isinstance(val, bool):
        if val:
            return "true"
        return "false"
    elif isinstance(val, int):
        return str(val)
    elif isinstance(val, float):
        return str(val)
    return "null"
```

## Automatic Narrowing: You Can Skip cast

In the code above, `cast` is written every time. However, Pytra looks at `isinstance` checks and **automatically narrows the variable's type within the if block**. This feature is called **isinstance narrowing**.

The earlier code can be rewritten like this:

```python
def process(val: JsonVal) -> None:
    if isinstance(val, dict):
        # val is automatically treated as dict[str, JsonVal]
        val.get("key")      # OK: methods work without cast
        for k, v in val.items():
            print(k)

    elif isinstance(val, list):
        # val is automatically treated as list[JsonVal]
        for item in val:     # OK: looping works without cast
            print(item)
```

Inside the if block immediately after `isinstance`, the variable's type is automatically narrowed, so you can use method calls and loops directly without `cast`.

### Patterns Where Narrowing Works

#### if/elif

```python
if isinstance(x, int):
    print(x + 1)        # x is int
elif isinstance(x, str):
    print(x.upper())    # x is str
```

#### Early Return Guard

If you early-return on a negated `isinstance`, the type is narrowed for the lines that follow.

```python
def process(val: JsonVal) -> str:
    if not isinstance(val, dict):
        return ""
    # From here on, val is dict[str, JsonVal]
    return val.get("name")
```

The same effect applies to `raise`, `break`, and `continue`.

#### Ternary Expression

```python
owner_node = owner if isinstance(owner, dict) else None
# owner_node is inferred as dict[str, JsonVal] | None
```

### Patterns Where Narrowing Does Not Work (Use cast)

In the following patterns, automatic narrowing does not apply. Use `cast` instead.

```python
from pytra.typing import cast

# else block: not narrowed
if isinstance(x, dict):
    pass
else:
    # x's type is not narrowed, so cast is needed
    s: str = cast(str, x)
```

### Reassignment Invalidates Narrowing

If a variable is reassigned inside an if block, narrowing is invalidated.

```python
if isinstance(val, dict):
    val = other_value    # reassigned
    # val is no longer narrowed to dict here
```

## isinstance on POD Types

Integer types (`int8`, `int16`, `int32`, `int64`, etc.) and floating-point types (`float32`, `float64`) use **exact type matching**. Value range inclusion is not considered.

```python
x: int16 = 1
print(isinstance(x, int16))   # True  — same type
print(isinstance(x, int8))    # False — different type (int8 is not a subtype of int16)
print(isinstance(x, int32))   # False — different type (even if the value range is included)
```

## Summary

| Goal | How to write |
|---|---|
| Define a union type | `type X = A \| B \| C` |
| Use Optional | `Optional[T]` or `T \| None` |
| Check a type | `isinstance(x, T)` |
| Call methods after checking | Use directly inside the if block (automatic narrowing) |
| When narrowing doesn't work | Use `cast(T, x)` |

For detailed specifications, see:
- [Tagged union specification](../spec/spec-tagged-union.md) — Union type definition and code generation rules for each language
- [type_id specification §4.2](../spec/spec-type_id.md) — isinstance check method for POD and class types
- [EAST specification §7.1](../spec/spec-east.md) — Detailed rules for isinstance narrowing
