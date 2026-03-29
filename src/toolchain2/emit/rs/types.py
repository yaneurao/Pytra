"""Rust type mapping from EAST3 resolved types.

§5 準拠: Any/object 禁止, pytra.std.* のみ, selfhost 対象。
"""

from __future__ import annotations


# EAST3 resolved_type → Rust type
_TYPE_MAP: dict[str, str] = {
    "int": "i64",
    "int8": "i8",
    "int16": "i16",
    "int32": "i32",
    "int64": "i64",
    "uint8": "u8",
    "uint16": "u16",
    "uint32": "u32",
    "uint64": "u64",
    "float": "f64",
    "float32": "f32",
    "float64": "f64",
    "bool": "bool",
    "str": "String",
    "None": "()",
    "none": "()",
    "bytes": "Vec<u8>",
    "bytearray": "Vec<u8>",
    "list": "PyList<Box<dyn std::any::Any>>",
    "dict": "HashMap<String, Box<dyn std::any::Any>>",
    "set": "HashSet<String>",
    "tuple": "Vec<Box<dyn std::any::Any>>",
    "object": "Box<dyn std::any::Any>",
    "Obj": "Box<dyn std::any::Any>",
    "Any": "Box<dyn std::any::Any>",
    "JsonVal": "Box<dyn std::any::Any>",
    "Node": "HashMap<String, Box<dyn std::any::Any>>",
    "Callable": "Box<dyn Fn()>",
    "callable": "Box<dyn Fn()>",
    "Exception": "Box<dyn std::error::Error>",
    "BaseException": "Box<dyn std::error::Error>",
    "RuntimeError": "Box<dyn std::error::Error>",
    "ValueError": "Box<dyn std::error::Error>",
    "TypeError": "Box<dyn std::error::Error>",
    "IndexError": "Box<dyn std::error::Error>",
    "KeyError": "Box<dyn std::error::Error>",
}


def _split_generic_args(s: str) -> list[str]:
    """Split comma-separated generic type args respecting brackets."""
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for ch in s:
        if ch == "[":
            depth += 1
            current.append(ch)
        elif ch == "]":
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


def _parse_callable_signature(resolved_type: str) -> tuple[list[str], str]:
    if not (
        (resolved_type.startswith("callable[") or resolved_type.startswith("Callable["))
        and resolved_type.endswith("]")
    ):
        return ([], "unknown")
    prefix_len = len("Callable[") if resolved_type.startswith("Callable[") else len("callable[")
    inner = resolved_type[prefix_len:-1].strip()
    if inner == "":
        return ([], "unknown")
    if inner.startswith("["):
        depth = 0
        close_idx = -1
        i = 0
        while i < len(inner):
            ch = inner[i]
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    close_idx = i
                    break
            i += 1
        if close_idx >= 0 and close_idx + 1 < len(inner) and inner[close_idx + 1] == ",":
            params_text = inner[1:close_idx].strip()
            ret_text = inner[close_idx + 2:].strip()
            params: list[str] = []
            if params_text != "":
                params = _split_generic_args(params_text)
            return (params, ret_text if ret_text != "" else "unknown")
    arrow_idx = inner.find("->")
    if arrow_idx >= 0:
        params_text2 = inner[:arrow_idx].strip()
        ret_text2 = inner[arrow_idx + 2:].strip()
        params2: list[str] = []
        if params_text2 != "":
            for part in params_text2.split(","):
                item = part.strip()
                if item != "":
                    params2.append(item)
        return (params2, ret_text2 if ret_text2 != "" else "unknown")
    return ([], inner)


_RS_KEYWORDS: set[str] = {
    "as", "break", "const", "continue", "crate", "else", "enum", "extern",
    "false", "fn", "for", "if", "impl", "in", "let", "loop", "match", "mod",
    "move", "mut", "pub", "ref", "return", "self", "Self", "static", "struct",
    "super", "trait", "true", "type", "unsafe", "use", "where", "while",
    "async", "await", "dyn", "abstract", "become", "box", "do", "final",
    "macro", "override", "priv", "typeof", "unsized", "virtual", "yield",
}


def safe_rs_ident(name: str) -> str:
    """Make a string safe as a Rust identifier."""
    if name == "self":
        return "self"
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
    if out in _RS_KEYWORDS:
        out = "py_" + out
    return out


def rs_type(resolved_type: str) -> str:
    """Convert an EAST3 resolved_type to a Rust type string."""
    if resolved_type == "" or resolved_type == "unknown":
        return "Box<dyn std::any::Any>"

    if (resolved_type.startswith("callable[") or resolved_type.startswith("Callable[")) and resolved_type.endswith("]"):
        params, ret = _parse_callable_signature(resolved_type)
        param_rts = [rs_type(p) for p in params]
        ret_rt = rs_type(ret)
        if ret_rt == "()" or ret_rt == "":
            return "Box<dyn Fn(" + ", ".join(param_rts) + ")>"
        return "Box<dyn Fn(" + ", ".join(param_rts) + ") -> " + ret_rt + ">"

    # Direct mapping
    if resolved_type in _TYPE_MAP:
        return _TYPE_MAP[resolved_type]

    # list[T] → PyList<T>
    if resolved_type.startswith("list[") and resolved_type.endswith("]"):
        inner = resolved_type[5:-1]
        return "PyList<" + rs_type(inner) + ">"

    # dict[K, V] → HashMap<K, V>
    if resolved_type.startswith("dict[") and resolved_type.endswith("]"):
        inner = resolved_type[5:-1]
        parts = _split_generic_args(inner)
        if len(parts) == 2:
            return "HashMap<" + rs_type(parts[0]) + ", " + rs_type(parts[1]) + ">"
        return "HashMap<String, Box<dyn std::any::Any>>"

    # set[T] → HashSet<T>
    if resolved_type.startswith("set[") and resolved_type.endswith("]"):
        inner = resolved_type[4:-1]
        return "HashSet<" + rs_type(inner) + ">"

    # tuple[A, B, ...] → use Vec<Box<dyn Any>> for now
    if resolved_type.startswith("tuple[") and resolved_type.endswith("]"):
        return "Vec<Box<dyn std::any::Any>>"

    # Optional[T] / T | None → Option<T>
    if resolved_type.endswith(" | None") or resolved_type.endswith("|None"):
        inner = resolved_type[:-7].strip() if resolved_type.endswith(" | None") else resolved_type[:-5].strip()
        rt = rs_type(inner)
        if rt == "Box<dyn std::any::Any>":
            return rt
        return "Option<" + rt + ">"

    # Union type (A | B) → Box<dyn Any>
    if "|" in resolved_type:
        parts2 = [p.strip() for p in resolved_type.split("|") if p.strip() != ""]
        if len(parts2) > 1:
            return "Box<dyn std::any::Any>"

    # User class → Box<ClassName> (owned reference via Box for heap allocation)
    return "Box<" + safe_rs_ident(resolved_type) + ">"


def rs_zero_value(resolved_type: str) -> str:
    """Return the Rust default/zero value for a type."""
    rt = rs_type(resolved_type)
    if rt in ("i8", "i16", "i32", "i64", "u8", "u16", "u32", "u64"):
        return "0"
    if rt in ("f32", "f64"):
        return "0.0"
    if rt == "bool":
        return "false"
    if rt == "String":
        return "String::new()"
    if rt == "()":
        return "()"
    if rt.startswith("Option<"):
        return "None"
    if rt.startswith("PyList<"):
        return rt + "::new()"
    if rt.startswith("HashMap<"):
        return rt + "::new()"
    if rt.startswith("HashSet<"):
        return rt + "::new()"
    if rt.startswith("Vec<"):
        return "Vec::new()"
    return "Default::default()"


def rs_signature_type(resolved_type: str, class_names: set[str] = set(), trait_names: set[str] = set()) -> str:
    """Return the Rust type for a function parameter/return type."""
    if resolved_type in class_names:
        return "Box<" + safe_rs_ident(resolved_type) + ">"
    if resolved_type in trait_names:
        return "Box<dyn " + safe_rs_ident(resolved_type) + ">"
    return rs_type(resolved_type)
