# P0: Align non-C++ runtimes to a C++-comparable `generated/native` layout

Last updated: 2026-03-12

Related TODO:
- `docs/ja/todo/index.md` `ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01`

Background:
- The current non-C++ runtimes still depend on `pytra-core/pytra-gen/pytra` naming, while C++ already has a clearer ownership split under `generated/native/core/pytra`.
- That makes tree-level comparison harder: for modules such as `json/pathlib/gif/png/...`, it is not obvious whether a backend is missing a generated artifact or still hiding handwritten logic in the core lane.
- Per the user directive, anything placed under `generated/` must be emitted from the SoT (`src/pytra/**`). Moving handwritten files into `generated/` is invalid.

Goal:
- Make non-C++ backends use `generated/` and `native/` as formal runtime lanes so their trees can be compared against C++ at the file/module level.
- Keep `generated/` strictly SoT-generated and `native/` strictly handwritten.
- Start with `rs/cs`, because they are the current work targets and the immediate blocker for layout convergence.

Scope:
- `src/runtime/{rs,cs}/**`
- `tools/gen_runtime_from_manifest.py`
- `tools/runtime_generation_manifest.json`
- `src/toolchain/compiler/backend_registry_metadata.py`
- `src/toolchain/compiler/pytra_cli_profiles.py`
- runtime guards / allowlists / docs

Out of scope:
- redesigning the C++ runtime itself
- renaming every backend in one turn
- immediately deleting the `pytra/` public shim lane

Acceptance criteria:
- `src/runtime/{rs,cs}/generated/**` exists and contains only generated artifacts with `source:` and `generated-by:` markers.
- `src/runtime/{rs,cs}/native/**` exists and does not contain `generated-by:` markers.
- `tools/runtime_generation_manifest.json` emits `rs/cs` SoT artifacts into `generated/`.
- `backend_registry_metadata.py`, `pytra_cli_profiles.py`, and selfhost checks reference the new `rs/cs` layout.
- Runtime guards no longer treat `pytra-gen/pytra-core` as the canonical vocabulary; `generated/native` becomes the primary audited layout.
- When runtime trees are compared by `<lane>/<bucket>/<module>`, missing vs. lingering runtime modules in `rs/cs` are obvious from the filesystem alone.

Planned verification:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_runtime_core_gen_markers.py`
- `python3 tools/check_runtime_pytra_gen_naming.py`
- `python3 tools/check_runtime_std_sot_guard.py`
- `python3 tools/check_cs_single_source_selfhost_compile.py`
- `PYTHONPATH=src:.:test/unit python3 -m unittest discover -s test/unit/backends/cs -p 'test_py2cs_smoke.py'`

Execution policy:
1. Do not move handwritten files into `generated/`; regenerate them from the SoT through the manifest/generator lane.
2. Introduce `native/` as the renamed handwritten lane for current `pytra-core`.
3. Keep `pytra/` as a compatibility/public shim lane for now if needed, but do not treat it as the ownership source of truth.
4. Compare runtime coverage by `<lane>/<bucket>/<module>` and ignore extension multiplicity (`.h/.cpp` vs `.rs/.cs`) as a secondary detail.

## Target Layout

Canonical `rs/cs` layout:

- `src/runtime/<lang>/generated/{built_in,std,utils}/`
  - generated from `src/pytra/**` only
- `src/runtime/<lang>/native/{built_in,std,utils}/`
  - handwritten runtime only
- `src/runtime/<lang>/pytra/{built_in,std,utils}/`
  - public shim / compatibility lane when needed

Notes:
- C++-specific `core/` and `.h/.cpp` pairing are not copied literally into every backend.
- The important part is to make ownership visible by lane/module, such as `generated/std/json`, `generated/utils/gif`, and `native/built_in/py_runtime`.

## Compare Unit

The canonical compare unit is `<lane>/<bucket>/<module>`, and extension differences or backend-specific header/source splits are excluded from comparison.

- lane:
  - `generated`
  - `native`
  - `pytra` (compat/public shim, not used for ownership decisions)
- bucket:
  - `built_in`
  - `std`
  - `utils`
  - `compiler`
- module examples:
  - `generated/utils/gif`
  - `generated/utils/png`
  - `native/built_in/py_runtime`
  - `native/std/json`

This compare unit is the basis for making `missing generated artifact` and `hand-written residual still in native` obvious from tree diffs alone.

## Current -> Target Mapping (first wave: rs/cs)

### Rust

| current path | target lane/module | ownership |
| --- | --- | --- |
| `src/runtime/rs/pytra-core/built_in/py_runtime.rs` | `native/built_in/py_runtime` | hand-written |
| `src/runtime/rs/pytra-gen/utils/gif.rs` | `generated/utils/gif` | SoT generated |
| `src/runtime/rs/pytra-gen/utils/png.rs` | `generated/utils/png` | SoT generated |
| `src/runtime/rs/pytra-gen/utils/image_runtime.rs` | `generated/utils/image_runtime` | SoT generated |
| `src/runtime/rs/pytra/**` | `pytra/**` | compat/public shim |

### C#

| current path | target lane/module | ownership |
| --- | --- | --- |
| `src/runtime/cs/pytra-core/built_in/math.cs` | `native/built_in/math` | hand-written |
| `src/runtime/cs/pytra-core/built_in/py_runtime.cs` | `native/built_in/py_runtime` | hand-written |
| `src/runtime/cs/pytra-core/built_in/time.cs` | `native/built_in/time` | hand-written |
| `src/runtime/cs/pytra-core/std/json.cs` | `native/std/json` | hand-written |
| `src/runtime/cs/pytra-core/std/pathlib.cs` | `native/std/pathlib` | hand-written |
| `src/runtime/cs/pytra-gen/utils/gif.cs` | `generated/utils/gif` | SoT generated |
| `src/runtime/cs/pytra-gen/utils/png.cs` | `generated/utils/png` | SoT generated |
| `src/runtime/cs/pytra/**` | `pytra/**` | compat/public shim |

## Breakdown

- [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S1-01] Fix the canonical non-C++ `generated/native/pytra` layout and compare unit in spec/plan docs.
- [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S1-02] Build the `rs/cs` mapping table from the current `pytra-core/pytra-gen` tree to the new `generated/native` tree.
- [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S2-01] Cut Rust over from `pytra-core/pytra-gen` to `native/generated`, then sync runtime hooks and guards.
- [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S2-02] Cut C# over from `pytra-core/pytra-gen` to `native/generated`, then sync build/selfhost/runtime paths.
- [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S2-03] Regenerate `rs/cs` `png/gif` into the new `generated/utils` lane and remove old-path dependencies.
- [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S3-01] Decide module-by-module which `cs` std lanes (`json/pathlib/math/re/argparse/enum`) belong in `generated/std` and which stay in `native`.
- [ ] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S3-02] Migrate the `rs/cs` std lanes into `generated/std` and shrink handwritten logic in `native`.
- [ ] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S4-01] Update runtime guards / allowlists / docs to the `generated/native` vocabulary.
- [ ] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S4-02] Define the rollout waves for `go/java/kt/scala/swift/nim/js/ts/lua/rb/php`.

Decision log:
- 2026-03-12: Per user direction, promoted the non-C++ runtime layout reset to P0 and fixed the rule that `generated/` may contain only SoT-emitted artifacts.
- 2026-03-12: Chose `<lane>/<bucket>/<module>` as the canonical compare unit instead of forcing literal C++ header/source duplication into every backend.
- 2026-03-12: Closed `S1-01/S1-02` by fixing the canonical `<lane>/<bucket>/<module>` compare unit and mapping the current `pytra-core/pytra-gen` trees for `rs/cs` onto the target `generated/native/pytra` layout. In the first wave, `pytra/**` remains the compat/public shim lane and is excluded from ownership decisions.
- 2026-03-12: Closed `P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S2-01` / `P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S2-02` / `P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S2-03` by cutting the real `src/runtime/{rs,cs}/{native,generated}` trees over, syncing the Rust runtime hook, the C# build/selfhost/runtime paths, and the runtime guards / allowlists / inventories, then rerunning `tools/gen_runtime_from_manifest.py --targets rs,cs --items utils/png,utils/gif`.
- 2026-03-12: As the first probe for `P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S3-01`, checked whether `json.py` / `pathlib.py` can already flow into `cs/rs` generated std lanes. `json.py` still stops on the `@abi` target restriction, while `pathlib.py` still lacks wired `os/os_path/glob` runtime import lanes, so the std-lane migration remains a follow-up wave.
- 2026-03-12: As a compare-lane expansion under `P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01`, added `rs/cs` `std/{time,math,os,os_path,glob,pathlib}` entries to `tools/runtime_generation_manifest.json` and generated `src/runtime/{rs,cs}/generated/std/*` from SoT. For now these files exist to make tree-level comparison concrete; build/runtime hooks still stay on the `native` lane.
- 2026-03-12: Closed `P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S3-01` by fixing the C# std lane ownership contract in `noncpp_runtime_layout_contract.py` / `check_noncpp_runtime_layout_contract.py`. The current decision is `json=native/std + generated blocked`, `pathlib=native/std canonical + generated compare artifact`, `math=native/built_in canonical + generated compare artifact`, and `re/argparse/enum=no runtime module`, guarded across the build profile, emitter alias lane, and C# smoke tests.
