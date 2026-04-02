"""Nim type mapping from EAST3 resolved types.

selfhost 対象。pytra.std.* のみ import 可。
"""

from __future__ import annotations


# EAST3 resolved_type -> Nim type
_TYPE_MAP: dict[str, str] = {
    "int": "int64",
    "byte": "uint8",
    "int8": "int8",
    "int16": "int16",
    "int32": "int32",
    "int64": "int64",
    "uint8": "uint8",
    "uint16": "uint16",
    "uint32": "uint32",
    "uint64": "uint64",
    "float": "float64",
    "float32": "float32",
    "float64": "float64",
    "bool": "bool",
    "str": "string",
    "None": "void",
    "none": "void",
    "bytes": "seq[uint8]",
    "bytearray": "seq[uint8]",
    "list": "seq[PyObj]",
    "dict": "Table[string, PyObj]",
    "set": "HashSet[PyObj]",
    "tuple": "seq[PyObj]",
    "object": "PyObj",
    "Obj": "PyObj",
    "Any": "PyObj",
    "JsonVal": "PyObj",
    "Callable": "proc",
    "callable": "proc",
    "Exception": "ref CatchableError",
    "BaseException": "ref CatchableError",
    "RuntimeError": "ref ValueError",
    "ValueError": "ref ValueError",
    "TypeError": "ref ValueError",
    "IndexError": "ref IndexDefect",
    "KeyError": "ref KeyError",
    "Path": "PyPath",
}

_NIM_KEYWORDS: set[str] = {
    "addr", "and", "as", "asm",
    "bind", "block", "break",
    "case", "cast", "concept", "const", "continue", "converter",
    "defer", "discard", "distinct", "div", "do",
    "elif", "else", "end", "enum", "except", "export",
    "finally", "for", "from", "func",
    "if", "import", "in", "include", "interface", "is", "isnot", "iterator",
    "let", "macro", "method", "mixin", "mod", "nil", "not", "notin",
    "object", "of", "or", "out",
    "proc", "ptr", "raise", "ref", "return", "result",
    "shl", "shr", "static",
    "template", "try", "tuple", "type",
    "using", "var", "when", "while", "yield",
}


def _safe_nim_ident(name: str) -> str:
    """Make a string safe as a Nim identifier."""
    chars: list[str] = []
    for ch in name:
        if ch.isalnum() or ch == "_":
            chars.append(ch)
        else:
            chars.append("_")
    out = "".join(chars)
    if out == "":
        return "unnamed"
    # Nim identifiers cannot start with underscore in public context;
    # however private identifiers can. Use backtick escaping for keywords.
    if out[0] == "_" or out[0].isdigit():
        out = "v" + out
    if out in _NIM_KEYWORDS:
        out = "`" + out + "`"
    return out


def _split_generic_args(s: str) -> list[str]:
    """Split comma-separated generic type args respecting brackets."""
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for ch in s:
        if ch == "[" or ch == "<":
            depth += 1
            current.append(ch)
        elif ch == "]" or ch == ">":
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


def nim_type(resolved_type: str, *, for_return: bool = False) -> str:
    """Convert an EAST3 resolved_type to a Nim type string."""
    if resolved_type == "" or resolved_type == "unknown":
        return "PyObj"

    # callable[...]
    if resolved_type.startswith("callable[") and resolved_type.endswith("]"):
        inner = resolved_type[9:-1]
        parts = _split_generic_args(inner)
        if len(parts) == 0:
            return "proc()"
        ret_type = nim_type(parts[-1], for_return=True)
        param_parts: list[str] = []
        idx = 0
        while idx < len(parts) - 1:
            param_parts.append("arg" + str(idx) + ": " + nim_type(parts[idx]))
            idx += 1
        if ret_type == "void":
            return "proc(" + ", ".join(param_parts) + ")"
        return "proc(" + ", ".join(param_parts) + "): " + ret_type

    # multi_return[...]
    if resolved_type.startswith("multi_return[") and resolved_type.endswith("]"):
        inner = resolved_type[13:-1]
        parts = _split_generic_args(inner)
        return "(" + ", ".join(nim_type(p) for p in parts) + ")"

    # Direct mapping
    if resolved_type in _TYPE_MAP:
        mapped = _TYPE_MAP[resolved_type]
        if resolved_type == "None" and not for_return:
            return "void"
        return mapped

    # list[T] -> seq[T]
    if resolved_type.startswith("list[") and resolved_type.endswith("]"):
        inner = resolved_type[5:-1]
        return "seq[" + nim_type(inner) + "]"

    # dict[K, V] -> Table[K, V]
    if resolved_type.startswith("dict[") and resolved_type.endswith("]"):
        inner = resolved_type[5:-1]
        parts = _split_generic_args(inner)
        if len(parts) == 2:
            return "Table[" + nim_type(parts[0]) + ", " + nim_type(parts[1]) + "]"
        return "Table[string, PyObj]"

    # set[T] -> HashSet[T]
    if resolved_type.startswith("set[") and resolved_type.endswith("]"):
        inner = resolved_type[4:-1]
        return "HashSet[" + nim_type(inner) + "]"

    # tuple[A, B, ...] -> (A, B, ...)
    if resolved_type.startswith("tuple[") and resolved_type.endswith("]"):
        inner = resolved_type[6:-1]
        parts = _split_generic_args(inner)
        return "(" + ", ".join(nim_type(p) for p in parts) + ")"

    # Optional: T | None -> Option[T] ... but for simplicity in Nim we can use ptr-like nil
    if resolved_type.endswith(" | None") or resolved_type.endswith("|None"):
        inner = resolved_type[:-7] if resolved_type.endswith(" | None") else resolved_type[:-5]
        inner_nim = nim_type(inner)
        # ref types are already nullable in Nim
        if inner_nim.startswith("ref ") or inner_nim.startswith("seq[") or inner_nim == "string" or inner_nim == "PyObj":
            return inner_nim
        return inner_nim

    # Union type
    if "|" in resolved_type:
        parts = [part.strip() for part in resolved_type.split("|") if part.strip() != ""]
        if len(parts) > 1:
            # Nim doesn't have native union types; use PyObj as fallback
            return "PyObj"

    # User class -> ClassName
    return _safe_nim_ident(resolved_type)


def nim_zero_value(resolved_type: str) -> str:
    """Return a Nim zero/default value for a type."""
    nt = nim_type(resolved_type)
    if nt in ("int64", "int32", "int16", "int8", "uint8", "uint16", "uint32", "uint64"):
        return "0"
    if nt in ("float64", "float32"):
        return "0.0"
    if nt == "bool":
        return "false"
    if nt == "string":
        return '""'
    if nt == "void":
        return ""
    return "nil"
