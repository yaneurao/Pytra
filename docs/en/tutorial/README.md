<a href="../../ja/tutorial/README.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# Tutorial

This is the entry point for first-time Pytra users.
Start here.

## Smallest Example to Try in 3 Minutes

Start with a single file like this.

```python
def add(a: int, b: int) -> int:
    return a + b


if __name__ == "__main__":
    print(add(3, 4))
```

Save it as `add.py`, then transpile it to C++ and run it.

```bash
./pytra add.py --output-dir out/add_case --build --run --exe add.out
```

Expected stdout:

```text
7
```

If you want to look at the generated code first, this is enough:

```bash
./pytra add.py --output out/add.cpp
```

If you want Rust instead, only the target changes:

```bash
./pytra add.py --target rs --output out/add.rs
```

Once this smallest example works, the pages below become much easier to read.

## Recommended Reading Order

1. Check differences from Python: [Python Compatibility Guide](../spec/spec-python-compat.md)
2. Check how to run it: [Usage Guide](./how-to-use.md)
3. Check the spec entry point: [Specification Index](../spec/index.md)
4. Check type inference details: [Type Inference Rules](../spec/spec-east.md#7-type-inference-rules)
5. Check `@extern` / `extern(...)`: [extern.md](./extern.md)
6. Use `py2x.py` / `east2x.py` directly: [transpiler-cli.md](./transpiler-cli.md)
7. Check error categories and common blockers: [troubleshooting.md](./troubleshooting.md)
8. Check advanced transpilation routes: [Advanced Usage](./advanced-usage.md)
9. Check parity / selfhost / local CI: [Development Operations Guide](./dev-operations.md)

## How To Choose Pages

- If you want to know differences from Python or unsupported syntax
  - [Python Compatibility Guide](../spec/spec-python-compat.md)
- If you want to transpile `.py` files into target languages and run them
  - [Usage Guide](./how-to-use.md)
- If you want type inference details
  - [Type Inference Rules](../spec/spec-east.md#7-type-inference-rules)
- If you want the source-of-truth specs
  - [Specification Index](../spec/index.md)
- If you want to use `py2x.py` / `east2x.py` directly
  - [transpiler-cli.md](./transpiler-cli.md)
- If you want error categories and common blockers
  - [troubleshooting.md](./troubleshooting.md)
- If you want Pytra-specific decorators
  - `@template`: something like C++ templates. Current v1 is limited to linked runtime helpers.
    - [Template Specification (Draft)](../spec/spec-template.md)
  - `@extern` / `extern(...)`: for calling external functions and classes.
    - [extern.md](./extern.md)
  - `@abi`: for defining ABI.
    - [Advanced Usage](./advanced-usage.md)
- If you want parity check procedures or development operations including selfhost
  - [Development Operations Guide](./dev-operations.md)

## Smallest Examples for Pytra-Specific Decorators

`@extern`:

```python
from pytra.std import extern

@extern
def sin(x: float) -> float:
    ...
```

`@abi`:

```python
from pytra.std import abi

@abi(args={"parts": "value"}, ret="value")
def py_join(sep: str, parts: list[str]) -> str:
    ...
```

`@template`:

```python
from pytra.std.template import template

@template("T")
def py_min(a: T, b: T) -> T:
    ...
```

Notes:
- `@template` is currently v1 for linked runtime helpers, not for general user code.
- If you only want to transpile and run ordinary `.py` files, you do not need `@extern`, `@abi`, or `@template` at first.

## Small Nominal ADT Example

The nominal ADT v1 source surface is `@sealed` plus top-level variants plus `isinstance`.

```python
from dataclasses import dataclass

@sealed
class Maybe:
    pass

@dataclass
class Just(Maybe):
    value: int

class Nothing(Maybe):
    pass

def unwrap_or_zero(x: Maybe) -> int:
    if isinstance(x, Just):
        return x.value
    return 0
```

Notes:
- This is the current canonical user surface.
- The nominal ADT `match/case` contract is already fixed in the representative EAST3 / backend lane, but the source parser still treats `isinstance` plus field access as the canonical accepted surface.
- C++ is the representative backend. Other backends still fail closed on nominal ADT lanes according to the rollout policy.

## Related Links

- Python Compatibility Guide: [spec-python-compat.md](../spec/spec-python-compat.md)
- Specification Index: [index.md](../spec/index.md)
- User Specification: [spec-user.md](../spec/spec-user.md)
- Option Specification: [spec-options.md](../spec/spec-options.md)
- Tools Guide: [spec-tools.md](../spec/spec-tools.md)
