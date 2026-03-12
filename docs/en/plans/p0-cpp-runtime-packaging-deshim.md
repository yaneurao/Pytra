# P0: Move C++ runtime packaging to compiler-direct headers and retire repo shims

Last updated: 2026-03-13

Related TODO:
- `docs/ja/todo/index.md` `ID: P0-CPP-RUNTIME-PACKAGING-DESHIM-01`

Background:
- The current C++ backend still uses the runtime symbol index `public_headers` as both the compiler include surface and the SDK/public surface, so generated code reaches the runtime through shim trees under `src/runtime/cpp/pytra/**` and `src/runtime/cpp/core/**`.
- EAST3 itself only needs to decide which runtime module / symbol is required. The `pytra/**` and `core/**` forwarder trees are packaging artifacts, not semantic requirements.
- The user explicitly directed that if C++ runtime packaging can include internal headers directly, the compiler should stop depending on shims and use the real `generated/native` artifacts instead.
- Under the current shared `public_headers` model, even checked-in generated runtime files such as `generated/std/pathlib.cpp` still include `pytra/std/*.h`, while `generated/std/*.h` still depend on `runtime/cpp/core/*.h` forwarders. That blocks shim retirement from the compiler path.

Goals:
- Switch the C++ compiler/emitter to include `src/runtime/cpp/{generated,native}/**` and `src/runtime/cpp/native/core/**` directly.
- Split compiler-facing headers from SDK/public headers in `runtime_symbol_index`, so `public_headers` is reserved for export/package use while `compiler_headers` becomes the codegen/build source of truth.
- Eventually remove `src/runtime/cpp/pytra/**` and `src/runtime/cpp/core/**` from the compiler path in the repo itself, and keep them only as export-time generated artifacts if they are still needed.

Scope:
- `src/toolchain/frontends/runtime_symbol_index.py`
- `tools/gen_runtime_symbol_index.py`
- `tools/runtime_symbol_index.json`
- `src/backends/cpp/emitter/runtime_paths.py`
- `src/backends/cpp/emitter/module.py`
- `src/backends/cpp/emitter/header_builder.py`
- `src/backends/cpp/emitter/cpp_emitter.py`
- `src/backends/cpp/emitter/multifile_writer.py`
- `src/backends/cpp/program_writer.py`
- `src/backends/cpp/cli.py`
- `tools/cpp_runtime_deps.py`
- `tools/check_runtime_cpp_layout.py`
- `src/runtime/cpp/generated/**`
- related docs / tests

Out of scope:
- adding new runtime APIs
- rolling this design out to non-C++ backends
- feature-parity work in the C++ runtime itself
- deleting `src/runtime/cpp/pytra/**` and `src/runtime/cpp/core/**` immediately in the first slice

Acceptance criteria:
- `runtime_symbol_index` gains `compiler_headers`, and for the `cpp` target it resolves module runtime to `generated/**` or `native/**`, and core runtime to `native/core/**`.
- The C++ emitter / runtime emit / multi-file prelude / helper artifact flow includes compiler headers instead of `pytra/**` or `core/**`.
- Checked-in generated runtime files under `src/runtime/cpp/generated/**` stop using `pytra/**` and `runtime/cpp/core/**` as compiler-time include paths, and point directly at `generated/**` and `runtime/cpp/native/core/**`.
- `public_headers` may remain as the SDK/public shim surface, but compiler path selection must not depend on it anymore.
- `tools/check_runtime_cpp_layout.py` is updated to enforce the new contract: generated/native/compiler lanes may include `native/core` directly, while `pytra/core` are no longer the compiler ownership roots.
- By the end of the first wave, transpiled user code, checked-in generated runtime, and the build graph all work without depending on `pytra/**` or `core/**`.
- By the end of the final wave, `src/runtime/cpp/pytra/**` and `src/runtime/cpp/core/**` can either move to export-time generated artifacts or be removed if unnecessary.

Planned verification:
- `python3 tools/check_todo_priority.py`
- `python3 tools/gen_runtime_symbol_index.py --check`
- `python3 tools/check_runtime_cpp_layout.py`
- `PYTHONPATH=src:. python3 -m unittest test.unit.tooling.test_runtime_symbol_index`
- `PYTHONPATH=src:. python3 -m unittest test.unit.tooling.test_cpp_runtime_build_graph`
- `PYTHONPATH=src:. python3 -m unittest test.unit.backends.cpp.test_cpp_runtime_symbol_index_integration`
- `PYTHONPATH=src:. python3 -m unittest test.unit.backends.cpp.test_py2cpp_features`

Execution policy:
1. Do not remove `public_headers` yet. First add `compiler_headers` and make the compiler consult only that list.
2. For module runtime, prefer `generated/<bucket>/<module>.h` as the compiler header, and only fall back to `native/<bucket>/<module>.h` when no generated header exists.
3. For core runtime, treat `native/core/<module>.h` as canonical for the compiler. `core/<module>.h` may remain only as a compatibility/export lane.
4. Reduce hard-coded `pytra/...` / `core/...` strings in helper include maps and runtime emit output. Resolve runtime module headers through the symbol index whenever possible.
5. In the first wave, do not delete repo shims yet. The completion condition is that the compiler stops depending on them.

## Target structure

Compiler/build-facing surface:

- `src/runtime/cpp/generated/{built_in,std,utils,compiler}/`
- `src/runtime/cpp/native/{built_in,std,utils,compiler}/`
- `src/runtime/cpp/native/core/`

Optional SDK/export-facing surface:

- `src/runtime/cpp/pytra/**`
- `src/runtime/cpp/core/**`

Roles:

- `compiler_headers`
  - the internal source of truth included by generated C++ and checked-in generated runtime
- `public_headers`
  - a stable surface for SDK/export/package use if still needed
- `compile_sources`
  - the concrete implementation files collected by the build graph

## Breakdown

- [x] [ID: P0-CPP-RUNTIME-PACKAGING-DESHIM-01-S1-01] Fix the new C++ runtime packaging contract in docs/TODO and introduce the two-surface model: `compiler_headers` vs `public_headers`.
- [x] [ID: P0-CPP-RUNTIME-PACKAGING-DESHIM-01-S1-02] Add `compiler_headers` to `tools/gen_runtime_symbol_index.py`, the loader, and tests; lock the rule that modules resolve to `generated/native` and core resolves to `native/core`.
- [x] [ID: P0-CPP-RUNTIME-PACKAGING-DESHIM-01-S2-01] Switch the C++ emitter/runtime-path/helper include resolution to `compiler_headers`, so transpiled user code stops including `pytra/**` and `core/**`.
- [x] [ID: P0-CPP-RUNTIME-PACKAGING-DESHIM-01-S2-02] Switch `emit-runtime-cpp`, the multi-file prelude, and helper artifacts to `runtime/cpp/native/core/**`, and regenerate the checked-in generated runtime files.
- [x] [ID: P0-CPP-RUNTIME-PACKAGING-DESHIM-01-S3-01] Update `tools/cpp_runtime_deps.py` and the build-graph tests to the compiler-direct include contract, so compile sources are still recovered without shim dependence.
- [x] [ID: P0-CPP-RUNTIME-PACKAGING-DESHIM-01-S3-02] Update `tools/check_runtime_cpp_layout.py` and docs so `generated/native/compiler` lanes may include `native/core` directly, and `pytra/core` are treated as export/sdk lanes.
- [ ] [ID: P0-CPP-RUNTIME-PACKAGING-DESHIM-01-S4-01] Decide whether an export-time SDK generator is still needed. If yes, move `pytra/**` and `core/**` forwarders to build/export-time generation; if not, delete them from the repo.

Decision log:
- 2026-03-13: Per user direction, raised a new P0 to move the C++ compiler away from `pytra/**` / `core/**` shims and toward direct inclusion of the `generated/native` runtime artifacts.
- 2026-03-13: The first wave does not need to delete repo shims immediately. It only needs to remove them from the compiler path. `public_headers` may remain temporarily, but they are no longer the codegen/build source of truth.
- 2026-03-13: `compiler_headers`, `runtime_paths.py`, `emit-runtime-cpp`, `program_writer.py`, the checked-in generated runtime, `cpp_runtime_deps.py`, and `check_runtime_cpp_layout.py` were already aligned with the current `generated/native` + `native/core` contract. The early slices were therefore closed by syncing the README/docs language and progress state to the implemented layout.
- 2026-03-13: `runtime_symbol_index` now carries `compiler_headers` separately from `public_headers`. For C++, the loader gained `lookup_target_module_primary_compiler_header()`, which prefers `generated/**` for module runtime and `native/core/**` for core runtime. The emitter-side include resolution now consults only that API.
- 2026-03-13: The helper include maps no longer hard-code `pytra/built_in/*.h`. They resolve `pytra.built_in.*` module ids through the compiler-header path, so transpiled user code now includes `generated/built_in/*`, `generated/std/*`, and `generated/utils/*` directly.
- 2026-03-13: `emit-runtime-cpp` was switched to direct `runtime/cpp/native/core/**` includes. When a matching `native/<bucket>/<module>.h` exists, `generated/<bucket>/<module>.h` now auto-injects that companion include, moving the old `generated + native` aggregation from the `pytra/**` shim layer into the compiler-facing header itself.
- 2026-03-13: `src/toolchain/compiler/backend_registry_static.py` still fails `--emit-runtime-cpp` regeneration because of a known self-hosted-parser residual (`unterminated string literal`). In the first wave, the generated compiler shim stays in place, while the handwritten `native/compiler/backend_registry_static.{h,cpp}` includes were manually synchronized to `generated/std/{json,pathlib}.h` and `runtime/cpp/native/core/py_runtime.h`.
