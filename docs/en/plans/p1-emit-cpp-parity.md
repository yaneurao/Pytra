<a href="../../ja/plans/p1-emit-cpp-parity.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-2563EB?style=flat-square">
</a>

# P1: toolchain2 C++ emitter runtime alignment and parity completion

Last updated: 2026-03-27

Related TODOs:
- `docs/ja/todo/index.md` `ID: P1-EMIT-CPP-S2`
- `docs/ja/todo/index.md` `ID: P1-EMIT-CPP-S3`
- `docs/ja/todo/index.md` `ID: P1-EMIT-CPP-S9`
- `docs/ja/todo/index.md` `ID: P1-EMIT-CPP-S10`

## Background

The C++ emitter itself in `toolchain2/emit/cpp/` has been introduced, but the runtime side and build paths still carry assumptions from the old `toolchain/` era. In particular, runtime header/source generation, native companion integration, CLI build wiring, and sample parity verification were all mixed into one TODO, making progress and completion conditions unclear.

Per [spec-emitter-guide.md](../spec/spec-emitter-guide.md), the following cleanup is needed around the C++ emitter / runtime:

- The emitter renders only EAST3 and does not depend on the old `toolchain`'s type system or header builder
- Runtime symbol resolution is placed in `mapping.json` / metadata / loader; module ID hardcoding is not increased
- `src/runtime/cpp/` maintains its existing split structure while aligning with the new pipeline's output

## Objective

Bring `P1-EMIT-CPP-S2` and `P1-EMIT-CPP-S3` through to guide-compliant runtime alignment and parity completion.

## Target

- `src/toolchain2/emit/cpp/`
- `src/runtime/cpp/`
- `src/pytra-cli.py`
- `src/pytra-cli2.py`
- Tests / tooling required for C++ parity

## Out of scope

- Additional improvements to other backends such as `toolchain2/emit/go/`
- selfhost completion (`P2-SELFHOST-S4`)
- `int32` as default (`P4-INT32`)

## Acceptance Criteria

- `src/runtime/cpp/` aligns with toolchain2 C++ emitter output and does not bring in old `toolchain` header/type assumptions
- C++ build path in `pytra-cli.py` / `pytra-cli2.py` works on a toolchain2 basis
- All 18 samples satisfy `emit + g++ compile + run + stdout match`

## Verification commands

- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest test.unit.toolchain2.test_linker_spec_conform2 -v`
- `python3 tools/check/runtime_parity_check.py --targets cpp --cmd-timeout-sec 60 --case-root sample`

## Subtasks

- [x] [ID: P1-EMIT-CPP-S2-01] Place runtime symbol resolution and include/path resolution in `mapping.json` / metadata-based approach; clean up module ID hardcoding and old include fallbacks.
- [x] [ID: P1-EMIT-CPP-S2-02] Align runtime bundle header/source generation with the toolchain2 C++ type system; remove dependency on the old `toolchain.emit.cpp.emitter.header_builder`.
- [x] [ID: P1-EMIT-CPP-S2-03] Correctly integrate runtime bundle and native companion in the C++ build path of `pytra-cli.py` / `pytra-cli2.py`; get representative fixture compile passing.
- [x] [ID: P1-EMIT-CPP-S3-01] Get `emit + g++ compile` passing for all 18 samples.
- [x] [ID: P1-EMIT-CPP-S3-02] Confirm `run + stdout match` for all 18 samples; get `runtime_parity_check.py --targets cpp` passing.

## Decision Log

- 2026-03-27: Initial version created. `P1-EMIT-CPP-S2` and `P1-EMIT-CPP-S3` were too coarse-grained with runtime alignment, build wiring, and parity execution all mixed together, so they were decomposed into concrete work-unit subtasks.
- 2026-03-27: The main blocker at this point is that `runtime_bundle.py` generates runtime `.cpp` in toolchain2 style, while the old `toolchain` type system is mixed into the header side, causing a mismatch between `py_assert_all(std::vector<bool>, std::string)` and the old `Object<list<bool>>` declaration. Prioritizing `S2-02` first.
- 2026-03-27: Completed `S2-01` through `S2-03`. Placed runtime symbol and include resolution in metadata-based approach via `runtime_paths.py` / `dependencies.py` / `mapping.json`. Unified `header_gen.py` / `runtime_bundle.py` / `emitter.py` to toolchain2 C++ type system. `pytra-cli.py test/fixture/source/py/stdlib/path_stringify.py --target cpp` compiles successfully; `test_linker_spec_conform2` runtime bundle/pathlib regression also passes.
- 2026-03-27: Completed `S3-01` / `S3-02`. Fixed `runtime_bundle.py` / `header_gen.py` to keep extern declarations for native-companion-only runtime modules in the header; restored `io.h` core type circularity; unified `ObjStr` to the `py_to_string` lane. Also rendered `image.save_gif.keyword_defaults` adapter in C++ emitter and excluded `pytra.std.template` as a type-only dependency from includes. `python3 tools/check/runtime_parity_check.py --case-root sample --targets cpp --cmd-timeout-sec 60` passes `18/18`.
- 2026-03-27: Switched runtime EAST source-of-truth generation from legacy `toolchain` to toolchain2 (`parse -> resolve -> lower`). Added `open -> PyFile` resolver typing, `pytra.built_in.type_id` dependency injection for type predicates, and nominal class `type_id`/`Box`/`cast`/`isinstance` rendering to C++ emitter. Confirmed `json_extended`, `17_monte_carlo_pi`, `18_mini_language_interpreter`, and sample compile sweep `18/18`.
- 2026-03-27: Completed `S8`. Unified default C++ container representation to `Object<list<T>>` / `Object<dict<K,V>>` / `Object<set<T>>`; only locals with `container_value_locals_v1` degrade to value type. Updated `types.py` / `emitter.py` / `src/runtime/cpp/`. Confirmed `dict_wrapper_methods.py` and `set_wrapper_methods.py` C++ build+run; `json_extended` remaining failure isolated as a separate runtime bundle issue.
- 2026-03-27: Completed `S9`. Moved rel-tail resolution for runtime modules to a shared helper in `link/runtime_discovery.py`; removed `pytra.built_in/std/utils/core` prefix/path convention hardcoding from `emit/cpp/runtime_paths.py`. Also replaced the C++ emitter's per-module `pytra.core.py_runtime` branch with common include path resolution. Added focused runtime path / include regression.
- 2026-03-27: Completed `S10`. Moved `py_int_from_str` / `py_float_from_str` native mappings to `runtime/cpp/mapping.json`. Removed per-case branches for `append → push_back`, container helpers, and string-to-number casts from the C++ emitter. Attribute calls now also prefer mapping resolution when runtime metadata is available. Confirmed with focused regression and representative C++ build.
- 2026-03-27: Completed `S11`. C++ emitter `main_guard_body` / `main()` output now uses `emit_context.is_entry` as the single source of truth; library modules (`is_entry=False`) no longer generate a main guard or entrypoint. Entry modules retain `__pytra_main_guard()` as before. Added focused regression.
- 2026-03-27: Completed `S12`. Removed `/* slice */` and `/* assign */` placeholders remaining in the C++ emitter; now fails fast via `unsupported_slice_shape` / `unsupported_assign_target`. Added focused regression alongside the existing fail-closed group.
- 2026-03-27: Completed `S13`. Added `implicit_promotions` to the common `RuntimeMapping`; defined an integer/float implicit promotion table in C++ `mapping.json`. `BinOp.casts` now omit `static_cast` only when the promotion matches this table; non-matching casts still use `static_cast`. Confirmed with focused regression.
- 2026-03-27: Completed `S14`. Moved concrete names for type-only modules and `pytra.core.*` helper skip remaining in the C++ backend helper to a shared helper. `runtime_paths.py` is now a thin adapter using `link/dependencies.py:is_type_only_dependency_module_id()` and `runtime_discovery.py:is_runtime_internal_helper_module()`. Passed focused runtime path regression.
- 2026-03-27: Completed `S15`. When `_emit_attribute()` sees `attribute_access_kind == "property_getter"`, the C++ emitter now emits `obj.method()` rather than a member access. Confirmed with `test_cpp_emitter_calls_property_getters_with_parens` and `runtime_parity_check.py --targets cpp property_method_call`.
