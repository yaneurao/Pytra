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
- [ ] [ID: P2-MULTILANG-EXTERN-RUNTIME-REALIGN-01-S1-02] Lock the cross-target contract in spec/plan so `@extern` means declaration-only, native owners provide implementations, and ambient externs stay a separate category.
- [ ] [ID: P2-MULTILANG-EXTERN-RUNTIME-REALIGN-01-S2-01] Remove module-specific extern rewrites from `tools/runtime_generation_manifest.json` and `tools/gen_runtime_from_manifest.py`, and align generated lanes to declaration/wrapper-only output.
- [ ] [ID: P2-MULTILANG-EXTERN-RUNTIME-REALIGN-01-S2-02] Establish canonical extern-backed owners under `src/runtime/<lang>/native/**` for each target and synchronize the runtime symbol index plus layout contracts.
- [ ] [ID: P2-MULTILANG-EXTERN-RUNTIME-REALIGN-01-S2-03] Remove backend-emitter hardcodes such as `pytra.std.math` and move them to generic extern/runtime metadata.
- [ ] [ID: P2-MULTILANG-EXTERN-RUNTIME-REALIGN-01-S3-01] Sync representative runtime artifacts, smoke tests, docs, and contract inventories to the current extern-ownership contract and close the task.

Decision log:
- 2026-03-13: Opened after the user called out the current non-C++ design as incorrect. The task resets all targets to the SoT/native-owner/generic-emitter split instead of backend shortcuts for `@extern`.
- 2026-03-14: Added `extern_contract_v1` / `extern_v1` to `tools/gen_runtime_symbol_index.py` and `runtime_symbol_index.py` as a prerequisite slice, so runtime-SoT `@extern` modules and symbols can be queried through generic metadata before the manifest/emitter hardcodes are removed.
- 2026-03-14: For C#, matched the existing `time_native` pattern by turning `generated/std/math.cs` back into a wrapper over `math_native`, and moved the direct `System.Math` bindings into `src/runtime/cs/native/std/math_native.cs`.
- 2026-03-14: As the first realignment slice, stopped the C# `std/math` generated wrapper from inventing a `tau` symbol that does not exist in the SoT, restoring `pi/e` as the only source-defined exported constants.
- 2026-03-14: Added `multilang_extern_runtime_realign_inventory.py`, its checker, and unit tests for `S1-01`, locking the current manifest postprocess targets, C++ native owners, non-C++ native seams, emitter hardcodes, and generated drift for `std/math,time,os,os_path,sys,glob` plus `built_in/io_ops,scalar_ops`. The C# `std/math` inventory now records `math_native.cs` as the current non-C++ owner seam.
