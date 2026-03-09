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

1. Check how to run it: [Usage Guide](../how-to-use.md)
2. Check the spec entry point: [Specification Index](../spec/index.md)
3. Check type inference details: [Type Inference Rules](../spec/spec-east.md#7-type-inference-rules)
4. Check `@extern` / `extern(...)`: [extern.md](./extern.md)
5. Check `@template`: [Template Specification (Draft)](../spec/spec-template.md)
6. Check how to read errors and common blockers: [troubleshooting.md](./troubleshooting.md)

## How To Choose Pages

- If you want to transpile `.py` files into target languages and run them
  - [Usage Guide](../how-to-use.md)
- If you want type inference details
  - [Type Inference Rules](../spec/spec-east.md#7-type-inference-rules)
- If you want the source-of-truth specs
  - [Specification Index](../spec/index.md)
- If you want error categories and common blockers
  - [troubleshooting.md](./troubleshooting.md)
- If you want Pytra-specific decorators
  - `@template`: [Template Specification (Draft)](../spec/spec-template.md)
  - `@extern` / `extern(...)`: [extern.md](./extern.md)
  - `@abi`: [ABI Specification](../spec/spec-abi.md)
- If you want `py2x.py` / `ir2lang.py` direct-entry workflows, parity checks, or selfhost-related runbooks
  - [Usage Guide](../how-to-use.md)

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

## Related Links

- Specification Index: [index.md](../spec/index.md)
- User Specification: [spec-user.md](../spec/spec-user.md)
- Option Specification: [spec-options.md](../spec/spec-options.md)
- Tools: [spec-tools.md](../spec/spec-tools.md)
