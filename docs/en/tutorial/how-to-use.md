<a href="../../ja/tutorial/how-to-use.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# Usage Guide

This document is an execution runbook for actually running Pytra.
For normative input constraints and language specification, see the [Specification Index](../spec/index.md).
For type inference details, see [Type Inference Rules in the EAST Specification](../spec/spec-east.md#7-type-inference-rules).

## Run This One File First

At the beginning, it is faster to run one small example yourself than to start by reading fixture files.

`add.py`:

```python
def add(a: int, b: int) -> int:
    return a + b


if __name__ == "__main__":
    print(add(3, 4))
```

The shortest way to transpile this to C++ and immediately build and run it is:

```bash
./pytra add.py --output-dir out/add_case --build --run --exe add.out
```

Expected stdout:

```text
7
```

If you want to inspect the generated code first, use single-file output.

```bash
./pytra add.py --output out/add.cpp
```

If you want Rust instead, just change `--target`.

```bash
./pytra add.py --target rs --output out/add.rs
```

Later sections on this page also use `test/fixtures/...` examples, but keeping this `add.py` as the baseline makes things easiest.

## Unified CLI (`./pytra`) Usage

Root `./pytra` is a unified launcher that calls `python3 src/pytra-cli.py`.

```bash
# Help
./pytra --help

# Single-file C++ output
./pytra test/fixtures/core/add.py --output /tmp/add.cpp

# Single-file Rust output
./pytra test/fixtures/core/add.py --target rs --output /tmp/add.rs

# Multi-file C++ output (with manifest)
./pytra test/fixtures/core/add.py --output-dir out/add_case

# Multi-file Rust output under out/
./pytra test/fixtures/core/add.py --target rs --output-dir out/rs_case

# Transpile + build + run
./pytra test/fixtures/core/add.py --build --output-dir out/add_case --exe add.out --run
```

Notes:
- `--target` supports `cpp` and `rs`.
- `--build` supports `--target cpp` only (Rust is transpile-only).
- Generated-code optimization level can be set with `--codegen-opt {0,1,2,3}`.
- `--target cpp --codegen-opt 3` is the max Pytra codegen route for C++. Internally it runs raw `EAST3` → linked-program optimizer → backend restart.
- `--opt -O3` is the C++ compiler flag used during `--build`, and is separate from `--codegen-opt 3`.
- `--target cpp --codegen-opt 3` assumes multi-file output. In transpile-only mode, use `--output-dir` instead of `--output`.
- In `--build` mode, generated artifacts (`src/*.cpp`, `include/*.h`, `.obj/*.o`, executable) are written under `--output-dir` (default: `out/`).
- `--exe` sets executable name/output path. Relative values (e.g. `add.out`) are generated under `--output-dir`.
- When `--output` is omitted, Rust transpilation writes to `--output-dir/<input-stem>.rs` (e.g. `out/rs_case/add.rs`).
- For temporary outputs, prefer consolidating into `out/`, and use `/tmp` only when shared temporary inspection is really needed.

## PowerShell Backend (Experimental)

PowerShell is implemented as an independent target backend that generates native PowerShell code directly.
The original plan was a `pwsh + py2cs` host profile (a thin wrapper around the C# backend), but after an experimental direct PowerShell emitter proved viable, the strategy was changed to a pure PowerShell backend.

For details on the retired C# host profile plan, see the [archive](../plans/archive/20260312-p5-powershell-csharp-host-profile.md).

## Constraints To Check First

- Direct import of Python standard library modules is generally not recommended. Use `pytra.std.*`.
- Exception: `typing` imports are allowed as annotation-only no-op imports (`import typing`, `from typing import ...`) and are not retained as runtime/dependency imports.
- Exception: `dataclasses` imports are allowed as decorator-resolution no-op imports (`import dataclasses`, `from dataclasses import ...`) and are not retained as runtime/dependency imports.
- Modules like `math`, `random`, `timeit`, and `enum` are used at runtime through normalized `pytra.std.*` shims.
- Importable modules are limited to those under `src/pytra/` (`pytra.std.*`, `pytra.utils.*`, `pytra.compiler.*`) and user-authored `.py` modules.
- User module imports are handled in multi-file transpilation. Besides `from helper import f`, relative forms such as `from .helper import f`, `from ..pkg import y`, `from .. import helper`, and `from .helper import *` are also normalized statically.
- Relative imports that escape above the entry root fail closed as `input_invalid(kind=relative_import_escape)`.
- See [Module Index](../spec/spec-pylib-modules.md) for supported modules and APIs.
- See [Option Specification](../spec/spec-options.md) for option policy and candidates.
- See [Tools Guide](../spec/spec-tools.md) for helper script purposes.
- For normative constraint definitions, see the [Specification Index](../spec/index.md).

## Next Pages To Read

- For the language specification entry point, see the [Specification Index](../spec/index.md).
- For type inference details, see [Type Inference Rules](../spec/spec-east.md#7-type-inference-rules).
- For `@extern` / `extern(...)` usage, see [extern.md](./extern.md).
- To use `py2x.py` / `east2cpp.py` directly, see [transpiler-cli.md](./transpiler-cli.md).
- For error categories and common blockers, see [troubleshooting.md](./troubleshooting.md).
- For advanced transpilation routes and `@abi`, see [Advanced Usage](./advanced-usage.md).
- For parity / local CI / backend health runbooks, see [Development Operations Guide](./dev-operations.md).
- For CLI option details, see the [Option Specification](../spec/spec-options.md).
