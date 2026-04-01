"""C# type helpers for toolchain2 emitter."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from toolchain2.emit.common.code_emitter import RuntimeMapping


_CS_KEYWORDS: set[str] = {
    "abstract", "as", "base", "bool", "break", "byte", "case", "catch",
    "char", "checked", "class", "const", "continue", "decimal", "default",
    "delegate", "do", "double", "else", "enum", "event", "explicit",
    "extern", "false", "finally", "fixed", "float", "for", "foreach",
    "goto", "if", "implicit", "in", "int", "interface", "internal", "is",
    "lock", "long", "namespace", "new", "null", "object", "operator", "out",
    "override", "params", "private", "protected", "public", "readonly", "ref",
    "return", "sbyte", "sealed", "short", "sizeof", "stackalloc", "static",
    "string", "struct", "switch", "this", "throw", "true", "try", "typeof",
    "uint", "ulong", "unchecked", "unsafe", "ushort", "using", "virtual",
    "void", "volatile", "while", "yield", "var", "dynamic",
}

_VALUE_TYPES: set[str] = {
    "sbyte", "byte", "short", "ushort", "int", "uint", "long", "ulong",
    "float", "double", "bool",
}

_TYPE_MAP: dict[str, str] = {
    "int": "long",
    "byte": "byte",
    "int8": "sbyte",
    "uint8": "byte",
    "int16": "short",
    "uint16": "ushort",
    "int32": "int",
    "uint32": "uint",
    "int64": "long",
    "uint64": "ulong",
    "float": "double",
    "float32": "float",
    "float64": "double",
    "bool": "bool",
    "str": "string",
    "None": "void",
    "none": "void",
    "bytes": "List<byte>",
    "bytearray": "List<byte>",
    "list": "List<object>",
    "dict": "Dictionary<string, object>",
    "set": "HashSet<object>",
    "tuple": "object[]",
    "object": "object",
    "Obj": "object",
    "Any": "object",
    "JsonVal": "object",
    "Node": "Dictionary<string, object>",
    "Callable": "Delegate",
    "callable": "Delegate",
    "Exception": "Exception",
    "BaseException": "Exception",
    "RuntimeError": "Exception",
    "ValueError": "Exception",
    "TypeError": "Exception",
    "IndexError": "Exception",
    "KeyError": "Exception",
    "NameError": "Exception",
    "Path": "string",
}

CS_PATH_TYPE_NAME = "Path"
CS_EXCEPTION_BASE_NAME = _TYPE_MAP["Exception"]
CS_PATH_MEMBER_NAMES: set[str] = {"parent", "parents", "name", "suffix", "stem"}
CS_EXCEPTION_TYPE_NAMES: set[str] = {
    name for name, mapped in _TYPE_MAP.items() if mapped == CS_EXCEPTION_BASE_NAME
}
PYTRA_STD_MODULE_PREFIX = ".".join(["pytra", "std"]) + "."
PYTRA_BUILTIN_MODULE_PREFIX = ".".join(["pytra", "built_in"]) + "."
PYTRA_TYPE_ID_PREFIX = "PYTRA" + "_TID_"


def _split_generic_args(text: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    for ch in text:
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


def is_cs_path_type(type_name: str) -> bool:
    return type_name == CS_PATH_TYPE_NAME


def is_cs_exception_type(type_name: str) -> bool:
    return type_name in CS_EXCEPTION_TYPE_NAMES


def is_pytra_type_id_name(name: str) -> bool:
    return name.startswith(PYTRA_TYPE_ID_PREFIX)


def _is_value_type(cs_name: str) -> bool:
    return cs_name in _VALUE_TYPES


def _mapping_lookup(resolved_type: str, mapping: "RuntimeMapping | None") -> str:
    if mapping is None:
        return ""
    return mapping.types.get(resolved_type, "")


def _safe_cs_ident(name: str) -> str:
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
    if out in _CS_KEYWORDS:
        out = out + "_"
    return out


def _callable_signature_parts(resolved_type: str) -> tuple[list[str], str] | None:
    if not resolved_type.startswith("callable[") or not resolved_type.endswith("]"):
        return None
    inner = resolved_type[len("callable["):-1].strip()
    if not inner.startswith("["):
        return None
    close = inner.find("]")
    if close < 0:
        return None
    args_text = inner[1:close].strip()
    ret_text = inner[close + 1:].lstrip(",").strip()
    args = _split_generic_args(args_text) if args_text != "" else []
    return (args, ret_text)


def cs_type(resolved_type: str, *, mapping: "RuntimeMapping | None" = None, for_return: bool = False) -> str:
    if resolved_type == "" or resolved_type == "unknown":
        return "object"
    compact_optional = resolved_type.replace(" ", "")
    if compact_optional.endswith("|None"):
        inner = compact_optional[:-5]
        base = cs_type(inner, mapping=mapping)
        if _is_value_type(base):
            return base + "?"
        return base

    mapped = _mapping_lookup(resolved_type, mapping)
    if mapped != "":
        if mapped == "void" and not for_return:
            return "object"
        return mapped
    if resolved_type in _TYPE_MAP:
        mapped2 = _TYPE_MAP[resolved_type]
        if mapped2 == "void" and not for_return:
            return "object"
        return mapped2

    if resolved_type.startswith("list[") and resolved_type.endswith("]"):
        inner = resolved_type[5:-1].strip()
        return "List<" + cs_type(inner, mapping=mapping) + ">"
    if resolved_type.startswith("set[") and resolved_type.endswith("]"):
        inner2 = resolved_type[4:-1].strip()
        return "HashSet<" + cs_type(inner2, mapping=mapping) + ">"
    if resolved_type.startswith("dict[") and resolved_type.endswith("]"):
        inner3 = resolved_type[5:-1].strip()
        parts = _split_generic_args(inner3)
        if len(parts) == 2:
            return "Dictionary<" + cs_type(parts[0], mapping=mapping) + ", " + cs_type(parts[1], mapping=mapping) + ">"
        return "Dictionary<object, object>"
    if resolved_type.startswith("tuple[") and resolved_type.endswith("]"):
        inner4 = resolved_type[6:-1].strip()
        parts2 = _split_generic_args(inner4)
        if len(parts2) == 0:
            return "object[]"
        rendered = [cs_type(part, mapping=mapping) for part in parts2]
        first = rendered[0]
        all_same = True
        for item in rendered:
            if item != first:
                all_same = False
                break
        if all_same:
            return first + "[]"
        return "object[]"
    callable_parts = _callable_signature_parts(resolved_type)
    if callable_parts is not None:
        arg_types, ret_type = callable_parts
        rendered_args = [cs_type(part, mapping=mapping) for part in arg_types]
        rendered_ret = cs_type(ret_type, mapping=mapping, for_return=True)
        if rendered_ret == "void":
            if len(rendered_args) == 0:
                return "Action"
            return "Action<" + ", ".join(rendered_args) + ">"
        return "Func<" + ", ".join(rendered_args + [rendered_ret]) + ">"
    if "|" in resolved_type:
        return "object"
    return _safe_cs_ident(resolved_type)


def cs_zero_value(resolved_type: str, *, mapping: "RuntimeMapping | None" = None) -> str:
    cs_name = cs_type(resolved_type, mapping=mapping)
    if cs_name in ("sbyte", "byte", "short", "ushort", "int", "uint", "long", "ulong"):
        return "0"
    if cs_name in ("float", "double"):
        return "0.0"
    if cs_name == "bool":
        return "false"
    if cs_name == "string":
        return "\"\""
    return "null"
