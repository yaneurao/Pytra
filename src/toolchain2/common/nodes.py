"""EAST expression/statement node constructors (selfhost-safe).

Factory functions for synthesizing common EAST3 expression nodes.
§5.1: Any/object 禁止 — JsonVal のみ使用。
"""

from __future__ import annotations

from pytra.std.json import JsonVal


def const_int_node(value: int) -> dict[str, JsonVal]:
    """Create a constant int64 expression node."""
    return {
        "kind": "Constant",
        "resolved_type": "int64",
        "borrow_kind": "value",
        "casts": [],
        "repr": str(value),
        "value": value,
    }


def const_int_value(expr: JsonVal) -> int | None:
    """Extract int value from a Constant node, or None."""
    if not isinstance(expr, dict):
        return None
    if expr.get("kind") != "Constant":
        return None
    value_val = expr.get("value")
    if isinstance(value_val, int) and not isinstance(value_val, bool):
        return int(value_val)
    return None


def binop_expr(op: str, left: dict[str, JsonVal], right: dict[str, JsonVal]) -> dict[str, JsonVal]:
    """Create a BinOp expression node (resolved_type=int64)."""
    return {
        "kind": "BinOp",
        "op": op,
        "left": left,
        "right": right,
        "resolved_type": "int64",
        "borrow_kind": "value",
        "casts": [],
    }


def compare_expr(op: str, left: dict[str, JsonVal], right: dict[str, JsonVal]) -> dict[str, JsonVal]:
    """Create a Compare expression node (resolved_type=bool)."""
    return {
        "kind": "Compare",
        "left": left,
        "ops": [op],
        "comparators": [right],
        "resolved_type": "bool",
        "borrow_kind": "value",
        "casts": [],
    }


def ifexp_expr(test: dict[str, JsonVal], body: dict[str, JsonVal], orelse: dict[str, JsonVal]) -> dict[str, JsonVal]:
    """Create an IfExp expression node (resolved_type=int64)."""
    return {
        "kind": "IfExp",
        "test": test,
        "body": body,
        "orelse": orelse,
        "resolved_type": "int64",
        "borrow_kind": "value",
        "casts": [],
    }
