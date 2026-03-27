<a href="../../../ja/plans/archive/20260312-p4-crossruntime-pyruntime-residual-caller-shrink.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P4 Crossruntime PyRuntime Residual Caller Shrink

Last updated: 2026-03-12

Purpose:
- Prepare the next `py_runtime.h` shrink by cleaning up the remaining non-emitter `py_runtime` callers.
- Inventory the residual callers in native compiler wrappers, generated C++ runtime code, and Rust/C# runtime builtins, then narrow the reasons `object_bridge_compat` and `shared_type_id_contract` still remain.
- Separate the residual caller seams that must survive until the final header shrink from the seams that should be moved onto thin helpers first.

Background:
- The existing [p4-crossruntime-pyruntime-emitter-shrink.md](./p4-crossruntime-pyruntime-emitter-shrink.md) covers C++ / Rust / C# emitter dependencies, but emitter cleanup alone does not remove the residual callers that still keep `py_runtime.h` large.
- The remaining callers are concentrated in native compiler wrappers (`transpile_cli.cpp`, `backend_registry_static.cpp`), generated C++ runtime modules (`type_id.cpp`, `json.cpp`, `iter_ops.cpp`, and related files), and Rust/C# runtime builtins.
- Even after emitter-side cleanup, these callers would still force `py_runtime.h` to keep `object_bridge_compat` and `shared_type_id_contract` surface, so they need a separate caller-side inventory and handoff.
- This is not the final header deletion step. It is a cross-runtime residual caller contract cleanup, so it is tracked as a later `P4`.

Out of scope:
- Immediate deletion or large rewrites inside `py_runtime.h`.
- Re-doing the emitter-side residual dependency cleanup.
- Introducing a new runtime object model or type system.

Acceptance criteria:
- Residual `py_runtime.h` callers in native compiler wrappers, generated C++ runtime code, and Rust/C# runtime builtins are inventoried in the plan.
- The residual callers are classified into `object_bridge_compat` and `shared_type_id_contract`, with a clear handoff for which ones should move onto thin helpers first.
- Representative source-guard / inventory / smoke lanes are defined so caller re-entry fails closed.
- The residual seam needed for the later header shrink handoff is explicitly documented.
- The English mirror stays aligned with the Japanese source plan.

## Child tasks

- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-RESIDUAL-CALLER-SHRINK-01-S1-01] Inventory residual `py_runtime` callers in native compiler wrappers, generated C++ runtime code, and Rust/C# runtime builtins, then classify them into `object_bridge_compat` and `shared_type_id_contract`.
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-RESIDUAL-CALLER-SHRINK-01-S2-01] Move native compiler-wrapper `type_id` / object-bridge callers toward thin helper seams and define representative regressions.
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-RESIDUAL-CALLER-SHRINK-01-S2-02] Re-classify residual callers in the generated C++ runtime and separate callers that must remain from callers that can be re-delegated before header shrink.
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-RESIDUAL-CALLER-SHRINK-01-S2-03] Inventory Rust/C# runtime builtin dependencies on the shared seams and define the final cross-runtime residual contract shape.
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-RESIDUAL-CALLER-SHRINK-01-S3-01] Add residual-caller inventory tooling, source guards, and smoke coverage, then connect the final residual seam to the later header-shrink handoff.

## Emitter Handoff Snapshot

- The preceding [20260312-p4-crossruntime-pyruntime-emitter-shrink.md](./archive/20260312-p4-crossruntime-pyruntime-emitter-shrink.md) task already reduced the emitter-driven `typed_collection_compat` and `shared_type_id_compat` buckets to empty.
- The only header residual bucket handed to this task is `object_bridge_mutation`, and the header surface source of truth remains [check_cpp_pyruntime_header_surface.py](/workspace/Pytra/tools/check_cpp_pyruntime_header_surface.py).
- This task therefore focuses on non-emitter callers that still keep `object_bridge_mutation` alive, while the preceding emitter inventory tool keeps watching for emitter-side re-entry.

## Current residual caller inventory (S1-01)

- `native_wrapper_object_bridge_residual`
  - `py_runtime_object_isinstance` @ `src/runtime/cpp/native/compiler/transpile_cli.cpp`
  - `py_runtime_object_isinstance` @ `src/runtime/cpp/native/compiler/backend_registry_static.cpp`
- `generated_cpp_object_bridge_residual`
  - `py_runtime_object_isinstance` @ `src/runtime/cpp/generated/std/json.cpp`
  - `py_append` @ `src/runtime/cpp/generated/built_in/iter_ops.cpp`
- `generated_cpp_shared_type_id_residual`
  - `py_runtime_object_type_id` @ `src/runtime/cpp/generated/built_in/type_id.cpp`
- `cs_runtime_utils_object_bridge_residual`
  - `py_append` @ `src/runtime/cs/pytra/utils/png.cs`
  - `py_append` @ `src/runtime/cs/pytra/utils/gif.cs`
- `rs_runtime_builtin_shared_type_id_residual`
  - `py_runtime_value_type_id` / `py_runtime_value_isinstance` / `py_runtime_type_id_is_subtype` / `py_runtime_type_id_issubclass`
  - `src/runtime/rs/pytra/built_in/py_runtime.rs`
  - `src/runtime/rs/pytra-core/built_in/py_runtime.rs`
- `cs_runtime_builtin_shared_type_id_residual`
  - `py_runtime_value_type_id` / `py_runtime_value_isinstance` / `py_runtime_type_id_is_subtype` / `py_runtime_type_id_issubclass`
  - `src/runtime/cs/pytra/built_in/py_runtime.cs`
  - `src/runtime/cs/pytra-core/built_in/py_runtime.cs`

Classification:
- `object_bridge_compat`
  - `native_wrapper_object_bridge_residual`
  - `generated_cpp_object_bridge_residual`
  - `cs_runtime_utils_object_bridge_residual`
- `shared_type_id_contract`
  - `generated_cpp_shared_type_id_residual`
  - `rs_runtime_builtin_shared_type_id_residual`
  - `cs_runtime_builtin_shared_type_id_residual`

Inventory source of truth:
- [check_crossruntime_pyruntime_residual_caller_inventory.py](/workspace/Pytra/tools/check_crossruntime_pyruntime_residual_caller_inventory.py)
- [test_check_crossruntime_pyruntime_residual_caller_inventory.py](/workspace/Pytra/test/unit/tooling/test_check_crossruntime_pyruntime_residual_caller_inventory.py)

Generated C++ runtime policy (S2-02):
- `must remain`
  - `py_runtime_object_isinstance` @ `src/runtime/cpp/generated/std/json.cpp`
  - `py_append` @ `src/runtime/cpp/generated/built_in/iter_ops.cpp`
  - `py_runtime_object_type_id` @ `src/runtime/cpp/generated/built_in/type_id.cpp`
- `re-delegatable before header shrink`
  - none

Rust/C# runtime builtin policy (S2-03):
- `must remain`
  - `py_runtime_value_type_id`
  - `py_runtime_value_isinstance`
  - `py_runtime_type_id_is_subtype`
  - `py_runtime_type_id_issubclass`
  - targets: `src/runtime/{rs,cs}/pytra/built_in/py_runtime.*`
  - targets: `src/runtime/{rs,cs}/pytra-core/built_in/py_runtime.*`
- `re-delegatable before header shrink`
  - none
- source guard
  - the four helpers above must stay as the public thin seam in the Rust/C# runtime builtins
  - `py_runtime_type_id` / `py_isinstance` / `py_is_subtype` / `py_issubclass` must not re-enter the public surface

Representative smoke lanes (S3-01):
- native wrapper residual
  - `test/unit/common/test_py2x_entrypoints_contract.py`
  - `py_runtime_object_isinstance` count guards in `transpile_cli.cpp` / `backend_registry_static.cpp`
- generated C++ residual
  - `test/unit/backends/cpp/test_cpp_runtime_iterable.py`
  - `test/unit/backends/cpp/test_cpp_runtime_type_id.py`
- Rust runtime builtin residual
  - `test/unit/backends/rs/test_py2rs_smoke.py`
  - `type_predicate` lowering must stay on runtime builtin thin helpers
- C# residual
  - `test/unit/backends/cs/test_py2cs_smoke.py`
  - `type_predicate` lowering and the `pytra.utils.gif` runtime-import helper lane stay explicit

## Decision log

- 2026-03-12: Emitter-side cleanup alone is not enough to reduce the remaining `py_runtime.h` surface, so a separate `P4` was added for native/generated/runtime-builtin callers.
- 2026-03-12: This task is a residual caller inventory and thin-seam cleanup step, not the final header deletion step, so it remains a `P4`.
- 2026-03-12: The emitter-shrink handoff is fixed as `typed_collection_compat = empty`, `shared_type_id_compat = empty`, and `object_bridge_mutation = residual caller owned`, so this task now owns the last non-emitter header blocker.
- 2026-03-12: `S1-01` freezes the residual callers into six buckets (`native_wrapper_object_bridge_residual`, `generated_cpp_object_bridge_residual`, `generated_cpp_shared_type_id_residual`, `cs_runtime_utils_object_bridge_residual`, `rs_runtime_builtin_shared_type_id_residual`, `cs_runtime_builtin_shared_type_id_residual`) and limits the category split to `object_bridge_compat` and `shared_type_id_contract`.
- 2026-03-12: The first `S2-01` bundle centralizes direct `py_runtime_object_isinstance` checks in the native compiler wrappers behind a file-local `_object_is_runtime_type(...)` helper so the wrapper body itself no longer re-enters raw type checks at multiple sites.
- 2026-03-12: `S2-01` completes by adding a representative smoke/source-guard manifest for the native wrapper residual bucket and wiring the `_object_is_runtime_type(...)` guard in `test_py2x_entrypoints_contract.py` into the inventory source of truth.
- 2026-03-12: `S2-02` separates the generated C++ residual callers into must-remain and re-delegatable buckets, and currently freezes `json.cpp` / `iter_ops.cpp` / `type_id.cpp` as must-remain with no re-delegatable generated callers left.
- 2026-03-12: `S2-03` separates the Rust/C# runtime builtin residuals into must-remain and re-delegatable buckets, and fixes the public residual contract in both runtime trees to the four thin helpers `py_runtime_value_type_id`, `py_runtime_value_isinstance`, `py_runtime_type_id_is_subtype`, and `py_runtime_type_id_issubclass`.
- 2026-03-12: `S3-01` registers the representative smoke lanes in the inventory tool and makes native-wrapper / generated-C++ / Rust-runtime-builtin / C# residual test-name drift fail closed.
