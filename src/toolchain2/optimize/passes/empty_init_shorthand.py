"""Annotate safe empty-container initializers for C++ = {}; shorthand."""

from __future__ import annotations

from pytra.std.json import JsonVal

from toolchain2.optimize.optimizer import East3OptimizerPass, PassContext, PassResult, make_pass_result
from toolchain2.optimize.utils import normalize_type_name, split_generic_types

_CPP_EMPTY_INIT_HINT_KEY = "cpp_empty_init_shorthand_v1"


def _is_any_like(type_name: str) -> bool:
    t = normalize_type_name(type_name)
    return t == "" or t == "unknown" or t == "Any" or t == "object"


def _container_kind_from_type(type_name: str) -> str:
    t = normalize_type_name(type_name)
    if t.startswith("list[") and t.endswith("]"):
        return "List"
    if t.startswith("dict[") and t.endswith("]"):
        return "Dict"
    if t.startswith("set[") and t.endswith("]"):
        return "Set"
    return ""


def _safe_container_type(type_name: str, rhs_kind: str) -> bool:
    t = normalize_type_name(type_name)
    if _is_any_like(t) or "|" in t:
        return False
    kind = _container_kind_from_type(t)
    if kind == "" or kind != rhs_kind:
        return False
    if kind == "List":
        elem_parts = split_generic_types(t[5:-1])
        if len(elem_parts) != 1:
            return False
        elem_t = normalize_type_name(elem_parts[0])
        if _is_any_like(elem_t) or "|" in elem_t:
            return False
        return True
    if kind == "Set":
        elem_parts = split_generic_types(t[4:-1])
        if len(elem_parts) != 1:
            return False
        elem_t = normalize_type_name(elem_parts[0])
        if _is_any_like(elem_t) or "|" in elem_t:
            return False
        return True
    if kind == "Dict":
        kv_parts = split_generic_types(t[5:-1])
        if len(kv_parts) != 2:
            return False
        key_t = normalize_type_name(kv_parts[0])
        val_t = normalize_type_name(kv_parts[1])
        if _is_any_like(key_t) or _is_any_like(val_t):
            return False
        if "|" in key_t or "|" in val_t:
            return False
        return True
    return False


def _stmt_target_type(stmt: dict[str, JsonVal]) -> str:
    decl_t = normalize_type_name(stmt.get("decl_type"))
    if decl_t != "unknown":
        return decl_t
    ann_t = normalize_type_name(stmt.get("annotation"))
    if ann_t != "unknown":
        return ann_t
    target_obj = stmt.get("target")
    target = target_obj if isinstance(target_obj, dict) else None
    if target is not None:
        target_t = normalize_type_name(target.get("resolved_type"))
        if target_t != "unknown":
            return target_t
    return "unknown"


def _empty_container_rhs_kind(value_node: dict[str, JsonVal]) -> str:
    kind = normalize_type_name(value_node.get("kind"))
    if kind == "List":
        elems = value_node.get("elements")
        elem_list = elems if isinstance(elems, list) else []
        if len(elem_list) == 0:
            return "List"
        return ""
    if kind == "Dict":
        entries = value_node.get("entries")
        entry_list = entries if isinstance(entries, list) else []
        if len(entry_list) == 0:
            return "Dict"
        return ""
    if kind == "Set":
        elems = value_node.get("elements")
        elem_list = elems if isinstance(elems, list) else []
        if len(elem_list) == 0:
            return "Set"
        return ""
    return ""


class EmptyInitShorthandPass(East3OptimizerPass):
    """Mark empty List/Dict/Set initializers eligible for C++ = {}; shorthand."""

    name: str = "EmptyInitShorthandPass"
    min_opt_level: int = 1

    def _set_hint(self, stmt: dict[str, JsonVal], hint: dict[str, JsonVal] | None) -> int:
        cur_val = stmt.get(_CPP_EMPTY_INIT_HINT_KEY)
        cur = cur_val if isinstance(cur_val, dict) else None
        if hint is None:
            if _CPP_EMPTY_INIT_HINT_KEY in stmt:
                stmt.pop(_CPP_EMPTY_INIT_HINT_KEY, None)
                return 1
            return 0
        if cur == hint:
            return 0
        stmt[_CPP_EMPTY_INIT_HINT_KEY] = hint
        return 1

    def _try_tag_stmt(self, stmt: dict[str, JsonVal]) -> int:
        kind = normalize_type_name(stmt.get("kind"))
        if kind != "Assign" and kind != "AnnAssign":
            return 0
        value_obj = stmt.get("value")
        value = value_obj if isinstance(value_obj, dict) else None
        if value is None:
            return self._set_hint(stmt, None)
        rhs_kind = _empty_container_rhs_kind(value)
        if rhs_kind == "":
            return self._set_hint(stmt, None)
        target_type = _stmt_target_type(stmt)
        if not _safe_container_type(target_type, rhs_kind):
            return self._set_hint(stmt, None)
        hint: dict[str, JsonVal] = {
            "version": "1",
            "target_type": target_type,
            "rhs_kind": rhs_kind,
        }
        return self._set_hint(stmt, hint)

    def _visit(self, node: JsonVal) -> int:
        if isinstance(node, list):
            changed = 0
            for item in node:
                changed += self._visit(item)
            return changed
        if not isinstance(node, dict):
            return 0
        changed = self._try_tag_stmt(node)
        for value in node.values():
            changed += self._visit(value)
        return changed

    def run(self, east3_doc: dict[str, JsonVal], context: PassContext) -> PassResult:
        _ = context
        change_count = self._visit(east3_doc)
        return make_pass_result(changed=change_count > 0, change_count=change_count)
