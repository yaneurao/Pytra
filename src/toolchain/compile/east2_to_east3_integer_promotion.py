"""EAST3 integer promotion pass — C++ style promotion rules.

Applies integer promotion to arithmetic operation nodes and iteration
variables so that all downstream emitters receive consistent promoted types:

- int8, uint8, int16, uint16 → int32 (for arithmetic operands and results)
- bytes/bytearray iteration variables → int32 (Python semantics: for v in bytes yields int)

This matches C/C++ integer promotion and ensures correct behavior in
languages without implicit promotion (Julia, Go, Rust, Zig, Swift).
"""

from __future__ import annotations

from typing import Any

_SMALL_INT_TYPES = {"int8", "uint8", "int16", "uint16"}

_ARITHMETIC_OPS = {
    "Add", "Sub", "Mult", "Div", "FloorDiv", "Mod", "Pow",
    "LShift", "RShift", "BitOr", "BitXor", "BitAnd",
}

_UNARY_OPS = {"UAdd", "USub", "Invert"}


def _normalize_type(t: Any) -> str:
    if isinstance(t, str):
        s: str = t
        return s.strip()
    return ""


def _needs_promotion(t: str) -> bool:
    return t in _SMALL_INT_TYPES


def _promoted_type(t: str) -> str:
    """Return the promoted type for a small integer type."""
    if t in _SMALL_INT_TYPES:
        return "int32"
    return t


def _promote_binop_result(left_type: str, right_type: str) -> str:
    """Determine the result type of a binary arithmetic operation after promotion.

    Rules (C++ style):
    - If either operand is a small int, promote to int32
    - If both are >= int32, keep the wider type
    - float types are not affected by integer promotion
    """
    left = _normalize_type(left_type)
    right = _normalize_type(right_type)

    if left == "" or left == "unknown" or right == "" or right == "unknown":
        return ""

    # Float operands → float result (no integer promotion)
    float_types = {"float32", "float64"}
    if left in float_types or right in float_types:
        return ""

    # If either operand needs promotion, result is at least int32
    left_promoted = _promoted_type(left)
    right_promoted = _promoted_type(right)

    # Choose the wider of the two promoted types
    int_rank = {
        "int32": 0, "uint32": 1, "int64": 2, "uint64": 3,
    }
    left_rank = int_rank.get(left_promoted, -1)
    right_rank = int_rank.get(right_promoted, -1)

    if left_rank < 0 and right_rank < 0:
        return ""

    if left_rank >= right_rank:
        return left_promoted
    return right_promoted


def _apply_integer_promotion(node: Any) -> None:
    """Recursively walk EAST3 and apply integer promotion rules."""
    if isinstance(node, list):
        for item in node:
            _apply_integer_promotion(item)
        return
    if not isinstance(node, dict):
        return
    nd: dict[str, Any] = node
    kind = nd.get("kind")

    # Promote BinOp result types
    if kind == "BinOp":
        op = nd.get("op", "")
        if op in _ARITHMETIC_OPS:
            left = nd.get("left")
            right = nd.get("right")
            left_type = _normalize_type(left.get("resolved_type")) if isinstance(left, dict) else ""
            right_type = _normalize_type(right.get("resolved_type")) if isinstance(right, dict) else ""

            promoted = _promote_binop_result(left_type, right_type)
            if promoted != "":
                current = _normalize_type(nd.get("resolved_type"))
                if current == "" or current == "unknown" or _needs_promotion(current):
                    nd["resolved_type"] = promoted

    # Promote UnaryOp result types
    if kind == "UnaryOp":
        op = nd.get("op", "")
        if op in _UNARY_OPS:
            operand = nd.get("operand")
            operand_type = _normalize_type(operand.get("resolved_type")) if isinstance(operand, dict) else ""
            if _needs_promotion(operand_type):
                current = _normalize_type(nd.get("resolved_type"))
                if current == "" or current == "unknown" or _needs_promotion(current):
                    nd["resolved_type"] = _promoted_type(operand_type)

    # Promote ForCore target_plan for bytes/bytearray iteration
    if kind == "ForCore":
        target_plan = nd.get("target_plan")
        if isinstance(target_plan, dict):
            target_type = _normalize_type(target_plan.get("target_type"))
            if target_type == "uint8":
                target_plan["target_type"] = "int32"

    # Recurse into all children
    for value in nd.values():
        if isinstance(value, (dict, list)):
            _apply_integer_promotion(value)


def apply_integer_promotion(module: dict[str, Any]) -> dict[str, Any]:
    """Top-level entry: apply integer promotion to an EAST3 Module.

    Mutates *module* in place and returns it.
    """
    _apply_integer_promotion(module)
    return module
