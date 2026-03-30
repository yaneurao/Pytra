"""Rust type mapping from EAST3 resolved types.

§5 準拠: Any/object 禁止, pytra.std.* のみ, selfhost 対象。

型写像の正本は src/runtime/rs/mapping.json の "types" テーブル。
_FALLBACK_TYPE_MAP はmapping未ロード時のフォールバック専用。
"""

from __future__ import annotations


# Active mapping types dict — set by emitter at emit time via set_mapping_types().
# When set, rs_type() consults this first.
_active_mapping_types: dict[str, str] = {}


def set_mapping_types(types: dict[str, str]) -> None:
    """Set the active mapping types dict from mapping.json."""
    global _active_mapping_types
    _active_mapping_types = types


# Fallback type map — used only when mapping.json types table is not available.
_FALLBACK_TYPE_MAP: dict[str, str] = {}
_FALLBACK_TYPE_MAP["int"] = "i64"
_FALLBACK_TYPE_MAP["int8"] = "i8"
_FALLBACK_TYPE_MAP["int16"] = "i16"
_FALLBACK_TYPE_MAP["int32"] = "i32"
_FALLBACK_TYPE_MAP["int64"] = "i64"
_FALLBACK_TYPE_MAP["uint8"] = "u8"
_FALLBACK_TYPE_MAP["uint16"] = "u16"
_FALLBACK_TYPE_MAP["uint32"] = "u32"
_FALLBACK_TYPE_MAP["uint64"] = "u64"
_FALLBACK_TYPE_MAP["float"] = "f64"
_FALLBACK_TYPE_MAP["float32"] = "f32"
_FALLBACK_TYPE_MAP["float64"] = "f64"
_FALLBACK_TYPE_MAP["bool"] = "bool"
_FALLBACK_TYPE_MAP["str"] = "String"
_FALLBACK_TYPE_MAP["None"] = "()"
_FALLBACK_TYPE_MAP["none"] = "()"
_FALLBACK_TYPE_MAP["bytes"] = "PyList<i64>"
_FALLBACK_TYPE_MAP["bytearray"] = "PyList<i64>"
_FALLBACK_TYPE_MAP["list"] = "PyList<PyAny>"
_FALLBACK_TYPE_MAP["dict"] = "HashMap<String, PyAny>"
_FALLBACK_TYPE_MAP["set"] = "HashSet<String>"
_FALLBACK_TYPE_MAP["tuple"] = "Vec<PyAny>"
_FALLBACK_TYPE_MAP["object"] = "PyAny"
_FALLBACK_TYPE_MAP["Obj"] = "PyAny"
_FALLBACK_TYPE_MAP["Any"] = "PyAny"
_FALLBACK_TYPE_MAP["JsonVal"] = "PyAny"
_FALLBACK_TYPE_MAP["Node"] = "HashMap<String, PyAny>"
_FALLBACK_TYPE_MAP["Callable"] = "Box<dyn Fn()>"
_FALLBACK_TYPE_MAP["callable"] = "Box<dyn Fn()>"
_FALLBACK_TYPE_MAP["deque"] = "VecDeque<PyAny>"
_FALLBACK_TYPE_MAP["Exception"] = "Box<dyn std::error::Error>"
_FALLBACK_TYPE_MAP["BaseException"] = "Box<dyn std::error::Error>"
_FALLBACK_TYPE_MAP["RuntimeError"] = "Box<dyn std::error::Error>"
_FALLBACK_TYPE_MAP["ValueError"] = "Box<dyn std::error::Error>"
_FALLBACK_TYPE_MAP["TypeError"] = "Box<dyn std::error::Error>"
_FALLBACK_TYPE_MAP["IndexError"] = "Box<dyn std::error::Error>"
_FALLBACK_TYPE_MAP["KeyError"] = "Box<dyn std::error::Error>"


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
    is_callable = resolved_type.startswith("callable[")
    if not is_callable:
        is_callable = resolved_type.startswith("Callable[")
    if not is_callable or not resolved_type.endswith("]"):
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


_RS_KEYWORDS: set[str] = set()
for _rs_keyword in [
    "as", "break", "const", "continue", "crate", "else", "enum", "extern",
    "false", "fn", "for", "if", "impl", "in", "let", "loop", "match", "mod",
    "move", "mut", "pub", "ref", "return", "self", "Self", "static", "struct",
    "super", "trait", "true", "type", "unsafe", "use", "where", "while",
    "async", "await", "dyn", "abstract", "become", "box", "do", "final",
    "macro", "override", "priv", "typeof", "unsized", "virtual", "yield",
    "Box", "Vec", "String", "Option", "Result", "HashMap", "HashSet", "VecDeque",
]:
    _RS_KEYWORDS.add(_rs_keyword)


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


def _lookup_type(resolved_type: str) -> str:
    """Look up a direct type mapping from active mapping or fallback."""
    if len(_active_mapping_types) > 0:
        mapped = _active_mapping_types.get(resolved_type, "")
        if mapped != "":
            return mapped
    return _FALLBACK_TYPE_MAP.get(resolved_type, "")


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

    # Direct mapping (mapping.json types table → fallback)
    direct = _lookup_type(resolved_type)
    if direct != "":
        return direct

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

    # deque[T] → VecDeque<T>
    if resolved_type.startswith("deque[") and resolved_type.endswith("]"):
        inner = resolved_type[6:-1]
        return "VecDeque<" + rs_type(inner) + ">"

    # tuple[A, B, ...] → Vec<A> if all args same type, else Vec<Box<dyn Any>>
    if resolved_type.startswith("tuple[") and resolved_type.endswith("]"):
        inner = resolved_type[6:-1]
        parts = _split_generic_args(inner)
        if len(parts) == 1:
            elem_rt = rs_type(parts[0])
            if elem_rt != "Box<dyn std::any::Any>":
                return "Vec<" + elem_rt + ">"
        return "Vec<Box<dyn std::any::Any>>"

    # Optional[T] / T | None → Option<T>
    if resolved_type.endswith(" | None") or resolved_type.endswith("|None"):
        inner = resolved_type[:-7].strip() if resolved_type.endswith(" | None") else resolved_type[:-5].strip()
        rt = rs_type(inner)
        if rt in ("Box<dyn std::any::Any>", "PyAny"):
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
    # Check trait_names first — traits take priority over classes
    if resolved_type in trait_names:
        return "Box<dyn " + safe_rs_ident(resolved_type) + ">"
    if resolved_type in class_names:
        return "Box<" + safe_rs_ident(resolved_type) + ">"
    return rs_type(resolved_type)
