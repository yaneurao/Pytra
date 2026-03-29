<a href="../../ja/spec/spec-make.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# Makefile Generation and One-Shot Build Specification

This document defines the operational specification that routes C++ build flow through the shared `pytra` CLI instead of direct `py2cpp.py` invocation.

## 2026-02-24 Alignment Note

- `src/pytra-cli.py`, `tools/gen/gen_makefile_from_manifest.py`, and `./pytra` are already implemented and provide the `--target cpp --build` route through `./pytra`.
- The `manifest.json` contract for `--multi-file` and the `tools/build_multi_cpp.py` route remain active specifications (`docs/en/spec/spec-dev.md` / `docs/en/spec/spec-tools.md`).
- This document is operated as an implementation-aligned specification. Anything treated as a future idea is split out as a separate task.

## 1. Decisions

- The user-facing entry point is `./pytra` (extensionless launcher).
- The implementation body is `src/pytra-cli.py` (`python src/pytra-cli.py`).
- `py2cpp.py` remains as the transpilation backend and must not own build orchestration.
- C++ build is performed through `manifest.json` as the source of truth plus Makefile generation plus `make`.
- `manifest.json` is not written directly by `ModuleEmitter`; it is treated as the build manifest emitted by `CppProgramWriter` from a `ProgramArtifact`.
- Manual `PYTHONPATH` setup is unnecessary because `./pytra` sets it internally.

## 2. Objective

- Shorten the command line and make conversion through build a single command.
- Reuse existing multi-file output and `manifest.json` to provide a reproducible build path.
- Establish an entry point that can later grow into a unified multi-language CLI via `--target`.

## 3. Non-Goals

- Implementing full build execution for every language at once. In v1, only `--target cpp` is in scope.
- Generating IDE-specific projects such as Visual Studio or Xcode projects.
- Automatic build inference without going through `manifest.json`.

## 4. Entry Point Specification

### 4.1 `./pytra` Launcher

Place an extensionless executable `pytra` at the repository root and make it do the following:

1. add `ROOT/src` to `PYTHONPATH`
2. execute `python3 src/pytra-cli.py "$@"`

Intent:

- remove the need to type `PYTHONPATH=src ...` on every invocation
- provide an executable form that does not collide with input-project files named `pytra.py`

### 4.2 Real CLI

- The real CLI is `src/pytra-cli.py`.
- The direct form is `python3 src/pytra-cli.py ...`.

## 5. Shared CLI Specification (v1)

### 5.1 Basic Form

```bash
./pytra INPUT.py --target cpp [OPTIONS]
```

### 5.2 Required / Supported Arguments in v1

- `INPUT.py`
- `--target cpp`
- `--output-dir DIR` (default: `out`)
- `--build` (run build only when specified)

### 5.3 C++ Build Options for `--build`

- `--compiler CXX` (default: `g++`)
- `--std STD` (default: `c++20`)
- `--opt FLAG` (default: `-O2`)
- `--exe NAME` (default: `app.out`)
- `--run` (optional: execute after a successful build)

Notes:

- In this document, `--opt` means the C++ compiler flag.
- The generated-code optimization level (`py2cpp` `-O0..-O3`) may be separated as `--codegen-opt {0,1,2,3}` and uses its default when omitted.
- In `pytra-cli`, `--target cpp --codegen-opt 3` means the maximum Pytra codegen route, not a mere `-O3` pass-through. It selects backend emission through the linked-program optimizer.
- `--target cpp --codegen-opt 0/1/2` keeps the existing route and is treated independently from compiler flags such as `--opt -O3`.

### 5.4 Constraints

- `--build` is valid only with `--target cpp`.
- `--compiler`, `--std`, `--opt`, `--exe`, and `--run` are valid only when `--build` is present.
- If `--build` is specified with a target other than `cpp`, exit with an error.

## 6. C++ Build Flow

The processing order for `./pytra ... --target cpp --build` is:

1. When `--codegen-opt 3` is selected, materialize raw `EAST3` modules, run the linked-program optimizer, and generate C++ multi-file output from the linked modules.
2. When `--codegen-opt 0/1/2` is selected, build `ProgramArtifact` through the existing compatibility route.
3. `CppProgramWriter` generates the output tree and `manifest.json`.
4. `tools/gen/gen_makefile_from_manifest.py` generates the `Makefile`.
5. Run `make -f <Makefile>` and produce the binary.
6. If `--run` is specified, run `make -f <Makefile> run`.

Notes:

- In the current CLI implementation, `ProgramArtifact` is an internal concept, but `manifest.json` is treated as its concrete build artifact.
- Non-C++ backends using `SingleFileProgramWriter` do not require a build manifest. This document covers the manifest contract emitted by C++ `CppProgramWriter`.

## 7. `manifest.json` Input Specification

`manifest.json` must satisfy at least the following:

- `modules` is an array
- each element is an object and `source` is a non-empty string
- `include_dir` is a string; when omitted, sibling `include/` next to the manifest may be used as default

Meaning during the linked-program period:

- `manifest.json` is the C++ build serialization of `ProgramArtifact`
- generation is the responsibility of `CppProgramWriter`; `CppEmitter` / `ModuleEmitter` do not generate `manifest.json` directly
- `manifest.json` is the source of truth for build layout and runtime layout, not for language semantics

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

## 8. Makefile Generation Specification

Use `tools/gen/gen_makefile_from_manifest.py`, which accepts:

- positional arguments
  - `manifest`
- options
  - `-o`, `--output`
  - `--exe`
  - `--compiler`
  - `--std`
  - `--opt`

The generated `Makefile` must include at least:

- variables: `CXX`, `CXXFLAGS`, `INCLUDES`, `SRCS`, `OBJS`, `TARGET`
- targets: `all`, `$(TARGET)`, `%.o: %.cpp`, `run`, `clean`

## 9. Error Contract

Exit non-zero in the following cases:

- `manifest` does not exist
- JSON parsing fails
- `modules` is not an array
- there is no valid `source`
- `--compiler`, `--std`, `--opt`, `--exe`, or `--run` is specified without `--build`
- `--build` is specified for a non-`cpp` target
- `make` is not found

## 10. Acceptance Criteria

- `./pytra sample/py/01_mandelbrot.py --target cpp --output-dir out/mandelbrot` generates multi-file output.
- `./pytra sample/py/01_mandelbrot.py --target cpp --build --output-dir out/mandelbrot` performs conversion, Makefile generation, and build in sequence.
- `./pytra sample/py/01_mandelbrot.py --target cpp --build --compiler g++ --std c++20 --opt -O3 --exe mandelbrot.out` reflects the specified values into the Makefile and the build.
- `./pytra sample/py/01_mandelbrot.py --target cpp --codegen-opt 3 --build --output-dir out/mandelbrot` selects the maximum-opt C++ route through the linked-program optimizer.
- `python3 tools/check/runtime_parity_check.py --targets cpp --case-root sample --all-samples --cpp-codegen-opt 3 --east3-opt-level 2` remains green.
- `./pytra sample/py/01_mandelbrot.py --target rs --build` exits with an error as specified.
- Running `make -f out/mandelbrot/Makefile` a second time results in an incremental build with minimal relink/recompile.

## 11. Staged Rollout

1. Phase 1: add `tools/gen/gen_makefile_from_manifest.py`
2. Phase 2: add `src/pytra-cli.py` and implement `--target cpp --build`
3. Phase 3: add the root launcher `./pytra` and internalize `PYTHONPATH` setup
4. Phase 4: add `--run`, `--codegen-opt`, and `--jobs` if needed

## 12. Practical Examples

### 12.1 Transpile Only

```bash
./pytra sample/py/01_mandelbrot.py --target cpp --output-dir out/mandelbrot
```

### 12.2 One-Shot Build

```bash
./pytra sample/py/01_mandelbrot.py \
  --target cpp \
  --build \
  --output-dir out/mandelbrot
```

### 12.3 One-Shot Build with Explicit Compiler Settings

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

### 12.4 Build + Run

```bash
./pytra sample/py/01_mandelbrot.py \
  --target cpp \
  --build \
  --run \
  --output-dir out/mandelbrot
```

## 13. Notes

- Operate `out/` as a local build-artifact directory and do not put it under Git.
- Keep `py2cpp.py` as a backend and call it through the shared CLI.
- In the future, `pip install -e .` plus a console script could replace `./pytra` so that `pytra ...` works directly.

## 14. `pytra-cli` Responsibility Boundary (Fixed P0 Contract)

`src/pytra-cli.py` is restricted to shared control at the entry point and must not inline target-specific build or run implementations.

- CLI body (`src/pytra-cli.py`)
  - Role: argument normalization, input validation, profile resolution, and calling a shared runner
  - Allowed: passing the target name into the `toolchain` profile layer
  - Forbidden: hard-coding target-specific compiler/runtime/execution commands
- Backend profiles (`src/toolchain/misc/*`)
  - Role: declare target-specific transpile/build/run contracts such as required tools, output naming, and auxiliary runtime files
  - Allowed: defining target-specific commands, file names, and extensions
  - Forbidden: reimplementing entry-point responsibilities such as CLI argument parsing or stdio control
- Execution runner (shared CLI)
  - Role: subprocess execution, stdout/stderr forwarding, exit-code handling, timeout management
  - Allowed: mechanically executing the `command/cwd/env` returned by a profile
  - Forbidden: branching on target names and rewriting commands there

### 14.1 Forbidden Items (Guarded in CI)

- Do not add new `if/elif target == "...":` branches to `src/pytra-cli.py`.
- Do not hard-code `<lang>`-specific runtime file paths such as `py_runtime.kt` or `png.java` in `src/pytra-cli.py`.
- Tools around the CLI, such as `tools/check/runtime_parity_check.py`, must not duplicate target-specific build or run commands. The route must be unified through `pytra-cli`.
