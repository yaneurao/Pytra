# 計画: typed_container_access fixture の全言語 parity (P0-TYPED-CONTAINER)

## 背景

selfhost で必要な 4 つの基本変換パターンが fixture になかったため、`test/fixture/source/py/typing/typed_container_access.py` を追加した。各言語の emitter がこれらを正しく処理できているかを検証する。

## EAST3 に既にある情報

4 パターン全て、EAST3 には emitter が必要とする情報が載っている。EAST 側の追加作業は不要。

| パターン | EAST3 のフィールド | emitter がやるべきこと |
|---|---|---|
| **dict.items() tuple unpack** | `target_plan.direct_unpack_names: ["key", "value"]`, `target_type: "tuple[str,int64]"`, `tuple_expanded: true` | `direct_unpack_names` と `target_type` を見て各変数に型を割り当て、C++ なら `std::get<N>()` 、Rust なら `.0`/`.1` で展開 |
| **typed dict.get()** | `resolved_type: "int64"`, `yields_dynamic: true`, `semantic_tag: "stdlib.method.get"` | `resolved_type` で戻り値型を知っている。`yields_dynamic` でダウンキャスト要否も判定可能 |
| **typed list[T][i]** | `Subscript.resolved_type: "str"`, `value.resolved_type: "list[str]"` | `resolved_type` から要素型がわかる。型付き `[]` アクセスを生成するだけ |
| **str() 不要 unbox** | `str()` の `semantic_tag: "cast.str"`, `runtime_call: "py_to_string"`, inner arg の `resolved_type` | inner arg が既に `str` なら `py_to_string` は no-op。`dict[str, object].get()` は `yields_dynamic: true` + `resolved_type: "object"` なので Unbox は必要 |

## fixture の内容

`test/fixture/source/py/typing/typed_container_access.py`:

- `test_dict_items_tuple_unpack()` — `for key, value in d.items()` の key/value 展開
- `test_typed_dict_get()` — `dict[str, int].get()` / `dict[str, str].get()` の具体型戻り値
- `test_typed_list_index()` — `list[str][0]` / `list[int][-1]` の要素型アクセス
- `test_str_cast_on_known_str()` — `str()` on str (no-op) / int (cast) / object (unbox)
- `test_dict_keys_values()` — `dict.keys()` / `dict.values()` の iteration

## 実施

各言語の emitter で `typed_container_access` fixture が compile + run parity PASS することを確認する。失敗した場合は emitter を修正する（source や EAST の変更は不要）。
