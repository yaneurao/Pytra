"""Shared link-stage dataclasses.

§5 準拠: Any/object 禁止, pytra.std.* のみ, selfhost 対象。
"""

from __future__ import annotations

from dataclasses import dataclass

from pytra.std.json import JsonVal

from toolchain.compile.jv import jv_is_dict, jv_dict


@dataclass
class LinkedModule:
    """1 module の linked 結果。"""
    module_id: str
    input_path: str
    source_path: str
    is_entry: bool
    east_doc: dict[str, JsonVal]
    module_kind: str  # "user" | "runtime" | "helper"


def linked_module_id(module: LinkedModule) -> str:
    return module.module_id


def linked_module_input_path(module: LinkedModule) -> str:
    return module.input_path


def linked_module_source_path(module: LinkedModule) -> str:
    return module.source_path


def linked_module_is_entry(module: LinkedModule) -> bool:
    return module.is_entry


def linked_module_set_is_entry(module: LinkedModule, is_entry: bool) -> None:
    module.is_entry = is_entry


def linked_module_east_doc(module: LinkedModule) -> dict[str, JsonVal]:
    return module.east_doc


def linked_module_kind(module: LinkedModule) -> str:
    return module.module_kind


def linked_module_mark_non_entry(module: LinkedModule) -> None:
    module.is_entry = False
    meta_val = module.east_doc.get("meta")
    if not jv_is_dict(meta_val):
        return
    meta: dict[str, JsonVal] = jv_dict(meta_val)
    emit_context_val = meta.get("emit_context")
    if not jv_is_dict(emit_context_val):
        return
    emit_context: dict[str, JsonVal] = jv_dict(emit_context_val)
    emit_context["is_entry"] = False
