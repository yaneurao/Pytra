<a href="../../en/todo/cpp.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — C++ backend

> Domain-specific TODO. See [index.md](./index.md) for the full index.

Last updated: 2026-04-02

## Operating Rules

- **The old toolchain1 (`src/toolchain/emit/cpp/`) must not be modified.** All new development and fixes go in `src/toolchain2/emit/cpp/` ([spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1).
- Each task requires an `ID` and a context file (`docs/ja/plans/*.md`).
- Work in priority order (lower P numbers first).
- Progress notes and commit messages must always include the same `ID`.
- **When a task is complete, change `[ ]` to `[x]` and append a completion note, then commit.**
- Completed tasks are periodically moved to `docs/ja/todo/archive/`.
- **Completion criteria for parity tests: "emit + compile + run + stdout match".**
- **You must read the [emitter implementation guide](../spec/spec-emitter-guide.md).** It covers the parity check tool, prohibited patterns, and how to use mapping.json.

## Incomplete Tasks

### P0-CPP-VARIANT: Migrate C++ to std::variant-based approach and retire object/box/unbox

Context: [docs/ja/plans/plan-cpp-variant-migration.md](../plans/plan-cpp-variant-migration.md)
Spec: [docs/ja/spec/spec-adt.md](../spec/spec-adt.md)

Phase 1 (adding variant output) and Phase 2 through S5 are complete (see [archive/20260402.md](archive/20260402.md)).

**Phase 2: Delete the object type (remaining)**

1. [x] [ID: P0-CPP-VARIANT-S6] Isolate blockers for deleting the `object` class from `object.h` and lock down the deletion order
   - Completion note: Blockers were split into `P0-CPP-VARIANT-S6A`, `P0-CPP-VARIANT-S10A`, and `P0-CPP-VARIANT-S10B` and locked down. The seams before deleting `object.h` were inventoried in [p0-cpp-object-seam-inventory.md](../plans/p0-cpp-object-seam-inventory.md), and remaining iter boundary items were extracted into [p0-cpp-iter-boundary-runtime-contract.md](../plans/p0-cpp-iter-boundary-runtime-contract.md). At this point, `resolved_type="object"` in non-explicit dynamic paths has been removed; remaining items are limited to explicit object / bare `Callable` / iter runtime contracts.
2. [x] [ID: P0-CPP-VARIANT-S6A] Remove unnecessary `PYTRA_TID_OBJECT` / object-type-id normalization remnants from the C++ runtime / emitter
   - Completion note: `isinstance(x, object)` / `issubclass(X, object)` are now lowered to the constant `True`, and `object -> PYTRA_TID_OBJECT` was removed from `_builtin_type_id_symbol()`. The C++ emitter's `PYTRA_TID_OBJECT -> object` normalization was also removed, and confirmed 0 remaining `PYTRA_TID_OBJECT` occurrences under `src/toolchain2/emit/cpp`, `src/toolchain2/compile`, and `src/runtime/cpp`.
3. [x] [ID: P0-CPP-VARIANT-S7] Confirm all fixture and sample cases PASS without the `object` type
   - Completion note: Rechecked `in_membership`, `iterable`, `callable_higher_order`, `finally`, `float`, and `type_ignore_from_import` via fresh in-memory probe, confirming `object(` / `.unbox<...>()` / `.as<...>()` are gone from generated C++ entry `.cpp` files. The last blocker, `type_ignore_from_import`, was resolved by fixing the resolver to account for `main -> __pytra_main` renaming when refining bare `Callable` to `callable[[],None]`; `runtime_parity_check_fast --case-root fixture --targets cpp type_ignore_from_import` also confirmed PASS. Marked complete based on `18/18 PASS` for sample broad parity and the immediately preceding `139/139 PASS` for fixture broad parity, together with the final blocker resolution from the fresh probe.

**Phase 3: Remove box/unbox**

4. [x] [ID: P0-CPP-VARIANT-S8] Remove box/unbox handling from the C++ emitter and replace with variant assignment / `std::get`
   - Completion note: In the fresh `parity-fast` run, generated C++ entry `.cpp` files show 0 occurrences of `.unbox<...>()` / `.as<...>()`. Stale runtime EAST was also isolated, and `[src/runtime/east/utils/assertions.east](/workspace/Pytra/src/runtime/east/utils/assertions.east)` was re-synced to the canonical source. Additionally, promoting `py_assert_stdout` in `[src/pytra/utils/assertions.py](/workspace/Pytra/src/pytra/utils/assertions.py)` to `callable[[], None]` means the `([&](object) -> object { ... })` bridge in the `_case_main` harness is also gone in the fresh in-memory transpile. The only remaining `object` path in the fresh probe is `type_ignore_from_import`, which lowers bare `Callable` to `::std::function<object(object)>` — this is not a box/unbox remnant.

**Phase 4: Remove object degradation / box / unbox from EAST**

5. [x] [ID: P0-CPP-VARIANT-S10A] Remove `resolved_type="object"` generation from non-explicit dynamic paths in lower.py
   - Completion note: For the C++ backend with `target_language="cpp"`, iter boundary lowering is suppressed and `py_iter_or_raise` / `py_next_or_stop` calls are left as-is. Additionally, the dynamic target `Box` for C++ now preserves the target type rather than fixing `resolved_type="object"`, and this behavior is locked in by `test_compile_uses_dynamic_target_resolved_type_for_cpp_box` / `test_compile_uses_union_target_resolved_type_for_cpp_box` / `test_compile_cpp_lowering_avoids_object_resolved_type_for_representative_dynamic_cases`. After scanning all fixtures lowered for C++, only 6 nodes in `trait_basic`, `trait_with_inheritance`, and `typed_container_access` with explicit dynamic/object contracts have `resolved_type="object"`; 0 non-explicit dynamic path items remain.
6. [x] [ID: P0-CPP-VARIANT-S10B] Organize remaining iter boundary and explicit object / bare `Callable` boundary items as separate contracts and lock down the deletion order
   - Completion note: Re-scanned all fixtures lowered for C++ and reconfirmed 0 non-explicit dynamic path `resolved_type="object"` items; remaining items are limited to the 6 explicit object contract nodes in `trait_basic`, `trait_with_inheritance`, and `typed_container_access`. Also confirmed that iter boundary seams reside not in the old `iter_ops` but in the generic `py_any` / `py_all` in `src/runtime/east/built_in/predicates.east`, and updated [p0-cpp-iter-boundary-runtime-contract.md](../plans/p0-cpp-iter-boundary-runtime-contract.md). The remaining items for the `S10` body are now locked to three lines: explicit object / bare `Callable` / runtime generic iter helpers.
7. [x] [ID: P0-CPP-VARIANT-S11] Add "error if `resolved_type: "object"`" validation to EAST3
   - Completion note: Added `toolchain2.compile.validate_east3` and configured it to throw a `RuntimeError` at the end of `lower_east2_to_east3()` if `resolved_type: "object"` is detected. Added validator unit and regression test confirming that an `object`-annotated source fails at compile time.

### P20-CPP-SELFHOST: Convert toolchain2 to C++ via the C++ emitter and pass g++ build

Context: [docs/ja/plans/p4-cpp-selfhost.md](../plans/p4-cpp-selfhost.md)

S0–S4 are complete (see [archive/20260402.md](archive/20260402.md)).

1. [ ] [ID: P20-CPP-SELFHOST-S5] Build the selfhost C++ binary with g++ and confirm linking succeeds
2. [ ] [ID: P20-CPP-SELFHOST-S6] Confirm fixture parity PASS with `run_selfhost_parity.py --selfhost-lang cpp --emit-target cpp --case-root fixture`
3. [ ] [ID: P20-CPP-SELFHOST-S7] Confirm sample parity PASS with `run_selfhost_parity.py --selfhost-lang cpp --emit-target cpp --case-root sample`
