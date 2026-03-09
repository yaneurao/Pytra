<a href="../../ja/tutorial/extern.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# How to Use `@extern` / `extern(...)`

`@extern` and `extern(...)` are Pytra-specific syntax for referring to external implementations and ambient globals from Pytra code.  
For the normative specification, see the [ABI Specification](../spec/spec-abi.md).

## Function extern

- Use `@extern` when you want to delegate a top-level function to an external implementation.
- The transpiler does not generate the function body. It treats the function as a call into a target-side implementation.

```python
from pytra.std import extern

@extern
def sin(x: float) -> float:
    ...
```

## Variable extern

- You cannot attach `@extern` to variables.
- Variable extern must be written as `name = extern(...)`.

Use the following three forms.

- `name: T = extern(expr)`
  - A variable extern that uses host fallback or runtime-hook initialization
- `name: Any = extern()`
  - An ambient global with the same name
- `name: Any = extern("symbol")`
  - An ambient global with a different symbol name

```python
from typing import Any
from pytra.std import extern

document: Any = extern()
console: Any = extern("console")
```

Notes:

- Ambient globals are currently limited to the JS/TS backends.
- `document: Any = extern()` lowers to a direct reference to `document`, and `console: Any = extern("console")` lowers to a direct reference to `console`.
