# Implementation Specification (Pytra)

<a href="../docs-jp/spec-dev.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>


This document summarizes transpiler implementation policy, structure, and conversion rules.

## 1. Repository Layout

- `src/`
  - `py2cs.py`, `py2cpp.py`, `py2rs.py`, `py2js.py`, `py2ts.py`, `py2go.py`, `py2java.py`, `py2swift.py`, `py2kotlin.py`
  - Place only transpiler entry scripts (`py2*.py`) directly under `src/`.
  - `common/`: shared base implementations and utilities used across multiple languages
  - `profiles/`: language-difference JSON for `CodeEmitter` (types/operators/runtime-call/syntax)
  - `runtime/cpp/`, `cs_module/`, `rs_module/`, `js_module/`, `ts_module/`, `go_module/`, `java_module/`, `swift_module/`, `kotlin_module/`: runtime helpers for each target language
  - `pytra/`: canonical Python-side shared library
- `test/`: `py` inputs and converted outputs for each target language
- `sample/`: practical sample inputs and converted outputs for each language
- `docs/`: specifications, usage guides, and implementation status

### 1.1 `src/pytra/` Public API (Implementation Baseline)

`src/pytra/` is the source of truth for shared Python libraries including selfhost.
Names starting with `_` are treated as internal. The following are public APIs.

- Direct import of standard library modules from transpiled code is forbidden.
- Allowed imports are `pytra.*` and user-authored modules (`.py`).

- `pytra.utils.assertions`
  - Functions: `py_assert_true`, `py_assert_eq`, `py_assert_all`, `py_assert_stdout`
- `pytra.std.pathlib`
  - class: `Path`
  - Members: `parent`, `parents`, `name`, `suffix`, `stem`, `resolve`, `exists`, `mkdir`, `read_text`, `write_text`, `glob`, `cwd`
- `pytra.std.json`
  - Functions: `loads`, `dumps`
- `pytra.std.sys`
  - Variables: `argv`, `path`, `stderr`, `stdout`
  - Functions: `exit`, `set_argv`, `set_path`, `write_stderr`, `write_stdout`
- `pytra.std.typing`
  - Type names: `Any`, `List`, `Set`, `Dict`, `Tuple`, `Iterable`, `Sequence`, `Mapping`, `Optional`, `Union`, `Callable`, `TypeAlias`
  - Functions: `TypeVar`
- `pytra.std.os`
  - Variable: `path` (`join`, `dirname`, `basename`, `splitext`, `abspath`, `exists`)
  - Functions: `getcwd`, `mkdir`, `makedirs`
- `pytra.std.glob`
  - Function: `glob`
- `pytra.std.argparse`
  - Classes: `ArgumentParser`, `Namespace`
  - Functions: `ArgumentParser.add_argument`, `ArgumentParser.parse_args`
- `pytra.std.re`
  - Constant: `S`
  - Class: `Match`
  - Functions: `match`, `sub`
- `pytra.std.dataclasses`
  - Decorator: `dataclass`
- `pytra.std.enum`
  - Classes: `Enum`, `IntEnum`, `IntFlag`
- `pytra.utils.png`
  - Function: `write_rgb_png`
- `pytra.utils.gif`
  - Functions: `grayscale_palette`, `save_gif`
- `pytra.compiler.east`
  - Classes/constants: `EastBuildError`, `BorrowKind`, `INT_TYPES`, `FLOAT_TYPES`
  - Functions: `convert_source_to_east`, `convert_source_to_east_self_hosted`, `convert_source_to_east_with_backend`, `convert_path`, `render_east_human_cpp`, `main`
- `pytra.compiler.east_parts.east_io`
  - Functions: `extract_module_leading_trivia`, `load_east_from_path`

### Current enum Support

- Input side uses `from pytra.std.enum import Enum, IntEnum, IntFlag` (standard `enum` module is not allowed).
- Class bodies of `Enum` / `IntEnum` / `IntFlag` support `NAME = expr` member definitions.
- C++ lowering uses `enum class`.
  - `IntEnum` / `IntFlag` generate helper comparison operators with `int64`.
  - `IntFlag` generates helper operators for `|`, `&`, `^`, `~`.

## 2. C# Conversion Spec (`py2cs.py`)

- Parses Python AST and generates C# code with a `Program` class.
- Converts `import` / `from ... import ...` into `using`.
- Main type mapping:
  - `int -> int`
  - `float -> double`
  - `str -> string`
  - `bool -> bool`
  - `None -> void` (for return annotation)
- Class members are emitted as `public static`.
- `self` attributes initialized in `__init__` are generated as instance members.

## 3. C++ Conversion Spec (`py2cpp.py`)

- Parses Python AST and generates a single `.cpp` (with required includes).
- Detailed support granularity (`enumerate(start)`, `lambda`, comprehensions, etc.) is managed in `docs/language/cpp/spec-support.md`.
- Generated code uses runtime helpers under `src/runtime/cpp/`.
- Helper functions are not inlined into generated `.cpp`; use `runtime/cpp/pytra/built_in/py_runtime.h`.
- Not only `json`: standard-library-equivalent features use `src/pytra/std/*.py` as source of truth, and should not be reimplemented independently in `runtime/cpp`.
  - C++ side should use transpiled results of these Python source modules.
- Classes are emitted as C++ classes inheriting `pytra::gc::PyObj` (except exception classes).
- Class members are emitted as `inline static`.
- `@dataclass` generates field definitions and constructors.
- Supports `raise` / `try` / `except` / `while`.
- list/string bounds checks are controlled by `--bounds-check-mode`.
  - `off` (default): normal `[]` access
  - `always`: runtime-checked `py_at_bounds`
  - `debug`: debug-build-only checked `py_at_bounds_debug`
- `//` floor division is controlled by `--floor-div-mode`.
  - `native` (default): emit C++ `/` directly
  - `python`: emit `py_floordiv` to follow Python floor-division semantics
- `%` modulo is controlled by `--mod-mode`.
  - `native` (default): emit C++ `%` directly
  - `python`: insert runtime helper for Python modulo semantics
- Output integer width is controlled by `--int-width`.
  - `64` (default): `int64`/`uint64`
  - `32`: `int32`/`uint32`
  - `bigint`: not implemented (error if specified)
- String index/slice is controlled by:
  - `--str-index-mode {byte,native}` (`codepoint` not implemented)
  - `--str-slice-mode {byte}` (`codepoint` not implemented)
  - Current `byte` / `native` return type of `str[i]` is `str` (single-character string)
  - Out-of-range behavior follows `--bounds-check-mode` (`off`/`always`/`debug`)
- Generation optimization level is controlled by `-O0` to `-O3`.
  - `-O0`: no optimization (debug/diff investigation)
  - `-O1`: light optimization
  - `-O2`: medium optimization
  - `-O3` (default): aggressive optimization
- Top namespace for generated C++ can be set with `--top-namespace NS`.
  - Omitted (default): no top namespace
  - With namespace: keep `main` global and call `NS::__pytra_main(...)`
- Negative indexing for list/string (example: `a[-1]`) is controlled by `--negative-index-mode`.
  - default `const_only`: enable Python-compatible handling only for constant negative indexes
  - `always`: enable Python-compatible handling for all index accesses
  - `off`: disable Python-compatible negative-index handling and emit plain `[]`
- PNG identity check criterion is exact byte-for-byte file equality.
- GIF identity check criterion is also exact byte-for-byte file equality.

### 3.1 import and `runtime/cpp` Mapping

`py2cpp.py` emits includes according to import statements.

- `import pytra.std.math` -> `#include "pytra/std/math.h"`
- `import pytra.std.pathlib` -> `#include "pytra/std/pathlib.h"`
- `import pytra.std.time` / `from pytra.std.time import ...` -> `#include "pytra/std/time.h"`
- `from pytra.std.dataclasses import dataclass` -> `#include "pytra/std/dataclasses.h"`
- `import pytra.utils.png` -> `#include "pytra/utils/png.h"`
- `import pytra.utils.gif` -> `#include "pytra/utils/gif.h"`
- GC always uses `#include "runtime/cpp/pytra/built_in/gc.h"`

`module.attr(...)` calls are resolved to C++ side by `LanguageProfile` (JSON) mapping or module-name-to-namespace fallback.

- Example: `runtime_calls.module_attr_call.pytra.std.sys.write_stdout -> pytra::std::sys::write_stdout`
- If mapping is undefined, derive C++ namespace from imported module and fall back to `ns::attr(...)`.
- At startup, profile JSON is loaded; undefined fields are filled by common defaults and fallback rules.

Notes:

- Canonical import source is EAST `meta.import_bindings` (`ImportBinding[]`).
- `from module import symbol` is normalized into EAST `meta.qualified_symbol_refs` (`QualifiedSymbolRef[]`), with alias resolution completed before backend.
- `meta.import_modules` / `meta.import_symbols` remain for compatibility and are derived from canonical data.
- `import module as alias` resolves `alias.attr(...)` as `module.attr(...)`.
- `from module import *` is unsupported.
- Relative import (`from .mod import x`) is currently unsupported; detection returns `input_invalid`.
- `pytra` namespace is reserved. `pytra.py` / `pytra/__init__.py` under input root is treated as conflict and returns `input_invalid`.
- User module lookup is relative to input file parent directory (`foo.bar` -> `foo/bar.py` or `foo/bar/__init__.py`).
- Unresolved user-module import and circular import fail early with `input_invalid`.
- If only `from M import S` exists, then referencing `M.T` is `input_invalid` (`kind=missing_symbol`) because `M` is not bound.

Main helper module implementations:

- `src/runtime/cpp/pytra/std/math.h`, `src/runtime/cpp/pytra/std/math.cpp`
- `src/runtime/cpp/pytra/std/pathlib.h`, `src/runtime/cpp/pytra/std/pathlib.cpp`
- `src/runtime/cpp/pytra/std/time.h`, `src/runtime/cpp/pytra/std/time.cpp`
- `src/runtime/cpp/pytra/std/dataclasses.h`, `src/runtime/cpp/pytra/std/dataclasses.cpp`
- `src/runtime/cpp/pytra/std/json.h`, `src/runtime/cpp/pytra/std/json.cpp`
- `src/runtime/cpp/pytra/std/typing.h`, `src/runtime/cpp/pytra/std/typing.cpp`
- `src/runtime/cpp/pytra/built_in/gc.h`, `src/runtime/cpp/pytra/built_in/gc.cpp`
- `src/runtime/cpp/pytra/std/sys.h`, `src/runtime/cpp/pytra/std/sys.cpp`
- `src/runtime/cpp/pytra/utils/png.h`, `src/runtime/cpp/pytra/utils/png.cpp`
- `src/runtime/cpp/pytra/utils/gif.h`, `src/runtime/cpp/pytra/utils/gif.cpp`
- `src/runtime/cpp/pytra/utils/assertions.h`, `src/runtime/cpp/pytra/utils/assertions.cpp`
- `src/runtime/cpp/pytra/built_in/py_runtime.h`

Role of `src/runtime/cpp/pytra/built_in/`:

- Common layer implementing Python built-in types and foundational features in C++.
- Examples: GC, I/O, bytes helpers, container/string wrappers.
- Reused by language-specific modules (`src/runtime/cpp/pytra/std/*`, `src/runtime/cpp/pytra/utils/*`).
- `py_runtime.h` directly includes `str/path/list/dict/set` (`containers.h` removed).
- Include guards in `built_in` headers are unified with relative-path-derived `PYTRA_BUILT_IN_*` naming.

Container policy in `src/runtime/cpp/pytra/built_in/py_runtime.h`:

- `list<T>`: wrapper over `std::vector<T>` (provides `append`, `extend`, `pop`)
- `dict<K, V>`: wrapper over `std::unordered_map<K,V>` (provides `get`, `keys`, `values`, `items`)
- `set<T>`: wrapper over `std::unordered_set<T>` (provides `add`, `discard`, `remove`)
- `str`, `list`, `dict`, `set`, `bytes`, and `bytearray` are wrappers with Python-compatible APIs, not standard-container inheritance.

Constraints:

- Python modules imported by input should generally have corresponding runtime implementations in each target language.
- Helper functions used by generated code should be centralized into runtime modules of each language to avoid duplicate definitions in generated output.
- Attribute access or method calls on `object` values (including `Any`-origin values) are disallowed by language policy.
  - EAST/emit path must assume method calls on `object` receivers are not allowed.

### 3.2 Function Argument Passing Policy

- Expensive-to-copy types (`string`, `vector<...>`, `unordered_map<...>`, `unordered_set<...>`, `tuple<...>`) are passed as `const T&` when not directly mutated in function body.
- If direct mutation of the argument is detected, keep pass-by-value (or non-const).
- Mutation detection covers assignment, augmented assignment, `del`, and destructive method calls (`append`, `extend`, `insert`, `pop`, etc.).

### 3.3 Image Runtime Policy (PNG/GIF)

- `png` / `gif` use Python side (`src/pytra/utils/`) as source-of-truth implementation.
- `*_module` implementations in each language should, in principle, use transpiled artifacts from that source-of-truth Python implementation.
- Handwritten language-specific code should be minimized to required scope for performance/I/O reasons.
- Cross-language consistency is primarily judged by exact byte equality of generated files.
- `src/pytra/utils/png.py` uses pure Python implementation independent of `binascii` / `zlib` / `struct` (CRC32/Adler32/DEFLATE stored block).
- Acceptance criteria:
  - During replacement work, output bytes from `src/pytra/utils/*.py` and each language runtime output must match for identical input.
  - In C++, run `tools/verify_image_runtime_parity.py` and confirm minimal PNG/GIF parity.

### 3.4 Python Helper Library Naming

- Legacy compatibility name `pylib.runtime` has been removed; canonical name is `pytra.utils.assertions`.
- Test helper functions (`py_assert_*`) must be used via `from pytra.utils.assertions import ...`.

### 3.5 Image Runtime Optimization Policy (`py2cpp`)

- Target files: `src/runtime/cpp/pytra/utils/png.cpp` / `src/runtime/cpp/pytra/utils/gif.cpp` (auto-generated).
- Preconditions: keep `src/pytra/utils/png.py` / `src/pytra/utils/gif.py` as source-of-truth, and do not introduce semantic differences.
- Generation steps:
  - `python3 src/py2cpp.py src/pytra/utils/png.py -o /tmp/png.cpp`
  - `python3 src/py2cpp.py src/pytra/utils/gif.py -o /tmp/gif.cpp`
  - Artifacts are output directly to `src/runtime/cpp/pytra/utils/png.cpp` / `src/runtime/cpp/pytra/utils/gif.cpp`.
  - Do not add handwritten core logic to these two files.
  - Derive C++ namespace automatically from source Python path (no hardcoding).
    - Example: `src/pytra/utils/gif.py` -> `pytra::utils::gif`
    - Example: `src/pytra/utils/png.py` -> `pytra::utils::png`
- Allowed optimizations:
  - loop unrolling, `reserve` additions, temporary buffer reduction, etc., as long as output bytes are unchanged
  - lightweight bounds-check optimizations that do not change exception messages
- Disallowed by default:
  - optimizations that change image output format/spec behavior (PNG chunk layout, GIF control blocks, color-table order, etc.)
  - changes to defaults/format/rounding that diverge from Python source-of-truth
- Acceptance criteria:
  - `python3 tools/verify_image_runtime_parity.py` returns `True` after change.
  - `test/unit/test_image_runtime_parity.py` and `test/unit/test_py2cpp_features.py` pass.

## 4. Verification Procedure (C++)

1. Convert `test/fixtures` to `test/transpile/cpp` with Python transpiler.
2. Compile generated C++ into `test/transpile/obj/`.
3. Compare runtime results against Python execution results.
4. For selfhost verification, use self-converted executable to generate `test/fixtures` -> `test/transpile/cpp2`.
5. Confirm consistency between `test/transpile/cpp` and `test/transpile/cpp2`.

### 4.1 Goal Conditions for selfhost Verification

- Required:
  - `selfhost/py2cpp.cpp` generated from `selfhost/py2cpp.py` compiles successfully.
  - That executable can convert `sample/py/01_mandelbrot.py` to C++.
- Recommended checks:
  - Check source diff between version generated by `src/py2cpp.py` and version generated by `selfhost` (diff itself is allowed).
  - Compile/run converted C++ and confirm it matches Python runtime output.

### 4.2 Consistency Criteria (selfhost / normal comparison)

- Source-level equality:
  - Full textual equality of generated C++ is a reference metric, not a requirement.
- Runtime equality:
  - For same input, Python runtime result and generated C++ runtime result must match.
- Image equality:
  - For both PNG and GIF, exact byte equality of output files is required.

## 5. EAST-based C++ Path

- `src/pytra/compiler/east.py`: Python -> EAST JSON (canonical)
- `src/pytra/compiler/east_parts/east_io.py`: load EAST from `.py/.json` and supplement leading trivia (canonical)
- `src/pytra/compiler/east_parts/code_emitter.py`: common base utilities for multi-language emitters (node predicates/type-string helpers/`Any` safe conversion)
- `src/py2cpp.py`: EAST JSON -> C++
- `src/runtime/cpp/pytra/built_in/py_runtime.h`: consolidated C++ runtime
- Responsibility separation:
  - `range(...)` semantics are fully resolved during EAST build
  - `src/py2cpp.py` stringifies normalized EAST
  - language-agnostic helper logic is progressively centralized into `CodeEmitter`
- Output structure policy:
  - final goal is module-level multi-file output (`.h/.cpp`)
  - single `.cpp` output is treated as compatibility path during migration

### 5.1 CodeEmitter Test Policy

- Regression coverage for `src/pytra/compiler/east_parts/code_emitter.py` is provided by `test/unit/test_code_emitter.py`.
- Main targets:
  - output buffer ops (`emit`, `emit_stmt_list`, `next_tmp`)
  - dynamic-input safety (`any_to_dict`, `any_to_list`, `any_to_str`, `any_dict_get`)
  - node predicates (`is_name`, `is_call`, `is_attr`, `get_expr_type`)
  - type-string helpers (`split_generic`, `split_union`, `normalize_type_name`, `is_*_type`)
- When adding/changing `CodeEmitter` behavior, add/update tests in that file before rolling out changes to downstream emitters.

### 5.2 Responsibility Boundaries (CodeEmitter / EAST parser / shared compiler layer)

- `CodeEmitter` responsibilities:
  - Receive already-built EAST (`node` + `meta`) and emit target-language code strings via profile/hooks.
  - Own only codegen-local logic (scope handling, shared statement/expression lowering, syntax template expansion).
  - Do not own filesystem traversal, import-graph analysis, or project-wide dependency resolution.
- EAST parser (`src/pytra/compiler/east.py`) responsibilities:
  - Parse a single input module (`.py`) and produce a single-module EAST.
  - Handle language-agnostic normalization (for example, `range` lowering) and single-file symbol/type annotations.
  - Do not own cross-module import graph analysis or module index construction.
- Shared compiler layer responsibilities (incrementally extracted under `src/pytra/compiler/`):
  - Own FS-dependent import resolution, module EAST map construction, symbol index / type schema building, and deps dump generation.
  - Each `py2*.py` CLI should complete project-level analysis in this layer, then pass results into `CodeEmitter`.

## 6. LanguageProfile / CodeEmitter

- `CodeEmitter` handles language-agnostic skeleton responsibilities (node traversal, scope management, shared helper logic).
- Language-specific differences are defined in `LanguageProfile` JSON.
  - type mappings
  - operator mappings
  - runtime-call mappings
  - syntax templates
- Cases hard to express in JSON are handled by `hooks`.
- Canonical detailed schema is `docs/spec-language-profile.md`.

## 7. Common Implementation Rules

- Put only language-agnostic reusable logic in `src/common/`.
- Do not put language-specific specs (type mapping, keywords, runtime symbol names, etc.) into `src/common/`.
- Consolidate common CLI args (`input`/`output`/`--negative-index-mode`/`--parser-backend`, etc.) into `src/pytra/compiler/transpile_cli.py` and reuse them from each `py2*.py` `main()`.
- In selfhost-target code, avoid dynamic imports (`try/except ImportError` split imports, `importlib`) and use only static imports.
- Add Japanese comments (purpose explanations) to class names, function names, and member variable names.
- For standard-library compatibility documentation, specify function-level support, not only module names.
- Functions not documented are treated as unsupported.

## 8. Notes on Execution Modes by Target

- `py2rs.py`: native conversion mode (independent of Python interpreter at runtime)
- `py2js.py` / `py2ts.py`: native conversion mode (Node.js runtime)
- `py2go.py` / `py2java.py`: native conversion mode (independent of Python interpreter at runtime)
- `py2swift.py` / `py2kotlin.py`: Node-backend execution mode (independent of Python interpreter at runtime)
