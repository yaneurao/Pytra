"""Infer typed materialization for repeat-based list constructions."""

from __future__ import annotations

from pytra.std.typing import Any

from pytra.compiler.east_parts.east3_optimizer import East3OptimizerPass
from pytra.compiler.east_parts.east3_optimizer import PassContext
from pytra.compiler.east_parts.east3_optimizer import PassResult


_INT_LIKE_TYPES = {
    "int8",
    "uint8",
    "int16",
    "uint16",
    "int32",
    "uint32",
    "int64",
    "uint64",
    "int",
}


def _normalize_type_name(value: Any) -> str:
    if isinstance(value, str):
        text = value.strip()
        if text != "":
            return text
    return "unknown"


def _is_unknown_or_any(value: Any) -> bool:
    t = _normalize_type_name(value)
    return t in {"", "unknown", "Any", "any", "object"}


def _is_int_like_type(value: Any) -> bool:
    return _normalize_type_name(value) in _INT_LIKE_TYPES


def _list_inner_type(value: Any) -> str:
    t = _normalize_type_name(value)
    if not t.startswith("list[") or not t.endswith("]"):
        return ""
    inner = t[5:-1].strip()
    return inner if inner != "" else ""


class TypedRepeatMaterializationPass(East3OptimizerPass):
    """Infer concrete element types for `[x] * n` style list materialization."""

    name = "TypedRepeatMaterializationPass"
    min_opt_level = 1

    def _infer_repeat_result_type(self, node: dict[str, Any]) -> str:
        if node.get("kind") != "BinOp" or node.get("op") != "Mult":
            return ""
        left_obj = node.get("left")
        right_obj = node.get("right")
        left = left_obj if isinstance(left_obj, dict) else None
        right = right_obj if isinstance(right_obj, dict) else None
        if left is None or right is None:
            return ""
        left_t = _normalize_type_name(left.get("resolved_type"))
        right_t = _normalize_type_name(right.get("resolved_type"))
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

    def _rewrite(self, node: Any) -> int:
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
            current_t = _normalize_type_name(node.get("resolved_type"))
            if current_t in {"", "unknown"}:
                inferred_t = self._infer_repeat_result_type(node)
                if inferred_t != "":
                    node["resolved_type"] = inferred_t
                    changed += 1

        if node.get("kind") == "ListComp":
            current_t = _normalize_type_name(node.get("resolved_type"))
            if current_t in {"", "unknown", "list[unknown]"}:
                elt_obj = node.get("elt")
                elt = elt_obj if isinstance(elt_obj, dict) else None
                if elt is not None:
                    elt_t = _normalize_type_name(elt.get("resolved_type"))
                    if not _is_unknown_or_any(elt_t):
                        node["resolved_type"] = "list[" + elt_t + "]"
                        changed += 1
        return changed

    def run(self, east3_doc: dict[str, object], context: PassContext) -> PassResult:
        _ = context
        change_count = self._rewrite(east3_doc)
        return PassResult(changed=change_count > 0, change_count=change_count)
