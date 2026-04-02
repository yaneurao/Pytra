"""PHP type mapping from EAST3 resolved types.

§5 準拠: Any/object 禁止, pytra.std.* のみ, selfhost 対象。
"""

from __future__ import annotations


# EAST3 resolved_type → PHP type
_TYPE_MAP: dict[str, str] = {
    "int": "int",
    "byte": "int",
    "int8": "int",
    "int16": "int",
    "int32": "int",
    "int64": "int",
    "uint8": "int",
    "uint16": "int",
    "uint32": "int",
    "uint64": "int",
    "float": "float",
    "float32": "float",
    "float64": "float",
    "bool": "bool",
    "str": "string",
    "None": "void",
    "none": "void",
    "bytes": "array",
    "bytearray": "array",
    "list": "array",
    "dict": "array",
    "set": "array",
    "tuple": "array",
    "object": "mixed",
    "Obj": "mixed",
    "Any": "mixed",
    "JsonVal": "mixed",
    "Node": "array",
    "Callable": "callable",
    "callable": "callable",
    "Exception": "\\Exception",
    "BaseException": "\\Exception",
    "RuntimeError": "\\RuntimeException",
    "ValueError": "\\InvalidArgumentException",
    "TypeError": "\\TypeError",
    "IndexError": "\\OutOfRangeException",
    "KeyError": "\\OutOfRangeException",
    "Path": "string",
}

_PHP_KEYWORDS: set[str] = {
    "abstract", "and", "array", "as", "break", "callable", "case",
    "catch", "class", "clone", "const", "continue", "declare",
    "default", "do", "echo", "else", "elseif", "empty",
    "enddeclare", "endfor", "endforeach", "endif", "endswitch",
    "endwhile", "eval", "exit", "extends", "final", "finally",
    "fn", "for", "foreach", "function", "global", "goto", "if",
    "implements", "include", "include_once", "instanceof",
    "insteadof", "interface", "isset", "list", "match", "namespace",
    "new", "or", "print", "private", "protected", "public",
    "readonly", "require", "require_once", "return", "static",
    "switch", "throw", "trait", "try", "unset", "use", "var",
    "while", "xor", "yield",
}

_PHP_RESERVED_IDENTIFIERS: set[str] = {
    "ParseError",
    "Serializable",
}


def _safe_php_ident(name: str) -> str:
    """Make a string safe as a PHP identifier (without $ prefix)."""
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
    if out in _PHP_KEYWORDS:
        out = out + "_"
    if out in _PHP_RESERVED_IDENTIFIERS:
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


def php_type(resolved_type: str, *, for_return: bool = False) -> str:
    """Convert an EAST3 resolved_type to a PHP type string."""
    if resolved_type == "" or resolved_type == "unknown":
        return "mixed"

    # Direct mapping
    if resolved_type in _TYPE_MAP:
        mapped = _TYPE_MAP[resolved_type]
        if resolved_type == "None" and not for_return:
            return "null"
        return mapped

    # list[T] → array
    if resolved_type.startswith("list[") and resolved_type.endswith("]"):
        return "array"

    # dict[K, V] → array
    if resolved_type.startswith("dict[") and resolved_type.endswith("]"):
        return "array"

    # set[T] → array
    if resolved_type.startswith("set[") and resolved_type.endswith("]"):
        return "array"

    # tuple[A, B, ...] → array
    if resolved_type.startswith("tuple[") and resolved_type.endswith("]"):
        return "array"

    # callable[...] → callable
    if resolved_type.startswith("callable[") or resolved_type.startswith("Callable["):
        return "callable"

    # Optional: T | None → ?T
    if resolved_type.endswith(" | None") or resolved_type.endswith("|None"):
        inner = resolved_type[:-7] if resolved_type.endswith(" | None") else resolved_type[:-5]
        inner_type = php_type(inner)
        if inner_type == "mixed":
            return "mixed"
        return "?" + inner_type

    # Union type → mixed
    if "|" in resolved_type:
        return "mixed"

    # User class → ClassName
    return _safe_php_ident(resolved_type)


def php_zero_value(resolved_type: str) -> str:
    """Return a PHP zero/default value for a type."""
    pt = php_type(resolved_type)
    if pt == "int":
        return "0"
    if pt == "float":
        return "0.0"
    if pt == "bool":
        return "false"
    if pt == "string":
        return '""'
    if pt == "array":
        return "[]"
    if pt == "void":
        return ""
    return "null"
