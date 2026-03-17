<a href="../../ja/spec/spec-runtime.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# Runtime Specification

## 0. Source of Truth and Responsibility Boundary

The only runtime source of truth (SoT) is the following pure Python module set:

- `src/pytra/built_in/*.py`
- `src/pytra/std/*.py`
- `src/pytra/utils/*.py`

Required rules:

- If logic can be expressed in SoT, do not manually reimplement it in runtime code.
- Backends / emitters must only render module / symbol / signature information that EAST has already resolved.
- Do not hardcode module names, helper names, dispatch tables, or ad-hoc runtime special cases inside backend / emitter code.

## 0.5 Runtime Directory Classification

Across all languages, runtime layout is unified into the following four responsibility buckets:

- `core`
  - low-level runtime / ABI / object representation / GC / I/O / OS / SDK glue
- `built_in`
  - runtime responsibility corresponding to `src/pytra/built_in/*.py`
- `std`
  - runtime responsibility corresponding to `src/pytra/std/*.py`
- `utils`
  - runtime responsibility corresponding to `src/pytra/utils/*.py`

Representative layouts:

- default / legacy:
  - `src/runtime/<lang>/core/`
  - `src/runtime/<lang>/built_in/`
  - `src/runtime/<lang>/std/`
  - `src/runtime/<lang>/utils/`
- current C++ runtime layout:
  - `src/runtime/cpp/generated/{built_in,std,utils,compiler}/`
  - `src/runtime/cpp/native/{built_in,std,utils,compiler}/`
  - `src/runtime/cpp/generated/core/`
  - `src/runtime/cpp/native/core/`

Notes:

- `built_in/std/utils` are responsibility buckets derived from SoT and must not be duplicated under `core/`.
- In C++, those responsibility names are expressed through subdirectories under `generated/native`.

## 0.6 Runtime File Naming Rules

Runtime ownership may be expressed in one of the following target-specific ways:

- suffix-based layout (legacy / `core/` / not-yet-migrated targets)
  - generated:
    - `<name>.gen.h`
    - `<name>.gen.cpp`
  - handwritten extension:
    - `<name>.ext.h`
    - `<name>.ext.cpp`
- directory-based layout (current C++ module runtime)
  - generated:
    - `src/runtime/cpp/generated/<group>/<name>.h`
    - `src/runtime/cpp/generated/<group>/<name>.cpp`
  - native:
    - `src/runtime/cpp/native/<group>/<name>.h`
    - `src/runtime/cpp/native/<group>/<name>.cpp`

Meaning:

- `generated/`
  - generated source of truth for the C++ module runtime
- `native/`
  - target-language-specific companion for the C++ module runtime

Required rules:

- Under `src/runtime/cpp/{built_in,std,utils}`, do not add new module-runtime `.h/.cpp`; suffix-based ownership there is legacy-closed.
- Not-yet-migrated targets may keep `.gen/.ext`.
- C++ `core` uses plain naming as canonical (`core/*.h`, `native/core/*.{h,cpp}`).
- Ownership in the C++ module runtime is identified by directories (`generated/native`), not basename suffixes.

Examples:

- `src/runtime/cpp/generated/std/math.h`
- `src/runtime/cpp/native/std/math.cpp`
- `src/runtime/cpp/generated/std/math.h`
- `src/runtime/cpp/native/core/py_runtime.h`

### 0.6n Native File Naming Convention for Non-C++ Languages

For languages other than C++ (C#, Java, Rust, Go, Kotlin, Swift, etc.), `native/` files follow this convention:

- Native file name: `<name>_native.<ext>`
- Native class/module name: `<name>_native` (file name and class name must match)

Rationale:

- In C++, `generated/` and `native/` use **same-named files** (e.g., `math.h` / `math.cpp`), with the directory alone distinguishing ownership. This works because the linker/include system unifies same-named symbols.
- In non-C++ languages, `generated/std/os.cs` and `native/std/os.cs` would both appear in the same build, making them **indistinguishable by filename alone** (with potential class name collision risk in C#).
- Applying `_native` suffix to both file name and class name satisfies each language's convention of **file name = class name** while clearly distinguishing from the generated side.

Examples (C#):

- `src/runtime/cs/generated/std/os.cs` → `public static class os` (generated, from SoT)
- `src/runtime/cs/native/std/os_native.cs` → `public static class os_native` (native, host API implementation)

Mandatory rules:

- Non-C++ `native/std/<name>_native.<ext>` acts as a thin wrapper delegated to by the corresponding `generated/std/<name>.<ext>`.
- The canonical form is: `generated/` delegates to `native/` (calling `<name>_native.<method>()`). Reverse dependencies are not allowed.
- The `native/` side must not duplicate SoT-level logic. Limit it to minimal host API binding code.
- Compiler optimization (inlining) eliminates delegation overhead at runtime. Single-file approaches via mix-in or partial class are not used.

### 0.60 Current C++ Module Runtime Layout

The checked-in C++ runtime uses this ownership layout:

- `src/runtime/cpp/generated/{built_in,std,utils,core}/`
- `src/runtime/cpp/native/{built_in,std,utils,core}/`

Meaning:

- `generated/`
  - checked-in runtime artifacts generated from the SoT
- `native/`
  - handwritten canonical runtime and C++-specific companion / ABI glue

Mandatory rules:

- do not keep checked-in `src/runtime/cpp/{core,pytra}/**`; if a stable SDK include surface is needed, generate it during export/packaging instead of committing it to the source tree
- generated code, compiler paths, and tests use direct ownership headers (`generated/...` or `native/core/...`)
- for C++, `runtime_symbol_index` keeps `public_headers` and `compiler_headers` aligned on the same direct ownership header
- declarations belong in `generated/*.h` by default; limit `native/*.h` to templates, inline helpers, or ABI glue that truly require handwritten C++
- `native/` is not a dumping ground; it is limited to C++-specific companion code

### 0.601 C++ Core Runtime Ownership Split

The low-level `core` responsibility stays, but the checked-in surface is limited to `generated/core` and `native/core`.

- `src/runtime/cpp/generated/core/`
  - low-level core artifacts that can be generated from pure-Python SoT
- `src/runtime/cpp/native/core/`
  - handwritten low-level runtime source of truth

Mandatory rules:

- handwritten low-level core lives only under `native/core/`
- only low-level helpers that stay pure may live under `generated/core/`
- do not reintroduce checked-in `runtime/cpp/core/*.h` or `runtime/cpp/pytra/core/*.h`
- compiler output, generated runtime, native companions, and backend code include `runtime/cpp/native/core/...` directly
- `generated/core` / `generated/built_in` artifacts may be produced only through `src/py2x.py --emit-runtime-cpp`; do not add module-specific generators or ad-hoc templates
- checked-in `generated/core` / `generated/built_in` artifacts require plain naming plus `source:` / `generated-by:` markers
- if an export-time SDK surface is needed, generate it from the runtime symbol index / manifest rather than keeping compatibility shims in the repo

## 0.61 Include / Reference Rules

- Backends / build scripts / transpiler code must reference runtime files via the canonical naming scheme of the target's current ownership model.
- Include / compile targets must remain uniquely determined by that ownership scheme.

Additional C++ rules:

- generated code includes the direct ownership header returned by the runtime symbol index (for example `generated/std/time.h`, `generated/utils/png.h`, `native/core/dict.h`)
- the low-level prelude is `runtime/cpp/native/core/py_runtime.h`
- resolution of `generated/` / `native/` real paths belongs to the runtime symbol index and build graph; emitters must not hardcode them
- `--emit-runtime-cpp` writes only generated artifacts under `src/runtime/cpp/generated/...`
- for C++, `runtime_symbol_index` / build graph keep `public_headers == compiler_headers` and derive compile sources from those direct ownership headers
- `check_runtime_cpp_layout.py` must fail if `src/runtime/cpp/{core,pytra}` reappears and must audit the ownership boundary under `generated/native`
- do not add new include roots beyond the direct ownership paths

## 0.62 Boundary Between `core` and Module Companions

- the low-level C++ runtime is represented by `generated/core` plus `native/core`; there is no standalone checked-in `core/` include surface
- module companion implementations for `std/utils/built_in` live in `native/` for the C++ module runtime
- `native/*.h` should be kept minimal; declarations belong in `generated/*.h` by default
- `native/core/*.h` may define object/container representations and low-level helpers, but must not absorb high-level module runtime again

`py_runtime` rules:

- `src/runtime/cpp/native/core/py_runtime.h` is the canonical low-level runtime header, not the canonical home for high-level built_in semantics
- `src/runtime/cpp/native/core/py_runtime.h` may keep only `PyObj` / `object` / `rc<>` / type_id / low-level container primitives / dynamic iteration / process I/O / C++ stdlib/OS glue
- helpers such as `str::split`, `splitlines`, `count`, and `join` must not remain permanently in `native/core/py_runtime.h`; they are candidates to move back into `generated/built_in` or SoT
- `generated/core` is not a dumping lane for overflow from `py_runtime`; only low-level helpers that can stay pure should go there

### 0.621 Emission-Lane Contract for `generated/built_in` and `generated/core`

When slimming `py_runtime`, route helpers as follows:

- `generated/built_in`
  - SoT: `src/pytra/built_in/*.py`
  - for pure built_in semantics that can be expressed in Python, such as `str::split` / `splitlines` / `count` / `join`
  - headers may include stable `native/core/*.h` headers and, when required, the matching `native/<bucket>/*.h` companion for the same module
  - `.cpp` may include `runtime/cpp/native/core/py_runtime.h` and sibling generated headers, but must not embed handwritten C++-only glue
  - mutable-container helpers that want value ABI at the helper boundary must use an explicit contract such as `@abi`
- `generated/core`
  - limited to low-level helpers that can still be generated from pure Python
  - do not use it as a second home for `built_in/std/utils` module runtime
  - there is no checked-in `runtime/cpp/core/*.h` surface; include paths must follow the `generated/core` or `native/core` ownership lanes
- common rules
  - build graph and runtime symbol index derive compile sources from direct ownership headers recorded in `public_headers` / `compiler_headers`
  - deciding to move a helper requires more than "it can be written in Python"; it must also preserve stable include surfaces and avoid new ownership/ABI glue

## 0.63 No Special Runtime Generators

- Do not add module-specific runtime generators outside `src/py2x.py` / the unified CLI.
- Modules such as `png.py`, `gif.py`, `json.py`, and `math.py` must generate their target runtime artifacts only through the canonical route.

## 0.64 `__all__` Is Forbidden in `src/pytra`

- Do not define `__all__` in `src/pytra/**/*.py`.
- The same rule applies to SoT modules in `built_in/std/utils`.

## 0.65 Host-Only Import Alias Rule (`as __name`)

Imports such as `import ... as __m` are host-only when the alias starts with `__`.

- they exist only for Python-runtime fallback behavior
- they must not be emitted into target-language code
- a single underscore does not count as host-only

## 0.66 Stdlib Submodule Rule

Treat stdlib submodules such as `os.path` as independent SoT modules.

Required:

- split submodules into `src/pytra/std/<name>.py`, for example `os.path` -> `src/pytra/std/os_path.py`
- parent modules reference them by module import
- calls stay as module function calls
- if native implementation is required, declare it with `@extern` in SoT and place the implementation in the matching companion layer
- `extern_contract_v1` / `extern_v1` must stay declaration-only metadata and must not encode the native implementation owner.
- Ambient-global `extern()` / `extern("symbol")` is separate from runtime-SoT `@extern` and must not participate in runtime symbol index ownership decisions.

## 0.67 Internal Representation Policy for Mutable Types

Inside runtime / backend internals, mutable types should preserve shared-reference semantics first.

- immutable types such as `str` may use value representation internally by default
- mutable containers and mutable user classes should stay ref-first
- lowering to value form is allowed only as an optimization proven safe

## 0.68 Runtime Symbol Index and Backend Responsibility Boundary

The canonical source for runtime symbol ownership and target artifacts is `tools/runtime_symbol_index.json`.

Mandatory rules:

- IR keeps target-independent `runtime_module_id` and `runtime_symbol`
- backends derive target-specific include paths / compile sources / companions from index data
- do not embed target-specific paths such as `runtime/cpp/generated/std/time.h` into IR
- do not re-hardcode module ownership such as `py_enumerate -> iter_ops` inside emitter code

Backends may read:

- `runtime_module_id`
- `runtime_symbol`
- declaration-only `extern_contract_v1` / `extern_v1`
- `semantic_tag`
- `runtime_call`
- `resolved_runtime_call`
- `resolved_runtime_source`
- adapter / ABI / import-binding metadata attached by lowerer/linker

Backends must not reinterpret source-side knowledge such as:

- source import names (`math`, `pytra.utils`, `pytra.std.math`)
- source attribute spelling (`.pi`, `.e`, `.sqrt`)
- helper names such as `pyMathPi`, `save_gif`, `write_rgb_png`
- ad-hoc helper-ABI rules such as emitter-side positional/keyword handling for `save_gif`

## 0.7 C++ Runtime Operation

Canonical checked-in C++ runtime directories:

- `src/runtime/cpp/generated/{built_in,std,utils,core}/`
- `src/runtime/cpp/native/{built_in,std,utils,core}/`

Canonical C++ runtime validation:

- `python3 tools/check_runtime_cpp_layout.py`
- `python3 tools/check_runtime_std_sot_guard.py`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples`

Forbidden:

- manual edits to generated artifacts
- reimplementing SoT-equivalent logic under `native/`
- reintroducing checked-in `src/runtime/cpp/{core,pytra}/**`
- hardcoded module/symbol resolution inside backend / emitter code
- dedicated module-specific runtime generators

## 0.71 Apply the Same Rule to Multi-Language Runtime

The same responsibility split should be rolled out to every runtime language.

- the canonical target layout is `src/runtime/<lang>/generated/**` plus `src/runtime/<lang>/native/**`
- the non-C++ runtime baseline end state is `generated = baseline`, using `cpp/generated/{built_in,std,utils}` as the canonical module set
- baseline modules may not use `blocked`, `compare_artifact`, `no_runtime_module`, `helper_artifact`, or `native canonical` as a close condition
- the blocked/native/helper descriptions kept in `src/toolchain/compiler/noncpp_runtime_layout_contract.py` and `src/toolchain/compiler/noncpp_runtime_layout_rollout_remaining_contract.py` are legacy inventory, not the active end-state policy
- `pytra-gen/pytra-core` and checked-in `pytra/**` remain compatibility-debt inventory, not the final layout

### 0.72 Runtime `@extern` Ownership Metadata

- `extern_contract_v1` / `extern_v1` must stay declaration-only metadata and must not encode the native implementation owner.
- Ambient-global `extern()` / `extern("symbol")` is separate from runtime-SoT `@extern` and must not participate in runtime symbol index ownership decisions.
