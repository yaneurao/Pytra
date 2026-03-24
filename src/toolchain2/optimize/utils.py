"""Shared utilities for EAST3 optimizer passes (selfhost-safe)."""

from __future__ import annotations

from pytra.std.json import JsonVal


def normalize_type_name(value: JsonVal) -> str:
    """Normalize a type name string, returning 'unknown' for missing/empty."""
    if isinstance(value, str):
        t = value.strip()
        if t != "":
            return t
    return "unknown"


def is_any_like_type(value: JsonVal) -> bool:
    """Check if a type name is polymorphic/unknown."""
    t = normalize_type_name(value)
    if t == "Any" or t == "any" or t == "object" or t == "unknown" or t == "":
        return True
    if "|" in t:
        parts = t.split("|")
        for p in parts:
            ps = p.strip()
            if ps == "Any" or ps == "any" or ps == "object":
                return True
    return False


def split_generic_types(text: str) -> list[str]:
    """Split comma-separated generic type parameters respecting nesting."""
    out: list[str] = []
    part = ""
    depth = 0
    for ch in text:
        if ch == "<" or ch == "[":
            depth += 1
            part += ch
            continue
        if ch == ">" or ch == "]":
            if depth > 0:
                depth -= 1
            part += ch
            continue
        if ch == "," and depth == 0:
            out.append(part.strip())
            part = ""
            continue
        part += ch
    last = part.strip()
    if last != "":
        out.append(last)
    return out


def deep_copy_json(val: JsonVal) -> JsonVal:
    """Deep copy a JSON-compatible value."""
    if val is None or isinstance(val, bool) or isinstance(val, int) or isinstance(val, float) or isinstance(val, str):
        return val
    if isinstance(val, list):
        return [deep_copy_json(item) for item in val]
    if isinstance(val, dict):
        return {key: deep_copy_json(value) for key, value in val.items()}
    return val


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
    """Create a BinOp expression node."""
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
    """Create a Compare expression node."""
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
    """Create an IfExp expression node."""
    return {
        "kind": "IfExp",
        "test": test,
        "body": body,
        "orelse": orelse,
        "resolved_type": "int64",
        "borrow_kind": "value",
        "casts": [],
    }
