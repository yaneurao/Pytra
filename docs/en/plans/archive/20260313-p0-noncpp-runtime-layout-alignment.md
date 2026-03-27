<a href="../../../ja/plans/archive/20260313-p0-noncpp-runtime-layout-alignment.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Align the `rs/cs` runtimes to a C++-comparable `generated/native` layout

Last updated: 2026-03-13

Related TODO:
- `docs/ja/todo/index.md` `ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01`

Background:
- The current `rs/cs` runtimes still depend on `pytra-core/pytra-gen/pytra` naming, while C++ already has a clearer ownership split under `generated/native/core/pytra`.
- That makes tree-level comparison harder: for modules such as `json/pathlib/gif/png/...`, it is not obvious whether a backend is missing a generated artifact or still hiding handwritten logic in the core lane.
- Per the user directive, anything placed under `generated/` must be emitted from the SoT (`src/pytra/**`). Moving handwritten files into `generated/` is invalid.
- Per the later user directive, `rs/cs` stay in P0 and the remaining non-C++ backends move to a separate P1 rollout.

Goal:
- Make `rs/cs` use `generated/` and `native/` as formal runtime lanes so their trees can be compared against C++ at the file/module level.
- Keep `generated/` strictly SoT-generated and `native/` strictly handwritten.
- Materialize `generated/built_in/*` for `rs/cs` from `src/pytra/built_in/*.py`, not only `std/utils`.

Scope:
- `src/runtime/{rs,cs}/**`
- `tools/gen_runtime_from_manifest.py`
- `tools/runtime_generation_manifest.json`
- `src/toolchain/compiler/backend_registry_metadata.py`
- `src/toolchain/compiler/pytra_cli_profiles.py`
- runtime guards / allowlists / docs

Out of scope:
- redesigning the C++ runtime itself
- rolling the remaining non-`rs/cs` backends
- immediately deleting the Rust `pytra/` compatibility lane

Acceptance criteria:
- `src/runtime/{rs,cs}/generated/**` exists and contains only generated artifacts with `source:` and `generated-by:` markers.
- `src/runtime/{rs,cs}/native/**` exists and does not contain `generated-by:` markers.
- `tools/runtime_generation_manifest.json` emits `rs/cs` SoT artifacts into `generated/`.
- `src/runtime/{rs,cs}/generated/built_in/*` exists for the `src/pytra/built_in/*.py` modules and can be compared to `cpp/generated/built_in/*` by `<lane>/<bucket>/<module>`.
- `backend_registry_metadata.py`, `pytra_cli_profiles.py`, and selfhost checks reference the new `rs/cs` layout.
- Runtime guards no longer treat `pytra-gen/pytra-core` as the canonical vocabulary; `generated/native` becomes the primary audited layout.
- When runtime trees are compared by `<lane>/<bucket>/<module>`, missing vs. lingering runtime modules in `rs/cs` are obvious from the filesystem alone.
- `src/runtime/cs/pytra/**` does not own canonical implementations; if it remains during tooling migration, it is transitional compatibility debris only and must eventually become empty or be removed.

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
3. Rust may keep `pytra/` as a temporary compatibility lane, but it must not be treated as the ownership source of truth. C# `pytra/` is not a valid shim lane and should not host implementation bodies; it is a deletion target.
4. Compare runtime coverage by `<lane>/<bucket>/<module>` and ignore extension multiplicity (`.h/.cpp` vs `.rs/.cs`) as a secondary detail.
5. Treat `generated/built_in/*` as the lane for `src/pytra/built_in/*.py`, while keeping substrate files such as `py_runtime.*` in `native/built_in/*`.

## Target Layout

Canonical `rs/cs` layout:

- `src/runtime/<lang>/generated/{built_in,std,utils}/`
  - generated from `src/pytra/**` only
- `src/runtime/<lang>/native/{built_in,std,utils}/`
  - handwritten runtime only
- `src/runtime/<lang>/pytra/{built_in,std,utils}/`
  - Rust-only compatibility lane when needed
  - not a canonical C# implementation lane; duplicate leftovers there should be removed

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
| `src/runtime/cs/pytra/**` | remove / empty lane | duplicate residual (delete target) |

## Breakdown

- [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S1-01] Fix the canonical non-C++ `generated/native/pytra` layout and compare unit in spec/plan docs.
- [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S1-02] Build the `rs/cs` mapping table from the current `pytra-core/pytra-gen` tree to the new `generated/native` tree.
- [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S2-01] Cut Rust over from `pytra-core/pytra-gen` to `native/generated`, then sync runtime hooks and guards.
- [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S2-02] Cut C# over from `pytra-core/pytra-gen` to `native/generated`, then sync build/selfhost/runtime paths.
- [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S2-03] Regenerate `rs/cs` `png/gif` into the new `generated/utils` lane and remove old-path dependencies.
- [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S3-01] Decide module-by-module which `cs` std lanes (`json/pathlib/math/re/argparse/enum`) belong in `generated/std` and which stay in `native`.
- [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S3-02] Migrate the `rs/cs` std lanes into `generated/std` and shrink handwritten logic in `native`.
  - [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S3-02-A] Lock the current `rs` std ownership baseline and guard `math/time` as native, `pathlib/os/os_path/glob` as compare artifacts, and `json/re/argparse/enum` as no-live-module lanes.
  - [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S3-02-B] Fix `time` as the first live-generated C# std candidate, and separate `json/pathlib/math` as deferred native-canonical lanes plus `re/argparse/enum` as deferred no-runtime lanes.
  - [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S3-02-C] Wire the chosen `rs/cs` std lane into the live build/runtime hook and shrink the compare-artifact-only state.
- [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S4-01] Generate `rs/cs` `generated/built_in/*` from `src/pytra/built_in/*.py` so the built-in compare lane is real.
- [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S4-02] Fix the `generated/built_in/*` vs `native/built_in/*` responsibility boundary and shrink built-in residuals in `py_runtime.*`. In the same slice, delete the duplicate C# `pytra/**` lane (`math/time/json/pathlib/png/gif` and related files) rather than trying to preserve it as a shim.
- [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S5-01] Update runtime guards / allowlists / docs to the `generated/native` vocabulary.

Decision log:
- 2026-03-12: Per user direction, promoted the non-C++ runtime layout reset to P0 and fixed the rule that `generated/` may contain only SoT-emitted artifacts.
- 2026-03-12: Chose `<lane>/<bucket>/<module>` as the canonical compare unit instead of forcing literal C++ header/source duplication into every backend.
- 2026-03-12: Closed `S1-01/S1-02` by fixing the canonical `<lane>/<bucket>/<module>` compare unit and mapping the current `pytra-core/pytra-gen` trees for `rs/cs` onto the target `generated/native/pytra` layout. In the first wave, `pytra/**` remains the compat/public shim lane and is excluded from ownership decisions.
- 2026-03-12: Closed `P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S2-01` / `P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S2-02` / `P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S2-03` by cutting the real `src/runtime/{rs,cs}/{native,generated}` trees over, syncing the Rust runtime hook, the C# build/selfhost/runtime paths, and the runtime guards / allowlists / inventories, then rerunning `tools/gen_runtime_from_manifest.py --targets rs,cs --items utils/png,utils/gif`.
- 2026-03-12: As the first probe for `P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S3-01`, checked whether `json.py` / `pathlib.py` can already flow into `cs/rs` generated std lanes. `json.py` still stops on the `@abi` target restriction, while `pathlib.py` still lacks wired `os/os_path/glob` runtime import lanes, so the std-lane migration remains a follow-up wave.
- 2026-03-12: As a compare-lane expansion under `P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01`, added `rs/cs` `std/{time,math,os,os_path,glob,pathlib}` entries to `tools/runtime_generation_manifest.json` and generated `src/runtime/{rs,cs}/generated/std/*` from SoT. For now these files exist to make tree-level comparison concrete; build/runtime hooks still stay on the `native` lane.
- 2026-03-12: Closed `P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S3-01` by fixing the C# std lane ownership contract in `noncpp_runtime_layout_contract.py` / `check_noncpp_runtime_layout_contract.py`. The current decision is `json=native/std + generated blocked`, `pathlib=native/std canonical + generated compare artifact`, `math=native/built_in canonical + generated compare artifact`, and `re/argparse/enum=no runtime module`, guarded across the build profile, emitter alias lane, and C# smoke tests.
- 2026-03-12: Re-scoped this P0 to `rs/cs` only and moved the remaining backend rollout into a separate P1 task. `generated/built_in/*` is part of the mandatory P0 end state, not an optional later extra.
- 2026-03-12: Closed `P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S3-02-A` by adding the Rust std ownership baseline to `noncpp_runtime_layout_contract.py` / `check_noncpp_runtime_layout_contract.py`. The current decision is `time/math=native/built_in canonical + generated compare artifact`, `pathlib/os/os_path/glob=no live runtime module + generated compare artifact`, `json=generated blocked + no live runtime module`, and `re/argparse/enum=no runtime module`, guarded across the manifest, native scaffold, and Rust smoke tests.
- 2026-03-12: Closed `P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S4-01` by adding `rs/cs` targets for `built_in/{contains,io_ops,iter_ops,numeric_ops,predicates,scalar_ops,sequence,string_ops,type_id,zip_ops}` to `tools/runtime_generation_manifest.json` and regenerating `src/runtime/{rs,cs}/generated/built_in/*` from SoT through `tools/gen_runtime_from_manifest.py --targets rs,cs --items ...`. The C# compare lane goes through `cs_program_to_helper` so multiple generated built-ins do not collide on `Program`.
- 2026-03-12: Closed `P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S3-02-B` by fixing the first live-generated C# std candidate as `time`. `generated/std/time.cs` remains a compare artifact for now, but its representative surface is only the `perf_counter()` lane, so it is the narrowest next live-generated target. `json/pathlib/math` stay deferred native-canonical lanes, while `re/argparse/enum` remain deferred no-runtime lanes.
- 2026-03-12: Closed `P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S3-02-C` by regenerating C# `generated/std/time.cs` through `cs_std_time_live_wrapper` into `namespace Pytra.CsModule { public static class time { ... } }`, with the wrapper calling the native `time_native` backing seam. The C# build plan now compiles `generated/std/time.cs` as the canonical module while keeping `native/built_in/time.cs` only as the backing seam, and the contract checker validates the wrapper content directly.
- 2026-03-12: Per user direction, clarified that C# `pytra/` is not a shim/public lane. Because there is no `#include`-style indirection in C#, `src/runtime/cs/pytra/**` has no reason to host implementation bodies; any remaining duplicate files there are part of `S4-02` and should be deleted.
- 2026-03-12: Fixed the current `S4-02` boundary inventory: `generated/built_in/*` must stay the exact SoT set `contains/io_ops/iter_ops/numeric_ops/predicates/scalar_ops/sequence/string_ops/type_id/zip_ops`, `native/built_in/*` residuals are `rs={py_runtime}` and `cs={math,py_runtime,time}`, the C# `pytra/**` delete-target allowlist is the 7 files `built_in/{math,py_runtime,time}`, `std/{json,pathlib}`, and `utils/{gif,png}`, and Rust `pytra/**` is reduced to the compatibility allowlist `README* + built_in/py_runtime.rs`.
- 2026-03-12: Closed `S4-02` by physically deleting the 7 duplicate C# `pytra/**` files (`built_in/{math,py_runtime,time}`, `std/{json,pathlib}`, `utils/{gif,png}`). The checker moved from an allowlist of duplicate targets to the stronger rule that the duplicate lane must be empty and every delete target must be absent, and the crossruntime residual/thincompat inventories plus docs were retargeted to the canonical native/generated lane only.
- 2026-03-13: As the first `S5-01` docs/guard bundle, updated the policy wording in `check_runtime_pytra_gen_naming.py` and `check_runtime_core_gen_markers.py` to treat `rs/cs = generated/native canonical` while scanning `pytra-gen/pytra-core` only as legacy lanes. User-facing Rust runtime docs were aligned to `src/runtime/rs/{native,generated}/` as the canonical path and `src/runtime/rs/pytra/` as the compatibility lane.
- 2026-03-13: As the second `S5-01` guard bundle, updated `check_rs_runtime_layout.py` to require `src/runtime/rs/native/**` as the canonical handwritten lane while treating `src/runtime/rs/pytra/**` as optional compatibility only, and locked that contract with `test_check_rs_runtime_layout.py`.
- 2026-03-13: As the third `S5-01` docs/guard bundle, synchronized `check_runtime_std_sot_guard.py` and `spec-tools.md` to the `rs/cs = generated/native canonical, pytra-gen/pytra-core = legacy / not-yet-migrated backend context` vocabulary, so the `std/utils` guard also describes the `generated/native/pytra` ownership split consistently.
- 2026-03-13: As the fourth `S5-01` guard bundle, updated `runtime_std_sot_allowlist.txt` and the `check_runtime_std_sot_guard.py` status messages to speak in terms of the canonical generated lane, and clarified that every allowlist entry is legacy migration debt only.
