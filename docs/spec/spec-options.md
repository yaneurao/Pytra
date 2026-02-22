<a href="../../docs-jp/spec/spec-options.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# Transpile Option Specification (Draft)

This document is a draft for organizing Pytra option design.  
Its purpose is to let users explicitly choose trade-offs between "Python compatibility" and "generated-code performance."

## 1. Design Policy

- Defaults should be `native`-oriented (performance-first).
- When compatibility is prioritized, explicitly opt in via `balanced` / `python` presets or individual options.
- Introduce options in phases:
  - Phase 1: `py2cpp.py` first
  - Phase 2: consolidate into common CLI (`src/pytra/compiler/transpile_cli.py`)
  - Phase 3: make language-specific defaults switchable via LanguageProfile

## 2. Implemented Options (Current)

Enabled in `py2cpp.py`:

- `--negative-index-mode {always,const_only,off}`
  - `always`: always process negative indices with Python-compatible behavior
  - `const_only`: Python-compatible behavior only for constant negative indices (current default)
  - `off`: do not apply Python-compatible behavior
- `--bounds-check-mode {always,debug,off}`
  - `always`: always check index access
  - `debug`: check only when `NDEBUG` is disabled
  - `off`: no checks (current default)
- `--floor-div-mode {python,native}`
  - `python`: Python-compatible via `py_floordiv`
  - `native`: use C++ `/` directly (current default)
- `--mod-mode {python,native}`
  - `python`: Python-compatible via `py_mod`
  - `native`: use C++ `%` directly (current default)
- `--int-width {32,64,bigint}`
  - `32`/`64` are implemented
  - `bigint` is not implemented yet (error if specified)
- `--str-index-mode {byte,codepoint,native}`
  - `byte`/`native` are available
  - `codepoint` is not implemented yet (error if specified)
- `--str-slice-mode {byte,codepoint}`
  - `byte` is available
  - `codepoint` is not implemented yet (error if specified)
- `-O0` / `-O1` / `-O2` / `-O3`
  - Generated code optimization level
  - `-O0`: no optimization (readability/investigation first)
  - `-O1`: light optimization
  - `-O2`: medium optimization
  - `-O3`: aggressive optimization (default)
- `--parser-backend {self_hosted,cpython}`
  - Select EAST generation backend
- `--no-main`
  - Do not generate `main` function
- `--dump-deps`
  - Output dependency information
- `--preset {native,balanced,python}`
  - Apply a bundled compatibility/performance setting set
  - Individually specified options after that take precedence
- `--dump-options`
  - Output resolved options
- `--top-namespace NS`
  - If `NS` is specified, wrap generated C++ body in `namespace NS { ... }`
  - Keep `main` global, calling `NS::__pytra_main(...)`
  - If omitted (default), no top namespace
- `--single-file` / `--multi-file`
  - `--multi-file` (default): output `out/include`, `out/src`, and `manifest.json` per module
  - `--single-file`: legacy single `.cpp` output
  - For compatibility, specifying `-o xxx.cpp` implicitly enables `--single-file` when no explicit mode is set.
- `--output-dir DIR`
  - Output directory for `--multi-file` (`out` if omitted)

## 3. Candidate Additional Options

### 3.1 Compatibility/Safety

- `--any-cast-mode {checked,unchecked}`
  - Whether to runtime-check extraction from `Any/object`

### 3.2 String Specification

- `--str-index-mode {byte,codepoint,native}`
  - Concrete string character model
  - `byte`: 1-byte units (fast, current-implementation-oriented)
  - `codepoint`: Unicode character units (Python-compatibility-oriented)
  - `native`: use wrapped target-language string representation directly
- `--str-slice-mode {byte,codepoint}`
  - Align slice semantics similarly

### 3.3 Numeric Specification

- `--int-width=bigint`
  - Arbitrary-precision integer (Python-compatibility-oriented, high implementation cost)
  - Currently not implemented

### 3.4 Generated Code Form

- `--emit-layout {single,split}`
  - `single`: single-file output
  - `split`: module-split output
- `--runtime-linkage {header,static,shared}`
  - Runtime helper linkage form

## 4. Preset Proposal

- Policy:
  - Choose `native` defaults to prioritize C++ conversion performance.
  - Choose `python` presets when compatibility is prioritized.
  - When using both `--preset` and individual options, individual options take precedence.

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
  - `int-width=bigint` (after implementation)
  - `-O0`

## 5. Introduction Priority (Proposal)

1. Add `int-width=bigint` to make integer model explicit
2. Introduce `str-index-mode` to make string compatibility selectable
3. Add `preset` to reduce operation cost
4. Implement detailed `int-overflow` behavior and `emit-layout=split` in stages

## 6. Notes

- Must stay consistent with existing specification (`docs/spec-dev.md`), so update both simultaneously when introducing options.
- For potentially breaking items (`int-width`, `str-index-mode`), provide at least one-release migration period before changing defaults.

### 6.1 Specification Consistency Check Procedure

When adding/changing options, update all of the following at the same time:

1. `docs/spec-options.md` (option definitions, defaults, presets)
2. `docs/spec-dev.md` (implementation specification and CLI reflection)
3. `docs/spec-east.md` (responsibility boundary between EAST side and generator side)
4. `docs/how-to-use.md` (usage examples)

After updates, verify:

1. output of `python src/py2cpp.py INPUT.py --dump-options` matches specification
2. relevant option regressions in `test/unit/test_py2cpp_features.py` pass

