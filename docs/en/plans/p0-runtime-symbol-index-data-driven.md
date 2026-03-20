# P0: Make the Runtime Symbol Index Data-Driven (SoT-Generated JSON + IR Normalization)

Last updated: 2026-03-06

Related TODO:
- `docs/ja/todo/index.md` `ID: P0-RUNTIME-SYMBOL-INDEX-01`

Background:
- The current EAST3 and backend stack does not preserve enough information about which module owns a runtime call.
- In concrete terms, symbols such as `py_enumerate`, `py_any`, `py_strip`, and `dict.get` still survive in IR as bare `runtime_call` strings, and later stages still contain spots where the backend guesses, “this is probably `pytra.built_in.iter_ops`” or “this is probably `pytra.built_in.string_ops`”.
- Import resolution for paths such as `import pytra.std.time` or `from pytra.utils.png import write_rgb_png` already preserves `module_id` / `export_name` in metadata, but the final rules that map them to runtime headers and runtime sources are still scattered across backend-side implementations.
- Runtime symbol lookup tables are spread across `signature_registry.py` and IR construction code, so the responsibility boundary is too easy to break. That is a recurrent design problem and not the shape the transpiler should have.
- User policy:
  - The mapping from “which file owns which symbol” must not be hardcoded in code; it must be treated as data such as JSON.
  - That does not mean adding new handwritten JSON as the source of truth. The JSON must be generated from SoT (`src/pytra/*` and runtime layout).
  - IR should carry only target-independent information. Target-specific file paths such as `*.gen.h` and `*.ext.cpp` must not be embedded in IR.

Goal:
- Unify runtime-symbol ownership and companion rules into one index JSON generated from SoT.
- Extend EAST3 so it carries `runtime_module_id + runtime_symbol` (plus only the minimum companion/dispatch metadata as needed), and shrink the backends down so they only read that index and derive target-specific headers/sources.
- Stop regressions where handwritten runtime-symbol logic creeps back into `signature_registry.py`, `core.py`, or backend emitters.

Scope:
- `src/toolchain/ir/core.py`
- `src/toolchain/frontends/signature_registry.py`
- `src/toolchain/emit/*/`
- `tools/` (index generator / guards / tests)
- `src/pytra/{built_in,std,utils}/`
- `src/runtime/<lang>/{core,built_in,std,utils}/`

Out of scope:
- target-specific codegen quality work
- new runtime APIs
- full rewrites of every backend
- handwritten edits to `.gen.*`

## Rules fixed by this plan

1. Do not hardcode `runtime symbol -> module/file` mappings in Python source.
2. Do not make handwritten JSON the source of truth. JSON must always be generated.
3. Keep only target-independent runtime information in EAST3.
4. Do not embed target-specific file paths such as `runtime/cpp/std/math.gen.h` in EAST3.
5. Backends should shrink down to deriving target artifacts from `runtime_module_id` and `runtime_symbol`.
6. Direct edits to `*.gen.*` just to make tests pass are forbidden.

## Design goal

In the final state, runtime-call-family nodes should carry at least the following information:

```json
{
  "lowered_kind": "BuiltinCall",
  "runtime_module_id": "pytra.built_in.iter_ops",
  "runtime_symbol": "py_enumerate",
  "runtime_dispatch": "function",
  "runtime_companion": "gen+ext"
}
```

Likewise, import-derived symbols should carry at least:

```json
{
  "binding_module_id": "pytra.std.time",
  "binding_export_name": "perf_counter",
  "runtime_module_id": "pytra.std.time",
  "runtime_symbol": "perf_counter"
}
```

The important part is:
- `runtime_module_id` / `runtime_symbol` stay target-independent
- paths such as `runtime/cpp/std/time.gen.h` are derived later by the backend from the index
- the presence of `gen/ext` companions is tracked in the index

## Minimum generated-index specification

Provisional name: `tools/runtime_symbol_index.json`

Expected shape:

```json
{
  "schema_version": 1,
  "generated_by": "tools/gen_runtime_symbol_index.py",
  "modules": {
    "pytra.built_in.iter_ops": {
      "source_py": "src/pytra/built_in/iter_ops.py",
      "exports": {
        "py_enumerate_object": {
          "kind": "function",
          "companions": ["gen", "ext"]
        },
        "py_reversed_object": {
          "kind": "function",
          "companions": ["gen", "ext"]
        }
      }
    }
  },
  "targets": {
    "cpp": {
      "pytra.built_in.iter_ops": {
        "header": "src/runtime/cpp/built_in/iter_ops.gen.h",
        "sources": [
          "src/runtime/cpp/built_in/iter_ops.gen.cpp",
          "src/runtime/cpp/built_in/iter_ops.ext.h"
        ]
      }
    }
  }
}
```

Notes:
- During implementation it is fine to split `sources` into a clearer pair such as `public_headers` and `compile_sources`, as long as the result is easier for the implementer to reason about.
- The schema must still keep the three levels distinct: module, symbol, and target artifact.

## Detailed breakdown

- [x] [ID: P0-RUNTIME-SYMBOL-INDEX-01] Move runtime-symbol ownership and companion rules into SoT-generated JSON and switch IR/backend/tooling over to that index.
- [x] [ID: P0-RUNTIME-SYMBOL-INDEX-01-S1-01] Inventory the current handwritten runtime-symbol knowledge and fix a table that separates what remains in IR, what moves into the index, and what the backend derives.
- [x] [ID: P0-RUNTIME-SYMBOL-INDEX-01-S1-02] Define the `runtime symbol index` schema and document the responsibilities of `module / symbol / target artifact / companion`.
- [x] [ID: P0-RUNTIME-SYMBOL-INDEX-01-S2-01] Add a generator that scans `src/pytra/{built_in,std,utils}` and `src/runtime/<lang>/{core,built_in,std,utils}` and emits the index JSON.
- [x] [ID: P0-RUNTIME-SYMBOL-INDEX-01-S2-02] Add unit tests for the generator and fix representative cases such as `py_enumerate` / `py_any` / `py_strip` / `perf_counter` / `write_rgb_png` / `Path` at the index level.
- [x] [ID: P0-RUNTIME-SYMBOL-INDEX-01-S2-03] Integrate the index generator into CI/local checks so stale indexes fail fast when the runtime layout changes.
- [x] [ID: P0-RUNTIME-SYMBOL-INDEX-01-S3-01] Add `runtime_module_id` and `runtime_symbol` to EAST3 runtime-call nodes so they no longer depend only on a bare `runtime_call` string.
- [x] [ID: P0-RUNTIME-SYMBOL-INDEX-01-S3-02] Extend resolved imported symbols (`from X import Y` / `import X` + `X.Y`) so they also carry `runtime_module_id` / `runtime_symbol`.
- [x] [ID: P0-RUNTIME-SYMBOL-INDEX-01-S3-03] Retire the handwritten runtime-symbol tables in `signature_registry.py` in stages, until at least the responsibility for guessing file paths is gone.
- [x] [ID: P0-RUNTIME-SYMBOL-INDEX-01-S4-01] Use the C++ backend as the first consumer and switch include collection, namespace resolution, and runtime-source collection to the index JSON.
- [x] [ID: P0-RUNTIME-SYMBOL-INDEX-01-S4-02] Reorganize `build_multi_cpp.py` / `gen_makefile_from_manifest.py` so they consistently derive `*.gen.*` and `*.ext.*` companions from the index.
- [x] [ID: P0-RUNTIME-SYMBOL-INDEX-01-S4-03] Remove ownership-guessing logic for `py_enumerate` / `py_any` / `py_strip` / `dict.get` / `perf_counter` / `Path` from the C++ emitter and move it to IR + index dependence.
- [x] [ID: P0-RUNTIME-SYMBOL-INDEX-01-S5-01] Organize the application policy for non-C++ backends and align the responsibility boundary of `resolved_runtime_call` and module/file resolution around the index.
- [x] [ID: P0-RUNTIME-SYMBOL-INDEX-01-S5-02] Document in `docs/ja/spec` that “IR holds module+symbol” and “target file paths are derived by the index + backend”.
- [x] [ID: P0-RUNTIME-SYMBOL-INDEX-01-S5-03] Run representative regressions (C++ include resolution, runtime build graph, import resolution, unit parity) and confirm that the old ad-hoc fallbacks are no longer needed.

## S1-01 inventory result (fixed on 2026-03-06)

### 1. Classification table for handwritten sites

| Layer | File | Current information it owns | Problem | Correct destination |
| - | - | - | - | - |
| IR construction | `src/toolchain/ir/core.py` | bare `runtime_call` strings such as `enumerate -> py_enumerate`, `any -> py_any`, `all -> py_all`, `reversed -> py_reversed`, `bytes/bytearray/list/set/dict` ctors | symbol names exist without owning modules | keep `runtime_module_id` + `runtime_symbol` in IR |
| frontend | `src/toolchain/frontends/signature_registry.py` | runtime-call matching for `perf_counter`, `Path`, `json.loads`, `write_rgb_png`, `save_gif`, `math.sqrt`, owner methods, and type inference | it still owns file/path inference; target-independent and target-dependent knowledge are mixed | keep only minimal module/symbol normalization and move file/artifact mapping into the index |
| backend (C++) | `src/toolchain/emit/cpp/emitter/module.py` | guesses include paths and namespaces from `pytra.std.*` / `pytra.utils.*` / `pytra.built_in.*` | backend implementation re-guesses module tails and file paths | derive include/header information from the index |
| backend (C++) | `src/toolchain/emit/cpp/emitter/runtime_paths.py` | `module_tail -> *.gen.h`, `module_name -> runtime/cpp/...` conversion | as a C++ path-rule center it is fine, but it becomes over-responsible if it also decides symbol ownership | shrink it to `module -> target artifact` derivation only |
| backend (C++) | `src/toolchain/emit/cpp/profiles/runtime_calls.json` | C++ callee names for `os.path.join`, `glob.glob`, `ArgumentParser`, `re.sub`, `sys.stdout.write`, etc. | symbol ownership and final rendering names are mixed; without the index this invites ad-hoc fallbacks | keep it temporarily only as a C++ callee-name table and split module ownership into IR + index |
| tooling | `tools/build_multi_cpp.py` | recursively collects runtime sources starting from manifest sources | rebuilds `.gen/.ext` companions from includes but not on module/symbol units | derive required artifacts per module from the index |
| tooling | `tools/gen_makefile_from_manifest.py` | re-collects runtime sources from the manifest | the build graph still leans on include-based guessing | decide compile sources from the index + manifest module information |

### 2. What stays where

| Information | Kept in IR | Moved to index | Derived by backend/tooling |
| - | - | - | - |
| `runtime_module_id` | yes | no | no |
| `runtime_symbol` | yes | no | no |
| `runtime_dispatch` (`function` / `method` / `ctor`, etc.) | minimum only | may exist as helper metadata | consulted during rendering |
| target-specific header path (`runtime/cpp/std/time.gen.h`) | no | yes | read from the index |
| target-specific compile sources (`*.gen.cpp`, `*.ext.cpp`) | no | yes | read from the index |
| `gen/ext` companion rules | no | yes | read from the index |
| C++ namespace / fully-qualified symbol | no | no | derived by the backend from module + symbol + profile |
| include ordering / dedupe | no | no | backend/tooling |

### 3. Decisions fixed at this stage

- Bare `runtime_call` strings alone are insufficient. From S3 onward, `runtime_module_id` and `runtime_symbol` are the canonical form.
- Target-specific file paths must not be embedded in IR.
- `signature_registry.py` shrinks down to assisting with SoT-derived symbol / type / owner-method contracts only, and it must not own artifact-path or companion inference.
- In the C++ backend, responsibility was previously split across `module.py`, `runtime_paths.py`, and `runtime_calls.json`, but ownership resolution moves out of the backend once the index exists.

## S1-02 schema freeze (2026-03-06 version)

### 1. Schema responsibilities

The `runtime symbol index` owns only the following:

- module-level information about which symbols are provided by which runtime module
- target-level information about which artifacts are needed when that module is used
- whether `gen/ext` companions exist

It does not own:

- whole EAST3 nodes
- C++ namespace strings
- backend-specific rendering syntax
- owner-method resolution logic itself

### 2. Minimum schema

```json
{
  "schema_version": 1,
  "generated_by": "tools/gen_runtime_symbol_index.py",
  "modules": {
    "pytra.built_in.iter_ops": {
      "source_py": "src/pytra/built_in/iter_ops.py",
      "runtime_group": "built_in",
      "symbols": {
        "py_enumerate_object": {
          "kind": "function",
          "dispatch": "function"
        },
        "py_reversed_object": {
          "kind": "function",
          "dispatch": "function"
        }
      }
    }
  },
  "targets": {
    "cpp": {
      "modules": {
        "pytra.built_in.iter_ops": {
          "public_headers": [
            "src/runtime/cpp/built_in/iter_ops.gen.h",
            "src/runtime/cpp/built_in/iter_ops.ext.h"
          ],
          "compile_sources": [
            "src/runtime/cpp/built_in/iter_ops.gen.cpp"
          ],
          "companions": [
            "gen",
            "ext"
          ]
        }
      }
    }
  }
}
```

### 3. Meaning of each field

| field | Level | Meaning |
| - | - | - |
| `schema_version` | root | compatibility discriminator; changes only on breaking schema changes |
| `generated_by` | root | fixed generator name |
| `modules` | root | target-independent module/symbol definitions |
| `source_py` | module | Python SoT module |
| `runtime_group` | module | responsibility class such as `core / built_in / std / utils` |
| `symbols` | module | runtime symbols exported from that module |
| `kind` | symbol | `function` / `class` / `const` etc. |
| `dispatch` | symbol | `function` / `method` / `ctor` etc.; used only to assist rendering |
| `targets` | root | target-specific artifact information |
| `public_headers` | target module | headers that may be included |
| `compile_sources` | target module | sources that must enter the build |
| `companions` | target module | declared presence of `gen` / `ext` |

### 4. Companion rules

- `companions=["gen"]`
  - modules that only have `.gen.*`
- `companions=["gen","ext"]`
  - modules that have `.gen.*` plus `.ext.h` and/or `.ext.cpp`
- `companions=["ext"]`
  - allowed only in the future if low-level SoT-independent `core/` modules are indexed

At this stage, modules derived from `src/pytra/{built_in,std,utils}` are expected to require `gen` by default.

### 5. Implementer prohibitions

- Do not hardcode `py_enumerate -> iter_ops` inside a generator-side dict.
- Do not embed paths such as `runtime/cpp/std/time.gen.h` into IR.
- Do not turn `signature_registry.py` into the new source of truth for the index.
- Do not reinvent `public_headers` and `compile_sources` again on the backend side.

## Execution steps (for implementers)

### Step 1: Inventory the current state

Work to do:
- Search for `runtime_call`, `resolved_runtime_call`, `runtime_owner`, `module_id`, and `export_name`.
- Inventory the dict families inside `signature_registry.py`.
- Find backend-side sites that infer include paths from module names or symbol names.

Minimum files to inspect:
- `src/toolchain/ir/core.py`
- `src/toolchain/frontends/signature_registry.py`
- `src/toolchain/emit/cpp/emitter/module.py`
- `src/toolchain/emit/cpp/emitter/runtime_paths.py`
- `tools/build_multi_cpp.py`
- `tools/gen_makefile_from_manifest.py`

Artifacts to keep from this step:
- Leave inventory notes under `work/logs/...` or equivalent.
- Classify each piece as module-ownership information, target file-path information, or companion-rule information.

Do not:
- rewrite all `runtime_call` handling in `core.py` immediately
- delete the `signature_registry.py` maps without having a replacement ready

### Step 2: Freeze the index schema

Work to do:
- Decide the minimum JSON schema.
- At minimum it must carry:
  - module id
  - exported symbols
  - symbol kind
  - target-specific artifact information
  - `gen/ext` companion information

Decision criteria:
- can the backend stop re-guessing file paths?
- can IR stay free of target-specific paths?

### Step 3: Implement the generator

Work to do:
- Create a new generator such as `tools/gen_runtime_symbol_index.py`.
- Its input is SoT:
  - `src/pytra/built_in/*.py`
  - `src/pytra/std/*.py`
  - `src/pytra/utils/*.py`
  - `src/runtime/<lang>/{core,built_in,std,utils}`
- Its output is JSON.

Implementation policy:
- Use Python module names as the canonical module-id source.
- On the C++ side, scan `*.gen.h`, `*.gen.cpp`, `*.ext.h`, and `*.ext.cpp`, and attach them to the matching module.
- Decide companions from file existence.

Do not:
- hardcode module-to-file mappings as a giant generator-side `if/elif`
- fix `py_enumerate -> iter_ops` in a handwritten dict; derive it from SoT/module scanning

### Step 4: Extend IR

Work to do:
- Add `runtime_module_id` and `runtime_symbol` to payloads such as `BuiltinCall`.
- `runtime_call` may temporarily coexist during migration, but it must shrink down into compatibility-only metadata in the end.
- Populate the same information for resolved imported symbols too.

Important:
- What gets embedded here is only `pytra.built_in.iter_ops` and `py_enumerate`.
- `runtime/cpp/built_in/iter_ops.gen.h` does not go into IR.

### Step 5: Migrate the C++ backend to consume the index

Work to do:
- Collapse include collection into one path: `runtime_module_id -> index -> include path`.
- Move runtime source collection over to the index too.
- Remove module-ownership guesses for `py_enumerate` and similar cases from the backend.

Minimum cases that must pass:
- include dedupe/sort unit coverage
- `from pytra.std.time import perf_counter`
- `from pytra.utils import png`
- `from pytra.std.pathlib import Path`

### Step 6: Guards / docs / regressions

Work to do:
- Add stale-index detection to CI.
- Write the responsibility boundaries into docs.
- Pass representative regressions.

Planned verification commands:
- `python3 tools/check_todo_priority.py`
- `python3 tools/gen_runtime_symbol_index.py --check`
- `python3 -m unittest discover -s test/unit/tooling -p 'test_runtime_symbol_index*.py'`
- `python3 -m unittest discover -s test/unit/toolchain/emit/cpp -p test_*.py`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples`

### Policy for non-C++ backends (fixed by S5-01)

- Non-C++ backends also use `runtime_module_id + runtime_symbol` to decide runtime ownership.
- Target-specific import paths, package paths, and fully-qualified names may still be rendered on the backend side.
- However, no backend may reimplement its own handwritten ownership table that says which module owns which symbol.
- `resolved_runtime_call` may remain as compatibility metadata during migration, but it must not become the source of truth for module/file resolution.
- Target-specific file paths and companion information should be derived in the index-consumption layer. The emitter body must not grow new ownership tables such as `if target == ... and symbol == ...`.

Decision log:
- 2026-03-06: Following user direction, fixed the policy that `runtime symbol -> module/file` mapping must no longer be hardcoded in Python source, and that the design must converge on SoT-generated JSON plus IR normalization.
- 2026-03-06: Fixed the main contract of this plan as “IR holds only target-independent information” and “target-specific file paths are derived by the index + backend”.
- 2026-03-06: [ID: `P0-RUNTIME-SYMBOL-INDEX-01-S1-01`] Inventoried the handwritten sites and fixed the current roles as follows: `core.py` owns bare `runtime_call`, `signature_registry.py` owns runtime-symbol matching, the C++ backend (`module.py`, `runtime_paths.py`, `runtime_calls.json`) owns module/file/namespace guessing, and tooling (`build_multi_cpp.py`, `gen_makefile_from_manifest.py`) owns include-driven runtime-source recollection. The boundary is now `IR=module+symbol`, `index=artifact+companion`, and `backend/tooling=rendering and build-graph derivation`.
- 2026-03-06: [ID: `P0-RUNTIME-SYMBOL-INDEX-01-S1-02`] Fixed the index schema by separating `modules` and `targets`, so target-independent symbol ownership is separate from target-specific artifact information. Fixed `public_headers`, `compile_sources`, and `companions` as the minimum set and documented that paths must not go into IR.
- 2026-03-06: [ID: `P0-RUNTIME-SYMBOL-INDEX-01-S2-01`] Added `tools/gen_runtime_symbol_index.py`, making it possible to scan `src/pytra/{built_in,std,utils}` and the modern runtime layout (`src/runtime/<lang>/{core,built_in,std,utils}`) and generate `tools/runtime_symbol_index.json`. In stage 1, only targets that already use the modern layout are indexed; legacy runtime layouts are out of scope.
- 2026-03-06: [ID: `P0-RUNTIME-SYMBOL-INDEX-01-S2-02`] Fixed representative cases in `test/unit/tooling/test_runtime_symbol_index.py`, validating module/symbol/artifact/companion for `py_enumerate_object`, `py_any`, `py_strip`, `perf_counter`, `write_rgb_png`, and `Path`.
- 2026-03-06: [ID: `P0-RUNTIME-SYMBOL-INDEX-01-S2-03`] Added `--check` to the generator and integrated it into `tools/run_local_ci.py`. Stale indexes now fail fast.
- 2026-03-06: [ID: `P0-RUNTIME-SYMBOL-INDEX-01-S3-01`] Added `runtime_module_id` and `runtime_symbol` alongside `BuiltinCall` in EAST3. In stage 1, `runtime_call` stays for compatibility, while the nodes also carry target-independent forms such as `perf_counter -> pytra.std.time/perf_counter`, `enumerate -> pytra.built_in.iter_ops/enumerate`, `any -> pytra.built_in.predicates/any`, `dict.get -> pytra.core.dict/dict.get`, and `Path.exists -> pytra.std.pathlib/Path.exists`. `test_east_core.py` could not be run directly because of the existing `toolchain.compiler.east_parts` import breakage, so the values were confirmed with ad-hoc execution through the same API.
- 2026-03-06: [ID: `P0-RUNTIME-SYMBOL-INDEX-01-S3-02`] Extended resolved imported symbols to carry `runtime_module_id` / `runtime_symbol` too. Confirmed by ad-hoc execution that both Call and Attribute nodes are populated for `json.loads` from `from pytra.std import json`, `png.write_rgb_png` from `from pytra.utils import png`, and `math.sin` / `math.pi` from `import math`.
- 2026-03-06: [ID: `P0-RUNTIME-SYMBOL-INDEX-01-S3-03`] Fixed in `test_stdlib_signature_registry.py` that artifact-path guessing such as `runtime/cpp`, `*.gen.*`, `*.ext.*`, or `src/runtime` does not creep back into `signature_registry.py`. At this stage, runtime symbol / type / owner-method contracts remain there, but regression coverage guarantees that file-path inference has been completely split out into the generator + index side.
- 2026-03-06: [ID: `P0-RUNTIME-SYMBOL-INDEX-01-S4-01`] Extended the index generator to cover `pytra.core.*` artifacts and added `canonical_runtime_module_id`, `resolve_import_binding_runtime_module`, and `lookup_cpp_namespace_for_runtime_module` to `runtime_symbol_index.py`. Switched C++ import include collection and namespace resolution in `module.py` over to the index and fixed through unit/integration tests that `from pytra.utils import png`, `from pytra.std.time import perf_counter`, and `import math` all resolve C++ includes and namespaces through the index.
- 2026-03-06: [ID: `P0-RUNTIME-SYMBOL-INDEX-01-S4-02`] Added reverse index lookup to `tools/cpp_runtime_deps.py` and moved runtime companion derivation in `build_multi_cpp.py` / `gen_makefile_from_manifest.py` over to `runtime_symbol_index.json`. The existing forwarder-header test (`test_cpp_runtime_build_graph.py`) that resolves `math.ext.cpp` still passed.
- 2026-03-06: [ID: `P0-RUNTIME-SYMBOL-INDEX-01-S4-03`] Switched the C++ emitter's `BuiltinCall` dispatch and imported-symbol call rendering to prioritize `runtime_module_id/runtime_symbol` instead of depending only on `runtime_call` strings. The covered cases were `py_enumerate`, `py_any`, `py_all`, the `py_strip` family, the `dict.get` family, `perf_counter`, and `Path`. `test_cpp_runtime_symbol_index_integration.py` now fixes both the presence of the binding in IR and the final lowering to namespaced C++ calls.
- 2026-03-06: [ID: `P0-RUNTIME-SYMBOL-INDEX-01-S5-01` / `-S5-02`] Fixed in this plan and in `docs/ja/spec/{spec-runtime.md,spec-east.md}` that non-C++ backends also must use `runtime_module_id + runtime_symbol + runtime_symbol_index` as the only ownership-resolution path. Target-specific import/file paths may still be derived by the backend, but ownership tables for module membership must not be reintroduced per backend.
- 2026-03-06: [ID: `P0-RUNTIME-SYMBOL-INDEX-01-S5-03`] Ran representative regressions with `tools/gen_runtime_symbol_index.py --check`, `test_runtime_symbol_index.py`, `test_cpp_runtime_build_graph.py`, `test_cpp_runtime_symbol_index_integration.py`, and `tools/runtime_parity_check.py --targets cpp --case-root fixture`, and confirmed that C++ include resolution, runtime build graph, import resolution, and fixture parity all pass on the index-based path. `math_extended/pathlib_extended/inheritance_virtual_dispatch_multilang` all passed.
