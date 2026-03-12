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

### 0.60 Current C++ Module Runtime Layout

The canonical C++ module-runtime layout is:

- `src/runtime/cpp/core/`
- `src/runtime/cpp/generated/{built_in,std,utils}/`
- `src/runtime/cpp/native/{built_in,std,utils}/`
- `src/runtime/cpp/pytra/{built_in,std,utils}/`

Meaning:

- `core/`
  - low-level runtime foundation
- `generated/`
  - SoT-generated artifacts
- `native/`
  - target-language-specific companion for C++ stdlib / filesystem / chrono / regex / OS / ABI glue
- `pytra/`
  - generated public include shim and stable include path for generated code

Mandatory rules:

- generated code must continue to include `pytra/...` as the canonical public include surface
- `generated/` and `native/` are internal artifacts / compile sources and must not be included directly by user code
- declarations should live in `generated/*.h` by default; `native/*.h` must be limited to cases that truly require templates or inline helpers
- `native/` is not a general handwritten dumping ground; it is limited to C++-specific companion code

### 0.601 C++ Core Runtime Ownership Split

`src/runtime/cpp/core/` stays as the low-level runtime responsibility name, but ownership is split as follows:

- `src/runtime/cpp/core/`
  - stable include surface / compatibility forwarder
- `src/runtime/cpp/generated/core/`
  - low-level core artifacts transformed from pure Python SoT
- `src/runtime/cpp/native/core/`
  - handwritten low-level runtime source of truth

Mandatory rules:

- `core/` must ultimately shrink to a compatibility include surface rather than an implementation source of truth
- generated core goes only under `generated/core/`
- handwritten core goes only under `native/core/`
- core-lane naming stays plain (`core/*.h`, `native/core/*.{h,cpp}`); do not reintroduce `.ext` on the core lane
- do not introduce `pytra/core`
- compiler output, generated runtime, native companions, and backend code include `runtime/cpp/native/core/...` directly

Why `pytra/core` is not introduced:

- `pytra/` is reserved for generated public shims of `std/built_in/utils` module runtime
- adding `pytra/core` would create two public include roots for low-level core and blur ownership rather than clarifying it

## 0.61 Include / Reference Rules

- Backends / build scripts / transpiler code must reference runtime files via the canonical naming scheme of the target's current ownership model.
- Include / compile targets must remain uniquely determined by that ownership scheme.

Additional C++ rules:

- public includes used by generated code are fixed to the `pytra/...` shim
- resolution of `generated/` / `native/` real paths belongs to the runtime symbol index and build graph; emitters must not hardcode them
- `--emit-runtime-cpp` writes generated artifacts to `src/runtime/cpp/generated/...`
- `runtime_symbol_index` / build graph must treat `pytra/...` as the primary public header and derive compile sources from `generated/native`
- `check_runtime_cpp_layout.py` must validate both legacy-closed module dirs and the ownership boundary among `generated/native/pytra/core`
- low-level core includes stay under `core/...`; do not introduce `pytra/core/...`

## 0.62 Boundary Between `core` and Module Companions

- `core/` means low-level runtime responsibility, not a generic home for handwritten code
- after core-split rollout, `core/` is the stable include surface, handwritten source of truth lives in `native/core/`, and generated source of truth lives in `generated/core/`
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
  - headers may include only stable core headers
  - `.cpp` may include `runtime/cpp/native/core/py_runtime.h` and sibling generated headers, but must not embed handwritten C++-only glue
  - mutable-container helpers that want value ABI at the helper boundary must use an explicit contract such as `@abi`
- `generated/core`
  - limited to low-level helpers that can still be generated from pure Python
  - do not use it as a second home for `built_in/std/utils` module runtime
  - there is no checked-in `runtime/cpp/core/*.h` surface; include paths must follow the `generated/core` or `native/core` ownership lanes
- common rules
  - build graph and runtime symbol index derive compile sources from public headers
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

Canonical C++ runtime validation:

- `python3 tools/check_runtime_cpp_layout.py`
- `python3 tools/check_runtime_std_sot_guard.py`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples`

Forbidden:

- manual edits to generated artifacts
- reimplementing SoT-equivalent logic under `core/`
- hardcoded module/symbol resolution inside backend / emitter code
- dedicated module-specific runtime generators

## 0.71 Apply the Same Rule to Multi-Language Runtime

The same responsibility split applies to every runtime language:

- `src/runtime/<lang>/core/`
- `src/runtime/<lang>/built_in/`
- `src/runtime/<lang>/std/`
- `src/runtime/<lang>/utils/`

For C++, the directory names are represented through `generated/native/pytra/core`; for other targets, suffix-based ownership may continue until their migration is complete.
