<a href="../../ja/spec/spec-user.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# User Specification (Pytra)

This document summarizes usage and input constraints for Pytra.
This file is the normative specification; executable command workflows are maintained in [Usage Guide](../how-to-use.md).

## 1. Purpose

Pytra transpiles type-annotated Python code into multiple languages. The canonical CLI entrypoint is `src/pytra-cli.py`.

- Python -> C# (`python src/pytra-cli.py --target cs ...`)
- Python -> C++ (`python src/pytra-cli.py --target cpp ...`)
- Python -> Rust (`python src/pytra-cli.py --target rs ...`)
- Python -> JavaScript (`python src/pytra-cli.py --target js ...`)
- Python -> TypeScript (`python src/pytra-cli.py --target ts ...`)
- Python -> Go (`python src/pytra-cli.py --target go ...`)
- Python -> Java (`python src/pytra-cli.py --target java ...`)
- Python -> Swift (`python src/pytra-cli.py --target swift ...`)
- Python -> Kotlin (`python src/pytra-cli.py --target kotlin ...`)
- Python -> Ruby (`python src/pytra-cli.py --target ruby ...`)
- Python -> Lua (`python src/pytra-cli.py --target lua ...`)
- Python -> PHP (`python src/pytra-cli.py --target php ...`)

## 2. Python Input Specification

- Input Python is generally expected to be type-annotated code.
- Type annotations may be omitted under the following conditions (implicit type inference):
  - Assignment with a literal RHS and uniquely determined type (e.g., `x = 1`, `y = 1.5`, `s = "abc"`).
  - Simple assignment where RHS variable type is already known (e.g., `y = x` when `x` type is determined).
- In the self-hosted parser, type annotations on function arguments are recommended.
  - Unannotated arguments (e.g., `def f(x): ...`) are accepted and treated as `unknown`.
  - One-line definitions of the form `def f(...): return ...` (including class methods) are accepted.
- `class` supports single inheritance.
- Assignments to `self.xxx` inside `__init__` are treated as instance members.
- Members declared in class body are treated as class members (`static` in C#, `inline static` in C++).
- Classes with `@dataclass` are treated as dataclasses, generating fields and constructor.
- The nominal ADT declaration surface in v1 is defined as follows.
  - Declare the family as a top-level `class` annotated with `@sealed`.
  - Declare variants as top-level `class` declarations with exactly one base, the family class.
  - Variants with payload use `@dataclass`; unit variants use an ordinary class body.
  - The canonical constructor surface is an ordinary variant-class call (`Ok(...)`, `Err(...)`), and the family class itself is not a constructor entrypoint.
  - The canonical variant-access surface is `isinstance(x, Variant)` followed by field access in the success branch.
  - Nested variant classes, dedicated `adt` blocks, and namespace sugar such as `Result.Ok(...)` are outside v1.
- Nominal ADT destructuring via `match/case` has its contract fixed as the statement-first Stage B surface.
  - The current canonical source surface accepted directly by the selfhost parser remains Stage A: `isinstance` plus field access.
  - The representative EAST3 / backend lane already fixes `Match` / `VariantPattern` / `PatternBind` metadata, and source-parser acceptance of `match/case` will reuse that same contract.
  - A `match` over a closed family must be exhaustive. In v1, the canonical forms are either "list each variant exactly once" or "use a final `_` wildcard branch for the remaining variants."
  - Repeating the same variant or placing more branches after coverage is already closed is an error.
  - `match` expressions, guard patterns, and nested patterns are not part of the v1 accepted surface.
- Supports `import` / `from ... import ...`.
- Supports `from ... import *` (wildcard import).
- The canonical v1 surface for relative `from-import` is fixed as follows.
  - `from .m import x`
  - `from ..pkg import y`
  - `from .. import helper`
  - `from . import x`
  - `from .m import *`
  - Resolution is based on static module normalization against the importing file path and the entry root; runtime `__package__` is not consulted.
  - A relative import that escapes above the entry root fails closed as `input_invalid(kind=relative_import_escape)`.
  - If the normalized module does not exist, the diagnostic is `input_invalid(kind=missing_module)`.
  - Illegal Python syntax such as `import .m` is outside the supported surface.
- `type X = A | B | ...` (PEP 695) can declare a union type (tagged union).
  - Converted to each target language's native tagged union.
  - Recursive types (e.g., `type JsonVal = ... | list[JsonVal]`) are supported.
  - Use `typing.cast(T, v)` to extract a value from a union variable.
  - See [Tagged Union Specification](./spec-tagged-union.md) for details.
- In transpilation target code, **direct imports of Python standard modules are prohibited**. Use `pytra.*` for all such imports.
  - `from pytra.typing import cast` — instead of `typing.cast`
  - `from pytra.enum import Enum, IntEnum, IntFlag` — instead of `enum`
  - `from pytra.dataclasses import dataclass, field` — instead of `dataclasses`
  - `from pytra.types import int64, uint8` — Pytra-specific scalar types
  - `from pytra.std.collections import deque` — instead of `collections.deque`
  - `from pytra.std.math import sqrt` — instead of `math` and similar runtime modules
  - `pytra.typing` / `pytra.enum` / `pytra.dataclasses` / `pytra.types` are language-feature helper modules; the transpiler ignores these imports (the parser already recognizes `cast` / `Enum` / `dataclass` / `int64` etc.). At Python runtime they re-export from the standard library, so the code also runs as Python unchanged.
  - `pytra.std.*` is the runtime library; the transpiler uses it for dependency resolution and header generation.
  - Direct imports from Python standard modules such as `from typing import ...` / `from enum import ...` / `from dataclasses import ...` are errors.
- Importable modules are modules under `src/pytra/` and user-authored `.py` modules.
- User module import is legal by specification, but multi-file dependency resolution is still under staged implementation.
- Attribute access/method calls on `object` type (including `Any`-derived routes) are prohibited.
  - Example: for `x: object`, `x.foo()` / `x.bar` is not allowed.
  - If required, explicitly assign to a variable with a concrete type first, then access.
- `getattr(...)` / `setattr(...)` are not part of the user-language surface.
  - Generic dynamic attribute lookup/update by string name is unsupported by design.
  - This restriction exists so Pytra does not have to carry an open `object` / `Any` object model into every backend, and there is currently no plan to add general support.
  - If needed, use ordinary `x.field` access on a concrete type, `dict` / JSON objects, or dedicated seams such as `@extern` / ambient bindings.
- For C++, comment-based passthrough is available.
  - Place `# Pytra::cpp ...` / `# Pytra::pass ...` immediately before a statement to inject that line directly into generated C++.
  - For multi-line blocks, use `# Pytra::cpp begin` ... `# Pytra::cpp end` (or `pass`).
  - See [EAST Specification](./spec-east.md) for details.

## 3. Test Case Policy

- Place input Python cases under `test/fixtures/` (category-based subdirectories).
- Per-language transpilation outputs go to `work/transpile/cs/`, `work/transpile/cpp/`, `work/transpile/rs/`, `work/transpile/js/`, `work/transpile/ts/`, `work/transpile/go/`, `work/transpile/java/`, `work/transpile/swift/`, `work/transpile/kotlin/`, `work/transpile/ruby/`, `work/transpile/lua/`, `work/transpile/php/`.
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

- `work/transpile/` is a disposable artifact area. Delete and regenerate fully as needed.

## 4. Sample Program Policy

- Place practical samples under `sample/py/`.
- Per-language transpilation outputs go to `sample/cpp/`, `sample/rs/`, `sample/cs/`, `sample/js/`, `sample/ts/`, `sample/go/`, `sample/java/`, `sample/swift/`, `sample/kotlin/`, `sample/ruby/`, `sample/lua/`, `sample/php/`.
- Use `sample/obj/` and `sample/out/` for binaries/intermediate artifacts (not tracked by Git).
- For user libraries imported from Python, use modules under `src/pytra/` (`pytra.std.*`, `pytra.utils.*`).
  - Images: `from pytra.utils import png`, `from pytra.utils.gif import save_gif`
  - Test helpers: `from pytra.utils.assertions import py_assert_eq`, etc.
  - EAST converter: `python src/toolchain/misc/east.py <input.py> ...`
- Image output samples (`sample/py/01`, `02`, `03`) output PNG.
- GIF samples output to `sample/out/*.gif`.

## 5. How To Run Unit Tests

Run the following from project root (`Pytra/`):

```bash
python -m unittest discover -s test/unit -p "test_*.py" -v
```

If you want to verify only the shared emitter foundation (`src/toolchain/emit/common/emitter/code_emitter.py`):

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
- `work/transpile/obj/`, `work/transpile/cpp2/`, `sample/obj/`, `sample/out/` are artifact directories.
- For Python samples that use modules under `src/pytra/`, run with `PYTHONPATH=src` when needed.

## 7. Related Documents

- Quick reference for Python differences and unsupported features: [Python Compatibility Guide](./spec-python-compat.md)
- How to use: [Usage Guide](../tutorial/how-to-use.md)
- py2cpp feature support matrix (with test evidence): [C++ Support Matrix](../language/cpp/spec-support.md)
- Sample code: [Sample Code](../../sample/README.md)
- Detailed implementation status: [Pytra WIP Plan](../plans/archive/pytra-wip.md)
