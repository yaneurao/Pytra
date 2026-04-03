<a href="../../ja/plans/p1-julia-emitter.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-2563EB?style=flat-square">
</a>

# P1-JULIA-EMITTER

Last updated: 2026-04-04

## Target

- [ID: P1-JULIA-EMITTER-S1] Implement a new Julia emitter in `src/toolchain2/emit/julia/`
- [ID: P1-JULIA-EMITTER-S2] Create `src/runtime/julia/mapping.json`

## Objective

- Move the old `src/toolchain/emit/julia/` out of scope for future modifications, and establish the canonical Julia backend in toolchain2.
- Align the profile / mapping / emitter entry point to the standard toolchain2 structure following the emitter implementation guidelines.

## Approach

- In the first phase, add a `CommonRenderer`-based Julia emitter entry point on the toolchain2 side.
- To avoid inadvertently breaking existing parity, use the old Julia emitter as a compatibility delegate during bootstrap, while fixing the new implementation's home in toolchain2.
- Centralize runtime function names, type names, and target constants in `src/runtime/julia/mapping.json`.
- Place operator and syntax base configuration in `src/toolchain2/emit/profiles/julia.json`.

## Completion Criteria

- `src/toolchain2/emit/julia/` is importable.
- `src/runtime/julia/mapping.json` exists and has at minimum `builtin_prefix` / `calls` / `types` / `skip_modules` / `implicit_promotions`.
- Julia source strings can be generated from the bootstrap emitter.

## Decision Log

- 2026-04-02: [ID: P1-JULIA-EMITTER-S1] Fixed the new Julia backend implementation location at `src/toolchain2/emit/julia/`; started migration with a delegate to the old emitter during bootstrap.
- 2026-04-02: [ID: P1-JULIA-EMITTER-S2] Created `src/runtime/julia/mapping.json` as the new canonical source for runtime calls/types, in preparation for moving to a profile-driven emitter.
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] Improved smoke parity reproducibility by preferring the real binary over the `juliaup` launcher.
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] Separated `JuliaBootstrapRewriter` and `JuliaLegacyEmitterBridge` on the toolchain2 side, making the boundary of responsibilities between rewriting and legacy emit explicit.
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] Extracted emit pre-processing into `_prepare_module_for_emit()` and organized default expansion to be non-destructive to input.
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] Separated bootstrap helpers into `bootstrap.py`, isolating migration implementation details from the renderer body.
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] Moved `module_id_from_doc()` / `prepare_module_for_emit()` to the bootstrap module, separating migration helpers from the renderer body.
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] Added a narrow toolchain2-native Julia renderer in `subset.py`, creating the first migration path where simple modules are emitted without the legacy bridge.
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] Added `ForCore` / `AnnAssign` to the subset native renderer; `for_range` / `loop` can now be processed via the native path.
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] Added `BoolOp` / `IfExp` to the subset native renderer; `ifexp_bool` is now on the native path.
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] Added membership / slice / list repeat and `dict.get` / tuple `Swap` / `str.join` to the subset native renderer, broadening core/control simple fixture coverage.
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] Empty classes are not yet moved to subset; the legacy bridge is maintained. Early native migration of `ClassDef` conflicted with the existing Julia smoke contract, so phased migration is prioritized.
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] Added `Lambda` to the subset native renderer; moved core fixtures including anonymous functions and captures to the native path.
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] Moved the subset check to after bootstrap rewrite, switching to a phased migration that treats empty `ClassDef` as a no-op. This allows some fixtures including static class attrs and post-closure-rewrite to be included in the native path.
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] Added minimal class support to the subset native renderer; nativized empty class, simple `__init__`, class call, and instance field access.
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] Added `While` to the subset native renderer; also pulled in control fixtures after generator lowering to the native path.
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] Added `Try` / `Raise` to the subset native renderer; moved control fixture groups using standard exceptions and finally to the native path.
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] Added minimal custom exception class support to the subset native renderer; fixture/control is now handled entirely via the native path.
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] Corrected the approach: emitter verification reverts to the parity check canonical path per the guide; dedicated bootstrap unit tests are not maintained.
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] Aligned Julia execution in the parity runner to prefer the real binary; absorbed `str(...)` and negative-step `range(...)` in the subset native renderer to maintain control parity 16/16.
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] Added `ImportFrom(math/time/pytra.utils.png)`, minimal `int` / `bytearray` mapping, and Julia reserved-word identifier mangling to the subset native renderer; started moving simple import fixtures to the native path.
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] Added `str` method group, list mutation, `JoinedStr` / `FormattedValue` to the subset native renderer; moved simple string/list fixtures to the native path.
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] Added `pytra.std.collections.deque` import and deque/dict mutation to the subset native renderer; broadened simple collections fixtures to the native path.
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] Added extended `str` method group (`lower/find/index/isalnum/lstrip/split`) to the subset native renderer; moved additional string fixtures to the native path.
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] Added `Import(math)` and `ImportFrom(pytra.std.math)` to the subset native renderer; moved math module / symbol import fixtures to the native path.
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] Added `Import(pytra.std.env/os, pytra.utils.png)`, keyword-form `os.makedirs(..., exist_ok=...)`, and Julia-style string concatenation to the subset native renderer; moved PNG import fixtures to the native path.
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] Added `VarDecl` / `Set` / expression `range(...)` / `reversed(...)` and `__pytra_contains` lowering for membership to the subset native renderer; moved `enumerate_basic`, `reversed_enumerate`, `in_membership_iterable` to the native path.
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] Added `set.add`, `dict.keys/values`, `bytearray[...] = ...` to the subset native renderer; moved `set_mutation_methods`, `dict_wrapper_methods`, `bytearray_basic` to the native path.
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] Added `set.discard/remove` and builtin `set()` to the subset native renderer; moved `set_wrapper_methods` and `nested_types` to the native path.
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] Added `dict.items()` and `list.extend()` to the subset native renderer; moved `typed_container_access` to the native path.
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] Confirmed that `object_container_access` enters the subset native path / parity PASS without additional implementation. The nearest remaining gap is `property_method_call`'s class/property method lowering.
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] Added property getter / instance method to minimal class support in the subset native renderer; moved `property_method_call` to the native path.
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] Added bitwise `~`, `&`, `|`, `^` to the subset native renderer; moved `bitwise_invert_basic` to the native path.
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] Added `@staticmethod` class support to the subset native renderer; moved `staticmethod_basic` to the native path.
- 2026-04-04: [ID: P1-JULIA-EMITTER-S1] Added instance field `AugAssign` (`self.field += ...`) to the subset native renderer; moved `class_instance` to the native path.
- 2026-04-04: [ID: P1-JULIA-EMITTER-S1] Fixed bootstrap rewrite to also lift `AnnAssign` static attrs in class bodies to globals; moved `class_member` to the native path.
- 2026-04-04: [ID: P1-JULIA-EMITTER-S1] Subset native renderer now also handles object parameter field updates (`x.v += ...`); moved `alias_arg` to the native path.
- 2026-04-04: [ID: P1-JULIA-EMITTER-S1] Added Julia type mapping for `IsInstance` to the subset native renderer; moved `union_basic`, `union_dict_items`, `isinstance_pod_exact`, `isinstance_tuple_check` to the native path.
- 2026-04-04: [ID: P1-JULIA-EMITTER-S1] Added type-only `ImportFrom(pytra.std.json)`, `str.isdigit()`, and absorption of `Expr(Name("continue"|"break"))` to the subset native renderer; moved `union_return_errorcheck` and `isinstance_narrowing` to the native path / parity PASS.
- 2026-04-04: [ID: P1-JULIA-EMITTER-S1] Added `TypeAlias` no-op and `str.upper()` to the subset native renderer; moved `type_alias_pep695` and `callable_higher_order` to the native path / parity PASS.
- 2026-04-04: [ID: P1-JULIA-EMITTER-S1] Aligned `str(...)` / `bool(...)` / `str.isdigit()` in the subset native renderer to Julia runtime helpers; moved `union_list_mixed` to the native path / parity PASS.
- 2026-04-04: [ID: P1-JULIA-EMITTER-S1] Added bit shift (`<<`, `>>`) to the subset native renderer; moved `starred_call_tuple_basic` to the native path / parity PASS.
- 2026-04-04: [ID: P1-JULIA-EMITTER-S1] Subset native renderer can now receive `pytra.enum` import and empty enum classes (`Enum`, `IntEnum`, `IntFlag`); moved `enum_basic`, `intenum_basic`, `intflag_basic` to the native path / parity PASS.
- 2026-04-04: [ID: P1-JULIA-EMITTER-S1] Added tuple/list destructuring assignment and nested/subscript target unpack to the subset native renderer; moved `tuple_unpack_variants` to the native path / parity PASS.
- 2026-04-04: [ID: P1-JULIA-EMITTER-S1] Added single-generator `ListComp` / `SetComp` / `DictComp` and list concat (`vcat`) to the subset native renderer; moved `ok_list_concat_comp`, `comprehension_dict_set`, `comprehension_nested` to the native path / parity PASS.
- 2026-04-04: [ID: P1-JULIA-EMITTER-S1] Subset native renderer can now receive linked typed-vararg form (`arg_order` + `vararg_name`); also absorbs value-less `AnnAssign` and plain `Assign` to `Attribute` targets; moved `ok_typed_varargs_representative` to the native path / parity PASS.
- 2026-04-04: [ID: P1-JULIA-EMITTER-S1] Added class inheritance (`abstract type + backing struct`), `super()` lowering, builtin `bytes(...)`, bool index, `dict.get(key)`, `type(v).__name__`, fstring `format_spec` to the subset native renderer; moved inheritance-related fixtures and remaining string/typing/signature fixtures to the native path / parity PASS.
- 2026-04-04: [ID: P1-JULIA-EMITTER-S1] `runtime_parity_check_fast.py --case-root fixture --targets julia` maintains 146/146 PASS; the remaining gap in toolchain2-native determination has shrunk to 3 frontend blocker cases.
- 2026-04-04: [ID: P1-JULIA-EMITTER-S1] Import/runtime resolution in the subset native renderer is aligned to `build_import_alias_map()` / `build_runtime_import_map()` / `should_skip_module()` and `mapping.json`-based approach; direct branching for `pytra.std.*` / `pytra.utils.*` is reduced.
- 2026-04-04: [ID: P1-JULIA-EMITTER-S1] Added canonical native file / namespace expressions to `src/runtime/julia/mapping.json`; fixture parity 146/146 PASS is maintained even after adding `py_assert_*` / `__pytra_exception` to the Julia runtime.
