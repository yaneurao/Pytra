<a href="../../ja/spec/spec-make.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# Makefile Generation and One-Shot Build Specification (Decision)

This document defines the operational specification to consolidate the C++ build flow into the common `pytra` CLI instead of direct `py2cpp.py` invocation.

## 1. Decisions

- The user entry point is `./pytra` (extensionless launcher).
- The main implementation entry point is `src/pytra/cli.py` (`python -m pytra.cli`).
- `py2cpp.py` remains as the transpile backend and does not own build orchestration responsibility.
- C++ build uses: canonical `manifest.json` + generated `Makefile` + `make` execution.
- Manual `PYTHONPATH` setup is unnecessary (`./pytra` sets it internally).

## 2. Objectives

- Shorten manual commands and make transpile-to-build a single command.
- Reuse existing multi-file output and `manifest.json` for reproducible build procedures.
- Establish an entry point extensible to future multi-target CLI (`--target` switching).

## 3. Non-goals

- Implement full build execution for all languages immediately (v1 is `--target cpp` only).
- Generate IDE-specific projects (Visual Studio/Xcode).
- Auto-inferred build flow that bypasses `manifest.json`.

## 4. Entry Point Specification

### 4.1 `./pytra` launcher

Place executable `pytra` (without extension) at repository root, and do the following:

1. Add `ROOT/src` to `PYTHONPATH`.
2. Execute `python3 -m pytra.cli "$@"`.

Intent:

- Eliminate repeated manual `PYTHONPATH=src ...` usage.
- Provide an executable form that avoids name conflicts with input-project-side `pytra.py`.

### 4.2 actual CLI

- Runtime entry implementation is `src/pytra/cli.py`.
- Direct invocation form is `python3 -m pytra.cli ...`.

## 5. Common CLI specification (v1)

### 5.1 Basic form

```bash
./pytra INPUT.py --target cpp [OPTIONS]
```

### 5.2 Required/supported arguments in v1

- `INPUT.py`
- `--target cpp`
- `--output-dir DIR` (default: `out`)
- `--build` (run build only when specified)

### 5.3 C++ build options when `--build` is specified

- `--compiler CXX` (default: `g++`)
- `--std STD` (default: `c++20`)
- `--opt FLAG` (default: `-O2`)
- `--exe NAME` (default: `app.out`)
- `--run` (optional: execute after successful build)

Notes:

- In this spec, `--opt` means C++ compiler flags.
- Codegen optimization level (`py2cpp` `-O0..-O3`) may be separated as `--codegen-opt {0,1,2,3}` (default applies when omitted).

### 5.4 Constraints

- `--build` is valid only with `--target cpp`.
- `--compiler/--std/--opt/--exe/--run` are valid only when `--build` is specified.
- If `--build` is specified with non-`cpp` target, exit with an error.

## 6. C++ build flow

Execution order for `./pytra ... --target cpp --build`:

1. Execute `py2cpp.py --multi-file --output-dir <DIR>` to generate `manifest.json`.
2. Generate `Makefile` via `tools/gen_makefile_from_manifest.py`.
3. Execute `make -f <Makefile>` to produce binary.
4. Only when `--run` is specified, execute `make -f <Makefile> run`.

## 7. `manifest.json` input specification

`manifest.json` must satisfy at least:

- `modules` is an array.
- Each element is an object and `source` is a non-empty string.
- `include_dir` is a string (if omitted, implementation may default to sibling `include` next to `manifest`).

Example:

```json
{
  "entry": "path/to/main.py",
  "include_dir": "out/include",
  "src_dir": "out/src",
  "modules": [
    {
      "module": "path/to/main.py",
      "label": "main",
      "header": "out/include/main.h",
      "source": "out/src/main.cpp",
      "is_entry": true
    }
  ]
}
```

## 8. Makefile generation specification

Use `tools/gen_makefile_from_manifest.py`, accepting:

- Positional argument
  - `manifest`
- Options
  - `-o`, `--output`
  - `--exe`
  - `--compiler`
  - `--std`
  - `--opt`

Generated `Makefile` must include at least:

- Variables: `CXX`, `CXXFLAGS`, `INCLUDES`, `SRCS`, `OBJS`, `TARGET`
- Targets: `all`, `$(TARGET)`, `%.o: %.cpp`, `run`, `clean`

## 9. Error contract

Exit non-zero in the following cases:

- `manifest` does not exist.
- JSON parsing fails.
- `modules` is not an array.
- No valid `source` is found.
- `--compiler/--std/--opt/--exe/--run` is specified without `--build`.
- `--build` is specified with non-`cpp` target.
- `make` is not available.

## 10. Acceptance criteria

- `./pytra sample/py/01_mandelbrot.py --target cpp --output-dir out/mandelbrot` generates multi-file outputs.
- `./pytra sample/py/01_mandelbrot.py --target cpp --build --output-dir out/mandelbrot` runs transpile, Makefile generation, and build continuously.
- `./pytra sample/py/01_mandelbrot.py --target cpp --build --compiler g++ --std c++20 --opt -O3 --exe mandelbrot.out` reflects the specified values in generated `Makefile` and build.
- `./pytra sample/py/01_mandelbrot.py --target rs --build` exits with an error per spec.
- Second run of `make -f out/mandelbrot/Makefile` is incremental (minimal relink/recompile).

## 11. Phased introduction

1. Phase 1: add `tools/gen_makefile_from_manifest.py`.
2. Phase 2: add `src/pytra/cli.py` and implement `--target cpp --build`.
3. Phase 3: add root launcher `./pytra` with built-in `PYTHONPATH` setup.
4. Phase 4: add `--run`, `--codegen-opt`, and optionally `--jobs`.

## 12. Usage examples

### 12.1 Transpile only

```bash
./pytra sample/py/01_mandelbrot.py --target cpp --output-dir out/mandelbrot
```

### 12.2 One-shot build

```bash
./pytra sample/py/01_mandelbrot.py \
  --target cpp \
  --build \
  --output-dir out/mandelbrot
```

### 12.3 One-shot build (explicit compiler settings)

```bash
./pytra sample/py/01_mandelbrot.py \
  --target cpp \
  --build \
  --output-dir out/mandelbrot \
  --compiler g++ \
  --std c++20 \
  --opt -O3 \
  --exe mandelbrot.out
```

### 12.4 Build + run

```bash
./pytra sample/py/01_mandelbrot.py \
  --target cpp \
  --build \
  --run \
  --output-dir out/mandelbrot
```

## 13. Notes

- Operate `out/` as a local generated-artifact directory and do not version it.
- Keep `py2cpp.py` as backend and invoke it through common CLI.
- In future, `pip install -e .` + console script can allow migration from `./pytra` to direct `pytra ...` execution.
