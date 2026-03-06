<a href="../../ja/spec/spec-runtime.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# Runtime Specification

## 0. Source of Truth and Responsibility Boundary

The only runtime source of truth (SoT) is the pure Python module set below:

- `src/pytra/built_in/*.py`
- `src/pytra/std/*.py`
- `src/pytra/utils/*.py`

Required rules:

- If logic can be expressed in SoT, do not reimplement it manually in runtime code.
- Backends / emitters must only render module / symbol / signature information that EAST has already resolved.
- Do not hardcode library function names, module names, type names, dispatch tables, or ad-hoc special cases inside backend / emitter code.
- Knowledge such as `math`, `json`, `gif`, `png`, `Path`, `assertions`, `re`, or `typing` must not be embedded into transpiler source code.

## 0.5 Runtime Directory Classification

All runtimes across all languages must use the following four-way responsibility split:

- `src/runtime/<lang>/core/`
  - Low-level runtime / ABI / object representation / GC / I/O / OS / SDK glue.
  - Not a place for handwritten substitutes of SoT modules.
- `src/runtime/<lang>/built_in/`
  - Runtime generated from `src/pytra/built_in/*.py`.
- `src/runtime/<lang>/std/`
  - Runtime generated from `src/pytra/std/*.py`.
- `src/runtime/<lang>/utils/`
  - Runtime generated from `src/pytra/utils/*.py`.

Notes:

- This classification is by responsibility, not by "generated vs handwritten".
- `core/` may contain generated fragments in the future; it still remains the `core/` responsibility bucket.
- `built_in/std/utils` are the locations for SoT-derived runtime modules. Their equivalent logic must not be duplicated under `core/`.

## 0.6 Runtime File Naming Rule

Across `core / built_in / std / utils`, runtime filenames must use the following convention:

- Auto-generated:
  - `<name>.gen.h`
  - `<name>.gen.cpp`
- Handwritten extension:
  - `<name>.ext.h`
  - `<name>.ext.cpp`

Meaning:

- `.gen.*`
  - Files mechanically generated from SoT.
  - Manual edits are forbidden.
- `.ext.*`
  - Minimal language-specific implementations such as ABI glue, OS / SDK calls, and `@extern` landing points.
  - Manual edits are allowed.

Required rules:

- All newly added runtime files must use the `gen/ext` naming.
- Unsuffixed runtime files are legacy and migration targets. Do not add new ones.
- `*.ext.*` must not contain full logic that duplicates SoT.
- When a generated artifact and a handwritten complement coexist for the same module, they must share the same basename and differ only by `.gen.*` vs `.ext.*`.

Examples:

- `src/runtime/cpp/std/math.gen.h`
- `src/runtime/cpp/std/math.ext.cpp`
- `src/runtime/cpp/utils/png.gen.cpp`
- `src/runtime/cpp/core/py_runtime.ext.h`

## 0.61 Include / Reference Rule

- Backends, build scripts, and transpiler code must reference runtime files by their canonical suffixed names.
- Do not introduce unsuffixed aliases just because they are shorter for humans.
- Include / compile targets must remain uniquely determined by responsibility directory plus `gen/ext` suffix.

## 0.62 Boundary Between `core` and `ext`

- `core/` means "low-level runtime responsibility", not "a place for handwritten files in general".
- Module-specific complement implementations for `std/utils/built_in` must stay in the matching responsibility directory as `.ext.*`.
- Only module-independent ABI / object / container / I/O / OS glue belongs in `core/`.

Incorrect examples:

- Putting the complement implementation of `std/math` under `core/`
- Handwriting the body of `utils/png` under `core/`
- Embedding `built_in`-derived logic into `py_runtime`

## 0.63 No Special-Purpose Runtime Generators

- Do not add runtime generation scripts dedicated to specific modules outside `src/py2x.py` or the future unified CLI.
- Modules such as `png.py`, `gif.py`, `json.py`, and `math.py` must always generate `*.gen.*` through the canonical transpiler path.
- Do not introduce language-specific special naming or special templates just to generate runtime modules.

## 0.64 `__all__` Is Forbidden in `src/pytra`

Do not define `__all__` in `src/pytra/**/*.py`.

- Keep the selfhost and transpiler implementation simple.
- Control public symbols by presence of top-level definitions, not by `__all__`.
- The same rule applies to SoT modules under `built_in/std/utils`.

## 0.65 Host-Only Import Alias Rule (`as __name`)

Treat imports such as `import ... as __m` / `from ... import ... as __f` as host-only imports when the alias starts with `__`.

- Host-only imports are only for Python-runtime fallback behavior.
- The main use case is evaluating Python fallback bodies for `@extern` functions.
- The transpiler must not emit host-only imports as EAST `Import` / `ImportFrom` nodes.
- A single-underscore alias such as `_name` is not host-only.

## 0.66 Stdlib Submodule Rule

Treat stdlib submodules such as `os.path` as independent SoT modules.

Required:

- Split each submodule into `src/pytra/std/<name>.py`.
  - Example: `os.path` -> `src/pytra/std/os_path.py`
- Parent modules must reference them by module import.
  - Example: `from pytra.std import os_path as path`
- Keep calls as module function calls.
  - Example: `path.join(...)`
- If native implementation is required, declare it with `@extern` on the SoT side and place the concrete body in the matching `.ext.*` runtime file.

Forbidden:

- Storing a submodule into an `object` variable
- Adding emitter / runtime special cases tied to concrete submodule names

## 0.7 C++ Runtime Operation

The canonical C++ runtime layout is:

- `src/runtime/cpp/core/`
- `src/runtime/cpp/built_in/`
- `src/runtime/cpp/std/`
- `src/runtime/cpp/utils/`

Regeneration:

- SoT-derived modules in `built_in/std/utils` are emitted into their canonical locations via `--emit-runtime-cpp`.
- Examples:
  - `python3 src/py2x.py src/pytra/built_in/type_id.py --target cpp --emit-runtime-cpp`
  - `python3 src/py2x.py src/pytra/std/math.py --target cpp --emit-runtime-cpp`
  - `python3 src/py2x.py src/pytra/utils/png.py --target cpp --emit-runtime-cpp`

Minimum validation:

- `python3 tools/check_runtime_cpp_layout.py`
- `python3 tools/check_runtime_std_sot_guard.py`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples`

Forbidden:

- Manual edits to `*.gen.*`
- Reimplementing SoT-equivalent logic under `core/`
- Hardcoded module / symbol resolution inside backend / emitter code
- Adding module-specific runtime generation scripts

## 0.71 Apply the Same Rule to All Runtime Languages

This classification and naming rule is not C++-specific. It applies to every runtime language:

- `src/runtime/<lang>/core/`
- `src/runtime/<lang>/built_in/`
- `src/runtime/<lang>/std/`
- `src/runtime/<lang>/utils/`

Each backend must generate SoT-derived code into `built_in/std/utils`, and place only the minimum native implementation into `.ext.*`.
