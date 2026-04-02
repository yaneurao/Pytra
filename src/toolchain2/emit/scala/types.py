"""Scala type helpers for toolchain2 emitter."""

from __future__ import annotations


_SCALA_KEYWORDS: set[str] = {
    "abstract", "case", "catch", "class", "def", "do", "else", "enum", "export",
    "extends", "false", "final", "finally", "for", "forSome", "given", "if",
    "implicit", "import", "lazy", "match", "new", "null", "object", "override",
    "package", "private", "protected", "return", "sealed", "super", "then",
    "throw", "trait", "true", "try", "type", "val", "var", "while", "with",
    "yield",
}


def _split_generic_args(text: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    for ch in text:
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        elif ch == "," and depth == 0:
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


def _safe_scala_ident(name: str) -> str:
    chars: list[str] = []
    for ch in name:
        chars.append(ch if (ch.isalnum() or ch == "_") else "_")
    out = "".join(chars) or "_unnamed"
    if out[0].isdigit():
        out = "_" + out
    if out in _SCALA_KEYWORDS:
        out += "_"
    return out


def scala_type(resolved_type: str) -> str:
    if resolved_type in ("Callable", "callable"):
        return "() => Any"
    if resolved_type in ("int", "int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64"):
        return "Long"
    if resolved_type in ("float", "float32", "float64"):
        return "Double"
    if resolved_type == "bool":
        return "Boolean"
    if resolved_type == "str":
        return "String"
    if resolved_type in ("None", "none"):
        return "Unit"
    if resolved_type in ("Any", "Obj", "object", "unknown", "JsonVal"):
        return "Any"
    if resolved_type == "Path":
        return "java.nio.file.Path"
    if resolved_type.startswith("list[") and resolved_type.endswith("]"):
        inner = resolved_type[5:-1]
        return "scala.collection.mutable.ArrayBuffer[" + scala_type(inner) + "]"
    if resolved_type.startswith("set[") and resolved_type.endswith("]"):
        inner = resolved_type[4:-1]
        return "scala.collection.mutable.HashSet[" + scala_type(inner) + "]"
    if resolved_type.startswith("dict[") and resolved_type.endswith("]"):
        parts = _split_generic_args(resolved_type[5:-1])
        if len(parts) == 2:
            return "scala.collection.mutable.LinkedHashMap[" + scala_type(parts[0]) + ", " + scala_type(parts[1]) + "]"
        return "scala.collection.mutable.LinkedHashMap[Any, Any]"
    if resolved_type.startswith("tuple["):
        return "Product"
    if (resolved_type.startswith("callable[") or resolved_type.startswith("Callable[")) and resolved_type.endswith("]"):
        return "() => Any"
    if "|" in resolved_type:
        return "Any"
    return _safe_scala_ident(resolved_type)


def scala_zero_value(resolved_type: str) -> str:
    st = scala_type(resolved_type)
    if st == "Long":
        return "0L"
    if st == "Double":
        return "0.0"
    if st == "Boolean":
        return "false"
    if st == "String":
        return "\"\""
    if st == "Unit":
        return "()"
    return "null"


__all__ = ["scala_type", "scala_zero_value", "_safe_scala_ident", "_split_generic_args"]
