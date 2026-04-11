"""JsonVal helpers for EAST2 → EAST3 lowering.

Provides typed access to JSON trees without using Any/object.
§5.1: Any/object 禁止。
§5.3: Python 標準モジュール直接 import 禁止。
§5.6: グローバル可変状態禁止 — CompileContext に閉じ込める。

deep_copy_json と normalize_type_name は toolchain.common から re-export する。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pytra.typing import cast
from pytra.std.json import JsonVal

from toolchain.emit.common.profile_loader import LoweringProfile, load_lowering_profile

# common/ から共有ユーティリティを re-export
from toolchain.common.jv import deep_copy_json as deep_copy_json

# Runtime import contract for existing toolchain2 modules.
# The C++ emitter skips this typing-only alias assignment.
Node = dict[str, JsonVal]


def normalize_type_name(value: JsonVal) -> str:
    """Local selfhost-safe normalize to keep CompileContext methods statically typed."""
    if isinstance(value, str):
        text = value.strip()
        if text != "":
            return text
    return "unknown"


@dataclass
class CompileContext:
    """Lowering 中の可変状態を閉じ込めるコンテキスト (§5.6)。

    グローバル変数の代わりに関数引数で渡す。
    """

    # nominal ADT 宣言テーブル (type_summary.py が参照)
    nominal_adt_table: dict[str, dict[str, JsonVal]] = field(default_factory=dict)

    # legacy compat bridge フラグ (lower.py が参照)
    legacy_compat_bridge: bool = True
    lowering_profile: LoweringProfile = field(default_factory=lambda: load_lowering_profile("core"))
    target_language: str = "core"

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

    tuple_unpack_counter: int = 0
    current_return_type: str = ""
    local_storage_scopes: list[dict[str, str]] = field(default_factory=lambda: [{}])

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
    """JsonVal が str なら返す。それ以外は空文字。"""
    if isinstance(v, str):
        return v
    return ""


def jv_str_or(v: JsonVal, fallback: str) -> str:
    if isinstance(v, str):
        return v
    return fallback


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


def jv_dict(v: JsonVal) -> dict[str, JsonVal]:
    if isinstance(v, dict):
        return v
    return {}


def jv_is_dict(v: JsonVal) -> bool:
    return isinstance(v, dict)


def jv_is_list(v: JsonVal) -> bool:
    return isinstance(v, list)


def nd_kind(node: JsonVal) -> str:
    if not isinstance(node, dict):
        return ""
    return jv_str(cast(dict[str, JsonVal], node).get("kind", ""))


def nd_get_str(node: JsonVal, key: str) -> str:
    if not isinstance(node, dict):
        return ""
    return jv_str(cast(dict[str, JsonVal], node).get(key, ""))


def nd_get_str_or(node: JsonVal, key: str, fallback: str) -> str:
    if not isinstance(node, dict):
        return fallback
    return jv_str_or(cast(dict[str, JsonVal], node).get(key), fallback)


def nd_get_dict(node: JsonVal, key: str) -> dict[str, JsonVal]:
    if not isinstance(node, dict):
        return {}
    return jv_dict(cast(dict[str, JsonVal], node).get(key))


def nd_get_list(node: JsonVal, key: str) -> list[JsonVal]:
    if not isinstance(node, dict):
        return []
    return jv_list(cast(dict[str, JsonVal], node).get(key))


def nd_get_int(node: JsonVal, key: str) -> int:
    if not isinstance(node, dict):
        return 0
    return jv_int(cast(dict[str, JsonVal], node).get(key))


def nd_get_bool(node: JsonVal, key: str) -> bool:
    if not isinstance(node, dict):
        return False
    return jv_bool(cast(dict[str, JsonVal], node).get(key))


def nd_source_span(node: JsonVal) -> JsonVal:
    if not isinstance(node, dict):
        return None
    return cast(dict[str, JsonVal], node).get("source_span")


def nd_repr(node: JsonVal) -> str:
    if not isinstance(node, dict):
        return ""
    return jv_str(cast(dict[str, JsonVal], node).get("repr", ""))
