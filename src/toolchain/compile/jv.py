"""JsonVal helpers for EAST2 -> EAST3 lowering.

Provides typed access to JSON trees without using Any/object.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pytra.std import json
from pytra.std.json import JsonVal

from toolchain.emit.common.profile_loader import LoweringProfile, load_lowering_profile
from toolchain.common.jv import deep_copy_json as deep_copy_json

Node = dict[str, JsonVal]


def normalize_type_name(value: JsonVal) -> str:
    if value is None:
        return "unknown"
    text = str(value).strip()
    if text != "":
        return text
    return "unknown"


@dataclass
class CompileContext:
    nominal_adt_table: dict[str, dict[str, JsonVal]] = field(default_factory=dict)
    legacy_compat_bridge: bool = True
    lowering_profile: LoweringProfile = field(default_factory=lambda: load_lowering_profile("core"))
    target_language: str = "core"
    comp_counter: int = 0
    enum_counter: int = 0
    tte_counter: int = 0
    swap_counter: int = 0
    tuple_unpack_counter: int = 0
    current_return_type: str = ""
    local_storage_scopes: list[dict[str, str]] = field(default_factory=lambda: [{}])

    def next_comp_name(self) -> str:
        self.comp_counter += 1
        return "__comp_" + str(self.comp_counter)

    def next_enum_name(self) -> str:
        self.enum_counter += 1
        return "__enum_idx_" + str(self.enum_counter)

    def next_tte_name(self) -> str:
        self.tte_counter += 1
        return "__iter_tmp_" + str(self.tte_counter)

    def next_swap_name(self) -> str:
        name = "__swap_tmp_" + str(self.swap_counter)
        self.swap_counter += 1
        return name

    def next_tuple_tmp_name(self) -> str:
        self.tuple_unpack_counter += 1
        return "__tup_" + str(self.tuple_unpack_counter)

    def push_storage_scope(self) -> None:
        self.local_storage_scopes.append({})

    def pop_storage_scope(self) -> None:
        if len(self.local_storage_scopes) > 1:
            self.local_storage_scopes.pop()

    def set_storage_type(self, name: str, type_name: str) -> None:
        n = name.strip()
        t = normalize_type_name(type_name)
        if n == "" or t == "" or len(self.local_storage_scopes) == 0:
            return
        self.local_storage_scopes[-1][n] = t

    def lookup_storage_type(self, name: str) -> str:
        n = name.strip()
        if n == "":
            return ""
        i = len(self.local_storage_scopes) - 1
        while i >= 0:
            scope = self.local_storage_scopes[i]
            t = scope.get(n, "")
            if t != "":
                return t
            i -= 1
        return ""


def jv_str(v: JsonVal) -> str:
    value = json.JsonValue(v).as_str()
    if value is None:
        return ""
    return value


def jv_str_or(v: JsonVal, fallback: str) -> str:
    value = json.JsonValue(v).as_str()
    if value is None:
        return fallback
    return value


def jv_int(v: JsonVal) -> int:
    value = json.JsonValue(v).as_int()
    if value is None:
        return 0
    return value


def jv_bool(v: JsonVal) -> bool:
    value = json.JsonValue(v).as_bool()
    if value is None:
        return False
    return value


def jv_is_int(v: JsonVal) -> bool:
    return json.JsonValue(v).as_int() is not None


def jv_is_bool(v: JsonVal) -> bool:
    return json.JsonValue(v).as_bool() is not None


def jv_list(v: JsonVal) -> list[JsonVal]:
    value = json.JsonValue(v).as_arr()
    if value is None:
        return []
    return value.raw


def jv_dict(v: JsonVal) -> dict[str, JsonVal]:
    value = json.JsonValue(v).as_obj()
    if value is None:
        return {}
    return value.raw


def jv_is_dict(v: JsonVal) -> bool:
    return json.JsonValue(v).as_obj() is not None


def jv_is_list(v: JsonVal) -> bool:
    return json.JsonValue(v).as_arr() is not None


def nd_kind(node: JsonVal) -> str:
    return jv_str(jv_dict(node).get("kind", ""))


def nd_get_str(node: JsonVal, key: str) -> str:
    return jv_str(jv_dict(node).get(key, ""))


def nd_get_str_or(node: JsonVal, key: str, fallback: str) -> str:
    return jv_str_or(jv_dict(node).get(key), fallback)


def nd_get_dict(node: JsonVal, key: str) -> dict[str, JsonVal]:
    return jv_dict(jv_dict(node).get(key))


def nd_get_list(node: JsonVal, key: str) -> list[JsonVal]:
    return jv_list(jv_dict(node).get(key))


def nd_get_int(node: JsonVal, key: str) -> int:
    return jv_int(jv_dict(node).get(key))


def nd_get_bool(node: JsonVal, key: str) -> bool:
    return jv_bool(jv_dict(node).get(key))


def nd_source_span(node: JsonVal) -> JsonVal:
    return jv_dict(node).get("source_span")


def nd_repr(node: JsonVal) -> str:
    return jv_str(jv_dict(node).get("repr", ""))
