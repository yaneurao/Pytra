# P2: realign the `@extern` runtime/emitter contract across all languages

Last updated: 2026-03-14

Related TODO:
- `docs/ja/todo/index.md` `ID: P2-MULTILANG-EXTERN-RUNTIME-REALIGN-01`

Background:
- Modules such as `src/pytra/std/math.py`, `src/pytra/std/time.py`, `src/pytra/std/os.py`, `src/pytra/std/os_path.py`, `src/pytra/std/sys.py`, `src/pytra/std/glob.py`, `src/pytra/built_in/io_ops.py`, and `src/pytra/built_in/scalar_ops.py` use `@extern` / `extern(...)` to declare runtime external boundaries.
- As of 2026-03-13, the non-C++ lanes collapse those declarations into host-API implementations through generated-runtime postprocess rewrites and backend-emitter special cases.
- A representative example is `src/runtime/cs/generated/std/math.cs`, which ships `System.Math` implementations plus a `tau` symbol that does not exist in the source, while `tools/gen_runtime_from_manifest.py` and multiple backend emitters carry hardcoded `pytra.std.math` knowledge.
- In that state, `src/pytra/**` stops being the source of truth, and `@extern` is misused as "a marker the backend may rewrite into host APIs" instead of "a declaration of an external boundary."
- The C++ lane still keeps a comparatively correct declaration/implementation split through header/source ownership, and the non-C++ lanes need to return to the same principle.

Objective:
- Restore `@extern` as a cross-language declaration of an external boundary and remove host-specific semantics from generated lanes.
- Concentrate host-API bindings in `src/runtime/<lang>/native/**`, and make backend emitters depend only on generic extern metadata.
- Restore `src/pytra/**` as the canonical API surface and stop adding source-absent symbols or module-specific rewrites.

In scope:
- Runtime-SoT `@extern` / `extern(...)` usage under `src/pytra/std/*` and `src/pytra/built_in/*`
- `tools/runtime_generation_manifest.json` and `tools/gen_runtime_from_manifest.py`
- Backend-emitter module-specific extern special cases such as `pytra.std.math`
- Extern-ownership descriptions in the runtime symbol index, layout contracts, representative smoke tests, and docs
- Generated/native runtime artifact updates for all target languages

Out of scope:
- Expanding the semantics of ambient-global `extern()` in user programs (`document`, `window.document`, etc.)
- A full redesign of all non-extern runtime helpers
- Adding new host-runtime APIs

Acceptance criteria:
- Generated runtime artifacts no longer hardcode host-specific implementations for `@extern` symbols.
- Host bindings such as `System.Math`, `Math.*`, and `pyMath*` are confined to canonical owners under `src/runtime/<lang>/native/**`.
- Backend emitters no longer carry module-specific extern hardcodes such as `pytra.std.math`, and instead route through generic extern/runtime metadata.
- Generated artifacts no longer add symbols that do not exist in `src/pytra/**` such as `tau`.
- The C++ reference lane does not regress, and representative runtime/emitter regressions for every non-C++ target are updated to the current contract.

Validation commands (planned):
- `python3 tools/check_todo_priority.py`
- `rg -n "std_math_live_wrapper|pytra\\.std\\.math|System\\.Math|Math\\.PI|Math\\.Sqrt|tau" src tools test docs -g '!**/archive/**'`
- `python3 tools/gen_runtime_from_manifest.py --items std/math,std/time,std/os,std/os_path,std/sys,std/glob,built_in/io_ops,built_in/scalar_ops --targets rs,cs,js,ts,go,java,swift,kotlin,ruby,lua,scala,php,nim`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_gen_runtime_from_manifest.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2*_smoke.py'`
- `git diff --check`

## Breakdown

- [x] [ID: P2-MULTILANG-EXTERN-RUNTIME-REALIGN-01-S1-01] Inventory every runtime-SoT `@extern` module plus the current generated rewrites, emitter hardcodes, and native owners across all targets.
- [x] [ID: P2-MULTILANG-EXTERN-RUNTIME-REALIGN-01-S1-02] Lock the cross-target contract in spec/plan so `@extern` means declaration-only, native owners provide implementations, and ambient externs stay a separate category.
- [ ] [ID: P2-MULTILANG-EXTERN-RUNTIME-REALIGN-01-S2-01] Remove module-specific extern rewrites from `tools/runtime_generation_manifest.json` and `tools/gen_runtime_from_manifest.py`, and align generated lanes to declaration/wrapper-only output.
- [ ] [ID: P2-MULTILANG-EXTERN-RUNTIME-REALIGN-01-S2-02] Establish canonical extern-backed owners under `src/runtime/<lang>/native/**` for each target and synchronize the runtime symbol index plus layout contracts.
- [x] [ID: P2-MULTILANG-EXTERN-RUNTIME-REALIGN-01-S2-03] Remove backend-emitter hardcodes such as `pytra.std.math` and move them to generic extern/runtime metadata.
- [ ] [ID: P2-MULTILANG-EXTERN-RUNTIME-REALIGN-01-S3-01] Sync representative runtime artifacts, smoke tests, docs, and contract inventories to the current extern-ownership contract and close the task.

For `S1-02`, add a contract/checker/spec wording that fixes runtime-SoT `@extern` as declaration-only metadata, native ownership to runtime layout / manifest / runtime symbol index, and ambient-global `extern()` as a separate category.

Decision log:
- 2026-03-13: Opened after the user called out the current non-C++ design as incorrect. The task resets all targets to the SoT/native-owner/generic-emitter split instead of backend shortcuts for `@extern`.
- 2026-03-14: Added `extern_contract_v1` / `extern_v1` to `tools/gen_runtime_symbol_index.py` and `runtime_symbol_index.py` as a prerequisite slice, so runtime-SoT `@extern` modules and symbols can be queried through generic metadata before the manifest/emitter hardcodes are removed.
- 2026-03-14: For C#, matched the existing `time_native` pattern by turning `generated/std/math.cs` back into a wrapper over `math_native`, and moved the direct `System.Math` bindings into `src/runtime/cs/native/std/math_native.cs`.
- 2026-03-14: Synchronized the `math_native` seam across the C# smoke suite, the non-C++ runtime layout contract, the generated-cpp baseline contract, the CLI build profile, and the selfhost compile checker so `generated/std/math.cs` no longer depends on an implicit host binding.
- 2026-03-14: As the first realignment slice, stopped the C# `std/math` generated wrapper from inventing a `tau` symbol that does not exist in the SoT, restoring `pi/e` as the only source-defined exported constants.
- 2026-03-14: Added `multilang_extern_runtime_realign_inventory.py`, its checker, and unit tests for `S1-01`, locking the current manifest postprocess targets, C++ native owners, non-C++ native seams, emitter hardcodes, and generated drift for `std/math,time,os,os_path,sys,glob` plus `built_in/io_ops,scalar_ops`. The C# `std/math` inventory now records `math_native.cs` as the current non-C++ owner seam.
- 2026-03-14: In the C# emitter, switched `std/math` and `std/time` owner resolution to generic extern metadata from `CodeEmitter.get_import_resolution_bindings()` / `lookup_import_resolution_binding()` plus `iter_cs_std_lane_ownership()`, reducing one more layer of direct `pytra.std.math` / `pytra.std.time` string hardcodes.
- 2026-03-14: For `S1-02`, add a contract/checker/spec wording that fixes runtime-SoT `@extern` as declaration-only metadata, native ownership to runtime layout / manifest / runtime symbol index, and ambient-global `extern()` as a separate category.
- 2026-03-14: In the Rust emitter, built the runtime-prelude re-export module set from `iter_rs_std_lane_ownership()` so root `use` suppression and prelude exports no longer depend on the direct `pytra.std.time` string hardcode, and removed that needle from the inventory.
- 2026-03-14: Also aligned the C# `std/time` rewrite in `tools/gen_runtime_from_manifest.py` to the shared `cs_std_native_owner_wrapper` that delegates to `helper_name + "_native"`, removing the one-off manifest postprocess that hardcoded `time_native`.
- 2026-03-14: As the second `S2-01` bundle, renamed the `std/time` postprocess names for `rs/java/js/ts/php` to generic `perf_counter` seam helpers and removed the module-specific `*_std_time_live_wrapper` naming from `tools/gen_runtime_from_manifest.py` and the inventory/checker.
- 2026-03-14: In the Nim emitter, moved the `std/math` `sqrt` / `pi` / `e` special handling from a runtime-module literal to `semantic_tag` plus `runtime_symbol`, removing the `pytra.std.math` needle from the inventory.
- 2026-03-14: In the PHP/Ruby emitters, switched zero-arg runtime value getter detection to `lookup_runtime_symbol_extern_doc(...).kind == "value"` and removed the old negative `pytra.std.math` needles from the inventory.
- 2026-03-14: In the Go/Kotlin/Swift emitters, replaced the direct `pytra.std.math` literal checks with runtime-extern-module metadata plus a math-symbol set, and removed the `_runtime_module_id(expr) == "pytra.std.math"` needles from the inventory.
- 2026-03-14: In the PHP and Ruby emitters, moved the `std/math` `pi` / `e` zero-arg getter check to `lookup_runtime_symbol_extern_doc(...).kind == "value"` plus `runtime_symbol`, and removed the `if _runtime_module_id(expr) != "pytra.std.math"` module-literal hardcode from the inventory. The value-getter adapter metadata itself is still not modeled yet, so the symbol set remains limited to `pi` / `e` for now.
- 2026-03-14: Added `math.float_args` / `math.value_getter` adapter metadata to the runtime symbol index and moved the Scala emitter away from the `std/math` host shortcut back to `pyMath*` helper calls. The self-hosted lane now uses adapter metadata, while the existing backend-only IR compare artifact is absorbed through a `math.pi` / `math.sin` fallback, and the `scala.math.*` / `pytra.std.math` literals are removed from the inventory.
- 2026-03-14: In the Lua emitter, moved `std/math` module/symbol aliases onto `math.float_args` / `math.value_getter` adapter metadata and `std/time` aliases onto the `stdlib.fn.perf_counter` semantic tag. That removes the `if mod == "pytra.std.math"` / `if mod == "pytra.std.time"` needles from the inventory and routes Lua import lowering for `math` / `perf_counter` through generic metadata.
- 2026-03-14: In the same Lua slice, moved `std/glob`, `std/os`, `std/os_path`, and `std/sys` over to symbol-table aliases driven by `semantic_tag`, removing the `if mod == "pytra.std.glob|os|os_path|sys"` literals from the inventory. The remaining Lua module-specific alias hardcodes are now limited to `enum`, `argparse`, `re`, `json`, `pathlib`, and `pytra.utils.*`.
- 2026-03-14: In the Lua emitter, also moved `std/os`, `std/os_path`, `std/sys`, and `std/glob` onto semantic-tag-driven symbol-table aliases. That removes the remaining `if mod == "pytra.std.*"` literal checks from the inventory and routes `os.getcwd`, `os_path.join`, `sys.write_stdout`, and `glob.glob` through generic extern metadata.
- 2026-03-14: Reflected `S2-03` in the docs after the emitter-hardcode inventory went green for every tracked row.
- 2026-03-14: As the first `S3-01` bundle, added `representative_smoke_needles` to the inventory and locked smoke evidence for `std/math/time` on C#/Go/Java/Rust, `std/os/os_path/sys/glob` on Lua/JS/TS/PHP, and `built_in/io_ops/scalar_ops` on Go/Kotlin/Scala/Swift.
- 2026-03-14: For JS/TS `std/math`, removed direct `Math.*` / `Math.PI` host bindings from generated wrappers and added `src/runtime/js|ts/native/std/math_native.*` as the canonical seam. Also synchronized the rollout/baseline contracts plus JS/TS smoke tests so the generated lane only talks to the native owner.
- 2026-03-14: Applied the same split to JS/TS `std/time`, removing `process.hrtime.bigint()` from `generated/std/time.{js,ts}` and turning those files back into wrappers over `src/runtime/js|ts/native/std/time_native.*`. The inventory, rollout contracts, baseline contract, and JS/TS smoke suite are now synchronized around that time seam.
- 2026-03-14: As an extra `S2-01` slice, folded C# `std/math` off the module-specific `cs_std_math_live_wrapper` and into the existing `cs_std_native_owner_wrapper`, and moved JS `std/math` onto `js_std_native_owner_wrapper + helper_name=math`. Both helpers now derive extern value/function order from the raw generated text before forwarding into the `math_native` seam.
- 2026-03-14: Continued the same `S2-01` thread by moving TS `std/math` onto `ts_std_native_owner_wrapper + helper_name=math`. The wrapper now preserves function/value order from the raw generated text, reattaches numeric signatures in postprocess, and forwards through the `math_native` seam.
- 2026-03-14: Moved Java `std/time` off direct `System.nanoTime()` calls in `generated/std/time.java` and added `src/runtime/java/native/std/time_native.java` as the canonical seam. The runtime-hook metadata, rollout/baseline contracts, inventory, and Java smoke tests now all assume that seam.
- 2026-03-14: Also folded the Java `std/time` manifest hook from `java_perf_counter_host_wrapper` into `java_std_native_owner_wrapper + helper_name=time`. The artifact shape stays the same, but the Java lane now follows the same “generic owner-wrapper, no module-specific postprocess name” contract as the other migrated targets.
- 2026-03-14: Applied the same split to Java `std/math`, removing `Math.*` / `Math.PI` from `generated/std/math.java` and turning it back into a wrapper over `src/runtime/java/native/std/math_native.java`. The manifest now uses `java_std_native_owner_wrapper + helper_name=math`, and the runtime-hook metadata, rollout/baseline contracts, inventory, and Java smoke tests are synchronized around that math seam.
