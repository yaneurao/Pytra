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
    "object": "object",
    "Any": "Any",
    "bytes": "bytes",
    "bytearray": "bytearray",
    "complex": "complex128",
}

_TYPING_ALIASES: dict[str, str] = {
    "typing.List": "List",
    "typing.Dict": "Dict",
    "typing.Set": "Set",
    "typing.Tuple": "Tuple",
    "typing.Deque": "Deque",
    "typing.Optional": "Optional",
    "typing.Union": "Union",
    "typing.Any": "Any",
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


def _strip_outer_quotes(t: str) -> str:
    result: str = t
    while len(result) >= 2:
        if (result[0] == '"' and result[-1] == '"') or (result[0] == "'" and result[-1] == "'"):
            result = result[1:-1].strip()
            continue
        break
    return result


def _normalize_typing_alias(name: str) -> str:
    alias: str = _TYPING_ALIASES.get(name, "")
    if alias != "":
        return alias
    return name


def _split_top_level_union(t: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    depth: int = 0
    for ch in t:
        if ch == "[":
            depth += 1
        elif ch == "]" and depth > 0:
            depth -= 1
        if ch == "|" and depth == 0:
            part: str = "".join(current).strip()
            if part != "":
                parts.append(part)
            current = []
            continue
        current.append(ch)
    tail: str = "".join(current).strip()
    if tail != "":
        parts.append(tail)
    return parts


def normalize_type(raw: str, aliases: dict[str, str] | None = None, _seen: set[str] | None = None) -> str:
    """Normalize a Python type annotation to EAST2 canonical form."""
    t: str = _strip_outer_quotes(raw.strip())
    if t == "":
        return "unknown"
    t = _normalize_typing_alias(t)
    alias_map: dict[str, str] = aliases if aliases is not None else {}
    seen: set[str] = _seen if _seen is not None else set()

    alias_target: str = alias_map.get(t, "")
    if alias_target != "":
        if t in seen:
            return "Any"
        next_seen: set[str] = set(seen)
        next_seen.add(t)
        return normalize_type(alias_target, alias_map, next_seen)

    # Direct mapping
    mapped: str = _TYPE_MAP.get(t, "")
    if mapped != "":
        return mapped

    # Optional[X] → X | None (as string representation)
    if t.startswith("Optional[") and t.endswith("]"):
        inner: str = t[9:-1].strip()
        return normalize_type(inner, alias_map, seen) + " | None"

    # Union[X, Y] → X | Y
    if t.startswith("Union[") and t.endswith("]"):
        union_inner: str = t[6:-1].strip()
        union_args: list[str] = split_generic_types(union_inner)
        return " | ".join([normalize_type(a, alias_map, seen) for a in union_args])

    # Union type: X | Y (top-level only)
    union_parts: list[str] = _split_top_level_union(t)
    if len(union_parts) > 1:
        norm_parts: list[str] = [normalize_type(p, alias_map, seen) for p in union_parts]
        return " | ".join(norm_parts)

    # Generic types: list[X], dict[K,V], set[X], tuple[X,...], deque[X]
    bracket: int = t.find("[")
    if bracket > 0 and t.endswith("]"):
        base: str = _normalize_typing_alias(t[:bracket].strip())
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
        norm_args: list[str] = [normalize_type(a, alias_map, seen) for a in args]
        if len(norm_args) == 1:
            return base_norm + "[" + norm_args[0] + "]"
        return base_norm + "[" + ",".join(norm_args) + "]"

    # Unknown type → keep as-is (user-defined class names etc.)
    return t


def make_type_expr(type_str: str) -> dict[str, JsonVal]:
    """Build a TypeExpr JSON from a normalized type string."""
    t: str = type_str.strip()
    if t == "":
        return {"kind": "NamedType", "name": "unknown"}

    # Any/object → DynamicType (spec-east2.md §6.3)
    if t == "Any" or t == "object":
        return {"kind": "DynamicType", "name": t}

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
