# Pytra Implementation Status Notes

This page contains implementation-status details separated from `README.md`.

## Implemented Language Features

- Variable assignment (main cases for normal assignment, annotated assignment, and augmented assignment)
- Arithmetic and bit operations (`+ - * / // % ** & | ^ << >>`)
- Comparison operations (main cases for `== != < <= > >= in not in is is not`)
- Logical operations (`and or not`)
- Branching (`if / elif / else`)
- Loops (`while`, `for in <iterable>`, `for in range(...)`)
- Exceptions (main cases for `try / except / finally` and `raise`)
- Function definition, function call, and return values
- Class definition (single inheritance, `__init__`, class members, instance members)
- Basic conversion for `@dataclass`
- Strings (main f-string cases, `replace`, etc.)
- Containers (main cases for `list`, `dict`, `set`, `tuple`)
- Main cases of list/set comprehension
- Slices (`a[b:c]`)
- Recognition of `if __name__ == "__main__":` guard
- EAST conversion (`src/pytra/compiler/east.py`) and EAST-based C++ conversion (`src/py2cpp.py`)

## Implemented Built-in Functions

- `print`, `len`, `range`
- `int`, `float`, `str`
- `ord`, `bytes`, `bytearray`
- `min`, `max`
- `grayscale_palette`, `save_gif`, `write_rgb_png` (via EAST/C++ runtime)

## Supported Modules

For Python standard libraries, support is limited not only by module name but by specific functions below (unspecified items are unsupported).

- `math`
  - Common support (C++/C#/Rust/JS/TS/Go/Java):
    - `sqrt`, `sin`, `cos`, `tan`, `exp`, `log`, `log10`, `fabs`, `floor`, `ceil`, `pow`
    - constants: `pi`, `e`
  - Differences:
    - Swift/Kotlin use the Node backend approach, so implementation depends on JS/TS-side `math`.
    - C# is designed to map directly to `System.Math` (no dedicated separated `math` runtime).
- `time`
  - `perf_counter`
- `pathlib`
  - Common support (C++/Rust/C#/JS/TS/Go/Java/Swift/Kotlin):
    - `Path(...)`, `pathlib.Path(...)`
    - `Path / "child"` (path join)
    - `exists`, `resolve`, `parent`, `name`, `stem`
    - `read_text`, `write_text`, `mkdir(parents, exist_ok)`
    - `str(Path)` (string conversion)
  - Implementation locations:
    - C++: `src/runtime/cpp/pytra/std/pathlib.h/.cpp`
    - Rust: `src/rs_module/py_runtime.rs` (`PyPath`)
    - C#: `src/cs_module/pathlib.cs` (`py_path`)
    - JS/TS: `src/js_module/pathlib.js`, `src/ts_module/pathlib.ts`
    - Go/Java: `src/go_module/py_runtime.go`, `src/java_module/PyRuntime.java`
    - Swift/Kotlin: because they use the Node backend approach, implementation depends on JS runtime (`src/js_module/pathlib.js`)
  - Differences:
    - This is not full Python `pathlib` compatibility; it is limited to Pytra's minimal common API.
    - `read_text` / `write_text` encoding is fixed to UTF-8 (arguments may be accepted for compatibility but ignored in some implementations).
- `dataclasses`
  - `@dataclass` decorator (expanded at conversion time)
  - C++ runtime helpers (minimal):
    - `dataclass(...)`, `DataclassTag`, `is_dataclass_v`
- `ast`
  - C++ implementation is removed (migrated to self-hosted EAST parser).

- Custom libraries:
  - `pytra.utils.png`
    - `write_rgb_png(path, width, height, pixels)`
  - `pytra.utils.gif`
    - `save_gif(path, width, height, frames, palette, delay_cs, loop)`
    - `grayscale_palette()`
  - `pytra.utils.assertions`
    - `py_assert_true`, `py_assert_eq`, `py_assert_all`, `py_assert_stdout`
- Per-target runtime locations:
  - `src/runtime/cpp`, `src/cs_module`, `src/rs_module`
  - `src/js_module`, `src/ts_module`
  - `src/go_module`, `src/java_module`
  - `src/swift_module`, `src/kotlin_module`

## In Progress

- Strengthening static type reflection for Go/Java (reducing degradation to `any`/`Object`)
- Optimizing `bytes` / `bytearray` paths for Go/Java

## EAST Implementation Status

- `src/pytra/compiler/east.py`
  - EAST conversion available for `test/fixtures` 32/32 and `sample/py` 16/16
  - `range(...)` is normalized to `ForRange` / `RangeExpr`; raw `Call(Name("range"))` is not passed downstream
- `src/py2cpp.py`
  - `sample/py` 16/16 passes through `transpile -> compile -> run`
  - Runtime integration for `append/extend/pop`, `perf_counter`, `min/max`, `save_gif` / `write_rgb_png` / `grayscale_palette`
- Benchmark
  - See latest measurements under `sample/` for list/details

## Not Implemented

- Full Python syntax compatibility (currently subset support)
- Slice forms other than `a[b:c]`
- Comprehensive standard library coverage
- Parts of advanced type inference and control-flow analysis
- Full support for dynamic import / dynamic typing

## Not Planned

- Full byte-for-byte compatibility with all Python syntax
- Advanced GC compatibility including circular references and weak references
- Full reproduction of all dynamic execution features (e.g., dynamic import)

