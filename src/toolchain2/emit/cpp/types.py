"""C++ type mapping from EAST3 resolved types.

toolchain2 C++ backend は `src/runtime/cpp/core/*` の公開 alias (`str`,
`list[T]`, `dict[K,V]`, `float64`, `object` など) を正本として使う。

型写像は mapping.json の `types` テーブルを正本とする（P0-CPP-TYPEMAP-S3）。
`init_types_mapping()` で emitter 起動時に注入する。`_TYPE_MAP` は後方互換フォールバック。
"""

from __future__ import annotations

import re


# mapping.json "types" テーブルの注入先。emitter 起動時に init_types_mapping() で設定する。
_g_types: dict[str, str] = {}


def init_types_mapping(types: dict[str, str]) -> None:
    """mapping.json の types テーブルを注入する。emit_module() 呼び出し前に一度だけ呼ぶ。"""
    _g_types.clear()
    for name, mapped in types.items():
        _g_types[name] = mapped


# フォールバック: mapping.json が空の場合に使うハードコード表。
# 正本は src/runtime/cpp/mapping.json の "types" テーブル。
_TYPE_MAP: dict[str, str] = {
    "int": "int64",
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
    "str": "str",
    "PyFile": "pytra::runtime::cpp::base::PyFile",
    "None": "void",
    "none": "void",
    "bytes": "bytes",
    "bytearray": "bytearray",
    "Any": "object",
    "Obj": "object",
    "object": "object",
    "JsonVal": "JsonVal",
    "Node": "Object<dict<str, object>>",
    "Callable": "::std::function<object(object)>",
}


_CPP_ALIAS_UNION_EXPANSIONS: dict[str, str] = {
    "JsonVal": "None | bool | int64 | float64 | str | list[JsonVal] | dict[str,JsonVal]",
}

_JSONVAL_EXPANDED_NORMS: set[str] = {
    "None|bool|int64|float64|str|list[Any]|dict[str,Any]",
    "bool|int64|float64|str|list[Any]|dict[str,Any]|None",
}
_JSONVAL_INNER_EXPANDED_NORM: str = "bool|int64|float64|str|list[Any]|dict[str,Any]"
_JSONVAL_INNER_CANON: str = "bool | int64 | float64 | str | list[JsonVal] | dict[str,JsonVal]"


def _norm_type_text(text: str) -> str:
    return "".join(ch for ch in text if ch != " " and ch != "\n" and ch != "\t")


def normalize_cpp_nominal_adt_type(resolved_type: str) -> str:
    norm = _norm_type_text(resolved_type)
    if norm in _JSONVAL_EXPANDED_NORMS:
        return "JsonVal"
    if norm == _JSONVAL_INNER_EXPANDED_NORM:
        return _JSONVAL_INNER_CANON
    if resolved_type.startswith("list[") and resolved_type.endswith("]"):
        inner = resolved_type[5:-1].strip()
        if _norm_type_text(inner) in _JSONVAL_EXPANDED_NORMS:
            return "list[JsonVal]"
    if resolved_type.startswith("dict[") and resolved_type.endswith("]"):
        inner = resolved_type[5:-1]
        parts = _split_generic_args(inner)
        if len(parts) == 2 and _norm_type_text(parts[0]) == "str" and _norm_type_text(parts[1]) in _JSONVAL_EXPANDED_NORMS:
            return "dict[str,JsonVal]"
    return resolved_type


def cpp_alias_union_expansion(resolved_type: str) -> str:
    normalized = normalize_cpp_nominal_adt_type(resolved_type)
    return _CPP_ALIAS_UNION_EXPANSIONS.get(normalized, "")


def _cpp_variant_lane_type(resolved_type: str) -> str:
    # None is no longer a variant lane — it is handled via std::optional wrapping.
    # This function should not receive "None"; if it does, fall through to cpp_signature_type.
    return cpp_signature_type(resolved_type)


def normalize_cpp_container_alias(resolved_type: str) -> str:
    resolved_type = normalize_cpp_nominal_adt_type(resolved_type)
    if resolved_type == "Node":
        return "dict[str,JsonVal]"
    return resolved_type


def is_container_resolved_type(resolved_type: str) -> bool:
    resolved_type = normalize_cpp_container_alias(resolved_type)
    return (
        resolved_type.startswith("list[")
        or resolved_type.startswith("dict[")
        or resolved_type.startswith("set[")
    )


def cpp_container_value_type(resolved_type: str) -> str:
    resolved_type = normalize_cpp_container_alias(resolved_type)
    if resolved_type.startswith("list[") and resolved_type.endswith("]"):
        inner = resolved_type[5:-1]
        return "list<" + cpp_signature_type(inner) + ">"
    if resolved_type.startswith("dict[") and resolved_type.endswith("]"):
        inner = resolved_type[5:-1]
        parts = _split_generic_args(inner)
        if len(parts) == 2:
            return "dict<" + cpp_signature_type(parts[0]) + ", " + cpp_signature_type(parts[1]) + ">"
    if resolved_type.startswith("set[") and resolved_type.endswith("]"):
        inner = resolved_type[4:-1]
        return "set<" + cpp_signature_type(inner) + ">"
    return ""


def cpp_type(resolved_type: str, *, prefer_value_container: bool = False) -> str:
    """Convert an EAST3 resolved_type to a C++ type string."""
    resolved_type = normalize_cpp_nominal_adt_type(resolved_type)
    if resolved_type == "" or resolved_type == "unknown":
        return "auto"

    # mapping.json "types" テーブルを優先（P0-CPP-TYPEMAP-S3）
    mapped = _g_types.get(resolved_type, "")
    if mapped == "":
        mapped = _TYPE_MAP.get(resolved_type, "")
    if mapped != "":
        return mapped

    if resolved_type == "callable":
        return "::std::function<object(object)>"

    # list[T] / dict[K, V] / set[T]
    container_value_type = cpp_container_value_type(resolved_type)
    if container_value_type != "":
        if prefer_value_container:
            return container_value_type
        return "Object<" + container_value_type + ">"

    # tuple[A, B, ...]
    if resolved_type.startswith("tuple[") and resolved_type.endswith("]"):
        inner = resolved_type[6:-1]
        parts = _split_generic_args(inner)
        if len(parts) > 0:
            return "::std::tuple<" + ", ".join(cpp_type(p) for p in parts) + ">"

    optional_inner = _top_level_optional_inner(resolved_type)
    if optional_inner != "":
        return "::std::optional<" + cpp_signature_type(optional_inner) + ">"

    # callable[[P1, P2, ...], RetType] → ::std::function<RetType(P1, P2, ...)>
    if resolved_type.startswith("callable[") and resolved_type.endswith("]"):
        inner = resolved_type[9:-1]  # strip "callable[" and "]"
        parts = _split_generic_args(inner)
        if len(parts) == 2:
            params_raw = parts[0].strip()
            ret_raw = parts[1].strip()
            if params_raw.startswith("[") and params_raw.endswith("]"):
                params_inner = params_raw[1:-1].strip()
                param_types = _split_generic_args(params_inner) if params_inner else []
                cpp_params = ", ".join(cpp_signature_type(p) for p in param_types)
                cpp_ret = cpp_signature_type(ret_raw)
                return "::std::function<" + cpp_ret + "(" + cpp_params + ")>"

    if _is_top_level_union(resolved_type):
        lanes = _split_top_level_union(resolved_type)
        if len(lanes) > 0:
            non_none = [l for l in lanes if l not in ("None", "none")]
            has_none = len(non_none) < len(lanes)
            if has_none and len(non_none) == 0:
                return "void"
            variant = "::std::variant<" + ", ".join(_cpp_variant_lane_type(lane) for lane in non_none) + ">"
            if has_none:
                return "::std::optional<" + variant + ">"
            return variant

    # User class → ClassName (by value or shared_ptr depending on context)
    return resolved_type


def cpp_signature_type(resolved_type: str, *, prefer_value_container: bool = False) -> str:
    """Type text for declarations/signatures.

    `unknown` / general union は `auto` にせず fail-closed で `object` に倒す。
    """
    resolved_type = normalize_cpp_nominal_adt_type(resolved_type)
    if resolved_type == "" or resolved_type == "unknown":
        return "object"
    if resolved_type in ("Callable", "callable"):
        return "::std::function<object(object)>"
    if resolved_type in ("Any", "Obj", "object"):
        return "object"
    optional_inner = _top_level_optional_inner(resolved_type)
    if optional_inner != "":
        return "::std::optional<" + cpp_signature_type(
            optional_inner,
            prefer_value_container=prefer_value_container,
        ) + ">"
    if _is_top_level_union(resolved_type):
        lanes = _split_top_level_union(resolved_type)
        if len(lanes) > 0:
            non_none = [l for l in lanes if l not in ("None", "none")]
            has_none = len(non_none) < len(lanes)
            if has_none and len(non_none) == 0:
                return "void"
            variant = "::std::variant<" + ", ".join(_cpp_variant_lane_type(lane) for lane in non_none) + ">"
            if has_none:
                return "::std::optional<" + variant + ">"
            return variant
    return cpp_type(resolved_type, prefer_value_container=prefer_value_container)


def cpp_param_decl(resolved_type: str, name: str, *, is_mutable: bool = False) -> str:
    """Render a function parameter declaration."""
    ct = cpp_signature_type(resolved_type)
    if _is_small_value_type(ct):
        return ct + " " + name
    if is_mutable:
        return ct + "& " + name
    return "const " + ct + "& " + name


def cpp_zero_value(resolved_type: str, *, prefer_value_container: bool = False) -> str:
    if is_container_resolved_type(resolved_type):
        container_value_type = cpp_container_value_type(resolved_type)
        if prefer_value_container:
            return container_value_type + "{}"
        if resolved_type.startswith("list[") and resolved_type.endswith("]"):
            inner = resolved_type[5:-1]
            return "rc_list_new<" + cpp_signature_type(inner) + ">()"
        if resolved_type.startswith("dict[") and resolved_type.endswith("]"):
            inner = resolved_type[5:-1]
            parts = _split_generic_args(inner)
            if len(parts) == 2:
                return (
                    "rc_dict_new<"
                    + cpp_signature_type(parts[0])
                    + ", "
                    + cpp_signature_type(parts[1])
                    + ">()"
                )
        if resolved_type.startswith("set[") and resolved_type.endswith("]"):
            inner = resolved_type[4:-1]
            return "rc_set_new<" + cpp_signature_type(inner) + ">()"

    ct = cpp_signature_type(resolved_type, prefer_value_container=prefer_value_container)
    if ct == "void":
        return ""
    if ct == "object":
        return "object()"
    if ct == "auto":
        return "{}"
    return ct + "{}"


def _is_small_value_type(cpp_text: str) -> bool:
    return cpp_text in {
        "bool",
        "int8",
        "int16",
        "int32",
        "int64",
        "uint8",
        "uint16",
        "uint32",
        "uint64",
        "float32",
        "float64",
    }


def _split_generic_args(s: str) -> list[str]:
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


def _split_top_level_union(resolved_type: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    i = 0
    while i < len(resolved_type):
        ch = resolved_type[i]
        if ch in "[<(":
            depth += 1
            current.append(ch)
            i += 1
            continue
        if ch in "]>)":
            depth -= 1
            current.append(ch)
            i += 1
            continue
        if ch == "|" and depth == 0:
            part = "".join(current).strip()
            if part != "":
                parts.append(part)
            current = []
            i += 1
            continue
        current.append(ch)
        i += 1
    tail = "".join(current).strip()
    if tail != "":
        parts.append(tail)
    return parts


def _is_top_level_union(resolved_type: str) -> bool:
    return len(_split_top_level_union(resolved_type)) > 1


def _top_level_optional_inner(resolved_type: str) -> str:
    parts = _split_top_level_union(resolved_type)
    if len(parts) != 2:
        return ""
    if parts[0] in ("None", "none"):
        return parts[1]
    if parts[1] in ("None", "none"):
        return parts[0]
    return ""


_TYPE_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def collect_cpp_type_vars(resolved_type: str) -> list[str]:
    """Collect generic type-variable names that should become C++ templates."""
    if resolved_type == "":
        return []
    out: list[str] = []
    seen: set[str] = set()
    for token in _TYPE_TOKEN_RE.findall(resolved_type):
        if token in _TYPE_MAP:
            continue
        if token in {
            "list",
            "dict",
            "set",
            "tuple",
            "Callable",
            "Iterator",
            "Iterable",
            "Optional",
            "None",
            "none",
            "object",
            "Any",
            "Obj",
            "unknown",
            "callable",
        }:
            continue
        if token.upper() != token:
            continue
        if token not in seen:
            seen.add(token)
            out.append(token)
    return out
