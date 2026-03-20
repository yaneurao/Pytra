"""Normalize redundant boolean compare forms in C++ IR."""

from __future__ import annotations

from pytra.typing import Any

from toolchain.emit.cpp.optimizer.context import CppOptContext
from toolchain.emit.cpp.optimizer.context import CppOptimizerPass
from toolchain.emit.cpp.optimizer.context import CppOptResult


def _normalize_type_name(value: Any) -> str:
    if isinstance(value, str):
        text = value.strip()
        if text != "":
            return text
    return "unknown"


def _bool_constant(expr: Any) -> bool | None:
    if not isinstance(expr, dict):
        return None
    if expr.get("kind") != "Constant":
        return None
    value = expr.get("value")
    if isinstance(value, bool):
        return value
    return None


def _make_not_expr(operand: dict[str, Any], template_node: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {
        "kind": "UnaryOp",
        "op": "Not",
        "operand": operand,
        "resolved_type": "bool",
        "borrow_kind": "value",
        "casts": [],
    }
    span_obj = template_node.get("source_span")
    if isinstance(span_obj, dict):
        out["source_span"] = span_obj
    return out


def _try_fold_compare(node: dict[str, Any]) -> dict[str, Any] | None:
    if node.get("kind") != "Compare":
        return None
    left_any = node.get("left")
    left = left_any if isinstance(left_any, dict) else None
    if left is None:
        return None
    if _normalize_type_name(left.get("resolved_type")) != "bool":
        return None
    ops_obj = node.get("ops")
    ops = ops_obj if isinstance(ops_obj, list) else []
    cmps_obj = node.get("comparators")
    cmps = cmps_obj if isinstance(cmps_obj, list) else []
    if len(ops) != 1 or len(cmps) != 1:
        return None
    op = ops[0] if isinstance(ops[0], str) else ""
    rhs_bool = _bool_constant(cmps[0])
    if rhs_bool is None:
        return None
    if op == "Eq":
        if rhs_bool:
            return left
        return _make_not_expr(left, node)
    if op == "NotEq":
        if rhs_bool:
            return _make_not_expr(left, node)
        return left
    return None


class CppCompareNormalizePass(CppOptimizerPass):
    """Fold redundant bool compare expressions into direct bool/Not form."""

    name = "CppCompareNormalizePass"
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
        folded = _try_fold_compare(node)
        if folded is not None:
            return folded, changed + 1
        return node, changed

    def run(self, cpp_ir: dict[str, Any], context: CppOptContext) -> CppOptResult:
        _ = context
        _, count = self._rewrite(cpp_ir)
        return CppOptResult(changed=count > 0, change_count=count)
