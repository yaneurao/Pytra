<a href="../../ja/language/backend-progress-fixture.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# Fixture parity matrix

> Machine-generated file. Run `python3 tools/gen/gen_backend_progress.py` to update.
> Generated at: 2026-03-30T05:38:09
> [Links](./index.md)

| Icon | Meaning |
|---|---|
| 🟩 | PASS (emit + compile + run + stdout match) |
| 🟥 | FAIL |
| ⬜ | Not run |

| Category | Case | cpp | go | rs | ts |
|---|---|---|---|---|---|
| collections | boolop_value_select | ⬜ | ⬜ | ⬜ | ⬜ |
| collections | comprehension | ⬜ | ⬜ | ⬜ | ⬜ |
| collections | comprehension_dict_set | ⬜ | ⬜ | ⬜ | ⬜ |
| collections | comprehension_filter | ⬜ | ⬜ | ⬜ | ⬜ |
| collections | comprehension_if_chain | ⬜ | ⬜ | ⬜ | ⬜ |
| collections | comprehension_ifexp | ⬜ | ⬜ | ⬜ | ⬜ |
| collections | comprehension_nested | ⬜ | ⬜ | ⬜ | ⬜ |
| collections | comprehension_range_step | ⬜ | ⬜ | ⬜ | ⬜ |
| collections | comprehension_range_step_like | ⬜ | ⬜ | ⬜ | ⬜ |
| collections | deque_basic | ⬜ | ⬜ | ⬜ | ⬜ |
| collections | dict_in | ⬜ | ⬜ | ⬜ | ⬜ |
| collections | dict_wrapper_methods | ⬜ | ⬜ | ⬜ | ⬜ |
| collections | in_membership | ⬜ | ⬜ | ⬜ | ⬜ |
| collections | iterable | ⬜ | ⬜ | ⬜ | ⬜ |
| collections | list_alias_shared_mutation | ⬜ | ⬜ | ⬜ | ⬜ |
| collections | list_repeat | ⬜ | ⬜ | ⬜ | ⬜ |
| collections | negative_index | ⬜ | ⬜ | ⬜ | ⬜ |
| collections | nested_types | ⬜ | ⬜ | ⬜ | ⬜ |
| collections | set_wrapper_methods | ⬜ | ⬜ | ⬜ | ⬜ |
| collections | slice_basic | ⬜ | ⬜ | ⬜ | ⬜ |
| control | exception_bare_reraise | ⬜ | ⬜ | ⬜ | ⬜ |
| control | exception_finally_order | ⬜ | ⬜ | ⬜ | ⬜ |
| control | exception_propagation_raise_from | ⬜ | ⬜ | ⬜ | ⬜ |
| control | exception_propagation_two_frames | ⬜ | ⬜ | ⬜ | ⬜ |
| control | exception_user_defined_multi_handler | ⬜ | ⬜ | ⬜ | ⬜ |
| control | finally | ⬜ | ⬜ | ⬜ | ⬜ |
| control | for_range | ⬜ | ⬜ | ⬜ | ⬜ |
| control | if_else | ⬜ | ⬜ | ⬜ | ⬜ |
| control | ifexp_bool | ⬜ | ⬜ | ⬜ | ⬜ |
| control | ifexp_ternary_regression | ⬜ | ⬜ | ⬜ | ⬜ |
| control | loop | ⬜ | ⬜ | ⬜ | ⬜ |
| control | nested_closure_def | ⬜ | ⬜ | ⬜ | ⬜ |
| control | not | ⬜ | ⬜ | ⬜ | ⬜ |
| control | range_downcount_len_minus1 | ⬜ | ⬜ | ⬜ | ⬜ |
| control | try_raise | ⬜ | ⬜ | ⬜ | ⬜ |
| control | yield_generator_min | ⬜ | ⬜ | ⬜ | ⬜ |
| core | add | ⬜ | ⬜ | ⬜ | ⬜ |
| core | assign | ⬜ | ⬜ | ⬜ | ⬜ |
| core | class_body_pass | ⬜ | ⬜ | ⬜ | ⬜ |
| core | class_tuple_assign | ⬜ | ⬜ | ⬜ | ⬜ |
| core | compare | ⬜ | ⬜ | ⬜ | ⬜ |
| core | default_param | ⬜ | ⬜ | ⬜ | ⬜ |
| core | dict_literal_entries | ⬜ | ⬜ | ⬜ | ⬜ |
| core | fib | ⬜ | ⬜ | ⬜ | ⬜ |
| core | float | ⬜ | ⬜ | ⬜ | ⬜ |
| core | lambda_as_arg | ⬜ | ⬜ | ⬜ | ⬜ |
| core | lambda_basic | ⬜ | ⬜ | ⬜ | ⬜ |
| core | lambda_capture_multiargs | ⬜ | ⬜ | ⬜ | ⬜ |
| core | lambda_ifexp | ⬜ | ⬜ | ⬜ | ⬜ |
| core | lambda_immediate | ⬜ | ⬜ | ⬜ | ⬜ |
| core | lambda_local_state | ⬜ | ⬜ | ⬜ | ⬜ |
| core | nested_call | ⬜ | ⬜ | ⬜ | ⬜ |
| core | obj_attr_space | ⬜ | ⬜ | ⬜ | ⬜ |
| core | pass_through_comment | ⬜ | ⬜ | ⬜ | ⬜ |
| core | str_join_method | ⬜ | ⬜ | ⬜ | ⬜ |
| core | sub_mul | ⬜ | ⬜ | ⬜ | ⬜ |
| core | top_level | ⬜ | ⬜ | ⬜ | ⬜ |
| core | tuple_assign | ⬜ | ⬜ | ⬜ | ⬜ |
| imports | bom_from_import | ⬜ | ⬜ | ⬜ | ⬜ |
| imports | from_import_symbols | ⬜ | ⬜ | ⬜ | ⬜ |
| imports | from_pytra_std_import_math | ⬜ | ⬜ | ⬜ | ⬜ |
| imports | import_math_module | ⬜ | ⬜ | ⬜ | ⬜ |
| imports | import_pytra_runtime_png | ⬜ | ⬜ | ⬜ | ⬜ |
| imports | import_time_from | ⬜ | ⬜ | ⬜ | ⬜ |
| imports | type_ignore_from_import | ⬜ | ⬜ | ⬜ | ⬜ |
| oop | alias_arg | ⬜ | ⬜ | ⬜ | ⬜ |
| oop | class | ⬜ | ⬜ | ⬜ | ⬜ |
| oop | class_inherit_basic | ⬜ | ⬜ | ⬜ | ⬜ |
| oop | class_instance | ⬜ | ⬜ | ⬜ | ⬜ |
| oop | class_member | ⬜ | ⬜ | ⬜ | ⬜ |
| oop | dataclass | ⬜ | ⬜ | ⬜ | ⬜ |
| oop | gc_reassign | ⬜ | ⬜ | ⬜ | ⬜ |
| oop | inheritance | ⬜ | ⬜ | ⬜ | ⬜ |
| oop | inheritance_polymorphic_dispatch | ⬜ | ⬜ | ⬜ | ⬜ |
| oop | inheritance_virtual_dispatch_multilang | ⬜ | ⬜ | ⬜ | ⬜ |
| oop | instance_member | ⬜ | ⬜ | ⬜ | ⬜ |
| oop | is_instance | ⬜ | ⬜ | ⬜ | ⬜ |
| oop | isinstance_user_class | ⬜ | ⬜ | ⬜ | ⬜ |
| oop | stateless_value | ⬜ | ⬜ | ⬜ | ⬜ |
| oop | staticmethod_basic | ⬜ | ⬜ | ⬜ | ⬜ |
| oop | super_init | ⬜ | ⬜ | ⬜ | ⬜ |
| oop | trait_basic | ⬜ | ⬜ | ⬜ | ⬜ |
| oop | trait_with_inheritance | ⬜ | ⬜ | ⬜ | ⬜ |
| signature | ok_class_inline_method | ⬜ | ⬜ | ⬜ | ⬜ |
| signature | ok_fstring_format_spec | ⬜ | ⬜ | ⬜ | ⬜ |
| signature | ok_generator_tuple_target | ⬜ | ⬜ | ⬜ | ⬜ |
| signature | ok_kwonly | ⬜ | ⬜ | ⬜ | ⬜ |
| signature | ok_lambda_default | ⬜ | ⬜ | ⬜ | ⬜ |
| signature | ok_list_concat_comp | ⬜ | ⬜ | ⬜ | ⬜ |
| signature | ok_multi_for_comp | ⬜ | ⬜ | ⬜ | ⬜ |
| signature | ok_top_level_for | ⬜ | ⬜ | ⬜ | ⬜ |
| signature | ok_top_level_if_import | ⬜ | ⬜ | ⬜ | ⬜ |
| signature | ok_top_level_tuple_assign | ⬜ | ⬜ | ⬜ | ⬜ |
| signature | ok_tuple_of_list_comp | ⬜ | ⬜ | ⬜ | ⬜ |
| signature | ok_typed_varargs_representative | ⬜ | ⬜ | ⬜ | ⬜ |
| signature | ok_untyped_param | ⬜ | ⬜ | ⬜ | ⬜ |
| stdlib | argparse_extended | ⬜ | ⬜ | ⬜ | ⬜ |
| stdlib | dataclasses_extended | ⬜ | ⬜ | ⬜ | ⬜ |
| stdlib | enum_extended | ⬜ | ⬜ | ⬜ | ⬜ |
| stdlib | json_extended | ⬜ | ⬜ | ⬜ | ⬜ |
| stdlib | json_indent_optional | ⬜ | ⬜ | ⬜ | ⬜ |
| stdlib | json_unicode_escape | ⬜ | ⬜ | ⬜ | ⬜ |
| stdlib | math_extended | ⬜ | ⬜ | ⬜ | ⬜ |
| stdlib | math_path_runtime_ir | ⬜ | ⬜ | ⬜ | ⬜ |
| stdlib | os_glob_extended | ⬜ | ⬜ | ⬜ | ⬜ |
| stdlib | path_stringify | ⬜ | ⬜ | ⬜ | ⬜ |
| stdlib | pathlib_extended | ⬜ | ⬜ | ⬜ | ⬜ |
| stdlib | pytra_runtime_png | ⬜ | ⬜ | ⬜ | ⬜ |
| stdlib | pytra_std_import_math | ⬜ | ⬜ | ⬜ | ⬜ |
| stdlib | re_extended | ⬜ | ⬜ | ⬜ | ⬜ |
| stdlib | sys_extended | ⬜ | ⬜ | ⬜ | ⬜ |
| stdlib | typing_extended | ⬜ | ⬜ | ⬜ | ⬜ |
| strings | enumerate_basic | ⬜ | ⬜ | ⬜ | ⬜ |
| strings | for_over_string | ⬜ | ⬜ | ⬜ | ⬜ |
| strings | fstring | ⬜ | ⬜ | ⬜ | ⬜ |
| strings | fstring_format_spec | ⬜ | ⬜ | ⬜ | ⬜ |
| strings | fstring_prefix | ⬜ | ⬜ | ⬜ | ⬜ |
| strings | reversed_enumerate | ⬜ | ⬜ | ⬜ | ⬜ |
| strings | str_for_each | ⬜ | ⬜ | ⬜ | ⬜ |
| strings | str_index_char_compare | ⬜ | ⬜ | ⬜ | ⬜ |
| strings | str_methods | ⬜ | ⬜ | ⬜ | ⬜ |
| strings | str_slice | ⬜ | ⬜ | ⬜ | ⬜ |
| strings | string | ⬜ | ⬜ | ⬜ | ⬜ |
| strings | string_ops | ⬜ | ⬜ | ⬜ | ⬜ |
| typing | any_basic | ⬜ | ⬜ | ⬜ | ⬜ |
| typing | any_dict_items | ⬜ | ⬜ | ⬜ | ⬜ |
| typing | any_list_mixed | ⬜ | ⬜ | ⬜ | ⬜ |
| typing | any_none | ⬜ | ⬜ | ⬜ | ⬜ |
| typing | bitwise_invert_basic | ⬜ | ⬜ | ⬜ | ⬜ |
| typing | bytearray_basic | ⬜ | ⬜ | ⬜ | ⬜ |
| typing | bytes_basic | ⬜ | ⬜ | ⬜ | ⬜ |
| typing | bytes_truthiness | ⬜ | ⬜ | ⬜ | ⬜ |
| typing | enum_basic | ⬜ | ⬜ | ⬜ | ⬜ |
| typing | ifexp_optional_inference | ⬜ | ⬜ | ⬜ | ⬜ |
| typing | int8 | ⬜ | ⬜ | ⬜ | ⬜ |
| typing | intenum_basic | ⬜ | ⬜ | ⬜ | ⬜ |
| typing | intflag_basic | ⬜ | ⬜ | ⬜ | ⬜ |
| typing | isinstance_narrowing | ⬜ | ⬜ | ⬜ | ⬜ |
| typing | isinstance_pod_exact | ⬜ | ⬜ | ⬜ | ⬜ |
| typing | isinstance_tuple_check | ⬜ | ⬜ | ⬜ | ⬜ |
| typing | list_bool_index | ⬜ | ⬜ | ⬜ | ⬜ |
| typing | none_optional | ⬜ | ⬜ | ⬜ | ⬜ |
| typing | property_method_call | ⬜ | ⬜ | ⬜ | ⬜ |
| typing | starred_call_tuple_basic | ⬜ | ⬜ | ⬜ | ⬜ |
| typing | type_alias_pep695 | ⬜ | ⬜ | ⬜ | ⬜ |
| typing | union_return_errorcheck | ⬜ | ⬜ | ⬜ | ⬜ |
| | **Total** | — | — | — | — |
