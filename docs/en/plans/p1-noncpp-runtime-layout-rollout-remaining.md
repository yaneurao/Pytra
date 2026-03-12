# P1: Roll the remaining non-C++ backend runtimes onto a C++-comparable `generated/native` layout

Last updated: 2026-03-13

Related TODO:
- `docs/ja/todo/index.md` `ID: P1-NONCPP-RUNTIME-LAYOUT-ROLLOUT-REMAINING-01`

Background:
- `rs/cs` have already been moved in P0 to `src/runtime/<lang>/{generated,native,pytra}`, and this P1 rollout was started to bring the remaining backends (`go/java/kotlin/scala/swift/nim/js/ts/lua/ruby/php`) onto the same ownership model.
- That mismatch makes it hard to compare tree diffs and tell which `built_in/std/utils` modules are already emitted from SoT and which ones still survive as handwritten residuals.
- Per the user directive, `generated/` may contain only artifacts emitted from the SoT (`src/pytra/**`). Renaming handwritten runtime files into that lane is invalid.
- `rs/cs` are handled first in P0; the remaining backends are rolled out in P1 by wave.

Goal:
- Align every remaining backend runtime tree to the `generated/native` ownership model.
- Materialize SoT-origin modules in `generated/{built_in,std,utils}` and leave only handwritten substrate/residual code under `native/**`.
- Fix the compare unit to `<lane>/<bucket>/<module>` so C++, `rs/cs`, and the remaining backends can be compared consistently.

Scope:
- `src/runtime/{go,java,kotlin,scala,swift,nim,js,ts,lua,ruby,php}/**`
- `tools/gen_runtime_from_manifest.py`
- `tools/runtime_generation_manifest.json`
- `src/toolchain/compiler/backend_registry_metadata.py`
- backend-specific CLI/runtime shim/selfhost/build path definitions
- runtime guards / allowlists / inventories / docs

Out of scope:
- further redesign of the `rs/cs` runtimes
- redesigning the C++ runtime itself
- backend parity cell implementation work itself
- immediately deleting all non-SoT handwritten runtime code

Acceptance criteria:
- Every target backend has `src/runtime/<lang>/{generated,native,pytra}`.
- Every file under `src/runtime/<lang>/generated/**` is a SoT-generated artifact with `source:` and `generated-by:` markers.
- No file under `src/runtime/<lang>/native/**` contains a `generated-by:` marker; only handwritten runtime remains there.
- `src/runtime/<lang>/generated/{built_in,std,utils}` contains the generatable modules from `src/pytra/{built_in,std,utils}` by `<lane>/<bucket>/<module>`.
- Any module that cannot yet be generated is recorded with a reason in backend-specific inventories/allowlists so missing vs. residual modules remain comparable.
- Backend hooks / build / shim / selfhost checks reference the new `generated/native` paths.
- Runtime guards / inventories / docs audit `generated/native` rather than `pytra-core/pytra-gen` as the canonical vocabulary.

Planned verification:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_noncpp_runtime_layout_rollout_remaining_contract.py`
- `python3 tools/check_runtime_core_gen_markers.py`
- `python3 tools/check_runtime_pytra_gen_naming.py`
- `python3 tools/check_runtime_std_sot_guard.py`
- `python3 tools/check_crossruntime_pyruntime_residual_caller_inventory.py`
- `python3 tools/check_crossruntime_pyruntime_final_thincompat_inventory.py`
- `python3 tools/check_cpp_pyruntime_contract_inventory.py`
- `python3 tools/check_multilang_selfhost_stage1.py`
- `python3 tools/check_multilang_selfhost_multistage.py`

Execution policy:
1. Never place renamed handwritten files into `generated/`; only manifest/generator output from the SoT is allowed there.
2. Use `native/` as the renamed destination for the current `pytra-core` lane and keep only substrate/residual handwritten runtime there.
3. Keep `pytra/` as a compatibility/public shim lane when needed, but never treat it as the ownership source of truth.
4. Compare coverage by `<lane>/<bucket>/<module>` and treat extension differences (`.go/.java/.kt/.scala/.swift/.nim/.js/.ts/.lua/.rb/.php`) as a secondary detail.
5. Treat `generated/built_in/*` as the SoT lane for `src/pytra/built_in/*.py`, while substrate files such as `native/built_in/py_runtime.*` stay handwritten.

## Rollout Waves

### Wave A: static runtime family

Targets:
- `go`
- `java`
- `kotlin`
- `scala`
- `swift`
- `nim`

Focus:
- Align the backends with more static compile-time/runtime packaging first.
- Generalize the path updates across `backend_registry_metadata.py` and selfhost/build checks.

### Wave B: script runtime family

Targets:
- `js`
- `ts`
- `lua`
- `ruby`
- `php`

Focus:
- Process loader/shim/package-export differences as one group.
- Standardize the responsibility boundary between `pytra/**` compatibility shims and the `generated/native` lanes.

## Backend-family Work Items

### static runtime family

- rename `pytra-core -> native`, `pytra-gen -> generated`
- update manifest outputs and runtime hooks
- materialize `generated/built_in/*`
- materialize `generated/std/*` and `generated/utils/*`
- inventory and shrink handwritten residuals left in `native/**`

### script runtime family

- rename `pytra-core -> native`, `pytra-gen -> generated`
- update runtime shims, import/require paths, and package exports
- materialize `generated/built_in/*`
- materialize `generated/std/*` and `generated/utils/*`
- separate `pytra/**` shim responsibility from `native/**` residual responsibility

## Breakdown

- [x] [ID: P1-NONCPP-RUNTIME-LAYOUT-ROLLOUT-REMAINING-01-S1-01] Build per-backend mapping tables from the current `pytra-core/pytra-gen/pytra` trees to the target `generated/native/pytra` trees.
- [x] [ID: P1-NONCPP-RUNTIME-LAYOUT-ROLLOUT-REMAINING-01-S1-02] Fix, per backend, which modules belong in `generated/{built_in,std,utils}`, which stay in `native/**` as substrate/residual code, and which remain blocked in inventories/allowlists.
- [x] [ID: P1-NONCPP-RUNTIME-LAYOUT-ROLLOUT-REMAINING-01-S2-01] Cut Wave A (`go/java/kotlin/scala/swift/nim`) path / hook / build / selfhost definitions over to `generated/native`.
- [x] [ID: P1-NONCPP-RUNTIME-LAYOUT-ROLLOUT-REMAINING-01-S2-02] Regenerate Wave A `generated/{built_in,std,utils}` from the SoT and make the compare lanes real.
- [x] [ID: P1-NONCPP-RUNTIME-LAYOUT-ROLLOUT-REMAINING-01-S2-03] Shrink Wave A `native/**` residuals module-by-module and sync the required allowlists/inventories.
- [x] [ID: P1-NONCPP-RUNTIME-LAYOUT-ROLLOUT-REMAINING-01-S3-01] Cut Wave B (`js/ts/lua/ruby/php`) path / shim / package-export / selfhost definitions over to `generated/native`.
- [x] [ID: P1-NONCPP-RUNTIME-LAYOUT-ROLLOUT-REMAINING-01-S3-02] Regenerate Wave B `generated/{built_in,std,utils}` from the SoT and make the compare lanes real.
- [ ] [ID: P1-NONCPP-RUNTIME-LAYOUT-ROLLOUT-REMAINING-01-S3-03] Clean up the responsibility boundary between Wave B `native/**` residuals and the `pytra/**` compatibility lane, then sync the required allowlists/inventories.
- [ ] [ID: P1-NONCPP-RUNTIME-LAYOUT-ROLLOUT-REMAINING-01-S4-01] Update cross-backend guards / inventories / docs to the `generated/native` vocabulary so no backend remains incomparable.

Decision log:
- 2026-03-12: Per user direction, split the program so `rs/cs` stay in P0 and the remaining backends (`go/java/kotlin/scala/swift/nim/js/ts/lua/ruby/php`) move into this P1 rollout. P1 keeps the same rule: `generated=SoT only`, `native=hand-written only`.
- 2026-03-12: Ordered the P1 rollout as static-runtime family first (`go/java/kotlin/scala/swift/nim`), then script-runtime family (`js/ts/lua/ruby/php`) so packaging and shim differences do not mix in the same slice.
- 2026-03-13: As `S1-01`, the remaining backend current->target mapping table was fixed in `noncpp_runtime_layout_rollout_remaining_contract.py`. The first checker bundle only guards backend order, runtime hook keys, current root presence, lane-level current prefix presence, and the `native/generated/compat -> native/generated/pytra` taxonomy.
- 2026-03-13: As the first `S1-02` bundle, the current materialized file inventory for each remaining backend (`pytra-core/pytra-gen/pytra`) was fixed in the contract. Detailed blocked-module and target generated/native bucket classification is deferred to later bundles.
- 2026-03-13: As a later `S1-02` bundle, the blocked baseline in the target module-bucket inventory was widened from only `std/*` gaps to the canonical compare baseline (`built_in` 10-module set plus `std/{json,math,pathlib,time}` and `utils/{gif,png}`). `kotlin/scala/swift/nim/lua/ruby` now explicitly block `utils/gif|png` because image runtime is still helper-shaped there, while `js/ts/php` promote compare modules that still exist only in handwritten std/native lanes into the blocked set.
- 2026-03-13: As the second `S1-02` bundle, the target inventory baseline (`generated/native/pytra`) derived from the current inventory and lane mappings was also fixed in the contract. The checker now guards the expected target-path sets for each ownership bucket.
- 2026-03-13: As the third `S1-02` bundle, the logical module buckets derived from the target inventory (`generated/native/compat`) and the per-backend blocked-module baseline were also fixed in the contract. Compat overlap with native/generated remains allowed, and `blocked` is treated as the still-unmaterialized portion of the canonical compare baseline.
- 2026-03-13: As the final `S1-02` bundle, the contract added the canonical compare-baseline coverage rule. The checker now requires `blocked ⊆ compare baseline`, and `generated ∩ compare baseline` together with `blocked` must cover the entire baseline (`generated ∪ blocked = baseline`). Overlap with `compat/native` remains allowed because those lanes still carry shim/residual code during rollout.
- 2026-03-13: As `S2-01`, moved the Wave A (`go/java/kotlin/scala/swift/nim`) runtime trees onto `generated/native/pytra`, then synchronized `backend_registry_metadata.py`, manifest outputs, runtime boundary/naming/std guards, the Wave A runtime-hook source contract, and the Java/Kotlin/Swift smoke path baseline. `check_noncpp_runtime_layout_rollout_remaining_contract.py`, `check_runtime_{core_gen_markers,pytra_gen_naming,std_sot_guard}.py`, `check_java_pyruntime_boundary.py`, tooling unit tests, and Kotlin/Swift smoke now pass.
- 2026-03-13: Remaining `S2-01` fallout is carried into `S2-02`: `gen_runtime_from_manifest.py --targets go,java,kotlin,scala,swift,nim` still stops because Nim's helper-shaped output (`png_helper.nim`) is not resolved as the temp output file, and `java/generated/std/json.java` still comes back as stale under `--check` after regeneration.
- 2026-03-13: The final `S1-02` bundle also taught the checker to accept the mixed current state already present in part of Wave A. When the legacy `pytra-core/pytra-gen/pytra` inventory no longer matches, the contract is still considered satisfied if the target inventory derived from it matches the actual `generated/native/pytra` tree.
- 2026-03-13: As the first `S2-02` bundle, `tools/gen_runtime_from_manifest.py` was switched to use `backend_registry_static` instead of the fail-soft runtime-generation registry, and it now raises an explicit error when a backend returns neither inline text nor an output file. That made it clear the Nim `utils/*_helper` stop is not a temp-output naming issue but the real emitter failure `nim native emitter: unsupported stmt kind: Try`.
- 2026-03-13: As the second `S2-02` bundle, the Java emitter string-literal escaping was extended to cover `\\r/\\t/\\b/\\f`, which clears the stale `src/runtime/java/generated/std/json.java` compare lane. `test_gen_runtime_from_manifest.py` now guards the explicit-failure contract and the surfaced Nim `Try` blocker, while `test_py2java_smoke.py` guards the control-character literal regression. Verification: `gen_runtime_from_manifest.py --check --targets go,java,kotlin,scala,swift` passes, and `--targets nim --items utils/png` now returns `unsupported stmt kind: Try`.
- 2026-03-13: As the third `S2-02` bundle, the Nim native emitter gained representative `Try/finally` lowering, which brought `utils/gif_helper.nim` and `utils/png_helper.nim` back onto the live regeneration lane. `test_gen_runtime_from_manifest.py` now guards the emitted `f.write(...)` and `f.close()` sequence, and `gen_runtime_from_manifest.py --targets go,java,kotlin,scala,swift,nim --check` passes again.
- 2026-03-13: As the first `S2-03` bundle, the Wave A `native/**` residuals were added to the contract and split into `substrate` versus `compare_residual`. `built_in/py_runtime` is now fixed as `substrate`, while Java `native/std/{math_impl,time_impl}` maps to the compare labels `std/{math,time}` under `compare_residual`, and the checker now guards category overlap and bucket escape against the module-bucket baseline.
- 2026-03-13: As the second `S2-03` bundle, the Wave A `native/**` residuals also gained an exact file-level inventory and now fix `go/java/kotlin/scala/swift/nim` to `built_in/py_runtime.*` only. The checker enforces exact equality between `src/runtime/<backend>/native/**` and `substrate_files ∪ compare_residual_files`, and Java `native/std/{math_impl,time_impl}.java` was removed by absorbing that bridge logic into the generated lane.
- 2026-03-13: As a follow-up `S2-03` bundle, Java `generated/std/time.java` now rewrites its live wrapper to `System.nanoTime()` and `generated/std/math.java` rewrites to `java.lang.Math` through manifest postprocess hooks, so `backend_registry_metadata.py` no longer ships `native/std/{time_impl,math_impl}.java`. `test_gen_runtime_from_manifest.py` and `test_py2java_smoke.py` now lock that generated-only end state.
- 2026-03-13: As the `S2-03` close-out, every Wave A backend now leaves only `built_in/py_runtime.*` substrate under `native/**`. The compare residual set is gone, and the contract/checker/docs are synchronized to that end state, so `S2-03` is marked complete.
- 2026-03-13: As the first `S3-01` bundle, the `js/ts` slice of Wave B moved onto the `generated/native/pytra` tree. `pytra-core -> native`, `pytra-gen -> generated`, and the old flat compat files were normalized into `pytra/std|utils`, while `js_runtime_shims.py`, the selfhost JS shim writers, the contract/checker, and the runtime-dispatch test were synchronized to the new paths. `src/runtime/{js,ts}/pytra/**` now contains compat shims only.
- 2026-03-13: As the second `S3-01` bundle, the `lua/ruby/php` runtime tree also moved onto `generated/native/pytra`. `backend_registry_metadata.py`, manifest outputs, the contract/current inventory, `check_py2x_profiles.json`, and the `lua/rb/php` smoke path baseline were synchronized to the new paths, and PHP also normalized its public output bucket from `pytra/runtime/*` to `pytra/utils/*`. That completes the Wave B path / shim / package-export baseline, so `S3-01` is now complete.
- 2026-03-13: As the first `S3-02` bundle, the existing Wave B generated lanes were revalidated as live-regenerated artifacts. `gen_runtime_from_manifest.py --check --targets lua,ruby,php --items utils/png,utils/gif` now passes cleanly, and `audit_image_runtime_sot.py --fail-on-core-mix --fail-on-gen-markers --fail-on-non-compliant` is green across all 14 languages. That confirms the `lua/ruby/php` generated utils lanes and the `lua/ruby` `image_runtime` canonical artifacts are reproducible from the SoT.
- 2026-03-13: As the next `S3-02` bundle, Lua runtime regeneration was still stopping on `from pytra.std import abi` inside `pytra.utils.gif`, so the Lua emitter import-alias path learned to ignore compile-time decorator imports (`abi/template/extern`). A regression was added to `test_gen_runtime_from_manifest.py`, and `gen_runtime_from_manifest.py --targets js,ts,lua,ruby,php --check` is green again.
- 2026-03-13: As the current `S3-02` bundle, the Wave B-wide `gen_runtime_from_manifest.py --targets js,ts,lua,ruby,php --check` green state was locked into `test_gen_runtime_from_manifest.py`. That means the tooling regression now guards the entire Wave B script-runtime family, not just the `lua/ruby/php` utils compare lanes.
- 2026-03-13: As the current `S3-02` bundle, the remaining Wave B blocked compare lanes were classified into `missing compare lane / native residual / helper-shaped gap`. `js/ts` now record `std/{math,pathlib,time}` as handwritten native residuals while `std/json` and `built_in/*` remain missing compare lanes, `php` records `std/time` as the native residual, and `lua/ruby` lock the entire canonical baseline as helper-shaped gap until their compare lanes stop being helper-only.
- 2026-03-13: As the current `S3-02` bundle, `js/ts/php` `std/time` was promoted into a live-generated compare lane from the SoT. `tools/gen_runtime_from_manifest.py` gained `std/time` live-wrapper postprocess hooks for `js/ts/php`, `src/runtime/{js,ts,php}/generated/std/time.*` was regenerated, `src/runtime/{js,ts,php}/pytra/std/time.*`, `js_runtime_shims.py`, and PHP runtime packaging were switched over to the generated lane, and the contract/checker plus tooling/smoke coverage were synchronized. That removes `std/time` from the Wave B blocked compare baseline.
- 2026-03-13: As the current `S3-02` bundle, `js/ts` `std/math` was promoted into a live-generated compare lane from the SoT. `tools/gen_runtime_from_manifest.py` gained `std/math` live-wrapper postprocess hooks for `js/ts`, `src/runtime/{js,ts}/generated/std/math.*` was regenerated, `src/runtime/{js,ts}/pytra/std/math.*` plus `js_runtime_shims.py` were switched over to the generated lane, and the contract/checker plus tooling/smoke coverage were synchronized. That removes `std/math` from the `js/ts` Wave B blocked compare baseline.
- 2026-03-13: As the current `S3-02` bundle, `php` `std/math` was promoted into a live-generated compare lane from the SoT. `tools/gen_runtime_from_manifest.py` gained a `std/math` live-wrapper postprocess hook for `php`, `src/runtime/php/generated/std/math.php` was regenerated, `src/runtime/php/pytra/std/math.php` was added as a thin compat shim, and PHP runtime packaging was extended to ship `std/math.php`. The contract/checker plus tooling/smoke coverage were synchronized, which removes `std/math` from the PHP Wave B blocked compare baseline.
- 2026-03-13: As the final `S3-02` bundle, the Wave B generated compare end state was locked in the contract/checker. `js/ts/php` now materialize the compare-baseline `std/{math,time}` and `utils/{gif,png}` lanes as generated artifacts, while `lua/ruby` keep no live compare lanes and only retain the helper-shaped generated artifacts `utils/{gif_helper,image_runtime,png_helper}`. That makes the generated compare footprint and the remaining helper-only residual explicit, so `S3-02` is now complete.
- 2026-03-13: As the first `S3-03` bundle, the Wave B native-residual responsibility baseline was added to the contract/checker. `js/ts` now treat `built_in/py_runtime` plus the native backing seams `std/{math,pathlib,time}` as substrate, `php` treats `built_in/py_runtime` plus `std/time` as substrate, and `lua/ruby` keep only `built_in/py_runtime` as substrate. Locking both the module and file inventory gives the later compat-allowlist bundles a stable native baseline to clean against.
- 2026-03-13: As the next `S3-03` bundle, `js/ts` `std/pathlib` was promoted into a live-generated compare lane from the SoT. `tools/gen_runtime_from_manifest.py` and `tools/runtime_generation_manifest.json` gained `std/pathlib` live-wrapper postprocess hooks for `js/ts`, `src/runtime/{js,ts}/generated/std/pathlib.*` was regenerated, and `src/runtime/{js,ts}/pytra/std/pathlib.*` plus `js_runtime_shims.py` were switched over to the generated lane. The contract/checker and tooling/smoke coverage were synchronized, which shrinks the `js/ts` blocked compare baseline down to `built_in/* + std/json` while intentionally leaving native `std/pathlib` in place as substrate until the later cleanup bundle.
- 2026-03-13: As the current `S3-03` bundle, `php` `std/pathlib` was promoted into a live-generated compare lane from the SoT. `tools/gen_runtime_from_manifest.py` and `tools/runtime_generation_manifest.json` gained a `std/pathlib` live-wrapper postprocess hook for `php`, `src/runtime/php/generated/std/pathlib.php` was regenerated, and both `src/runtime/php/pytra/std/pathlib.php` plus PHP runtime packaging were extended to the generated lane. The contract/checker and tooling/smoke coverage were synchronized, which shrinks the PHP blocked compare baseline down to `built_in/* + std/json`.
