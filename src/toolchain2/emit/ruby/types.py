"""Ruby type mapping from EAST3 resolved types."""

from __future__ import annotations


# EAST3 resolved_type → Ruby type (used for comments / type annotations where needed)
_TYPE_MAP: dict[str, str] = {
    "int": "Integer",
    "byte": "Integer",
    "int8": "Integer",
    "int16": "Integer",
    "int32": "Integer",
    "int64": "Integer",
    "uint8": "Integer",
    "uint16": "Integer",
    "uint32": "Integer",
    "uint64": "Integer",
    "float": "Float",
    "float32": "Float",
    "float64": "Float",
    "bool": "Boolean",
    "str": "String",
    "None": "nil",
    "none": "nil",
    "bytes": "Array",
    "bytearray": "Array",
    "list": "Array",
    "dict": "Hash",
    "set": "Set",
    "tuple": "Array",
    "object": "Object",
    "Obj": "Object",
    "Any": "Object",
    "JsonVal": "Object",
    "Node": "Hash",
    "Callable": "Proc",
    "callable": "Proc",
    "Exception": "RuntimeError",
    "BaseException": "RuntimeError",
    "RuntimeError": "RuntimeError",
    "ValueError": "ArgumentError",
    "TypeError": "TypeError",
    "IndexError": "IndexError",
    "KeyError": "KeyError",
    "Path": "String",
}

_RUBY_KEYWORDS: set[str] = {
    "BEGIN", "END", "alias", "and", "begin", "break", "case", "class",
    "def", "defined?", "do", "else", "elsif", "end", "ensure", "false",
    "for", "if", "in", "module", "next", "nil", "not", "or", "redo",
    "rescue", "retry", "return", "self", "super", "then", "true",
    "undef", "unless", "until", "when", "while", "yield",
    "__FILE__", "__LINE__", "__ENCODING__",
}


def _safe_ruby_ident(name: str) -> str:
    """Make a string safe as a Ruby identifier."""
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
    if out in _RUBY_KEYWORDS:
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


def ruby_type(resolved_type: str) -> str:
    """Convert an EAST3 resolved_type to a Ruby type comment string."""
    if resolved_type == "" or resolved_type == "unknown":
        return "Object"

    if resolved_type in _TYPE_MAP:
        return _TYPE_MAP[resolved_type]

    if resolved_type.startswith("list[") and resolved_type.endswith("]"):
        return "Array"

    if resolved_type.startswith("dict[") and resolved_type.endswith("]"):
        return "Hash"

    if resolved_type.startswith("set[") and resolved_type.endswith("]"):
        return "Set"

    if resolved_type.startswith("tuple[") and resolved_type.endswith("]"):
        return "Array"

    if resolved_type.endswith(" | None") or resolved_type.endswith("|None"):
        return "Object"

    if "|" in resolved_type:
        return "Object"

    return _safe_ruby_ident(resolved_type)


def ruby_zero_value(resolved_type: str) -> str:
    """Return a Ruby zero/default value for a type."""
    if resolved_type in ("int", "int8", "int16", "int32", "int64",
                         "uint8", "uint16", "uint32", "uint64", "byte"):
        return "0"
    if resolved_type in ("float", "float32", "float64"):
        return "0.0"
    if resolved_type == "bool":
        return "false"
    if resolved_type == "str":
        return '""'
    if resolved_type in ("None", "none"):
        return "nil"
    return "nil"


def ruby_exception_class(resolved_type: str) -> str:
    """Map an EAST3 exception type to a Ruby exception class."""
    mapping: dict[str, str] = {
        "Exception": "RuntimeError",
        "RuntimeError": "RuntimeError",
        "ValueError": "ArgumentError",
        "TypeError": "TypeError",
        "IndexError": "IndexError",
        "KeyError": "KeyError",
        "BaseException": "RuntimeError",
        "ZeroDivisionError": "ZeroDivisionError",
        "FileNotFoundError": "Errno::ENOENT",
        "OverflowError": "RangeError",
        "NotImplementedError": "NotImplementedError",
        "StopIteration": "StopIteration",
        "SystemExit": "SystemExit",
    }
    return mapping.get(resolved_type, "RuntimeError")


def ruby_is_builtin_exception(type_name: str) -> bool:
    """Return True when the type is a builtin exception handled by the runtime mapping."""
    return type_name in {
        "Exception",
        "RuntimeError",
        "ValueError",
        "TypeError",
        "IndexError",
        "KeyError",
        "BaseException",
        "ZeroDivisionError",
        "FileNotFoundError",
        "OverflowError",
        "NotImplementedError",
        "StopIteration",
        "SystemExit",
        "ArithmeticError",
        "LookupError",
        "AttributeError",
        "IOError",
        "OSError",
    }
