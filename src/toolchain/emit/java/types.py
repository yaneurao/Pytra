"""Java type helpers for toolchain2 emitter."""

from __future__ import annotations


_JAVA_KEYWORDS: set[str] = {
    "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char",
    "class", "const", "continue", "default", "do", "double", "else", "enum",
    "extends", "final", "finally", "float", "for", "goto", "if", "implements",
    "import", "instanceof", "int", "interface", "long", "native", "new",
    "package", "private", "protected", "public", "return", "short", "static",
    "strictfp", "super", "switch", "synchronized", "this", "throw", "throws",
    "transient", "try", "void", "volatile", "while",
}

_SAFE_JAVA_IDENT_CACHE: dict[str, str] = {}


def _split_generic_args(text: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    for ch in text:
        if ch == "[":
            depth += 1
            current.append(ch)
            continue
        if ch == "]":
            depth -= 1
            current.append(ch)
            continue
        if ch == "," and depth == 0:
            piece = "".join(current).strip()
            if piece != "":
                parts.append(piece)
            current = []
            continue
        current.append(ch)
    tail = "".join(current).strip()
    if tail != "":
        parts.append(tail)
    return parts


def _safe_java_ident(name: str) -> str:
    cached = _SAFE_JAVA_IDENT_CACHE.get(name, "")
    if cached != "":
        return cached
    chars: list[str] = []
    for ch in name:
        if ch.isalnum() or ch == "_":
            chars.append(ch)
        else:
            chars.append("_")
    out = "".join(chars)
    if out == "":
        out = "_unnamed"
    if out == "_":
        out = "__"
    if out[0].isdigit():
        out = "_" + out
    if out in _JAVA_KEYWORDS:
        out = out + "_"
    _SAFE_JAVA_IDENT_CACHE[name] = out
    return out


def java_module_class_name(module_id: str) -> str:
    if module_id == "":
        return "Main"
    return _safe_java_ident(module_id.replace(".", "_"))


def _java_ref_type(resolved_type: str, type_map: dict[str, str] | None = None) -> str:
    effective_map = type_map if type_map is not None else {}
    if resolved_type in effective_map:
        mapped = effective_map[resolved_type]
        if mapped not in ("long", "double", "boolean"):
            return mapped
    if resolved_type in ("int", "int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64"):
        return "Long"
    if resolved_type in ("float", "float32", "float64"):
        return "Double"
    if resolved_type == "bool":
        return "Boolean"
    if resolved_type == "str":
        return "String"
    if resolved_type in ("Callable", "callable"):
        return "Runnable"
    if resolved_type in ("None", "none", "Any", "Obj", "object", "unknown", "JsonVal"):
        return "Object"
    if resolved_type == "Node":
        return "HashMap<String, Object>"
    if resolved_type == "Path":
        return "pathlib.Path"
    if resolved_type.startswith("list[") and resolved_type.endswith("]"):
        return "ArrayList<" + _java_ref_type(resolved_type[5:-1], type_map) + ">"
    if resolved_type.startswith("set[") and resolved_type.endswith("]"):
        return "HashSet<" + _java_ref_type(resolved_type[4:-1], type_map) + ">"
    if resolved_type.startswith("dict[") and resolved_type.endswith("]"):
        parts = _split_generic_args(resolved_type[5:-1])
        if len(parts) == 2:
            return "HashMap<" + _java_ref_type(parts[0], type_map) + ", " + _java_ref_type(parts[1], type_map) + ">"
        return "HashMap<Object, Object>"
    if resolved_type.startswith("tuple[") and resolved_type.endswith("]"):
        return "ArrayList<Object>"
    if "|" in resolved_type:
        if resolved_type.endswith(" | None"):
            return _java_ref_type(resolved_type[:-7].strip(), type_map)
        return "Object"
    if resolved_type in effective_map:
        return effective_map[resolved_type]
    return _safe_java_ident(resolved_type)


def java_type(resolved_type: str, type_map: dict[str, str] | None = None, *, allow_void: bool = False) -> str:
    effective_map = type_map if type_map is not None else {}
    if resolved_type in effective_map:
        mapped = effective_map[resolved_type]
        if mapped != "void" or allow_void:
            return mapped
        return "Object"
    if resolved_type in ("None", "none"):
        return "void" if allow_void else "Object"
    if resolved_type in ("int", "int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64"):
        return "long"
    if resolved_type in ("float", "float32", "float64"):
        return "double"
    if resolved_type == "bool":
        return "boolean"
    if resolved_type == "str":
        return "String"
    if resolved_type in ("Callable", "callable"):
        return "Runnable"
    if resolved_type in ("Any", "Obj", "object", "unknown", "JsonVal"):
        return "Object"
    if resolved_type == "Node":
        return "HashMap<String, Object>"
    if resolved_type == "Path":
        return "pathlib.Path"
    if (
        resolved_type.startswith("list[")
        or resolved_type.startswith("set[")
        or resolved_type.startswith("dict[")
        or resolved_type.startswith("tuple[")
    ):
        return _java_ref_type(resolved_type, type_map)
    if "|" in resolved_type:
        if resolved_type.endswith(" | None"):
            return _java_ref_type(resolved_type[:-7].strip(), type_map)
        return "Object"
    return _safe_java_ident(resolved_type)


def java_zero_value(resolved_type: str) -> str:
    jt = java_type(resolved_type)
    if jt == "long":
        return "0L"
    if jt == "double":
        return "0.0"
    if jt == "boolean":
        return "false"
    if jt == "String":
        return "\"\""
    return "null"


__all__ = [
    "java_type",
    "java_zero_value",
    "java_module_class_name",
    "_java_ref_type",
    "_safe_java_ident",
    "_split_generic_args",
]
