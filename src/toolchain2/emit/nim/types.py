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
    "deque": "seq[int64]",
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
    "JsonValue": "JsonValue",
    "JsonArr": "JsonArr",
    "JsonObj": "JsonObj",
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
    "proc", "ptr", "raise", "ref", "return",
    "shl", "shr", "static",
    "template", "try", "tuple", "type",
    "using", "var", "when", "while", "yield",
}

_NIM_NORMALIZED_RESERVED: set[str] = {
    "parseint",
    "parsefloat",
    "result",  # Nim implicit return variable — rename to v_result to avoid ResultShadowed warning
}

_DYNAMIC_UNION_OPTIONS: set[str] = {
    "Any",
    "Obj",
    "object",
    "unknown",
}

_NILABLE_NOMINAL_TYPES: set[str] = {
    "JsonValue",
    "JsonArr",
    "JsonObj",
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
    while "__" in out:
        out = out.replace("__", "_")
    if out == "":
        return "unnamed"
    while len(out) > 1 and out.endswith("_"):
        out = out[:-1]
    # Nim identifiers cannot start with underscore in public context;
    # however private identifiers can. Use backtick escaping for keywords.
    if out[0] == "_" or out[0].isdigit():
        out = "v" + out
        while len(out) > 1 and out.endswith("_"):
            out = out[:-1]
    normalized = out.replace("_", "").lower()
    if normalized in _NIM_NORMALIZED_RESERVED:
        out = "v_" + out
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


def _is_unionish_type_spec(resolved_type: str) -> bool:
    resolved_type = resolved_type.strip()
    return "|" in resolved_type


def _split_union_options(resolved_type: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for ch in resolved_type:
        if ch == "[" or ch == "<":
            depth += 1
            current.append(ch)
        elif ch == "]" or ch == ">":
            depth -= 1
            current.append(ch)
        elif ch == "|" and depth == 0:
            part = "".join(current).strip()
            if part != "":
                parts.append(part)
            current = []
        else:
            current.append(ch)
    tail = "".join(current).strip()
    if tail != "":
        parts.append(tail)
    return parts


def union_options(resolved_type: str) -> list[str]:
    return _split_union_options(resolved_type.strip("() \t"))


def is_general_union_type(resolved_type: str) -> bool:
    resolved_type = resolved_type.strip("() \t")
    if "|" not in resolved_type:
        return False
    options = union_options(resolved_type)
    if len(options) <= 1:
        return False
    for option in options:
        if option == "None" or option in _DYNAMIC_UNION_OPTIONS:
            return False
    return True


def _union_name_part(type_spec: str) -> str:
    resolved_type = type_spec.strip("() \t")
    if resolved_type in _TYPE_MAP:
        mapped = _TYPE_MAP[resolved_type].replace("[", "_").replace("]", "").replace(", ", "_").replace(",", "_")
        return _safe_nim_ident(mapped)
    if resolved_type.startswith(("list[", "dict[", "set[", "tuple[", "deque[")) and resolved_type.endswith("]"):
        head = resolved_type.split("[", 1)[0]
        inner = resolved_type[len(head) + 1:-1]
        parts = [_union_name_part(p) for p in _split_generic_args(inner)]
        return _safe_nim_ident(head + "_" + "_".join(parts))
    return _safe_nim_ident(resolved_type)


def nim_union_type_name(resolved_type: str) -> str:
    options = union_options(resolved_type)
    parts = [_union_name_part(option) for option in options]
    return "PyUnion_" + "_".join(parts)


def nim_type(resolved_type: str, *, for_return: bool = False) -> str:
    """Convert an EAST3 resolved_type to a Nim type string."""
    resolved_type = resolved_type.strip("() \t")
    if resolved_type.startswith("[") and resolved_type.endswith("]"):
        resolved_type = resolved_type[1:-1].strip()
    if resolved_type == "" or resolved_type == "unknown":
        return "PyObj"

    # callable[...]
    if resolved_type.startswith("callable[") and resolved_type.endswith("]"):
        inner = resolved_type[9:-1]
        if inner.startswith("[],"):
            ret_type = nim_type(inner[3:].strip(), for_return=True)
            if ret_type == "void":
                return "proc()"
            return "proc(): " + ret_type
        if inner == "[]":
            return "proc()"
        parts = _split_generic_args(inner)
        if len(parts) == 0:
            return "proc()"
        ret_type = nim_type(parts[-1], for_return=True)
        param_parts: list[str] = []
        idx = 0
        while idx < len(parts) - 1:
            part = parts[idx]
            if part.startswith("[") and part.endswith("]"):
                subparts = _split_generic_args(part[1:-1])
                for sub in subparts:
                    param_parts.append("arg" + str(len(param_parts)) + ": " + nim_type(sub))
            else:
                param_parts.append("arg" + str(len(param_parts)) + ": " + nim_type(part))
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
        if is_general_union_type(inner):
            return "seq[" + nim_union_type_name(inner) + "]"
        if _is_unionish_type_spec(inner):
            return "seq[PyObj]"
        return "seq[" + nim_type(inner) + "]"

    # dict[K, V] -> Table[K, V]
    if resolved_type.startswith("dict[") and resolved_type.endswith("]"):
        inner = resolved_type[5:-1]
        parts = _split_generic_args(inner)
        if len(parts) == 2:
            key_type = nim_union_type_name(parts[0]) if is_general_union_type(parts[0]) else ("PyObj" if _is_unionish_type_spec(parts[0]) else nim_type(parts[0]))
            value_type = nim_union_type_name(parts[1]) if is_general_union_type(parts[1]) else ("PyObj" if _is_unionish_type_spec(parts[1]) else nim_type(parts[1]))
            return "Table[" + key_type + ", " + value_type + "]"
        return "Table[string, PyObj]"

    # set[T] -> HashSet[T]
    if resolved_type.startswith("set[") and resolved_type.endswith("]"):
        inner = resolved_type[4:-1]
        if is_general_union_type(inner):
            return "HashSet[" + nim_union_type_name(inner) + "]"
        if _is_unionish_type_spec(inner):
            return "HashSet[PyObj]"
        return "HashSet[" + nim_type(inner) + "]"

    # tuple[A, B, ...] -> (A, B, ...)
    if resolved_type.startswith("tuple[") and resolved_type.endswith("]"):
        inner = resolved_type[6:-1]
        parts = _split_generic_args(inner)
        return "(" + ", ".join(nim_type(p) for p in parts) + ")"

    # deque[T] -> seq[T]
    if resolved_type.startswith("deque[") and resolved_type.endswith("]"):
        inner = resolved_type[6:-1]
        if is_general_union_type(inner):
            return "seq[" + nim_union_type_name(inner) + "]"
        if _is_unionish_type_spec(inner):
            return "seq[PyObj]"
        return "seq[" + nim_type(inner) + "]"

    # Optional: T | None -> Option[T] ... but for simplicity in Nim we can use ptr-like nil
    if resolved_type.endswith(" | None") or resolved_type.endswith("|None"):
        inner = resolved_type[:-7] if resolved_type.endswith(" | None") else resolved_type[:-5]
        inner_nim = nim_type(inner)
        # ref types are already nullable in Nim
        if (
            inner_nim.startswith("ref ")
            or inner_nim.startswith("seq[")
            or inner_nim.startswith("proc")
            or inner_nim == "PyObj"
            or inner_nim in _NILABLE_NOMINAL_TYPES
        ):
            return inner_nim
        return "PyObj"

    # Union type
    if "|" in resolved_type:
        parts = union_options(resolved_type)
        if len(parts) > 1:
            if is_general_union_type(resolved_type):
                return nim_union_type_name(resolved_type)
            return "PyObj"

    # User class -> ClassName
    return _safe_nim_ident(resolved_type)


def nim_zero_value(resolved_type: str) -> str:
    """Return a Nim zero/default value for a type."""
    nt = nim_type(resolved_type)
    if nt.startswith("seq["):
        return "newSeq[" + nt[4:-1] + "]()"
    if nt.startswith("Table["):
        return "init" + nt + "()"
    if nt.startswith("HashSet["):
        return "init" + nt + "()"
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
