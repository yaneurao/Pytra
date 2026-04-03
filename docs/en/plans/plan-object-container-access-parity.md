# Plan: All-language parity for the object_container_access fixture (P0-OBJECT-CONTAINER)

## Background

The existing `typed_container_access` fixture only tested concrete-type containers such as `dict[str, int]` / `list[str]`. Selfhost makes heavy use of `dict[str, object]` / `list[object]`, and the following emitter bugs were exposed:

- `dict[str, object].items()` tuple unpack → collapses to `[N]` instead of `std::get<N>`
- `list[object][i]` → collapses to bare `[]` instead of `py_list_at_ref`
- `dict[str, object].get()` → receiver appears as `Object<void>`
- `.unbox<str>()` is applied to values that are already `str`
- `set[tuple[str, str]]` → compile error due to missing `std::hash`

All of these have information in EAST3. The emitter is not handling `object`-type containers correctly.

## Information available in EAST3

| Pattern | EAST3 field | What the emitter should do |
|---|---|---|
| `dict[str, object].items()` tuple unpack | `target_plan.direct_unpack_names`, `target_type: "tuple[str,object]"`, `tuple_expanded: true` | Expand using `std::get<N>` / `.0` / `.1`. Value has type `object` |
| `list[object][i]` | `Subscript.resolved_type: "object"`, `value.resolved_type: "list[object]"` | Typed access through an Object list. C++ should use `py_list_at_ref` |
| `dict[str, object].get()` | `resolved_type: "object"`, `yields_dynamic: true`, `semantic_tag: "stdlib.method.get"` | Treat receiver as `Object<dict<str, object>>` |
| Unnecessary str unbox | `resolved_type: "str"` matches on both source and destination | Same type → skip unbox |
| `set[tuple[str, str]]` | `resolved_type: "set[tuple[str,str]]"` | C++ needs specialization of `std::hash<std::tuple<str,str>>`. Rust's `HashSet<(String, String)>` works as-is |

## Fixture Contents

`test/fixture/source/py/typing/object_container_access.py`:

- `test_object_dict_items_unpack()` — `dict[str, object]` `.items()` tuple unpack
- `test_object_list_index()` — constant/variable index access on `list[object][i]`
- `test_object_dict_get()` — existing / default access via `dict[str, object].get()`
- `test_str_no_unnecessary_unbox()` — str passthrough / str dict get / str retrieval from object dict
- `test_set_tuple_keys()` — `set[tuple[str, str]]` add / in / len

## Relationship to Existing Fixtures

| Fixture | Container type | Target |
|---|---|---|
| `typed_container_access` | `dict[str, int]`, `list[str]` | Concrete types |
| `object_container_access` | `dict[str, object]`, `list[object]` | Dynamic types (selfhost pattern) |

Having both pass ensures coverage of both concrete and dynamic types.

## Implementation

Confirm that the `object_container_access` fixture passes compile + run parity in each language's emitter. If it fails, fix the emitter (no changes to the source or EAST are required).
