<a href="../../ja/tutorial/extern.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# How to Use `@extern` / `extern(...)`

`@extern` and `extern(...)` are Pytra-specific syntax for referring to external implementations and ambient globals from Pytra code.
For the normative definition, see the [ABI Specification](../spec/spec-abi.md).

## Function extern

- Use `@extern` when you want to delegate a top-level function to an external implementation.
- The transpiler does not generate the function body. It assumes an implementation exists on the target side and emits a call to it.

```python
from pytra.std import extern

@extern
def sin(x: float) -> float:
    ...
```

### v2 extern: `extern_fn` / `extern_var` / `extern_class`

In the new pipeline (`toolchain2`), `@extern` is split by use case and runtime information is required explicitly.

```python
# pytra: builtin-declarations

# Function
@extern_fn(module="my_game.physics", symbol="apply_gravity", tag="user.physics.gravity")
def apply_gravity(x: float, y: float, dt: float) -> float: ...

# Variable
gravity: float = extern_var(module="my_game.physics", symbol="GRAVITY", tag="user.physics.const_gravity")

# Class
@extern_class(module="my_game.entity", symbol="Player", tag="user.entity.player")
class Player:
    def move(self, dx: float, dy: float) -> None: ...
```

| Function | Purpose |
|---|---|
| `extern_fn` | External function declaration decorator |
| `extern_var` | External variable declaration |
| `extern_class` | External class declaration decorator |

| Argument | Meaning |
|---|---|
| `module` | Runtime module that provides the implementation, independent of target language |
| `symbol` | Name inside that runtime module |
| `tag` | `semantic_tag`, the key emitters use to recognize the meaning |

All arguments are required. See [spec-builtin-functions.md §10](../spec/spec-builtin-functions.md) for details.

## Variable extern

- You cannot attach `@extern` to variables.
- Variable extern is written as `name = extern(...)`.

Use the following three forms.

- `name: T = extern(expr)`
  A variable extern with host fallback or runtime-hook initialization.
- `name: Any = extern()`
  An ambient global with the same name.
- `name: Any = extern("symbol")`
  An ambient global with a different symbol name.

```python
from typing import Any
from pytra.std import extern

document: Any = extern()
console: Any = extern("console")
```

Notes:

- Ambient globals are currently supported only on the JS/TS backends.
- `document: Any = extern()` lowers to a direct reference to `document`, and `console: Any = extern("console")` lowers to a direct reference to `console`.
