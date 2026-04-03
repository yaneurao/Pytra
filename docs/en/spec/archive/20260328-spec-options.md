<a href="../../../ja/spec/archive/20260328-spec-options.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# Transpile Options Specification (Draft)

This document is a draft for organizing Pytra's option design.
The goal is to allow users to explicitly choose the trade-off between "Python compatibility" and "generated code performance".

## 1. Design Policy

- Defaults lean toward `native` (performance-first).
- When Python compatibility is a priority, opt in explicitly using `balanced` / `python` presets or individual options.
- Options are introduced incrementally.
  - Phase 1: `pytra-cli.py --target cpp` first
  - Phase 2: Consolidate into the common CLI (`src/toolchain/frontends/transpile_cli.py`) (`compiler/transpile_cli.py` becomes a compatibility shim)
  - Phase 3: Allow per-language defaults to be switched via LanguageProfile

## 2. Implemented Options (Current State)

Effective for `pytra-cli.py --target cpp`:

- `--negative-index-mode {always,const_only,off}`
  - `always`: Always handle negative subscripts in Python-compatible manner
  - `const_only`: Python-compatible handling only for constant negative subscripts (current default)
  - `off`: No Python-compatible handling
- `--bounds-check-mode {always,debug,off}`
  - `always`: Always check subscript accesses
  - `debug`: Check only when `NDEBUG` is not defined
  - `off`: No checking (current default)
- `--floor-div-mode {python,native}`
  - `python`: Python-compliant via `py_floordiv`
  - `native`: Use C++ `/` directly (current default)
- `--mod-mode {python,native}`
  - `python`: Python-compliant via `py_mod`
  - `native`: Use C++ `%` directly (current default)
- `--int-width {32,64,bigint}`
  - `32`/`64` are implemented
  - `bigint` is not yet implemented (specifying it causes an error)
- `--str-index-mode {byte,codepoint,native}`
  - `byte`/`native` are available
  - `codepoint` is not yet implemented (specifying it causes an error)
- `--str-slice-mode {byte,codepoint}`
  - `byte` is available
  - `codepoint` is not yet implemented (specifying it causes an error)
- `-O0` / `-O1` / `-O2` / `-O3`
  - Generated code optimization level
  - `-O0`: No optimization (prioritize readability / debugging)
  - `-O1`: Light optimization
  - `-O2`: Moderate optimization
  - `-O3`: Aggressive optimization (default)
- `--parser-backend {self_hosted,cpython}`
  - Select the EAST generation backend
- `--no-main`
  - Do not generate a `main` function
- `--dump-deps`
  - Output dependency information
- `--preset {native,balanced,python}`
  - Apply a bundle of compatibility/performance balance settings at once
  - Options specified individually afterward take precedence
- `--dump-options`
  - Output resolved options
- `--top-namespace NS`
  - When `NS` is specified, wrap the generated C++ body in `namespace NS { ... }`
  - `main` remains global and calls `NS::__pytra_main(...)`
  - When unspecified (default), no top-level namespace
- `--single-file` / `--multi-file`
  - `--multi-file` (default): Output per-module `out/include`, `out/src`, and `manifest.json`
  - `--single-file`: Conventional single `.cpp` output
  - As a compatibility measure, specifying `-o xxx.cpp` implicitly applies `--single-file` (when no explicit mode is specified).
- `--output-dir DIR`
  - Output directory for `--multi-file` (default: `out` when unspecified)

## 3. Additional Option Candidates

### 3.1 Compatibility / Safety

- `--any-cast-mode {checked,unchecked}`
  - Whether to runtime-verify extractions from `Any/object`

### 3.2 String Specification

- `--str-index-mode {byte,codepoint,native}`
  - The actual unit of string characters
  - `byte`: 1-byte unit (fast, closer to current implementation)
  - `codepoint`: 1 Unicode character unit (closer to Python-compatible)
  - `native`: Use (wrapped) whatever corresponds to the target language's string directly.
- `--str-slice-mode {byte,codepoint}`
  - Align slice semantics similarly

### 3.3 Numeric Specification

- `--int-width=bigint`
  - Arbitrary-precision integers (closer to Python-compatible, high implementation cost)
  - Not yet implemented

### 3.4 Generated Code Form

- `--emit-layout {single,split}`
  - `single`: Converted to a single file.
  - `split`: Module-split output
- `--runtime-linkage {header,static,shared}`
  - How the runtime auxiliary is embedded

## 4. Preset Proposals

- Policy:
  - Default to `native` choices, prioritizing C++ conversion performance.
  - Choose `python` when compatibility is a priority.
  - When `--preset` and individual options are combined, individual options take precedence.

- `--preset native` (default candidate)
  - `negative-index-mode=off`
  - `bounds-check-mode=off`
  - `floor-div-mode=native`
  - `mod-mode=native`
  - `str-index-mode=native`
  - `str-slice-mode=byte`
  - `int-width=64`
  - `-O3`

- `--preset balanced`
  - `negative-index-mode=const_only`
  - `bounds-check-mode=debug`
  - `floor-div-mode=python`
  - `mod-mode=python`
  - `str-index-mode=byte`
  - `str-slice-mode=byte`
  - `int-width=64`
  - `-O2`

- `--preset python`
  - `negative-index-mode=always`
  - `bounds-check-mode=always`
  - `floor-div-mode=python`
  - `mod-mode=python`
  - `str-index-mode=codepoint`
  - `str-slice-mode=codepoint`
  - `int-width=bigint` (once implementation is complete)
  - `-O0`

## 5. Introduction Priority Order (Proposal)

1. Add `int-width=bigint` to make the integer model explicit
2. Introduce `str-index-mode` to make string compatibility selectable
3. Add `preset` to reduce operational overhead
4. Incrementally implement `int-overflow` detailed behavior and `emit-layout=split`

## 6. Notes

- Consistency with the existing specification (`docs/ja/spec/spec-dev.md`) is required; when introducing options, always update both simultaneously.
- For items that could be breaking changes (`int-width`, `str-index-mode`), allow at least one release as a migration period before changing the default.

### 6.1 Specification Consistency Check Procedure

When adding or changing options, update the following simultaneously:

1. `docs/ja/spec/spec-options.md` (option definitions, defaults, presets)
2. `docs/ja/spec/spec-dev.md` (implementation spec and CLI reflection)
3. `docs/ja/spec/spec-east.md` (EAST-side and generator-side responsibility boundary)
4. `docs/ja/tutorial/how-to-use.md` (usage examples)

After updating, confirm the following:

1. The output of `python3 src/pytra-cli.py INPUT.py --target cpp --dump-options` matches the specification
2. The relevant option regression in `tools/unittest/emit/cpp/test_py2cpp_features.py` passes
