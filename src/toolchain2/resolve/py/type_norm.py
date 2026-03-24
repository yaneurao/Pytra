"""Type name normalization and type expression construction.

§5 準拠: Any/object 禁止、pytra.std.* のみ使用。
"""

from __future__ import annotations

from pytra.std.json import JsonVal
from toolchain2.common.types import split_generic_types


# Python → EAST2 type name mapping
_TYPE_MAP: dict[str, str] = {
    "int": "int64",
    "float": "float64",
    "byte": "uint8",
    "bool": "bool",
    "str": "str",
    "None": "None",
    "NoneType": "None",
    "int8": "int8",
    "int16": "int16",
    "int32": "int32",
    "int64": "int64",
    "uint8": "uint8",
    "uint16": "uint16",
    "uint32": "uint32",
    "uint64": "uint64",
    "float32": "float32",
    "float64": "float64",
    "Path": "Path",
    "pathlib.Path": "Path",
    "any": "Any",
    "object": "Any",
    "Any": "Any",
    "bytes": "list[uint8]",
    "bytearray": "list[uint8]",
    "complex": "complex128",
}

# Numeric types for promotion
_NUMERIC_TYPES: set[str] = {
    "int8", "int16", "int32", "int64",
    "uint8", "uint16", "uint32", "uint64",
    "float32", "float64",
}

_INT_TYPES: set[str] = {
    "int8", "int16", "int32", "int64",
    "uint8", "uint16", "uint32", "uint64",
}

_FLOAT_TYPES: set[str] = {"float32", "float64"}


def normalize_type(raw: str) -> str:
    """Normalize a Python type annotation to EAST2 canonical form."""
    t: str = raw.strip()
    if t == "":
        return "unknown"

    # Direct mapping
    mapped: str = _TYPE_MAP.get(t, "")
    if mapped != "":
        return mapped

    # Optional[X] → X | None (as string representation)
    if t.startswith("Optional[") and t.endswith("]"):
        inner: str = t[9:-1].strip()
        return normalize_type(inner) + " | None"

    # Generic types: list[X], dict[K,V], set[X], tuple[X,...], deque[X]
    bracket: int = t.find("[")
    if bracket > 0 and t.endswith("]"):
        base: str = t[:bracket].strip()
        inner_str: str = t[bracket + 1:-1]
        # Normalize base
        base_norm: str = base
        if base == "List":
            base_norm = "list"
        elif base == "Dict":
            base_norm = "dict"
        elif base == "Set":
            base_norm = "set"
        elif base == "Tuple":
            base_norm = "tuple"
        elif base == "Deque":
            base_norm = "deque"
        # Normalize inner type args
        args: list[str] = split_generic_types(inner_str)
        norm_args: list[str] = [normalize_type(a) for a in args]
        if len(norm_args) == 1:
            return base_norm + "[" + norm_args[0] + "]"
        return base_norm + "[" + ",".join(norm_args) + "]"

    # Union type: X | Y
    if "|" in t:
        parts: list[str] = t.split("|")
        norm_parts: list[str] = [normalize_type(p.strip()) for p in parts]
        return " | ".join(norm_parts)

    # Unknown type → keep as-is (user-defined class names etc.)
    return t


def make_type_expr(type_str: str) -> dict[str, JsonVal]:
    """Build a TypeExpr JSON from a normalized type string."""
    t: str = type_str.strip()
    if t == "":
        return {"kind": "NamedType", "name": "unknown"}

    # Generic types
    bracket: int = t.find("[")
    if bracket > 0 and t.endswith("]"):
        base: str = t[:bracket]
        inner: str = t[bracket + 1:-1]
        args: list[str] = split_generic_types(inner)
        return {
            "kind": "GenericType",
            "base": base,
            "args": [make_type_expr(a) for a in args],
        }

    # Union type: X | Y
    if " | " in t:
        parts: list[str] = t.split(" | ")
        # Special case: X | None → OptionalType
        non_none: list[str] = [p for p in parts if p != "None"]
        has_none: bool = len(non_none) < len(parts)
        if has_none and len(non_none) == 1:
            return {
                "kind": "OptionalType",
                "inner": make_type_expr(non_none[0]),
            }
        return {
            "kind": "UnionType",
            "types": [make_type_expr(p) for p in parts],
        }

    # Simple named type
    return {"kind": "NamedType", "name": t}


def is_numeric(t: str) -> bool:
    return t in _NUMERIC_TYPES


def is_int_type(t: str) -> bool:
    return t in _INT_TYPES


def is_float_type(t: str) -> bool:
    return t in _FLOAT_TYPES


def extract_base_type(t: str) -> str:
    """Extract base type from generic: 'list[int64]' → 'list'."""
    bracket: int = t.find("[")
    if bracket > 0:
        return t[:bracket]
    return t


def extract_type_args(t: str) -> list[str]:
    """Extract type arguments: 'dict[str, int64]' → ['str', 'int64']."""
    bracket: int = t.find("[")
    if bracket > 0 and t.endswith("]"):
        inner: str = t[bracket + 1:-1]
        return split_generic_types(inner)
    return []
