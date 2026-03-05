<a href="../../ja/spec/spec-user.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# User Specification (Pytra)

This document summarizes usage and input constraints for Pytra.
This file is the normative specification; executable command workflows are maintained in [Usage Guide](../how-to-use.md).

## 1. Purpose

Pytra transpiles type-annotated Python code into multiple languages. The canonical CLI entrypoint is `src/py2x.py`.

- Python -> C# (`python src/py2x.py --target cs ...`)
- Python -> C++ (`python src/py2x.py --target cpp ...`)
- Python -> Rust (`python src/py2x.py --target rs ...`)
- Python -> JavaScript (`python src/py2x.py --target js ...`)
- Python -> TypeScript (`python src/py2x.py --target ts ...`)
- Python -> Go (`python src/py2x.py --target go ...`)
- Python -> Java (`python src/py2x.py --target java ...`)
- Python -> Swift (`python src/py2x.py --target swift ...`)
- Python -> Kotlin (`python src/py2x.py --target kotlin ...`)
- Python -> Ruby (`python src/py2x.py --target ruby ...`)
- Python -> Lua (`python src/py2x.py --target lua ...`)
- Python -> PHP (`python src/py2x.py --target php ...`)

## 2. Python Input Specification

- Input Python is generally expected to be type-annotated code.
- Type annotations may be omitted under the following conditions (implicit type inference):
  - Assignment with a literal RHS and uniquely determined type (e.g., `x = 1`, `y = 1.5`, `s = "abc"`).
  - Simple assignment where RHS variable type is already known (e.g., `y = x` when `x` type is determined).
- `class` supports single inheritance.
- Assignments to `self.xxx` inside `__init__` are treated as instance members.
- Members declared in class body are treated as class members (`static` in C#, `inline static` in C++).
- Classes with `@dataclass` are treated as dataclasses, generating fields and constructor.
- Supports `import` / `from ... import ...`.
- `from ... import *` (wildcard import) is supported (relative import is still unsupported).
- In transpilation target code, direct imports of Python standard modules (`json`, `pathlib`, `sys`, `os`, `glob`, `argparse`, `re`, etc.) are prohibited.
- Exception: `typing` imports (`import typing`, `from typing import ...`) are allowed as annotation-only no-op imports and are removed from runtime/dependency import resolution.
- Exception: `dataclasses` imports (`import dataclasses`, `from dataclasses import ...`) are allowed as decorator-resolution no-op imports and are removed from runtime/dependency import resolution.
- Importable modules are modules under `src/pytra/` and user-authored `.py` modules.
- User module import is legal by specification, but multi-file dependency resolution is still under staged implementation.
- Attribute access/method calls on `object` type (including `Any`-derived routes) are prohibited.
  - Example: for `x: object`, `x.foo()` / `x.bar` is not allowed.
  - If required, explicitly assign to a variable with a concrete type first, then access.
- For C++, comment-based passthrough is available.
  - Place `# Pytra::cpp ...` / `# Pytra::pass ...` immediately before a statement to inject that line directly into generated C++.
  - For multi-line blocks, use `# Pytra::cpp begin` ... `# Pytra::cpp end` (or `pass`).
  - See [EAST Specification](./spec-east.md) for details.

## 3. Test Case Policy

- Place input Python cases under `test/fixtures/` (category-based subdirectories).
- Per-language transpilation outputs go to `test/transpile/cs/`, `test/transpile/cpp/`, `test/transpile/rs/`, `test/transpile/js/`, `test/transpile/ts/`, `test/transpile/go/`, `test/transpile/java/`, `test/transpile/swift/`, `test/transpile/kotlin/`, `test/transpile/ruby/`, `test/transpile/lua/`, `test/transpile/php/`.
- Do not modify `test/fixtures/` input cases for transpiler convenience. If transpilation fails, fix the transpiler implementation.
- Use descriptive `snake_case` for case naming (e.g., `dict_get_items.py`).

Standard `test/` structure:

```text
test/
  unit/         # unittest code (test_*.py)
  integration/  # integration test code
  fixtures/     # source Python cases for transpilation (*.py, by category)
    core/
    control/
    strings/
    imports/
    collections/
    oop/
    typing/
    stdlib/
    signature/
  transpile/    # transpilation artifacts and runtime artifacts (not tracked by Git)
```

- `test/transpile/` is a disposable artifact area. Delete and regenerate fully as needed.

## 4. Sample Program Policy

- Place practical samples under `sample/py/`.
- Per-language transpilation outputs go to `sample/cpp/`, `sample/rs/`, `sample/cs/`, `sample/js/`, `sample/ts/`, `sample/go/`, `sample/java/`, `sample/swift/`, `sample/kotlin/`, `sample/ruby/`, `sample/lua/`, `sample/php/`.
- Use `sample/obj/` and `sample/out/` for binaries/intermediate artifacts (not tracked by Git).
- For user libraries imported from Python, use modules under `src/pytra/` (`pytra.std.*`, `pytra.utils.*`).
  - Images: `from pytra.utils import png`, `from pytra.utils.gif import save_gif`
  - Test helpers: `from pytra.utils.assertions import py_assert_eq`, etc.
  - EAST converter: `python src/toolchain/compiler/east.py <input.py> ...`
- Image output samples (`sample/py/01`, `02`, `03`) output PNG.
- GIF samples output to `sample/out/*.gif`.

## 5. How To Run Unit Tests

Run the following from project root (`Pytra/`):

```bash
python -m unittest discover -s test/unit -p "test_*.py" -v
```

If you want to verify only the shared emitter foundation (`src/backends/common/emitter/code_emitter.py`):

```bash
python -m unittest discover -s test/unit/common -p "test_code_emitter.py" -v
```

Dedicated test to run all `test/fixtures/**/*.py` and verify trailing output `True`:

```bash
python -m unittest discover -s test/unit/common -p "test_fixtures_truth.py" -v
```

## 6. Usage Notes

- Use `-O3 -ffast-math -flto` for C++ speed comparisons.
- Unsupported syntax fails at transpilation time with `TranspileError`.
- `test/transpile/obj/`, `test/transpile/cpp2/`, `sample/obj/`, `sample/out/` are artifact directories.
- For Python samples that use modules under `src/pytra/`, run with `PYTHONPATH=src` when needed.

## 7. Related Documents

- How to use: [Usage Guide](../how-to-use.md)
- py2cpp feature support matrix (with test evidence): [C++ Support Matrix](../language/cpp/spec-support.md)
- Sample code: [Sample Code](../../sample/readme.md)
- Detailed implementation status: [Pytra WIP Plan](../plans/pytra-wip.md)
