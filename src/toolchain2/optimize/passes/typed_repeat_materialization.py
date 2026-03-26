"""Infer typed materialization for repeat-based list constructions."""

from __future__ import annotations

from pytra.std.json import JsonVal

from toolchain2.optimize.optimizer import East3OptimizerPass, PassContext, PassResult, make_pass_result
from toolchain2.common.types import normalize_type_name


_INT_LIKE_TYPES: set[str] = {
    "int8", "uint8", "int16", "uint16", "int32", "uint32",
    "int64", "uint64", "int",
}

_REPEAT_RESULT_TYPE_HINT_KEY = "repeat_result_type_hint"
_LIST_COMP_RESULT_TYPE_HINT_KEY = "list_comp_result_type_hint"


def _is_unknown_or_any(value: JsonVal) -> bool:
    t = normalize_type_name(value)
    return t == "" or t == "unknown" or t == "Any" or t == "any" or t == "object"


def _is_int_like_type(value: JsonVal) -> bool:
    return normalize_type_name(value) in _INT_LIKE_TYPES


def _list_inner_type(value: JsonVal) -> str:
    t = normalize_type_name(value)
    if not t.startswith("list[") or not t.endswith("]"):
        return ""
    inner = t[5:-1].strip()
    return inner if inner != "" else ""


def _set_hint(node: dict[str, JsonVal], key: str, hint: str) -> int:
    current = normalize_type_name(node.get(key))
    desired = normalize_type_name(hint)
    if desired == "":
        if key in node:
            node.pop(key, None)
            return 1
        return 0
    if current == desired:
        return 0
    node[key] = desired
    return 1


def _effective_expr_type(node: dict[str, JsonVal]) -> str:
    resolved = normalize_type_name(node.get("resolved_type"))
    if not _is_unknown_or_any(resolved):
        return resolved
    hinted = normalize_type_name(node.get(_REPEAT_RESULT_TYPE_HINT_KEY))
    if not _is_unknown_or_any(hinted):
        return hinted
    return resolved


class TypedRepeatMaterializationPass(East3OptimizerPass):
    """Infer concrete element types for [x] * n style list materialization."""

    name: str = "TypedRepeatMaterializationPass"
    min_opt_level: int = 1

    def _infer_repeat_result_type(self, node: dict[str, JsonVal]) -> str:
        if node.get("kind") != "BinOp" or node.get("op") != "Mult":
            return ""
        left_obj = node.get("left")
        right_obj = node.get("right")
        left = left_obj if isinstance(left_obj, dict) else None
        right = right_obj if isinstance(right_obj, dict) else None
        if left is None or right is None:
            return ""
        left_t = normalize_type_name(left.get("resolved_type"))
        right_t = normalize_type_name(right.get("resolved_type"))
        left_inner = _list_inner_type(left_t)
        right_inner = _list_inner_type(right_t)
        if left_inner != "" and _is_int_like_type(right_t):
            return "list[" + left_inner + "]"
        if right_inner != "" and _is_int_like_type(left_t):
            return "list[" + right_inner + "]"
        if left_t == "str" and _is_int_like_type(right_t):
            return "str"
        if right_t == "str" and _is_int_like_type(left_t):
            return "str"
        return ""

    def _rewrite(self, node: JsonVal) -> int:
        changed = 0
        if isinstance(node, list):
            for item in node:
                changed += self._rewrite(item)
            return changed
        if not isinstance(node, dict):
            return 0

        for value in node.values():
            changed += self._rewrite(value)

        if node.get("kind") == "BinOp":
            current_t = normalize_type_name(node.get("resolved_type"))
            if current_t == "" or current_t == "unknown":
                inferred_t = self._infer_repeat_result_type(node)
                if inferred_t != "":
                    changed += _set_hint(node, _REPEAT_RESULT_TYPE_HINT_KEY, inferred_t)
                else:
                    changed += _set_hint(node, _REPEAT_RESULT_TYPE_HINT_KEY, "")
            else:
                changed += _set_hint(node, _REPEAT_RESULT_TYPE_HINT_KEY, "")

        if node.get("kind") == "ListComp":
            current_t = normalize_type_name(node.get("resolved_type"))
            if current_t == "" or current_t == "unknown" or current_t == "list[unknown]":
                elt_obj = node.get("elt")
                elt = elt_obj if isinstance(elt_obj, dict) else None
                if elt is not None:
                    elt_t = _effective_expr_type(elt)
                    if not _is_unknown_or_any(elt_t):
                        changed += _set_hint(node, _LIST_COMP_RESULT_TYPE_HINT_KEY, "list[" + elt_t + "]")
                    else:
                        changed += _set_hint(node, _LIST_COMP_RESULT_TYPE_HINT_KEY, "")
                else:
                    changed += _set_hint(node, _LIST_COMP_RESULT_TYPE_HINT_KEY, "")
            else:
                changed += _set_hint(node, _LIST_COMP_RESULT_TYPE_HINT_KEY, "")
        return changed

    def run(self, east3_doc: dict[str, JsonVal], context: PassContext) -> PassResult:
        _ = context
        change_count = self._rewrite(east3_doc)
        return make_pass_result(changed=change_count > 0, change_count=change_count)
