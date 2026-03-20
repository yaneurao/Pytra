# Tagged Union Specification

<a href="../../ja/spec/spec-tagged-union.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

This document defines the semantics, code-generation rules, and type-manipulation rules for `type X = A | B | ...` declarations (PEP 695 type-alias union definitions) in Pytra.

## 1. Purpose

- Generate a native tagged union in each target language from a Python `type X = A | B | ...` declaration.
- Allow recursive types (`type JsonVal = ... | list[JsonVal] | dict[str, JsonVal]`) to be expressed naturally.
- Implement `isinstance` / `is None` / `cast` uniformly using a `type_id`-based mechanism.

## 2. Declaration

Declare at module level using the `type` statement (PEP 695).

```python
type ArgValue = str | bool | None
type JsonVal = None | bool | int | float | str | list[JsonVal] | dict[str, JsonVal]
```

- A union with two or more non-`None` members is treated as a tagged union.
- A union of one type + `None` is treated as `Optional[T]` and is not a tagged union.
- Generic type aliases (`type Stack[T] = list[T]`) are not in scope.

## 3. C++ Code Generation

A tagged union is emitted as a `struct` with a `uint32 tag`. Tag values use `PYTRA_TID_*` constants.

```cpp
struct ArgValue {
    uint32 tag;
    str str_val;
    bool bool_val;

    ArgValue() : tag(PYTRA_TID_NONE) {}
    ArgValue(const str& v) : tag(PYTRA_TID_STR), str_val(v) {}
    ArgValue(const bool& v) : tag(PYTRA_TID_BOOL), bool_val(v) {}
    ArgValue(::std::monostate) : tag(PYTRA_TID_NONE) {}
};
```

### 3.1 Tag Values

Tag values use `PYTRA_TID_*` constants defined in `spec-type_id.md`.

| Python type | Tag value |
|-------------|-----------|
| `None` | `PYTRA_TID_NONE` |
| `bool` | `PYTRA_TID_BOOL` |
| `int` | `PYTRA_TID_INT` |
| `float` | `PYTRA_TID_FLOAT` |
| `str` | `PYTRA_TID_STR` |
| `list[T]` | `PYTRA_TID_LIST` |
| `dict[K,V]` | `PYTRA_TID_DICT` |
| `set[T]` | `PYTRA_TID_SET` |
| User class | `ClassName::PYTRA_TYPE_ID` |

### 3.2 Recursive Types

Union members that contain the type itself (e.g. `list[JsonVal]`) are wrapped in a reference-counted pointer such as `rc<list<JsonVal>>`.

## 4. isinstance Check

An `isinstance` check against a tagged union variable is converted to a tag comparison.

```python
isinstance(v, int)   # v: JsonVal
```
→ C++:
```cpp
(v).tag == PYTRA_TID_INT
```

For class types, a range check via `py_tid_is_subtype` is used to respect inheritance hierarchies.

## 5. Type Narrowing (cast)

Use `typing.cast` to extract the value of a specific type from a tagged union variable.

```python
from pytra.typing import cast

if isinstance(v, int):
    x = cast(int, v)      # extract the int value from v
    print(x + 1)
```
→ C++:
```cpp
if ((v).tag == PYTRA_TID_INT) {
    int64 x = v.int64_val;
    py_print(x + 1);
}
```

### 5.1 Rules

- `cast(T, v)` is converted to an access to the field corresponding to type `T` in the tagged union variable `v`.
- At Python runtime, `typing.cast` is a no-op (it returns the value as-is), so the code also runs correctly in Python.
- Calling `cast` without an `isinstance` guard is allowed, but behavior is undefined if the tag does not match.
- **Implicit narrowing through an isinstance guard is not performed.** Use explicit `cast()` to make the type concrete.

### 5.2 Field Name Convention

Field names for each tagged union member are generated as `type_name.lower() + "_val"`.

| Python type | Field name |
|-------------|------------|
| `bool` | `bool_val` |
| `int` | `int64_val` |
| `float` | `float64_val` |
| `str` | `str_val` |
| `list[T]` | `list_t_val` |
| `dict[K,V]` | `dict_k_v_val` |

## 6. is None Check

```python
if v is None:     # → v.tag == PYTRA_TID_NONE
if v is not None: # → v.tag != PYTRA_TID_NONE
```

## 7. None Default Value

A default value of `None` for a tagged union argument is converted to a default constructor call (`tag = PYTRA_TID_NONE`).

## 8. Emit Strategy for Other Languages

| Language | Mechanism |
|----------|-----------|
| Rust | `enum` |
| Swift | `indirect enum` |
| Kotlin/Java | sealed class |
| Scala | sealed trait + case class |
| TypeScript | discriminated union |
| Go | struct + tag |

Support in each backend is deferred to subsequent tasks.
