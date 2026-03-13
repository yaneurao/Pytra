# P0: Align non-C++ generated runtime lanes to the `cpp/generated` baseline

Last updated: 2026-03-13

Related TODO:
- `docs/en/todo/index.md` item `ID: P0-NONCPP-RUNTIME-GENERATED-CPP-BASELINE-01`

Background:
- `src/runtime/cpp/generated/{built_in,std,utils}/` already materializes the canonical module baseline from the SoT modules under `src/pytra/{built_in,std,utils}/*.py`.
- The current non-C++ runtime layout rollout has not yet brought every backend's `generated/` lane up to that full baseline.
- Current contracts / manifests / build profiles still explicitly allow exceptions such as `generated blocked + native handwritten canonical`. A concrete example is C# `json`: `src/runtime/cs/native/std/json.cs` remains the canonical hand-written lane, while `src/runtime/cs/generated/std/json.cs` does not exist.
- The same drift exists for `utils/assertions`: many backends still lack `src/runtime/<lang>/generated/utils/assertions.*`, and helper-shaped names such as `gif_helper`, `png_helper`, and `image_runtime` still block module-basename compare.
- That does not satisfy the user instruction of “first generate the same modules that exist under `cpp/generated/` for every language and use those.”
- This task therefore re-opens the rollout at `P0` priority and raises the target from limited `generated/native` vocabulary alignment to full `cpp/generated` baseline parity.

Goal:
- Make the `generated/{built_in,std,utils}` module sets of every non-C++ runtime backend (`rs`, `cs`, `go`, `java`, `kotlin`, `scala`, `swift`, `nim`, `js`, `ts`, `lua`, `ruby`, `php`) match the canonical `cpp/generated/{built_in,std,utils}` baseline.
- Materialize every SoT-generatable module into each backend's `generated/` lane first, then treat the generated lane as the canonical owner in contracts and tooling.
- Raise file compare from “selected compare artifacts” to full-module-set compare derived from `cpp/generated`.

Scope:
- `src/runtime/{rs,cs,go,java,kotlin,scala,swift,nim,js,ts,lua,ruby,php}/generated/{built_in,std,utils}/**`
- ownership cleanup under `src/runtime/<lang>/native/{built_in,std,utils}/**`
- `tools/runtime_generation_manifest.json`
- `tools/gen_runtime_from_manifest.py`
- non-C++ runtime contracts / checkers / allowlists / inventory
- backend build profile / packaging / selfhost / smoke / runtime copy wiring
- docs / TODO / spec wording

Out of scope:
- Expanding `src/runtime/cpp/generated/compiler/**` or `src/runtime/cpp/generated/core/**` to non-C++ backends
- Redesigning the C++ runtime itself
- Deleting checked-in `pytra/**` trees for C# / non-C++ backends
  - that remains the responsibility of `P0-NONCPP-RUNTIME-PYTRA-DESHIM-01`, with this task as a prerequisite
- Changing SoT module semantics under `src/pytra/**`
- Adding backend-specific generated modules beyond the `cpp/generated` baseline

## Canonical generated baseline

The canonical baseline derived from `cpp/generated/{built_in,std,utils}` is the following 25-module set.

### built_in

- `contains`
- `io_ops`
- `iter_ops`
- `numeric_ops`
- `predicates`
- `scalar_ops`
- `sequence`
- `string_ops`
- `type_id`
- `zip_ops`

### std

- `argparse`
- `glob`
- `json`
- `math`
- `os`
- `os_path`
- `pathlib`
- `random`
- `re`
- `sys`
- `time`
- `timeit`

### utils

- `assertions`
- `gif`
- `png`

Notes:
- C++ `.h/.cpp` splits are collapsed to module basenames for compare.
- Helper-shaped non-C++ names such as `gif_helper`, `png_helper`, and `image_runtime` are not part of the canonical baseline and must be renamed to `<module>.<ext>`.
- `compiler/` and `core/` remain C++-specific lanes and stay outside this compare baseline.

Acceptance criteria:
- For every target backend, the `generated/{built_in,std,utils}` module-basename set matches the canonical generated baseline.
- Baseline modules may not rely on `blocked`, `no_runtime_module`, `helper_artifact`, `compare_artifact only`, or `native canonical` as a close condition.
- When a baseline module exists, backend build/runtime/selfhost/package/export must treat `generated/<bucket>/<module>.<ext>` as the canonical module.
- `native/**` may keep only substrate / low-level seams; hand-written files that still own baseline modules must be eliminated.
- The contract/checker performs full-module-set compare against the `cpp/generated` baseline and fails fast on missing modules, helper aliases, native-owned baseline modules, and naming drift outside the baseline.
- The `utils` baseline including `assertions` is materialized in every backend's generated lane.
- Docs / checker wording fix the end state as `generated = baseline`, not `generated ∪ blocked = baseline`.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_noncpp_runtime_generated_cpp_baseline_contract.py`
- `python3 tools/check_noncpp_runtime_layout_contract.py`
- `python3 tools/check_noncpp_runtime_layout_rollout_remaining_contract.py`
- `python3 tools/check_runtime_core_gen_markers.py`
- `python3 tools/check_runtime_pytra_gen_naming.py`
- `python3 tools/check_runtime_std_sot_guard.py`
- `python3 tools/check_multilang_selfhost_stage1.py`
- `python3 tools/check_multilang_selfhost_multistage.py`
- `find src/runtime -path '*/generated/*' -type f | sort`
- `git diff --check`

Implementation policy:
1. The compare source of truth is the actual module set under `cpp/generated/{built_in,std,utils}`. Do not reverse-engineer the baseline from non-C++ blocked inventories.
2. If a backend is missing `generated` files for a baseline module, first fix generators / manifests / postprocess / emitters / substrate until the generated lane exists. Do not close by keeping a hand-written `native` owner.
3. Once a baseline module is generated, switch build/runtime/selfhost/package to generated-first wiring and shrink any same-name `native` owner down to substrate helpers or delete it.
4. Helper-shaped generated artifacts (`gif_helper`, `png_helper`, `image_runtime`) are transitional only and must be renamed to canonical baseline module names.
5. `P0-NONCPP-RUNTIME-PYTRA-DESHIM-01` remains a follow-up and must not delete checked-in `pytra/**` before this baseline task is complete.

## Backend families

### rs/cs

- This family still carries the strongest legacy `blocked/native canonical` exceptions.
- Missing generated std/utils modules such as `json`, `assertions`, `re`, `random`, `sys`, `timeit`, and `argparse` must be brought to baseline.

### Static family

- `go`
- `java`
- `kotlin`
- `scala`
- `swift`
- `nim`

Target:
- raise partial generated `built_in/std/utils` support to the full baseline
- rename helper-shaped utils outputs to canonical module basenames

### Script family

- `js`
- `ts`
- `lua`
- `ruby`
- `php`

Target:
- materialize the full generated baseline
- switch package/export/runtime wiring to generated-first

## Breakdown

- [ ] [ID: P0-NONCPP-RUNTIME-GENERATED-CPP-BASELINE-01] Align non-C++ generated runtime lanes to the canonical `cpp/generated/{built_in,std,utils}` module baseline and make `generated/` the canonical owner for baseline modules.
- [x] [ID: P0-NONCPP-RUNTIME-GENERATED-CPP-BASELINE-01-S1-01] Extract the canonical baseline module set from `cpp/generated/{built_in,std,utils}` and lock it as the source of truth in plan / contract / checker form.
- [x] [ID: P0-NONCPP-RUNTIME-GENERATED-CPP-BASELINE-01-S1-02] Replace the old `blocked / compare_artifact / no_runtime_module / helper_artifact / native canonical` exceptions with a contract that forbids those states for baseline modules and remove the old rollout wording from active policy.
- [x] [ID: P0-NONCPP-RUNTIME-GENERATED-CPP-BASELINE-01-S2-01] Materialize the missing generated std/utils baseline for `rs/cs` (including `json`, `assertions`, `argparse`, `random`, `re`, `sys`, `timeit`) and bring the representative smoke / manifest / layout-checker bundle to green.
- [ ] [ID: P0-NONCPP-RUNTIME-GENERATED-CPP-BASELINE-01-S2-02] Raise the static family (`go/java/kotlin/scala/swift/nim`) generated `built_in/std/utils` lanes to the full baseline and rename helper-shaped outputs to canonical basenames.
- [ ] [ID: P0-NONCPP-RUNTIME-GENERATED-CPP-BASELINE-01-S2-03] Raise the script family (`js/ts/lua/ruby/php`) generated `built_in/std/utils` lanes to the full baseline and switch package/export wiring to generated-first.
- [ ] [ID: P0-NONCPP-RUNTIME-GENERATED-CPP-BASELINE-01-S3-01] Switch backend build profile / selfhost / smoke / runtime copy contracts to generated-first and shrink baseline `native` owners down to substrate seams.
- [ ] [ID: P0-NONCPP-RUNTIME-GENERATED-CPP-BASELINE-01-S3-02] Add a full file-compare contract checker that fails fast if any backend diverges from the baseline module set or still owns baseline modules through helper aliases / native files.
- [ ] [ID: P0-NONCPP-RUNTIME-GENERATED-CPP-BASELINE-01-S4-01] Sync docs / TODO / inventory / archive notes and leave `P0-NONCPP-RUNTIME-PYTRA-DESHIM-01` as a follow-up with prerequisites resolved.

Decision log:
- 2026-03-13: Following the user instruction, we concluded that “limited compare rollout with `generated/native` vocabulary” is insufficient and re-opened the work as a new `P0` for full `cpp/generated` baseline parity.
- 2026-03-13: The canonical generated baseline is fixed to the actual 25-module basename set under `cpp/generated/{built_in,std,utils}`, excluding C++-specific `compiler/core`.
- 2026-03-13: `S1-01` added a dedicated contract/checker/test that exact-matches the live `cpp/generated/{built_in,std,utils}` tree against the locked 25-module baseline.
- 2026-03-13: `S1-02` locked the baseline-module legacy states (`blocked / compare_artifact / no_runtime_module / native canonical`) as compact migration-debt inventory and added a checker that guarantees helper-artifact aliases never overlap the canonical baseline.
- 2026-03-13: The `S2-01` first bundle added `rs/cs` targets for `std/{argparse,json,random,re,sys,timeit}` and `utils/assertions` to `tools/runtime_generation_manifest.json`, then materialized the generated artifacts. In parallel it updated `noncpp_runtime_layout_contract.py`, smoke coverage, and unit tests so `json` moved forward from `blocked` and `argparse/re` moved forward from `no_runtime_module` into compare-artifact debt.
- 2026-03-13: The `S2-01` close bundle made the representative `rs/cs` `json/argparse/random/re/sys/timeit` smoke, manifest unit tests, and layout checker all green, and refreshed the remaining C# compare-artifact generated files to the current SoT. The remaining `native canonical` / `no_runtime_module` debt is deferred to `S3-01`, where the live build/runtime wiring will move to generated-first.
- 2026-03-13: The `S2-01` second bundle added a baseline checker guard for the `rs/cs` generated lanes, locking in that `generated/{built_in,std,utils}` has no missing modules relative to the 25-module baseline. Exact-match enforcement for extra artifacts (for example `rs/generated/utils/image_runtime.rs`) stays deferred to `S3-02`.
- 2026-03-13: The `S2-02` first bundle materialized Java's 13 missing modules (`built_in/{predicates,sequence,string_ops,type_id}`, `std/{argparse,glob,os,os_path,random,re,sys,timeit}`, and `utils/assertions`) into `generated/` from the SoT, then synced `tools/runtime_generation_manifest.json`, the runtime hook descriptor, the legacy rollout contract, Java runtime smoke, and the generated-cpp baseline checker. The next static-family bundle will start with `go` and remove the remaining full-baseline debt.
- 2026-03-13: The current `S2-02` bundle synced the Kotlin / Scala / Swift / Nim `generated/utils/{gif,png}` rename through the contract, test, and smoke expectations, updating `current_inventory`, `target_inventory`, `module_buckets`, `wave_a_generated_compare`, and `wave_a_generated_smoke` to canonical basenames. `utils/image_runtime` remains the only helper artifact in this group, and the next bundle moves on to the remaining static-family full-baseline gaps starting with `go`.
- 2026-03-13: The `S2-02` third bundle materialized Go's 17 missing modules (`built_in/{predicates,sequence,string_ops,type_id}`, `std/{argparse,glob,json,math,os,os_path,pathlib,random,re,sys,time,timeit}`, and `utils/assertions`) into `generated/` from the SoT and promoted Go to a materialized backend in the baseline-debt contract. The runtime hook copy set intentionally stays on the existing substrate / image-helper subset for now, while the legacy rollout contract, representative smoke, and tooling unit tests are synchronized to the full generated inventory. The remaining static-family full-baseline debt is now concentrated in Kotlin / Scala / Swift / Nim.
- 2026-03-13: The `S2-02` fourth bundle materialized Swift's 17 missing modules (`built_in/{numeric_ops,scalar_ops,string_ops,type_id}`, `std/{argparse,glob,json,math,os,os_path,pathlib,random,re,sys,time,timeit}`, and `utils/assertions`) into `generated/` from the SoT and promoted Swift to a materialized backend in the baseline-debt contract. It also added the `generated/std` lane mapping, synchronized current/target inventory plus module buckets and Wave-A generated compare/smoke expectations to the full generated inventory, and expanded the Swift runtime path smoke accordingly. The runtime hook copy set intentionally remains on the substrate subset (`py_runtime.swift` plus `utils/image_runtime.swift`) for now, and the remaining static-family full-baseline debt is now concentrated in Kotlin / Scala / Nim.
- 2026-03-13: The `S2-02` fifth bundle materialized Nim's 18 missing modules (`built_in/{io_ops,scalar_ops,sequence,string_ops,type_id}`, `std/{argparse,glob,json,math,os,os_path,pathlib,random,re,sys,time,timeit}`, and `utils/assertions`) into `generated/` from the SoT and promoted Nim to a materialized backend in the baseline-debt contract. It also added the `generated/std` lane mapping, synchronized current/target inventory plus module buckets and Wave-A generated compare/smoke expectations to the full generated inventory, and expanded the Nim runtime path smoke accordingly. The runtime hook copy set intentionally remains on the substrate subset (`py_runtime.nim` plus `utils/image_runtime.nim`) for now. In parallel, `tools/gen_runtime_from_manifest.py` switched its current-file read path to `newline=\"\"` so the raw carriage-return literal embedded in Nim `string_ops.nim` no longer produces false stale detections under `--check`. The remaining static-family full-baseline debt is now concentrated in Kotlin / Scala.
- 2026-03-13: The `S2-02` sixth bundle materialized Kotlin's 18 missing modules (`built_in/{io_ops,numeric_ops,scalar_ops,string_ops,type_id}`, `std/{argparse,glob,json,math,os,os_path,pathlib,random,re,sys,time,timeit}`, and `utils/assertions`) into `generated/` from the SoT and promoted Kotlin to a materialized backend in the baseline-debt contract. It also added the `generated/std` lane mapping, synchronized current/target inventory plus module buckets and Wave-A generated compare/smoke expectations to the full generated inventory, and expanded the Kotlin runtime path smoke accordingly. The runtime hook copy set intentionally remains on the substrate subset (`py_runtime.kt` plus `utils/image_runtime.kt`) for now, and the remaining static-family full-baseline debt is now limited to Scala.
