# Plan: All-language parity for the typed_container_access fixture (P0-TYPED-CONTAINER)

## Background

Four essential transformation patterns needed for selfhost were missing from fixtures, so `test/fixture/source/py/typing/typed_container_access.py` was added. This verifies that each language's emitter handles them correctly.

## Information Already in EAST3

All 4 patterns have the information the emitter needs in EAST3. No additional EAST work is required.

| Pattern | EAST3 field | What the emitter should do |
|---|---|---|
| **dict.items() tuple unpack** | `target_plan.direct_unpack_names: ["key", "value"]`, `target_type: "tuple[str,int64]"`, `tuple_expanded: true` | Use `direct_unpack_names` and `target_type` to assign types to each variable; expand using `std::get<N>()` for C++ and `.0` / `.1` for Rust |
| **typed dict.get()** | `resolved_type: "int64"`, `yields_dynamic: true`, `semantic_tag: "stdlib.method.get"` | Return type is known from `resolved_type`. `yields_dynamic` also tells whether a downcast is needed |
| **typed list[T][i]** | `Subscript.resolved_type: "str"`, `value.resolved_type: "list[str]"` | Element type is known from `resolved_type`. Simply generate typed `[]` access |
| **str() unnecessary unbox** | `str()`'s `semantic_tag: "cast.str"`, `runtime_call: "py_to_string"`, `resolved_type` of inner arg | If inner arg is already `str`, `py_to_string` is a no-op. `dict[str, object].get()` has `yields_dynamic: true` + `resolved_type: "object"`, so Unbox is needed |

## Fixture Contents

`test/fixture/source/py/typing/typed_container_access.py`:

- `test_dict_items_tuple_unpack()` — key/value expansion for `for key, value in d.items()`
- `test_typed_dict_get()` — concrete-type return values from `dict[str, int].get()` / `dict[str, str].get()`
- `test_typed_list_index()` — element type access for `list[str][0]` / `list[int][-1]`
- `test_str_cast_on_known_str()` — `str()` on str (no-op) / int (cast) / object (unbox)
- `test_dict_keys_values()` — iteration over `dict.keys()` / `dict.values()`

## Implementation

Confirm that the `typed_container_access` fixture passes compile + run parity in each language's emitter. If it fails, fix the emitter (no changes to the source or EAST are required).
