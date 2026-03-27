<a href="../../ja/tutorial/how-to-use.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# How to Use Pytra

This guide shows the execution steps for actually running Pytra.

## Run this one file first

`add.py`:

```python
def add(a: int, b: int) -> int:
    return a + b


if __name__ == "__main__":
    print(add(3, 4))
```

The shortest path to transpile it to C++, build it, and run it is:

```bash
./pytra add.py --output-dir out/add_case --build --run --exe add.out
```

Output:

```text
7
```

If you only want to inspect the transpiled result:

```bash
./pytra add.py --output-dir out/add_case
```

If you want Rust instead, only change `--target`:

```bash
./pytra add.py --target rs --output-dir out/rs_case
```

## Supported languages

Languages accepted by `--target`:

`cpp`, `rs`, `cs`, `js`, `ts`, `go`, `java`, `kotlin`, `swift`, `ruby`, `lua`, `scala`, `php`, `nim`, `dart`, `julia`, `zig`

For all languages, multi-file output with `--output-dir` is the canonical path.

## Main options

| Option | Description |
|---|---|
| `--target <lang>` | Output language. Default: `cpp` |
| `--output-dir <dir>` | Output directory. Default: `out/` |
| `--build` | C++ only. Compile after transpilation |
| `--run` | Use with `--build`. Run after compilation |
| `--exe <name>` | Executable name to generate under `--output-dir` |
| `--help` | Show help |

## Input-code constraints

Pytra transpiles a subset of Python. The main constraints are:

- Write type annotations. Function arguments and return values must be annotated.
- Use `pytra.std.*`. You cannot directly import the Python standard library. Use shim modules under `pytra.std.*` instead.

```python
from pytra.std import math
from pytra.std.time import perf_counter
from pytra.std.pathlib import Path
```

- `typing` and `dataclasses` are exceptions. They may be imported directly when used only for annotations and decorators.
- Write `if __name__ == "__main__":`. Pytra requires it as the entry point.

See the [Python Compatibility Guide](../spec/spec-python-compat.md) for details.
See the [pylib module list](../spec/spec-pylib-modules.md) for supported modules.

## A slightly larger example

There are 18 samples under `sample/py/`, including practical programs such as Mandelbrot, ray tracing, and Game of Life.

```bash
# Transpile + build + run a sample in C++
./pytra sample/py/01_mandelbrot.py --output-dir out/mandelbrot --build --run --exe mandelbrot.out
```

## What to read next

- [Python Compatibility Guide](../spec/spec-python-compat.md) - unsupported syntax and differences from Python
- [Specification Index](../spec/index.md) - entry point into the language specification
- [How to Use `@extern`](./extern.md) - calling external functions
- [Troubleshooting](./troubleshooting.md) - when you get stuck
- [Advanced Usage](./advanced-usage.md) - `@abi`, `@template`, and more
- [Development Operations Guide](./dev-operations.md) - parity checks, local CI, and related workflows for developers
