"""Normalize redundant numeric binop forms in C++ IR."""

from __future__ import annotations

from pytra.typing import Any

from backends.cpp.optimizer.context import CppOptContext
from backends.cpp.optimizer.context import CppOptimizerPass
from backends.cpp.optimizer.context import CppOptResult


_NUMERIC_TYPES = {"int64", "float64", "int32", "uint32", "uint64"}


def _normalize_type_name(value: Any) -> str:
    if isinstance(value, str):
        text = value.strip()
        if text != "":
            return text
    return "unknown"


def _is_numeric_expr(node: Any) -> bool:
    if not isinstance(node, dict):
        return False
    return _normalize_type_name(node.get("resolved_type")) in _NUMERIC_TYPES


def _const_number(node: Any) -> int | float | None:
    if not isinstance(node, dict):
        return None
    if node.get("kind") != "Constant":
        return None
    value = node.get("value")
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    return None


def _try_fold_binop(node: dict[str, Any]) -> dict[str, Any] | None:
    if node.get("kind") != "BinOp":
        return None
    op_any = node.get("op")
    op = op_any if isinstance(op_any, str) else ""
    left_any = node.get("left")
    right_any = node.get("right")
    if not isinstance(left_any, dict) or not isinstance(right_any, dict):
        return None
    left = left_any
    right = right_any
    if not (_is_numeric_expr(left) and _is_numeric_expr(right)):
        return None
    left_num = _const_number(left)
    right_num = _const_number(right)

    if op == "Add":
        if right_num == 0:
            return left
        if left_num == 0:
            return right
    if op == "Sub":
        if right_num == 0:
            return left
    if op == "Mult":
        if right_num == 1:
            return left
        if left_num == 1:
            return right
    return None


class CppBinOpNormalizePass(CppOptimizerPass):
    """Fold safe redundant numeric binop patterns."""

    name = "CppBinOpNormalizePass"
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
        folded = _try_fold_binop(node)
        if folded is not None:
            return folded, changed + 1
        return node, changed

    def run(self, cpp_ir: dict[str, Any], context: CppOptContext) -> CppOptResult:
        _ = context
        _, count = self._rewrite(cpp_ir)
        return CppOptResult(changed=count > 0, change_count=count)
