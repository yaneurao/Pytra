# `src/pytra/` Module Index

This page lists supported modules and public APIs under `src/pytra/`.  
Names starting with `_` are treated as internal implementation details and are out of support scope.
If you call functions/classes not listed here, transpilation-time errors or target-language compile errors may occur.

## 0. `pylib` Placement Policy (Purpose)

- `src/pytra/std/`:
  - Purpose: Area for providing **alternative implementations** of Python standard modules (`json`, `pathlib`, `sys`, `typing`, `os`, `glob`, `argparse`, `re`, `dataclasses`, `enum`, etc.).
  - Policy: In transpilation target code, avoid importing Python standard modules directly and use `pytra.std.*` instead.
  - Rule: Python-standard-module alternatives should, in principle, be placed in `src/pytra/std/`.
- `src/pytra/utils/`:
  - Purpose: Area for Pytra-specific features (e.g., EAST conversion, image output helpers, assertion helpers).
  - Policy: Put transpiler/runtime-driven features here when they are not Python-standard-module alternatives.
  - Rule: Pytra-specific modules must be placed in `src/pytra/utils/`.

## 1. Python Standard Module Alternatives (Compatibility Layer)

- `pytra.std.pathlib` (`pathlib` replacement)
  - class: `Path`
  - Main `Path` members: `parent`, `parents`, `name`, `suffix`, `stem`, `resolve()`, `exists()`, `mkdir(parents=False, exist_ok=False)`, `read_text()`, `write_text()`, `glob()`, `cwd()`
- `pytra.std.json` (`json` replacement)
  - functions: `loads(text)`, `dumps(obj, ensure_ascii=True, indent=None, separators=None)`
- `pytra.std.sys` (`sys` replacement)
  - variables: `argv`, `path`, `stderr`, `stdout`
  - functions: `exit(code=0)`, `set_argv(values)`, `set_path(values)`, `write_stderr(text)`, `write_stdout(text)`
- `pytra.std.typing` (`typing` replacement)
  - type aliases: `Any`, `List`, `Set`, `Dict`, `Tuple`, `Iterable`, `Sequence`, `Mapping`, `Optional`, `Union`, `Callable`, `TypeAlias`
  - function: `TypeVar(name)`
- `pytra.std.os` (`os` replacement, minimal implementation)
  - variable: `path`
  - main `path` members: `join`, `dirname`, `basename`, `splitext`, `abspath`, `exists`
  - functions: `getcwd()`, `mkdir(path)`, `makedirs(path, exist_ok=False)`
- `pytra.std.glob` (`glob` replacement, minimal implementation)
  - function: `glob(pattern)`
- `pytra.std.argparse` (`argparse` replacement, minimal implementation)
  - classes: `ArgumentParser`, `Namespace`
  - main `ArgumentParser` features: `add_argument(...)`, `parse_args(...)`
- `pytra.std.re` (`re` replacement, minimal implementation)
  - constant: `S`
  - class: `Match`
  - functions: `match(pattern, text, flags=0)`, `sub(pattern, repl, text, flags=0)`
- `pytra.std.dataclasses` (`dataclasses` replacement, minimal implementation)
  - decorator: `dataclass`
- `pytra.std.enum` (`enum` replacement, minimal implementation)
  - classes: `Enum`, `IntEnum`, `IntFlag`
  - constraint: Use `NAME = expr` form for class-body members.

## 2. Pytra-Specific Modules

- `pytra.utils.assertions`
  - functions: `py_assert_true(cond, label="")`, `py_assert_eq(actual, expected, label="")`, `py_assert_all(results, label="")`, `py_assert_stdout(expected_lines, fn)`
- `pytra.utils.png`
  - function: `write_rgb_png(path, width, height, pixels)`
- `pytra.utils.gif`
  - functions: `grayscale_palette()`, `save_gif(path, width, height, frames, palette, delay_cs=4, loop=0)`
- `pytra.compiler.east`
  - classes/constants: `EastBuildError`, `BorrowKind`, `INT_TYPES`, `FLOAT_TYPES`
  - functions: `convert_source_to_east(...)`, `convert_source_to_east_self_hosted(...)`, `convert_source_to_east_with_backend(...)`, `convert_path(...)`, `render_east_human_cpp(...)`, `main()`
- `pytra.compiler.east_parts.east_io`
  - functions: `extract_module_leading_trivia(source)`, `load_east_from_path(input_path, parser_backend="self_hosted")`

