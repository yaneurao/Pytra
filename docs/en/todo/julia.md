<a href="../../en/todo/julia.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — Julia backend

> Domain-specific TODO. See [index.md](./index.md) for the full index.

Last updated: 2026-04-03

## Operating Rules

- **The old toolchain1 (`src/toolchain/emit/julia/`) must not be modified.** All new development and fixes go in `src/toolchain2/emit/julia/` ([spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1).
- Each task requires an `ID` and a context file (`docs/ja/plans/*.md`).
- Work in priority order (lower P numbers first).
- Progress notes and commit messages must always include the same `ID`.
- **When a task is complete, change `[ ]` to `[x]` and append a completion note, then commit.**
- Completed tasks are periodically moved to `docs/ja/todo/archive/`.
- **Completion criteria for parity tests: "emit + compile + run + stdout match".**
- **You must read the [emitter implementation guide](../spec/spec-emitter-guide.md).** It covers the parity check tool, prohibited patterns, and how to use mapping.json.

## References

- Old toolchain1 Julia emitter: `src/toolchain/emit/julia/`
- toolchain2 TS emitter (reference implementation): `src/toolchain2/emit/ts/`
- Existing Julia runtime: `src/runtime/julia/`
- Emitter implementation guide: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json spec: `docs/ja/spec/spec-runtime-mapping.md`

## Incomplete Tasks

### P1-JULIA-EMITTER: Implement a new Julia emitter in toolchain2

1. [ ] [ID: P1-JULIA-EMITTER-S1] Implement a new Julia emitter in `src/toolchain2/emit/julia/` — CommonRenderer + override structure. Reference the old `src/toolchain/emit/julia/` and the TS emitter
   - 2026-04-02: Added Julia emitter / CLI / profile to toolchain2 side and connected `pytra-cli.py emit --target julia` to the toolchain2 path. Currently at bootstrap stage with old emitter delegate
   - 2026-04-03: Added `ClosureDef -> FunctionDef` compatibility transform to bootstrap emitter, resolving Julia emit failure for `test/fixture/source/py/control/nested_closure_def.py`
   - 2026-04-03: Fixed `tools/unittest/emit/julia/test_py2julia_smoke.py` to prefer the actual binary over the `juliaup` launcher; reconfirmed 39 tests `OK (skipped=1)`
   - 2026-04-03: Separated bootstrap rewrite into `JuliaBootstrapRewriter` and old emitter delegate into `JuliaLegacyEmitterBridge` within the toolchain2 Julia emitter, and made the `render_module()` entry point explicit
   - 2026-04-03: Extracted `render_module()` preprocessing into `_prepare_module_for_emit()` and fixed cross-module default expansion to apply only to a deep copy of the input doc. Non-destructiveness confirmed via unit test
   - 2026-04-03: Separated bootstrap helpers into `src/toolchain2/emit/julia/bootstrap.py`; `emitter.py` is now focused on the renderer entry point and orchestration
   - 2026-04-03: Moved `module_id_from_doc()` / `prepare_module_for_emit()` to `bootstrap.py` as well, separating bootstrap helpers from the renderer body
   - 2026-04-03: Added `src/toolchain2/emit/julia/subset.py`; narrow AST subsets equivalent to `add/assign/compare/if_else` can now be emitted via a toolchain2-native path without going through the legacy bridge
   - 2026-04-03: Added `AnnAssign` and `ForCore` (`StaticRangeForPlan` / `RuntimeIterForPlan`) to the subset native renderer, extending toolchain2-native coverage through `for_range` / `loop` equivalents
   - 2026-04-03: Added `BoolOp` and `IfExp` to the subset native renderer; `ifexp_bool` equivalents can now be handled by the toolchain2-native path
   - 2026-04-03: Added membership / slice / list repeat and `dict.get` / tuple `Swap` / `str.join` to the subset native renderer, moving `dict_in`, `negative_index`, `slice_basic`, `list_repeat`, `dict_literal_entries`, `tuple_assign`, `str_join_method` to the native path
   - 2026-04-03: Added `Lambda` to the subset native renderer, moving `lambda_basic`, `lambda_immediate`, `lambda_ifexp`, `lambda_as_arg`, `lambda_capture_multiargs`, `lambda_local_state` to the native path. Native coverage at this point: `core` 19 cases, `control` 7 cases
   - 2026-04-03: Moved subset determination to after bootstrap rewrite, and made empty `ClassDef` a no-op. `class_tuple_assign` and `nested_closure_def` are now on the native path; native coverage: `core` 20 cases, `control` 8 cases
   - 2026-04-03: Added minimal class support to the subset native renderer, nativizing empty class, simple `__init__`, class call, and instance field access. Moved `class_body_pass` and `obj_attr_space` to native path; native coverage: `core` 22 cases, `control` 8 cases
   - 2026-04-03: Added `While` to the subset native renderer and moved the post-generator-lowering `yield_generator_min` to the native path. Native coverage: `core` 22 cases, `control` 9 cases
   - 2026-04-03: Added `Try` / `Raise` to the subset native renderer, moving `try_raise`, `finally`, `exception_bare_reraise`, `exception_finally_order`, `exception_propagation_raise_from`, `exception_propagation_two_frames` to the native path. Only `exception_user_defined_multi_handler` still has a legacy dependency on the control side
   - 2026-04-03: Added minimal custom exception class support to the subset native renderer, moving `exception_user_defined_multi_handler` to the native path. Native coverage: `core` 22 cases, `control` 16 cases
   - 2026-04-03: Reverted Julia emitter verification to use `runtime_parity_check_fast.py` and smoke parity as canonical per the emitter guide; dedicated bootstrap unit tests are not maintained
   - 2026-04-03: Fixed `runtime_parity_check_fast.py`'s Julia execution path to prefer the actual binary over the `juliaup` launcher; absorbed `str(...)` and negative-step `range(...)` in the subset native renderer, reconfirmed `fixture/control` parity 16/16
   - 2026-04-03: Added `ImportFrom(math/time/pytra.utils.png)`, minimal mapping for `int` / `bytearray`, and Julia reserved-word identifier mangling to the subset native renderer, moving `from_import_symbols` and `import_time_from` to the native path
   - 2026-04-03: Added `str` methods (`strip/rstrip/startswith/endswith/replace/join`), list mutation (`clear/sort/reverse`), and `JoinedStr` / `FormattedValue` to the subset native renderer, moving `str_methods`, `list_mutation_methods`, and `fstring` to the native path
   - 2026-04-03: Added `pytra.std.collections.deque` import and `deque`/`dict` mutations (`appendleft/popleft/pop/clear/setdefault`) to the subset native renderer, moving `deque_basic` and `dict_mutation_methods` to the native path
   - 2026-04-03: Added extended `str` methods (`lower/find/index/isalnum/lstrip/split`) to the subset native renderer, moving `str_methods_extended` to the native path
   - 2026-04-03: Added `Import(math)` and `ImportFrom(pytra.std.math)` and allowed module attr calls (`sqrt/floor/fabs`) in the subset native renderer, moving `import_math_module` and `from_pytra_std_import_math` to the native path
   - 2026-04-03: Added `Import(pytra.std.env/os, pytra.utils.png)`, keyword `os.makedirs(..., exist_ok=...)`, and `str + str` concatenation to the subset native renderer, moving `import_pytra_runtime_png` to the native path
   - 2026-04-03: Added `VarDecl` / `Set` / expression `range(...)` / `reversed(...)` and `__pytra_contains` lowering for membership to the subset native renderer, moving `enumerate_basic`, `reversed_enumerate`, and `in_membership_iterable` to the native path
   - 2026-04-03: Added `set.add`, `dict.keys/values`, and `bytearray[...] = ...` to the subset native renderer, moving `set_mutation_methods`, `dict_wrapper_methods`, and `bytearray_basic` to the native path
   - 2026-04-03: Added `set.discard/remove` and builtin `set()` to the subset native renderer, moving `set_wrapper_methods` and `nested_types` to the native path
   - 2026-04-03: Added `dict.items()` and `list.extend()` to the subset native renderer, moving `typed_container_access` to the native path
   - 2026-04-03: Confirmed that `object_container_access` reaches native path / parity PASS via a combination of existing subset features (`dict.items/get`, `list.extend`, tuple-in-set, union container access)
   - 2026-04-03: Added property getter / instance method support to the minimal class support in the subset native renderer, moving `property_method_call` to the native path
   - 2026-04-03: Added bitwise `~`, `&`, `|`, `^` to the subset native renderer, moving `bitwise_invert_basic` to the native path
   - 2026-04-03: Added `@staticmethod` class support to the subset native renderer, moving `staticmethod_basic` to the native path
   - 2026-04-04: Added instance field `AugAssign` (`self.field += ...`) to the subset native renderer, moving `class_instance` to the native path
   - 2026-04-04: Fixed bootstrap rewrite to also lift `AnnAssign` static attrs in class bodies to global scope, moving `class_member` to the native path
   - 2026-04-04: Subset native renderer now handles object parameter field updates (`x.v += ...`), moving `alias_arg` to the native path
   - 2026-04-04: Added Julia type mappings for `IsInstance` (`PYTRA_TID_*`, `dict/list/tuple/set/str/int/float/bool`) to the subset native renderer, moving `union_basic`, `union_dict_items`, `isinstance_pod_exact`, and `isinstance_tuple_check` to the native path
   - 2026-04-04: Added type-only `ImportFrom(pytra.std.json)`, `str.isdigit()`, and absorption of `Expr(Name("continue"|"break"))` to the subset native renderer, moving `union_return_errorcheck` and `isinstance_narrowing` to native path / parity PASS
   - 2026-04-04: Added `TypeAlias` no-op and `str.upper()` to the subset native renderer, moving `type_alias_pep695` and `callable_higher_order` to native path / parity PASS
   - 2026-04-04: Aligned `str(...)` / `bool(...)` / `str.isdigit()` in the subset native renderer with Julia runtime helpers (`__pytra_str`, `__pytra_truthy`, `__pytra_str_isdigit`), moving `union_list_mixed` to native path / parity PASS
   - 2026-04-04: Added bit shifts (`<<`, `>>`) to the subset native renderer, moving `starred_call_tuple_basic` to native path / parity PASS
   - 2026-04-04: Subset native renderer now accepts `pytra.enum` import and empty enum classes (`Enum`, `IntEnum`, `IntFlag`), moving `enum_basic`, `intenum_basic`, and `intflag_basic` to native path / parity PASS
   - 2026-04-04: Added tuple/list destructuring assign and nested/subscript target unpack to the subset native renderer, moving `tuple_unpack_variants` to native path / parity PASS
   - 2026-04-04: Added single-generator `ListComp` / `SetComp` / `DictComp` and list concat (`vcat`) to the subset native renderer, moving `ok_list_concat_comp`, `comprehension_dict_set`, and `comprehension_nested` to native path / parity PASS
   - 2026-04-04: Subset native renderer now accepts the linked typed-vararg form (`arg_order` + `vararg_name`), and also absorbs value-less `AnnAssign` and plain `Assign` with `Attribute` target, moving `ok_typed_varargs_representative` to native path / parity PASS
   - 2026-04-04: Added class inheritance (`abstract type + backing struct`), inherited method/property lookup, `super().__init__()` / `super().method()`, builtin `bytes(...)`, `for` over string, bool index, `dict.get(key)`, `type(v).__name__`, and fstring `format_spec` to the subset native renderer, moving `class_inherit_basic`, `inheritance*`, `is_instance`, `isinstance_user_class`, `super_init`, `none_optional`, `negative_index_out_of_range`, `ok_class_inline_method`, `ok_fstring_format_spec`, and `str_for_each` to native path / parity PASS
   - 2026-04-04: Re-ran `runtime_parity_check_fast.py --case-root fixture --targets julia` and confirmed 146/146 PASS. At this point the only non-native remaining cases are frontend blockers: `oop/eo_extern_opaque_basic.py`, `oop/trait_basic.py`, `oop/trait_with_inheritance.py`
   - 2026-04-04: Reduced direct hardcoding of import/runtime module IDs that violated the emitter guide, migrating to use `build_import_alias_map()` / `build_runtime_import_map()` / `should_skip_module()` and `mapping.json`'s `module_native_files` / `module_namespace_exprs`. Removed most `pytra.std.*` / `pytra.utils.*` branches from `subset.py`
   - 2026-04-04: Added `py_assert_*` / `__pytra_exception` to the Julia runtime, and confirmed that `runtime_parity_check_fast.py --case-root fixture --targets julia` continues to maintain 146/146 PASS after the guide compliance changes
2. [x] [ID: P1-JULIA-EMITTER-S2] Create `src/runtime/julia/mapping.json` — define `calls`, `types`, `env.target`, `builtin_prefix`, `implicit_promotions`
   - 2026-04-02: Added `src/runtime/julia/mapping.json` and set up the runtime call/type mapping referenced by the toolchain2 Julia emitter bootstrap
3. [x] [ID: P1-JULIA-EMITTER-S3] Confirm Julia emit success for all fixtures
   - 2026-04-02: Confirmed emit success for 3 representative cases (`core/add`, `control/if_else`, `control/for_range`) using `check_py2x_transpile.py --target julia`
   - 2026-04-03: Sequentially verified from the beginning of `collections` through the first half of `oop` / `signature`, confirming Julia emit success for at least 90+ cases
   - 2026-04-03: Confirmed that `oop/trait_basic.py`, `oop/trait_with_inheritance.py`, `signature/ok_fstring_format_spec.py` fail on the frontend/linker side, not in the Julia emitter
   - 2026-04-03: Restored `control/exception_bare_reraise.py`, `control/exception_propagation_raise_from.py`, `control/exception_propagation_two_frames.py`, `control/exception_user_defined_multi_handler.py` to Julia emit+run parity
4. [x] [ID: P1-JULIA-EMITTER-S4] Align the Julia runtime with toolchain2 emit output
   - 2026-04-03: Added `std/json.jl`, `std/sys.jl`, `std/argparse.jl`, `std/pathlib.jl`, `utils/png.jl` to `src/runtime/julia/`, and enhanced Python-compatible helpers, exceptions, truthiness, and string/bytes/container representations in `py_runtime.jl`
   - 2026-04-03: Reorganized the emitter-side runtime alias/include resolution and aligned `pytra.std` / `pytra.utils` imports with the Julia runtime output for stdlib
5. [x] [ID: P1-JULIA-EMITTER-S5] Pass fixture Julia run parity (`julia`)
   - 2026-04-03: 28 parity cases in `tools/unittest/emit/julia/test_py2julia_smoke.py` PASS (`skipped=1`)
   - 2026-04-03: `runtime_parity_check_fast.py --case-root fixture --targets julia add fib if_else for_range` confirms 4/4 PASS
   - 2026-04-03: 3 of 4 exception cases (`exception_bare_reraise`, `exception_propagation_raise_from`, `exception_propagation_two_frames`) PASS. `exception_user_defined_multi_handler` remains a Julia runtime/class integration issue
   - 2026-04-03: Fixed the exception/custom-exception path; `runtime_parity_check_fast.py --case-root fixture --targets julia --category control` confirms 16/16 PASS
   - 2026-04-03: `runtime_parity_check_fast.py --case-root fixture --targets julia --category core` confirms 22/22 PASS
   - 2026-04-03: `staticmethod_basic` passing. Main remaining issues are concrete class inheritance (`class_inherit_basic`, `inheritance*`, `is_instance`, `super_init`) and trait-related typed varargs
   - 2026-04-03: Aligned Julia class inheritance model to `abstract type + backing struct`, passing `class_inherit_basic`, `inheritance`, `inheritance_polymorphic_dispatch`, `inheritance_virtual_dispatch_multilang`, `is_instance`, `isinstance_user_class`, and `super_init`
   - 2026-04-03: `runtime_parity_check_fast.py --case-root fixture --targets julia --category oop` shows 16 of 19 PASS. Remaining: `trait_basic`, `trait_with_inheritance` (typed `*args` constraint), and `extern_opaque_basic` (Python-side failure)
   - 2026-04-03: Added trait bootstrap, passing `trait_basic` / `trait_with_inheritance`
   - 2026-04-03: Fixed import/include paths and Julia runtime aliases, passing `from_import_symbols`, `from_pytra_std_import_math`, `import_time_from`, `negative_index_out_of_range`, `deque_basic`, `set_mutation_methods`, `set_wrapper_methods`, `property_method_call`, `enum_basic`, `intenum_basic`, `intflag_basic`, and `exception_user_defined_multi_handler`
   - 2026-04-03: Added `utils/png.jl` to the Julia runtime and Python-compatible `__pytra_str` / `__pytra_str_slice`, passing `import_pytra_runtime_png`, `callable_higher_order`, `for_over_string`, `nested_types`, `object_container_access`, `ok_class_inline_method`, `ok_list_concat_comp`, `ok_multi_for_comp`, `str_methods_extended`, `str_repr_containers`, `str_slice`, and `tuple_unpack_variants`
   - 2026-04-03: Restored `ok_fstring_format_spec`, `ok_generator_tuple_target`, `ok_typed_varargs_representative`; `runtime_parity_check_fast.py --case-root fixture --targets julia` confirms 145/145 PASS
6. [x] [ID: P1-JULIA-EMITTER-S6] Pass stdlib Julia parity (`--case-root stdlib`)
   - 2026-04-03: `runtime_parity_check_fast.py --case-root stdlib --targets julia` confirms 16/16 PASS
   - 2026-04-03: Restored `json_indent_optional`, `json_unicode_escape`, `math_path_runtime_ir`, `os_glob_extended`, `pathlib_extended`, `re_extended`, `sys_extended` via Julia runtime / import alias / Path lowering support
7. [x] [ID: P1-JULIA-EMITTER-S7] Pass sample Julia parity (`--case-root sample`)
   - 2026-04-03: `runtime_parity_check_fast.py --case-root sample --targets julia` confirms 18/18 PASS
   - 2026-04-03: Confirmed artifact parity for image-generation samples; all Julia runs complete from `01_mandelbrot` through `18_mini_language_interpreter`

### P2-JULIA-LINT: Resolve emitter hardcode lint violations for Julia

1. [x] [ID: P2-JULIA-LINT-S1] Confirm 0 violations in all categories for `check_emitter_hardcode_lint.py --lang julia`
   - 2026-04-02: Confirmed 0 violations with `python3 tools/check/check_emitter_hardcode_lint.py --lang julia`
