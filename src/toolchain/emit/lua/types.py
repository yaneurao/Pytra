"""Lua type mapping from EAST3 resolved types."""

from __future__ import annotations

LUA_EXCEPTION_TYPE_NAMES: set[str] = {
    "Exception", "BaseException", "RuntimeError", "ValueError",
    "TypeError", "IndexError", "KeyError", "StopIteration",
    "AttributeError", "NameError", "NotImplementedError",
    "OverflowError", "ZeroDivisionError", "AssertionError",
    "OSError", "IOError", "FileNotFoundError", "PermissionError",
}

LUA_PATH_TYPE_NAMES: set[str] = {"Path"}
LUA_NON_INHERITABLE_BASES: set[str] = {"object"}

LUA_PYTRA_ISINSTANCE_NAME = "pytra_isinstance"


_LUA_KEYWORDS: set[str] = {
    "and", "break", "do", "else", "elseif", "end",
    "false", "for", "function", "goto", "if", "in",
    "local", "nil", "not", "or", "repeat", "return",
    "then", "true", "until", "while",
}


def _safe_lua_ident(name: str) -> str:
    """Make a string safe as a Lua identifier."""
    chars: list[str] = []
    for ch in name:
        if ch.isalnum() or ch == "_":
            chars.append(ch)
        else:
            chars.append("_")
    out = "".join(chars)
    if out == "":
        return "_unnamed"
    if out[0].isdigit():
        out = "_" + out
    if out in _LUA_KEYWORDS:
        out = out + "_"
    return out


def _split_generic_args(s: str) -> list[str]:
    """Split comma-separated generic type args respecting brackets."""
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for ch in s:
        if ch == "<" or ch == "[":
            depth += 1
            current.append(ch)
        elif ch == ">" or ch == "]":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    tail = "".join(current).strip()
    if tail != "":
        parts.append(tail)
    return parts


def _lua_type_map_value(resolved_type: str) -> str:
    if resolved_type in (
        "int", "byte", "int8", "int16", "int32", "int64",
        "uint8", "uint16", "uint32", "uint64",
        "float", "float32", "float64",
    ):
        return "number"
    if resolved_type == "bool":
        return "boolean"
    if resolved_type == "str":
        return "string"
    if resolved_type == "None" or resolved_type == "none":
        return "nil"
    if resolved_type in (
        "bytes", "bytearray", "list", "dict", "set", "tuple", "Node", "Path",
    ):
        return "table"
    if resolved_type == "Callable" or resolved_type == "callable":
        return "function"
    if resolved_type in (
        "Exception", "BaseException", "RuntimeError", "ValueError",
        "TypeError", "IndexError", "KeyError",
    ):
        return "string"
    if resolved_type == "object" or resolved_type == "Obj" or resolved_type == "Any" or resolved_type == "JsonVal":
        return "any"
    return ""


def lua_type(resolved_type: str) -> str:
    """Convert an EAST3 resolved_type to a Lua type comment string."""
    if resolved_type == "" or resolved_type == "unknown":
        return "any"
    mapped = _lua_type_map_value(resolved_type)
    if mapped != "":
        return mapped
    if resolved_type.startswith("list[") or resolved_type.startswith("dict["):
        return "table"
    if resolved_type.startswith("set[") or resolved_type.startswith("tuple["):
        return "table"
    if resolved_type.startswith("callable[") or resolved_type.startswith("Callable["):
        return "function"
    if resolved_type.endswith(" | None") or resolved_type.endswith("|None"):
        return "any"
    if "|" in resolved_type:
        return "any"
    return "any"


def lua_zero_value(resolved_type: str) -> str:
    """Return a Lua zero/default value for a type."""
    lt = lua_type(resolved_type)
    if lt == "number":
        return "0"
    if lt == "boolean":
        return "false"
    if lt == "string":
        return '""'
    return "nil"


def is_numeric_type(resolved_type: str) -> bool:
    """Check if a resolved type is numeric."""
    return resolved_type in (
        "int", "int8", "int16", "int32", "int64",
        "uint8", "uint16", "uint32", "uint64",
        "float", "float32", "float64", "byte",
    )


def is_integer_type(resolved_type: str) -> bool:
    """Check if a resolved type is an integer."""
    return resolved_type in (
        "int", "int8", "int16", "int32", "int64",
        "uint8", "uint16", "uint32", "uint64", "byte",
    )
