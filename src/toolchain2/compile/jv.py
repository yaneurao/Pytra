"""JsonVal helpers for EAST2 → EAST3 lowering.

Provides typed access to JSON trees without using Any/object.
§5.1: Any/object 禁止。
§5.3: Python 標準モジュール直接 import 禁止。
§5.6: グローバル可変状態禁止 — CompileContext に閉じ込める。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union


# JsonVal 再帰型エイリアス (pytra.std.json.JsonVal と同等)
JsonVal = Union[None, bool, int, float, str, list["JsonVal"], dict[str, "JsonVal"]]

# Node = dict[str, JsonVal]
Node = dict[str, JsonVal]


@dataclass
class CompileContext:
    """Lowering 中の可変状態を閉じ込めるコンテキスト (§5.6)。

    グローバル変数の代わりに関数引数で渡す。
    """

    # nominal ADT 宣言テーブル (type_summary.py が参照)
    nominal_adt_table: dict[str, Node] = field(default_factory=dict)

    # legacy compat bridge フラグ (lower.py が参照)
    legacy_compat_bridge: bool = True

    # passes.py のカウンター
    comp_counter: int = 0
    enum_counter: int = 0
    tte_counter: int = 0
    swap_counter: int = 0

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


def deep_copy_json(val: JsonVal) -> JsonVal:
    """Deep copy a JSON-compatible value (copy.deepcopy の代替)。"""
    if val is None or isinstance(val, bool) or isinstance(val, int) or isinstance(val, float) or isinstance(val, str):
        return val
    if isinstance(val, list):
        return [deep_copy_json(item) for item in val]
    if isinstance(val, dict):
        return {key: deep_copy_json(value) for key, value in val.items()}
    return val


def jv_str(v: JsonVal) -> str:
    """JsonVal が str なら返す。それ以外は空文字。"""
    if isinstance(v, str):
        return v
    return ""


def jv_str_or(v: JsonVal, default: str) -> str:
    if isinstance(v, str):
        return v
    return default


def jv_int(v: JsonVal) -> int:
    if isinstance(v, int) and not isinstance(v, bool):
        return v
    return 0


def jv_bool(v: JsonVal) -> bool:
    if isinstance(v, bool):
        return v
    return False


def jv_list(v: JsonVal) -> list[JsonVal]:
    if isinstance(v, list):
        return v
    return []


def jv_dict(v: JsonVal) -> Node:
    if isinstance(v, dict):
        return v
    return {}


def jv_is_dict(v: JsonVal) -> bool:
    return isinstance(v, dict)


def jv_is_list(v: JsonVal) -> bool:
    return isinstance(v, list)


def nd_kind(node: Node) -> str:
    return jv_str(node.get("kind", ""))


def nd_get_str(node: Node, key: str) -> str:
    return jv_str(node.get(key, ""))


def nd_get_str_or(node: Node, key: str, default: str) -> str:
    return jv_str_or(node.get(key), default)


def nd_get_dict(node: Node, key: str) -> Node:
    return jv_dict(node.get(key))


def nd_get_list(node: Node, key: str) -> list[JsonVal]:
    return jv_list(node.get(key))


def nd_get_int(node: Node, key: str) -> int:
    return jv_int(node.get(key))


def nd_get_bool(node: Node, key: str) -> bool:
    return jv_bool(node.get(key))


def nd_source_span(node: Node) -> JsonVal:
    return node.get("source_span")


def nd_repr(node: Node) -> str:
    return jv_str(node.get("repr", ""))


def normalize_type_name(value: JsonVal) -> str:
    if isinstance(value, str):
        t = value.strip()
        if t != "":
            return t
    return "unknown"
