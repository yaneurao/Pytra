"""Normalize redundant cast/conversion call chains in C++ IR."""

from __future__ import annotations

from pytra.typing import Any

from backends.cpp.optimizer.context import CppOptContext
from backends.cpp.optimizer.context import CppOptimizerPass
from backends.cpp.optimizer.context import CppOptResult


_RUNTIME_CALL_TO_TYPE: dict[str, str] = {
    "py_to_int64": "int64",
    "py_to_float64": "float64",
    "py_to_bool": "bool",
    "py_to_string": "str",
}


def _normalize_type_name(value: Any) -> str:
    if isinstance(value, str):
        text = value.strip()
        if text != "":
            return text
    return "unknown"


def _runtime_call(node: dict[str, Any]) -> str:
    val = node.get("runtime_call")
    if isinstance(val, str):
        return val
    return ""


def _clone_with_outer_meta(inner_node: dict[str, Any], outer_node: dict[str, Any]) -> dict[str, Any]:
    folded = dict(inner_node)
    repr_obj = outer_node.get("repr")
    if isinstance(repr_obj, str) and repr_obj != "" and not isinstance(folded.get("repr"), str):
        folded["repr"] = repr_obj
    span_obj = outer_node.get("source_span")
    if isinstance(span_obj, dict) and not isinstance(folded.get("source_span"), dict):
        folded["source_span"] = span_obj
    return folded


def _try_fold(node: dict[str, Any]) -> dict[str, Any] | None:
    if node.get("kind") != "Call":
        return None
    runtime = _runtime_call(node)
    args_obj = node.get("args")
    args = args_obj if isinstance(args_obj, list) else []
    if len(args) != 1:
        return None
    arg_any = args[0]
    if not isinstance(arg_any, dict) or arg_any.get("kind") != "Call":
        return None
    inner = arg_any
    inner_runtime = _runtime_call(inner)
    if inner_runtime == "":
        return None

    if runtime in _RUNTIME_CALL_TO_TYPE and runtime == inner_runtime:
        return _clone_with_outer_meta(inner, node)

    if runtime == "static_cast":
        outer_t = _normalize_type_name(node.get("resolved_type"))
        inner_t = _RUNTIME_CALL_TO_TYPE.get(inner_runtime, "")
        if outer_t != "unknown" and inner_t != "" and outer_t == inner_t:
            return _clone_with_outer_meta(inner, node)
    return None


class CppCastCallNormalizePass(CppOptimizerPass):
    """Collapse redundant cast/conversion call nesting."""

    name = "CppCastCallNormalizePass"
    min_opt_level = 1

    def _rewrite(self, node: Any) -> tuple[Any, int]:
        if isinstance(node, list):
            changed = 0
            for i, item in enumerate(node):
                new_item, delta = self._rewrite(item)
                if new_item is not item:
                    node[i] = new_item
                changed += delta
            return node, changed

        if not isinstance(node, dict):
            return node, 0

        changed = 0
        for key in list(node.keys()):
            value = node.get(key)
            new_value, delta = self._rewrite(value)
            if new_value is not value:
                node[key] = new_value
            changed += delta

        folded = _try_fold(node)
        if folded is not None:
            return folded, changed + 1
        return node, changed

    def run(self, cpp_ir: dict[str, Any], context: CppOptContext) -> CppOptResult:
        _ = context
        _, count = self._rewrite(cpp_ir)
        return CppOptResult(changed=count > 0, change_count=count)
