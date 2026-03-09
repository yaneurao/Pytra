<a href="../../ja/spec/spec-dev.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# Implementation Specification (Pytra)

This document defines the transpiler's implementation policy, structure, and conversion behavior.

- The source of truth for folder responsibilities is [`docs/en/spec/spec-folder.md`](./spec-folder.md). This document covers implementation behavior itself.

## 1. Repository Layout

- `src/`
  - `py2cs.py`, `py2x.py --target cpp`, `py2rs.py`, `py2js.py`, `py2ts.py`, `py2go.py`, `py2java.py`, `py2swift.py`, `py2kotlin.py`, `py2rb.py`, `py2lua.py`, `py2php.py`, `py2scala.py`, `py2nim.py`
  - Place only transpiler entry scripts (`py2*.py`) directly under `src/`.
  - `backends/common/`: shared base implementations and common utilities reused across multiple languages
  - The standard backend stage layout is `src/backends/<lang>/{lower,optimizer,emitter}/` (source of truth: `spec-folder.md`).
  - During the transition period, `extensions/<topic>/` may coexist (plan 2). In the long run, the codebase will converge on `lower/optimizer/emitter` (plan 3).
  - `backends/common/profiles/` and `backends/<lang>/profiles/`: language-difference JSON for `CodeEmitter` (`types`, `operators`, `runtime_calls`, `syntax`)
  - `runtime/`: canonical runtime placement for each target language (`src/runtime/<lang>/pytra/`)
  - `*_module/`: legacy runtime placement kept only as a compatibility layer and scheduled for staged removal
  - `pytra/`: canonical shared library on the Python side
- `test/`: `py` inputs and converted outputs for each target language
- `sample/`: practical sample inputs and converted outputs for each language
- `docs/en/`: specifications, usage guides, and implementation status

### 1.1 Backend 3-Layer Standard (Non-C++)

- The standard pipeline for non-C++ backends is `Lower -> Optimizer -> Emitter`.
- The current 3-layer backends are `rs/cs/js/ts/go/java/kotlin/swift/ruby/lua/php/scala`.
- `py2<lang>.py` must keep the order `load_east3_document -> lower_east3_to_<lang>_ir -> optimize_<lang>_ir -> transpile`, and must not insert logic that skips layer boundaries.
- `lower/optimizer` must not import `emitter`, and `emitter` must not import `lower/optimizer`.
- The canonical regression guard is `python3 tools/check_noncpp_east3_contract.py`.

### 1.2 Backend-Shared Artifact / Writer Contract (Linked-Program Period)

After linked-program was introduced, the shared backend boundary is:

```text
linked module (EAST3)
  -> Lower
  -> Optimizer
  -> ModuleEmitter
  -> ModuleArtifact
  -> ProgramWriter
  -> output tree / manifest / runtime
```

#### `ModuleEmitter`

- Inputs:
  - one linked `EAST3` module
  - target-specific options
- Output:
  - `ModuleArtifact`
- Responsibilities:
  - final rendering at module granularity
  - enumerating per-module dependency information
  - attaching emitter-specific metadata
- Forbidden:
  - deciding output directories
  - placing runtime files
  - generating build manifests
  - recomputing `type_id`, non-escape, or ownership

#### Minimal `ModuleArtifact` Contract

`ModuleArtifact` is the shared backend representation of the rendered output for one module. It must contain at least:

- `module_id`
  - canonical module id
- `label`
  - stable label used in output names
- `extension`
  - for example `.cpp`, `.rs`, `.js`
- `text`
  - generated source text
- `is_entry`
  - whether the module is an entry module
- `dependencies`
  - array of `module_id`; only inter-module dependencies are recorded, not final paths
- `metadata`
  - target-specific auxiliary metadata object

Additional rules:

- `ModuleArtifact` must not contain a final output path.
- `ModuleArtifact` must not embed target-specific build or layout information.
- Even if more payload types are added later, the compatibility minimum remains the ability to return `text`.

#### Minimal `ProgramArtifact` Contract

`ProgramArtifact` is the writer input for one whole program and must contain at least:

- `target`
- `program_id`
- `entry_modules`
- `modules`
  - `ModuleArtifact[]`
- `layout_mode`
  - `single_file | multi_file`
- `link_output_schema`
  - for example `pytra.link_output.v1`
- `writer_options`
  - writer-specific options object

Additional rules:

- `ProgramArtifact` must preserve the exact module set resolved by the linked-program phase.
- `ProgramArtifact` must not become the canonical source of global semantics. The source of truth for global semantics remains `link-output.v1` plus the linked modules.
- `ProgramArtifact` is an input to packaging/build, not another decision point for language semantics.

#### `ProgramWriter`

- Inputs:
  - `ProgramArtifact`
  - `output_root`
- Outputs:
  - output tree
  - build manifest when required
- Responsibilities:
  - deciding file paths
  - handling single-file or multi-file layout
  - placing runtime files
  - generating build metadata and manifests
- Forbidden:
  - regenerating module text
  - repartitioning module boundaries
  - reinterpreting `type_id`, non-escape, or ownership

Default implementations:

- For non-C++ backends, the default is `SingleFileProgramWriter`.
- C++ uses `CppProgramWriter` and handles `manifest.json`, `Makefile`, and the runtime tree.
- Implementation-aligned note (2026-03-07):
  - `backend_registry.py` and `backend_registry_static.py` always materialize both `emit_module` and `program_writer` when normalizing backend specs.
  - If a backend does not define `program_writer`, the default is `write_single_file_program(...)` in `backends/common/program_writer.py`.
  - The single-module path in `ir2lang.py` already goes through `emit_module -> ProgramArtifact -> ProgramWriter`. The old `emit_source()` has been reduced to a compatibility wrapper that only returns `ModuleArtifact.text`.

Compatibility contract:

- The old `emit -> str` API is treated as a compatibility wrapper around an old emitter that effectively returns `ModuleArtifact(text only)` plus `SingleFileProgramWriter`.
- New backends and new routes must treat `emit_module + program_writer` as canonical and must not add new unary emit APIs.

#### Non-C++ Backend Recovery Baseline After Linked-Program

- After linked-program, the baseline for non-C++ backends is to keep the compatibility route based on `SingleFileProgramWriter`, then evaluate backends in this gate order:
  1. `static_contract`
  2. `common_smoke`
  3. `target_smoke`
  4. `transpile`
  5. `parity`
- The primary failure category in the health matrix is the first gate that fails. Later gates must not overwrite it.
- `parity` is measured only for targets that pass `static/common/target_smoke/transpile`. A target that already fails an earlier gate must not be reported as a parity failure.
- `toolchain_missing` is a separate category from `parity_fail`. If sample parity is skipped because the compiler or runtime is missing, record it as infrastructure baseline and do not mix it into backend bug counts.
- In the first snapshot as of 2026-03-08, the primary failure category is `green` for `js/ts`, `toolchain_missing` for `cs`, `target_smoke_fail` for `rs/go/java/scala/lua`, and `transpile_fail` for `kotlin/swift/ruby/php/nim`.

### 1.3 `src/pytra/` Public API (Implementation Baseline)

`src/pytra/` is the source of truth for shared Python libraries, including selfhost.
Names starting with `_` are treated as internal implementation details. The following are public APIs.

- Direct imports of standard modules from transpiled code are discouraged in principle. Prefer explicit `pytra.std.*` imports.
- Standard modules with compatibility shims (`math`, `random`, `timeit`, `enum`, and others) may be normalized to `pytra.std.*` during translation.
- Allowed imports are `pytra.*` and user-authored modules (`.py`).

- `pytra.utils.assertions`
  - Functions: `py_assert_true`, `py_assert_eq`, `py_assert_all`, `py_assert_stdout`
- `pytra.std.pathlib`
  - Class: `Path`
  - Members: `parent`, `parents`, `name`, `suffix`, `stem`, `resolve`, `exists`, `mkdir`, `read_text`, `write_text`, `glob`, `cwd`
- `pytra.std.json`
  - Functions: `loads`, `dumps`
- `pytra.std.sys`
  - Variables: `argv`, `path`, `stderr`, `stdout`
  - Functions: `exit`, `set_argv`, `set_path`, `write_stderr`, `write_stdout`
- `pytra.std.math`
  - Constants: `pi`, `e`
  - Functions: `sqrt`, `sin`, `cos`, `tan`, `exp`, `log`, `log10`, `fabs`, `floor`, `ceil`, `pow`
- `pytra.std.time`
  - Function: `perf_counter`
- `pytra.std.timeit`
  - Function: `default_timer`
- `pytra.std.random`
  - Functions: `seed`, `random`, `randint`
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
- `pytra.std.enum`
  - Classes: `Enum`, `IntEnum`, `IntFlag`
- `pytra.utils.png`
  - Function: `write_rgb_png`
- `pytra.utils.gif`
  - Functions: `grayscale_palette`, `save_gif`
- `pytra.utils.browser`
  - Variables/classes: `document`, `window`, `DOMEvent`, `Element`, `CanvasRenderingContext`
- `pytra.utils.browser.widgets.dialog`
  - Classes: `Dialog`, `EntryDialog`, `InfoDialog`
- `pytra.compiler.east`
  - Classes/constants: `EastBuildError`, `BorrowKind`, `INT_TYPES`, `FLOAT_TYPES`
  - Functions: `convert_source_to_east`, `convert_source_to_east_self_hosted`, `convert_source_to_east_with_backend`, `convert_path`, `render_east_human_cpp`, `main`
- `pytra.compiler.east_parts.east_io`
  - Functions: `extract_module_leading_trivia`, `load_east_from_path`

### Current enum Support

- On the input side, use `from pytra.std.enum import Enum, IntEnum, IntFlag` (`enum` from the standard library is not allowed).
- Class bodies of `Enum`, `IntEnum`, and `IntFlag` support member definitions in the form `NAME = expr`.
- C++ lowering uses `enum class`.
  - `IntEnum` and `IntFlag` get helper comparison operators against `int64`.
  - `IntFlag` gets helper operators for `|`, `&`, `^`, and `~`.

## 2. C# Conversion Specification (`py2cs.py`)

- Conversion is EAST-based (`.py/.json -> EAST -> C#`).
- `py2cs.py` is restricted to a thin CLI and I/O orchestrator.
- C#-specific logic is separated into `src/backends/cs/emitter/cs_emitter.py`.
- Language-specific differences are managed in `src/backends/cs/profiles/*.json` (`types/operators/runtime_calls/syntax`).
- `import` and `from ... import ...` are converted into `using` lines based on canonical EAST `meta.import_bindings`.
- Major types are mapped through `src/backends/cs/profiles/types.json` (for example `int64 -> long`, `float64 -> double`, `str -> string`).

## 3. C++ Conversion Specification (`py2x.py --target cpp`)

- It parses Python AST and generates a single `.cpp` with required includes.
- The `CppEmitter` implementation is separated into `src/backends/cpp/emitter/cpp_emitter.py`, and `py2x.py --target cpp` is treated as the CLI/orchestration layer.
- Detailed feature support such as `enumerate(start)`, `lambda`, and comprehensions is managed canonically in the [py2cpp support matrix](../language/cpp/spec-support.md).
- Generated code uses runtime helpers under `src/runtime/cpp/`.
- Helper functions are not inlined into generated `.cpp`; use `runtime/cpp/core/py_runtime.h` instead.
- Not only `json`: standard-library-equivalent features use `src/pytra/std/*.py` as their source of truth, and `runtime/cpp` must not carry independent reimplementations.
  - When the C++ side needs that behavior, it must use the transpiled result of those Python source modules.
- Classes are emitted as C++ classes inheriting `pytra::gc::PyObj` except for exception classes.
- Class-method calls are split by dispatch mode (`virtual`, `direct`, `fallback`) in `src/backends/cpp/emitter/call.py`.
  - `virtual` / `direct`: routes where user-defined class method signatures can be resolved
  - `fallback`: routes intentionally kept outside virtual-dispatch replacement, including runtime/type_id APIs such as `IsInstance`, `IsSubtype`, `IsSubclass`, and `ObjTypeId`, and routes that assume `BuiltinCall` lowering
- Selfhost regression fixes the invariant that no `type_id` comparison or switch-based dispatch remains in `sample/cpp` and `src/runtime/cpp/pytra-gen` except `built_in/type_id.cpp` (`test_selfhost_virtual_dispatch_regression.py`).
- Class members are emitted as `inline static`.
- `@dataclass` generates field definitions and constructors.
- Supports `raise`, `try`, `except`, and `while`.
- Bounds checks for list/str subscripts are controlled by `--bounds-check-mode`.
  - `off` (default): generate ordinary `[]`
  - `always`: generate runtime-checked `py_at_bounds`
  - `debug`: generate `py_at_bounds_debug`, checked only in debug builds
- `//` (floor division) is controlled by `--floor-div-mode`.
  - `native` (default): emit C++ `/` directly
  - `python`: emit `py_floordiv` so that floor division matches Python
- `%` (modulo) is controlled by `--mod-mode`.
  - `native` (default): emit C++ `%` directly
  - `python`: insert runtime helpers so modulo matches Python semantics
- Integer output width is controlled by `--int-width`.
  - `64` (default): emit `int64` / `uint64`
  - `32`: emit `int32` / `uint32`
  - `bigint`: not implemented and must fail
- String subscript/slice behavior is controlled by:
  - `--str-index-mode {byte,native}` (`codepoint` not implemented)
  - `--str-slice-mode {byte}` (`codepoint` not implemented)
  - With current `byte` / `native`, the return type of `str[i]` is `str` (a one-character string).
  - Out-of-bounds behavior follows `--bounds-check-mode` (`off` / `always` / `debug`).
- Generated-code optimization is controlled by `-O0` to `-O3`.
  - `-O0`: no optimization, for debugging and diff inspection
  - `-O1`: light optimization
  - `-O2`: medium optimization
  - `-O3` (default): aggressive optimization
- The top namespace of generated C++ can be set with `--top-namespace NS`.
  - If omitted, no top namespace is used.
  - If specified, keep `main` in the global namespace and call `NS::__pytra_main(...)`.
- Negative indexing for list/str such as `a[-1]` is controlled by `--negative-index-mode`.
  - Default is `const_only` (Python-compatible handling only for constant negative indices).
  - `always`: enable Python-compatible negative indexing for every subscript access.
  - `off`: do not apply Python-compatible negative indexing and generate ordinary `[]`.
- PNG equality is judged by exact byte-for-byte file equality.
- GIF equality is also judged by exact byte-for-byte file equality.

### 3.0 Multi-File Output and `manifest.json` / Build (Implemented)

- The default output mode of `py2x.py --target cpp` is `--multi-file` (switch to a single `.cpp` only with explicit `--single-file`).
- As a compatibility behavior, if the output path ends with `.cpp`, single-file output is selected even without an explicit mode.
- In `--multi-file` mode, the following are generated under `--output-dir` (default `out`):
  - `include/` (one `*.h` per module)
  - `src/` (one `*.cpp` per module)
  - `manifest.json`
- `manifest.json` must contain at least:
  - `entry`
  - `include_dir`
  - `src_dir`
  - `modules` (each element has `module`, `label`, `header`, `source`, `is_entry`)
- Use `tools/build_multi_cpp.py` to build multi-file C++ output.
  - Basic form: `python3 tools/build_multi_cpp.py out/manifest.json -o out/app.out`
  - Options: `--std` (default `c++20`), `--opt` (default `-O2`)
  - If `manifest.modules` is not an array, or if there is no valid `source`, exit with an error.
  - If `manifest.include_dir` is missing, use sibling `include/` next to the manifest as the default.
- The `./pytra --build` route, `src/pytra-cli.py`, and `tools/gen_makefile_from_manifest.py` described in `docs/en/spec/spec-make.md` were already implemented as of 2026-02-24.

### Guard Rules for py2cpp Commonization

- Before adding new logic to `src/backends/cpp/cli.py`, classify it as either C++-specific or language-agnostic.
- If it is language-agnostic, implement it under `src/toolchain/compiler/` (including `east_parts/` and `CodeEmitter`) and do not add it directly to `py2x.py --target cpp`.
- Keep logic in `py2x.py --target cpp` limited to C++-specific responsibilities such as type mapping, runtime-name resolution, header/include generation, and C++ syntax optimization.
- The only allowed exception is a backward-compatible public API wrapper (`load_east`, `_analyze_import_graph`, `build_module_east_map`, `dump_deps_graph_text`). Even those must do nothing except delegate to the common-layer API.
- When modifying an existing generic helper inside `py2x.py --target cpp`, also evaluate whether it can be moved into the common layer, and record the decision in `docs/ja/plans/p1-py2cpp-reduction.md`.
- If an emergency hotfix temporarily adds a generic helper to `py2x.py --target cpp`, the implementation site must include a `TEMP-CXX-HOTFIX` comment and the matching task ID.
- A temporary helper must be extracted into `src/toolchain/compiler/` within either 7 days of addition or the next patch release, whichever comes first.
- Until the extraction is done, keep an extraction task open in `docs/ja/todo/index.md`, and record the reason for the `tools/check_py2cpp_helper_guard.py` allowlist update in `docs/ja/plans/p1-py2cpp-reduction.md`.
- These responsibility boundaries are validated by `tools/check_py2cpp_boundary.py` and run continuously through `tools/run_local_ci.py`.
- Generic helpers in `src/toolchain/compiler/transpile_cli.py` use per-feature `class + @staticmethod` (`*Helpers`) as the canonical layout. `py2x.py --target cpp` uses class-level imports and startup binding only. Top-level functions remain temporarily for compatibility with existing CLI/selfhost callers.
- Inside `ImportGraphHelpers`, `analyze_import_graph` and `build_module_east_map` are operated as thin wrappers delegating their implementation body to `src/toolchain/compiler/east_parts/east1_build.py` (only the compatibility public API is retained).
- The import-graph/build entrypoints in `py2x.py --target cpp` (`_analyze_import_graph`, `build_module_east_map`) are restricted to delegation into `East1BuildHelpers`; implementation details must not be brought back into `transpile_cli`.
- Regressions are guarded through `test/unit/ir/test_east1_build.py`, `test/unit/backends/cpp/test_py2cpp_east1_build_bridge.py`, and `tools/check_py2cpp_transpile.py`, which detect responsibility backflow in dependency analysis.
- As part of `P0-PY2CPP-SPLIT-01`, also run `python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_smoke.py'` to confirm that the `py2x.py --target cpp` responsibility boundary (`tools/check_py2cpp_boundary.py`) remains intact.

### 3.1 Imports and `runtime/cpp`

`py2x.py --target cpp` generates includes according to imports.

- `import pytra.std.math` -> `#include "pytra/std/math.h"`
- `import pytra.std.pathlib` -> `#include "pytra/std/pathlib.h"`
- `import pytra.std.time` / `from pytra.std.time import ...` -> `#include "pytra/std/time.h"`
- `import pytra.utils.png` -> `#include "pytra/utils/png.h"`
- `import pytra.utils.gif` -> `#include "pytra/utils/gif.h"`
- GC always uses `#include "runtime/cpp/pytra/built_in/gc.h"`

Calls like `module.attr(...)` are resolved into C++ through `LanguageProfile` (JSON) or module-name to namespace resolution.

- Example: `runtime_calls.module_attr_call.pytra.std.sys.write_stdout -> pytra::std::sys::write_stdout`
- If the map is undefined, fall back to deriving a C++ namespace from the imported module name and emit `ns::attr(...)`
- Load the profile JSON at startup and fill missing items with shared defaults and fallback rules

Notes:

- The source of truth for import information is EAST `meta.import_bindings` (`ImportBinding[]`).
- `from module import symbol` is normalized into EAST `meta.qualified_symbol_refs` (`QualifiedSymbolRef[]`), so alias resolution must be completed before backend emission.
- `meta.import_modules` and `meta.import_symbols` remain only for compatibility and are derived from canonical metadata.
- `import module as alias` resolves `alias.attr(...)` as `module.attr(...)`.
- `from module import *` is kept as `binding_kind=wildcard` and conversion continues.
- Relative imports (`from .mod import x`) are currently unsupported and must fail with `input_invalid`.
- The `pytra` namespace is reserved. `pytra.py` and `pytra/__init__.py` under the input root are rejected as conflicts with `input_invalid`.
- User modules are searched relative to the parent directory of the input file (`foo.bar` -> `foo/bar.py` or `foo/bar/__init__.py`).
- Unresolved user-module imports and circular imports fail early with `input_invalid`.
- If only `from M import S` exists and the code later refers to `M.T`, `M` is not bound, so this is treated as `input_invalid` (`kind=missing_symbol`).

Main C++ runtime implementation layers:

- `src/runtime/cpp/core/py_runtime.h`
- `src/runtime/cpp/native/core/py_runtime.h`
- `src/runtime/cpp/generated/{built_in,std,utils}/*.h|*.cpp`
- `src/runtime/cpp/native/{built_in,std,utils}/*.h|*.cpp`
- `src/runtime/cpp/pytra/{built_in,std,utils}/*.h`

Positioning of `src/runtime/cpp/core/py_runtime.h` and `src/runtime/cpp/native/core/py_runtime.h`:

- `core/py_runtime.h` is the stable include surface.
- `native/core/py_runtime.h` is the handwritten source of truth and is the place for `PyObj`, `object`, `rc<>`, type_id, low-level container primitives, dynamic iteration, process I/O, and C++ glue.
- It is not a place to permanently accumulate built-in semantics that could be moved back into pure-Python SoT.
- High-level string/collection helpers are expected to move back into `generated/built_in` or `src/pytra/built_in/*.py`.
- `py_runtime.h` currently includes `str/path/list/dict/set` and similar headers directly, but this is only for low-level aggregation; it does not authorize adding replacement implementations of built-in modules there.

Container policy for `src/runtime/cpp/core/py_runtime.h`:

- `list<T>`: wrapper around `std::vector<T>` providing `append`, `extend`, and `pop`
- `dict<K, V>`: wrapper around `std::unordered_map<K,V>` providing `get`, `keys`, `values`, and `items`
- `set<T>`: wrapper around `std::unordered_set<T>` providing `add`, `discard`, and `remove`
- `str`, `list`, `dict`, `set`, `bytes`, and `bytearray` are treated as wrappers with Python-compatible APIs, not as direct inheritance from STL containers

Additional rules:

- Pure helpers such as `str::split`, `splitlines`, `count`, and `join` must not remain in `py_runtime` permanently. They are allowed only as migration debt and only with a concrete plan to move them back into the SoT side.
- Low-level dynamic helpers such as `dict_get_*`, `py_dict_get_default`, and object/`std::any` bridges must not be moved casually into `generated/built_in`. Until a proper lane is designed, keeping them in `native/core` is acceptable.
- Helpers placed in `generated/built_in` must use `src/pytra/built_in/*.py` as the only SoT, and checked-in artifacts must be updated only through the canonical `--emit-runtime-cpp` route.
- `generated/built_in/*.h` may only reference stable core headers, and `generated/built_in/*.cpp` may include only `runtime/cpp/core/py_runtime.h` and sibling generated headers. Direct includes of `runtime/cpp/native/core/...` are forbidden.
- A generated helper that wants mutable containers by value at its boundary must have an explicit contract such as `@abi`. The C++ backend's internal ref-first representation must not become helper ABI by default.
- `generated/core` is a reserved lane for low-level pure helpers only, and must not become a dumping ground for `built_in` semantics. Even helpers placed in `generated/core` must keep `runtime/cpp/core/*.h` as the public include surface.

Constraints:

- In principle, modules imported on the Python side must also have corresponding runtime implementations for each target language.
- Helper functions used by generated code must be collected into runtime modules for each language, avoiding duplicate definitions inside generated output.
- Attribute access and method calls on `object` values, including values derived from `Any`, are currently forbidden by language design.
  - Implement EAST and emitters under the assumption that method calls on `object` receivers are not allowed.

### 3.2 Function-Argument Passing Policy

- High-copy-cost types such as `string`, `vector<...>`, `unordered_map<...>`, `unordered_set<...>`, and `tuple<...>` are received as `const T&` when they are not mutated inside the function.
- If direct mutation of an argument is detected, pass by value or by non-const reference instead.
- Direct-mutation detection covers assignment, augmented assignment, `del`, and destructive method calls such as `append`, `extend`, `insert`, and `pop`.

### 3.3 Image Runtime Policy (PNG/GIF)

- `png` and `gif` use the Python side (`src/pytra/utils/`) as the source-of-truth implementation.
- Language-side runtime implementations should, in principle, use transpiled artifacts generated from that canonical Python implementation.
- All languages separate `src/runtime/<lang>/pytra-core/` (handwritten) from `src/runtime/<lang>/pytra-gen/` (generated from source of truth), and image-runtime bodies must always live on the `pytra-gen` side.
- Do not hand-write image-encoding bodies into core files such as `py_runtime.*`; when required, only thin delegation into `pytra-gen` APIs is allowed.
- The image runtime on the `pytra-gen` side must contain `source: src/pytra/utils/{png,gif}.py` and `generated-by: ...`, and manual editing is forbidden.
- Do not hand-write the PNG/GIF encoding bodies separately for each language.
- Only minimal I/O adapters and runtime connection code may be language-specific. Duplicating the encoding logic itself is forbidden.
- Cross-language equality is judged primarily by exact byte-for-byte equality of the generated files.
- `src/pytra/utils/png.py` uses a pure-Python implementation with CRC32, Adler32, and DEFLATE stored blocks and must not depend on `binascii`, `zlib`, or `struct`.
- Acceptance criteria:
  - During replacement work, the bytes produced by `src/pytra/utils/*.py` and the output of each language runtime must match for identical input.
  - On C++, run `tools/verify_image_runtime_parity.py` and confirm minimum PNG/GIF cases match.

### 3.3.1 Guard for std/utils SoT Operation (No Handwritten Reimplementation)

- `src/pytra/std/*.py` and `src/pytra/utils/*.py` are the only SoT for runtime functionality.
- Equivalent logic to the SoT must not be handwritten under `src/runtime/<lang>/pytra-core/**` or `src/runtime/<lang>/pytra/**`.
- SoT-derived code must always be generated into `src/runtime/<lang>/pytra-gen/**` and must preserve `source:` and `generated-by:` traces.
- Existing debt is allowed only when explicitly recorded in `tools/runtime_std_sot_allowlist.txt`; unrecorded additions are forbidden.
- The canonical validation is `python3 tools/check_runtime_std_sot_guard.py`, which runs continuously through `tools/run_local_ci.py`.

### 3.4 Naming of Python Helper Libraries

- The old compatibility name `pylib.runtime` is retired. `pytra.utils.assertions` is canonical.
- Test helper functions (`py_assert_*`) are used via `from pytra.utils.assertions import ...`.

### 3.5 Image Runtime Optimization Policy (py2cpp)

- Targets: `src/runtime/cpp/pytra/utils/png.cpp` and `src/runtime/cpp/pytra/utils/gif.cpp` (generated)
- Preconditions: `src/pytra/utils/png.py` and `src/pytra/utils/gif.py` are the source of truth; do not introduce semantic differences.
- Generation steps:
  - `python3 src/py2x.py src/pytra/utils/png.py --target cpp -o /tmp/png.cpp`
  - `python3 src/py2x.py src/pytra/utils/gif.py --target cpp -o /tmp/gif.cpp`
  - The generated output is written directly to `src/runtime/cpp/pytra/utils/png.cpp` and `src/runtime/cpp/pytra/utils/gif.cpp`.
  - Do not add handwritten body logic into those two files.
  - Derive the C++ namespace automatically from the source Python path instead of hard-coding it.
    - Example: `src/pytra/utils/gif.py` -> `pytra::utils::gif`
    - Example: `src/pytra/utils/png.py` -> `pytra::utils::png`
- Allowed optimizations:
  - loop unrolling, adding `reserve`, reducing temporary buffers, and other optimizations that do not change output bytes
  - lighter bounds checks as long as exception messages do not change
- Forbidden in principle:
  - any optimization that changes the image output specification, including PNG chunk layout, GIF control blocks, or color-table order
  - any change to defaults, formats, or rounding behavior that diverges from the Python SoT
- Acceptance conditions:
  - after changes, `python3 tools/verify_image_runtime_parity.py` must return `True`
  - `test/unit/common/test_image_runtime_parity.py` and `test/unit/backends/cpp/test_py2cpp_features.py` must pass

## 4. Validation Procedure (C++)

1. Use the Python transpiler to convert `test/fixtures` into `test/transpile/cpp`.
2. Compile the generated C++ into `test/transpile/obj/`.
3. Compare the execution result with the Python execution result.
4. During self-host verification, use the self-transpiled executable to generate `test/fixtures -> test/transpile/cpp2`.
5. Confirm `test/transpile/cpp` and `test/transpile/cpp2` match.

### 4.1 Goal Conditions for Selfhost Validation

- Required:
  - `selfhost/py2cpp.py` must generate `selfhost/py2cpp.cpp`, and that file must compile successfully.
  - The resulting executable must be able to convert `sample/py/01_mandelbrot.py` into C++.
- Recommended checks:
  - Inspect the C++ diff between the output generated by `src/backends/cpp/cli.py` and the output generated by selfhost. Diffs themselves are allowed.
  - Compile and run the converted C++ and confirm it matches Python execution.

### 4.2 Match Conditions (Selfhost / Ordinary Comparison)

- Source match:
  - exact full-text equality of generated C++ is only a reference metric, not a hard requirement
- Runtime match:
  - for the same input, Python execution and generated C++ execution must match
- Image match:
  - both PNG and GIF must match byte-for-byte

## 5. EAST-Based C++ Route

- `src/toolchain/compiler/east.py`: Python -> EAST JSON (canonical)
- `src/toolchain/compiler/east_parts/east_io.py`: read EAST from `.py/.json` input and fill leading trivia (canonical)
- `src/backends/common/emitter/code_emitter.py`: shared base utilities for emitters in all languages (node tests, type-string helpers, safe `Any` conversions)
- `src/backends/cpp/cli.py`: EAST JSON -> C++
- `src/runtime/cpp/core/py_runtime.h`: C++ runtime aggregation
- Responsibility split:
  - `range(...)` semantics must be resolved during EAST construction
  - `src/backends/cpp/cli.py` only stringifies already-normalized EAST
  - language-agnostic helper logic must gradually move into `CodeEmitter`
- Output-layout policy:
  - the final goal is multi-file output per module (`.h/.cpp`)
  - single `.cpp` output is a compatibility path for the migration period

### 5.1 CodeEmitter Test Policy

- Regressions in `src/backends/common/emitter/code_emitter.py` are covered by `test/unit/common/test_code_emitter.py`.
- Main targets:
  - output-buffer operations (`emit`, `emit_stmt_list`, `next_tmp`)
  - dynamic-input sanitization (`any_to_dict`, `any_to_list`, `any_to_str`, `any_dict_get`)
  - node classification (`is_name`, `is_call`, `is_attr`, `get_expr_type`)
  - type-string helpers (`split_generic`, `split_union`, `normalize_type_name`, `is_*_type`)
- When adding features or changing behavior in `CodeEmitter`, add the corresponding tests there before rolling the change out to target emitters.

### 5.2 EAST-Based Rust Route (Staged Migration)

- Restrict `src/py2rs.py` to a thin CLI and I/O orchestrator.
- Separate Rust-specific output into `src/backends/rs/emitter/rs_emitter.py` (`RustEmitter`).
- `src/py2rs.py` must not depend on `src/backends/common/` or `src/rs_module/` and is already unified on `src/runtime/rs/pytra/`.
- Separate language-specific differences into `src/backends/rs/profiles/` and `src/backends/rs/`.
- The canonical smoke check for convertibility is `tools/check_py2rs_transpile.py`.
- Default `--east-stage` is `3`. `--east-stage 2` remains a migration-compatibility mode with a warning.
- The current milestone prioritizes successful transpilation. Rust compile compatibility and output quality improve in later stages.

### 5.3 EAST-Based JavaScript Route (Staged Migration)

- Restrict `src/py2js.py` to a thin CLI and I/O orchestrator.
- Separate JavaScript-specific output into `src/backends/js/emitter/js_emitter.py` (`JsEmitter`).
- `src/py2js.py` must not depend on `src/backends/common/`.
- Separate language-specific differences into `src/backends/js/profiles/` and `src/backends/js/`.
- Treat `browser` and `browser.widgets.dialog` as externally provided runtime libraries in the browser environment, so `py2js` must not generate the import bodies themselves.
- The canonical smoke check for convertibility is `tools/check_py2js_transpile.py`.
- Default `--east-stage` is `3`. `--east-stage 2` remains a migration-compatibility mode with a warning.

### 5.4 Responsibility Boundary (CodeEmitter / EAST parser / Shared Compiler Layer)

- Responsibilities of `CodeEmitter`:
  - take already-built EAST (`nodes + meta`) and emit code strings using language profiles and hooks
  - keep only output-local processing such as scope management, common expression/statement lowering, and template expansion
  - do not handle filesystem scanning, import-graph analysis, or project-wide dependency resolution
  - only read `meta.dispatch_mode`; never re-decide the mode or swap semantics
  - treat `CodeEmitter` as syntax mapping from `EAST3` onward, not as semantic lowering (`EAST2 -> EAST3`)
  - forbidden: applying dispatch semantics, deciding type_id/boxing/built-in semantics, or reinterpreting semantics in the backend/hook layer
- Responsibilities of the EAST parser (`src/toolchain/compiler/east.py`):
  - lex and parse one input (`.py`) into one-module EAST
  - stay focused on language-agnostic normalization such as `range` and on type/symbol helper data that can be completed within a single file
  - do not own cross-module import-graph analysis or module-index construction
  - generate and preserve EAST documents satisfying the root contract (`east_stage`, `schema_version`, `meta.dispatch_mode`)
- Responsibilities of the shared compiler layer (extracted under `src/toolchain/compiler/` in stages):
  - own filesystem-dependent import resolution, module EAST map construction, symbol-index/type-schema construction, and dependency dumps
  - each `py2*.py` CLI must finish analysis in this shared layer and then pass the result into `CodeEmitter`
  - `--object-dispatch-mode` is decided exactly once at the start of compilation and kept as `meta.dispatch_mode` across stages
  - dispatch semantics are applied only in `EAST2 -> EAST3` lowering, never re-decided in the backend or hooks

### 5.5 `TypeExpr` Implementation Contract (Mandatory)

- Treat `type_expr` / `arg_type_exprs` / `return_type_expr` as the canonical carriers of type meaning, and treat `resolved_type` / `arg_types` / `return_type` only as migration-compat mirrors.
- Frontend, normalization, validators, and lowering must not re-split `resolved_type` to recover meaning when `type_expr` is present on a node.
- `OptionalType`, `UnionType(union_mode=dynamic)`, and `NominalAdtType` must stay on distinct lanes and must not be collapsed back into one string parser helper.
- Treat `JsonValue` / `JsonObj` / `JsonArr` as a nominal closed ADT lane, not as a general union. Connect them to IR/validators/backends while preserving the decode-first contract, and never turn them into a new spelling for `object` fallback.
- Even where `toolchain/link/runtime_template_specializer.py`, optimizer passes, or backend helpers still carry local type-string parsers or substitution helpers, they must switch to `type_expr` as the source of truth once it exists. Regenerating mirror strings is allowed; reconstructing meaning from those mirrors is not.
- Backends must not silently collapse unsupported general unions into `object`, `String`, or similar fallbacks. If temporary compatibility remains, it must come with a fail-fast guard, a decision-log entry, and a removal plan.
- Any mismatch between `type_expr` and its `resolved_type` mirror, or any path that tries to emit a nominal ADT as a general union, must fail closed as `semantic_conflict` or `unsupported_syntax`.

## 6. LanguageProfile / CodeEmitter

- `CodeEmitter` owns the language-agnostic skeleton: node traversal, scope management, and common helpers.
- Language-specific differences are defined in `LanguageProfile` JSON:
  - type mappings
  - operator mappings
  - runtime-call mappings
  - syntax templates
- Cases that cannot be represented cleanly in JSON are handled by hooks.
- The detailed schema is defined canonically in `docs/en/spec/spec-language-profile.md`.
- The common hook precedence for `render_expr` is:
  - `on_render_expr_<kind>` -> `on_render_expr_kind` -> `on_render_expr_leaf/complex` -> emitter default implementation
- The per-kind hook name uses the EAST kind converted into snake_case (example: `IfExp -> on_render_expr_if_exp`).
- `py2ts.py` is currently a preview implementation routed through the JavaScript emitter, so TypeScript follows the same `render_expr` hook order and naming convention.

### 6.1 Backend Runtime Metadata Contract

- The only inputs that the backend, emitter, or hooks may use to decide runtime calls are `runtime_module_id`, `runtime_symbol`, `semantic_tag`, `runtime_call`, `resolved_runtime_call`, `resolved_runtime_source`, and adapter-kind/import-binding metadata added by the lowerer or linker.
- The backend, emitter, and hooks must not branch on source-side knowledge.
  - Examples: `module_id == "math"`, `owner == "math"`, `module_name == "pytra.utils"`, `resolved_runtime.endswith(".pi")`
  - Examples: deciding semantics from helper names such as `pyMathPi`, `pyMathE`, `save_gif`, `write_rgb_png`, `grayscale_palette`
  - Examples: directly interpreting positional arity, defaults, or keywords (`delay_cs`, `loop`) for `save_gif`
- Target-specific backends are allowed only to render resolved metadata into target syntax.
  - Example: render `runtime_symbol=sin` as `scala.math.sin`
  - Example: render a resolved import as `using`, `use`, `import`, or `#include`
- It is allowed for a target helper name to appear in final output, but only as the result of rendering a target symbol chosen by the index or lowerer, never by reinterpreting source-side module names or helper ABI details.
- Continuous source-scan guards and representative backend smokes must ensure that the forbidden knowledge above does not re-enter emitter sources.

## 7. Shared Rules for Implementation

- Put only language-agnostic reusable logic under `src/backends/common/`.
- Do not place language-specific rules such as type mappings, reserved words, or runtime names under `src/backends/common/`.
- Place runtime bodies under `src/runtime/<lang>/pytra/`, and do not add new runtime bodies under `src/*_module/`.
- Logic that can be shared by `py2x.py --target cpp` and `py2rs.py` must first move into `CodeEmitter`, not directly into individual emitters.
- Separate language-specific branches into `hooks` or `profiles`, and keep each `py2*.py` as a thin orchestrator.
- Resolve runtime modules, helper ABI, and source-side stdlib names entirely through profiles, the runtime symbol index, and lowerers. Do not add new branches for `math`, `png`, `gif`, `save_gif`, `write_rgb_png`, and similar names to emitter bodies.
- Collect shared CLI arguments such as `input`, `output`, `--negative-index-mode`, and `--parser-backend` into `src/toolchain/compiler/transpile_cli.py` and reuse them from each `py2*.py` `main()`.
- In selfhost-targeted code, avoid dynamic imports such as `try/except ImportError` branching or `importlib`; use only static imports.
- In selfhost-targeted code, meaning the transpiler core, backends, and IR implementation under `src/`, do not depend on Python's standard `ast` module (`import ast` / `from ast ...`).
- If syntax parsing or dependency extraction is needed, implement it using EAST nodes and existing IR data, without adding fallbacks to `ast`.
- As an exception, code under `tools/` and `test/` is not selfhost-targeted and may use `ast`.
- Add Japanese comments that explain the purpose of class names, function names, and member variable names.
- When documenting standard-library support, list functions explicitly, not only module names.
- Functions not documented here are treated as unsupported.

## 8. Notes on Runtime Mode per Target

- `py2rs.py`: native conversion mode (does not depend on the Python interpreter)
- `py2js.py`: EAST-based conversion mode (browser runtime provided externally)
- `py2ts.py`: EAST-based preview mode (JS-compatible output)
- `py2go.py` / `py2java.py`: EAST-based preview mode (still moving in stages toward dedicated emitters)
- `py2swift.py` / `py2kotlin.py`: EAST-based preview mode (still moving in stages toward dedicated emitters)

### 8.1 `--east-stage` Operation (Implementation-Aligned)

- `py2x.py --target cpp` and the eight non-C++ converters (`py2rs.py`, `py2cs.py`, `py2js.py`, `py2ts.py`, `py2go.py`, `py2java.py`, `py2kotlin.py`, `py2swift.py`) all default to `--east-stage 3`.
- `py2x.py --target cpp` accepts only `--east-stage 3`; `--east-stage 2` is a hard error.
- Only the eight non-C++ converters accept `--east-stage 2` as a migration-compatibility mode and must print `warning: --east-stage 2 is compatibility mode; default is 3.`
- The canonical regression routes are `tools/check_py2cpp_transpile.py` and `tools/check_noncpp_east3_contract.py`.
