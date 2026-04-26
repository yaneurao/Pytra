"""C++ type mapping from EAST3 resolved types.

toolchain2 C++ backend は `src/runtime/cpp/core/*` の公開 alias (`str`,
`list[T]`, `dict[K,V]`, `float64`, `object` など) を正本として使う。

型写像は mapping.json の `types` テーブルを正本とする（P0-CPP-TYPEMAP-S3）。
`init_types_mapping()` で emitter 起動時に注入する。`_TYPE_MAP` は後方互換フォールバック。
"""

from __future__ import annotations


# mapping.json "types" テーブルの注入先。emitter 起動時に init_types_mapping() で設定する。
_g_types: dict[str, str] = {}


def init_types_mapping(types: dict[str, str]) -> None:
    """mapping.json の types テーブルを注入する。emit_module() 呼び出し前に一度だけ呼ぶ。"""
    _g_types.clear()
    for name, mapped in types.items():
        _g_types[name] = mapped


def _build_type_map() -> dict[str, str]:
    # フォールバック: mapping.json が空の場合に使うハードコード表。
    # 正本は src/runtime/cpp/mapping.json の "types" テーブル。
    out: dict[str, str] = {}
    out["int"] = "int64"
    out["int8"] = "int8"
    out["int16"] = "int16"
    out["int32"] = "int32"
    out["int64"] = "int64"
    out["uint8"] = "uint8"
    out["uint16"] = "uint16"
    out["uint32"] = "uint32"
    out["uint64"] = "uint64"
    out["float"] = "float64"
    out["float32"] = "float32"
    out["float64"] = "float64"
    out["bool"] = "bool"
    out["str"] = "str"
    out["None"] = "void"
    out["none"] = "void"
    out["bytes"] = "bytes"
    out["bytearray"] = "bytearray"
    out["Any"] = "object"
    out["Obj"] = "object"
    out["object"] = "object"
    out["JsonVal"] = "JsonVal"
    out["Node"] = "Object<dict<str, JsonVal>>"
    # toolchain.parse.py.nodes.TypeExpr = Union[NamedType, GenericType].
    # The alias itself may be elided from EAST3, so emit its storage type directly.
    out["TypeExpr"] = "::std::variant<NamedType, GenericType>"
    out["Callable"] = "::std::function<object(object)>"
    return out


def _build_cpp_alias_union_expansions() -> dict[str, str]:
    out: dict[str, str] = {}
    out["JsonVal"] = "None | bool | int64 | float64 | str | list[JsonVal] | dict[str,JsonVal]"
    return out


_TYPE_MAP: dict[str, str] = _build_type_map()
_CPP_ALIAS_UNION_EXPANSIONS: dict[str, str] = _build_cpp_alias_union_expansions()

_JSONVAL_EXPANDED_NORMS: list[str] = [
    "None|bool|int64|float64|str|list[Any]|dict[str,Any]",
    "bool|int64|float64|str|list[Any]|dict[str,Any]|None",
]
_JSONVAL_INNER_EXPANDED_NORM: str = "bool|int64|float64|str|list[Any]|dict[str,Any]"
_JSONVAL_INNER_CANON: str = "bool | int64 | float64 | str | list[JsonVal] | dict[str,JsonVal]"


def _norm_type_text(text: str) -> str:
    return text.replace(" ", "").replace("\n", "").replace("\t", "")


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
            cpp_parts: list[str] = []
            for p in parts:
                cpp_parts.append(cpp_type(p))
            return "::std::tuple<" + ", ".join(cpp_parts) + ">"

    optional_inner = _top_level_optional_inner(resolved_type)
    if optional_inner != "":
        return "::std::optional<" + cpp_signature_type(optional_inner) + ">"

    # callable[[P1, P2, ...], RetType] / Callable[[...], RetType]
    #   → ::std::function<RetType(P1, P2, ...)>
    callable_inner = ""
    if resolved_type.startswith("callable[") and resolved_type.endswith("]"):
        callable_inner = resolved_type[9:-1]
    elif resolved_type.startswith("Callable[") and resolved_type.endswith("]"):
        callable_inner = resolved_type[9:-1]
    if callable_inner != "":
        parts = _split_generic_args(callable_inner)
        if len(parts) == 2:
            params_raw = parts[0].strip()
            ret_raw = parts[1].strip()
            if params_raw.startswith("[") and params_raw.endswith("]"):
                params_inner = params_raw[1:-1].strip()
                param_types: list[str] = []
                if params_inner != "":
                    param_types = _split_generic_args(params_inner)
                cpp_param_parts: list[str] = []
                for p in param_types:
                    cpp_param_parts.append(cpp_signature_type(p))
                cpp_params = ", ".join(cpp_param_parts)
                cpp_ret = cpp_signature_type(ret_raw)
                return "::std::function<" + cpp_ret + "(" + cpp_params + ")>"

    if _is_top_level_union(resolved_type):
        lanes = _split_top_level_union(resolved_type)
        if len(lanes) > 0:
            non_none: list[str] = []
            for lane in lanes:
                if lane != "None" and lane != "none":
                    non_none.append(lane)
            has_none = len(non_none) < len(lanes)
            if has_none and len(non_none) == 0:
                return "void"
            variant_parts: list[str] = []
            for lane in non_none:
                variant_parts.append(_cpp_variant_lane_type(lane))
            variant = "::std::variant<" + ", ".join(variant_parts) + ">"
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
    if resolved_type == "Callable" or resolved_type == "callable":
        return "::std::function<object(object)>"
    if resolved_type == "Any" or resolved_type == "Obj" or resolved_type == "object":
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
            non_none: list[str] = []
            for lane in lanes:
                if lane != "None" and lane != "none":
                    non_none.append(lane)
            has_none = len(non_none) < len(lanes)
            if has_none and len(non_none) == 0:
                return "void"
            variant_parts: list[str] = []
            for lane in non_none:
                variant_parts.append(_cpp_variant_lane_type(lane))
            variant = "::std::variant<" + ", ".join(variant_parts) + ">"
            if has_none:
                return "::std::optional<" + variant + ">"
            return variant
    return cpp_type(resolved_type, prefer_value_container=prefer_value_container)


def cpp_param_decl(resolved_type: str, name: str, *, is_mutable: bool = False) -> str:
    """Render a function parameter declaration."""
    ct = cpp_signature_type(resolved_type)
    if _is_small_value_type(ct):
        return ct + " " + name
    if is_mutable and ct.startswith("::std::optional<"):
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
    return (
        cpp_text == "bool"
        or cpp_text == "int8"
        or cpp_text == "int16"
        or cpp_text == "int32"
        or cpp_text == "int64"
        or cpp_text == "uint8"
        or cpp_text == "uint16"
        or cpp_text == "uint32"
        or cpp_text == "uint64"
        or cpp_text == "float32"
        or cpp_text == "float64"
    )


def _split_generic_args(s: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    i = 0
    while i < len(s):
        ch = s[i:i + 1]
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
        i += 1
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
        ch = resolved_type[i:i + 1]
        if ch == "[" or ch == "<" or ch == "(":
            depth += 1
            current.append(ch)
            i += 1
            continue
        if ch == "]" or ch == ">" or ch == ")":
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
    if parts[0] == "None" or parts[0] == "none":
        return parts[1]
    if parts[1] == "None" or parts[1] == "none":
        return parts[0]
    return ""


def _is_type_token_start(ch: str) -> bool:
    return ("A" <= ch <= "Z") or ("a" <= ch <= "z") or ch == "_"


def _is_type_token_part(ch: str) -> bool:
    return _is_type_token_start(ch) or ("0" <= ch <= "9")


def _iter_type_tokens(text: str) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(text):
        ch = text[i:i + 1]
        if not _is_type_token_start(ch):
            i += 1
            continue
        start = i
        i += 1
        while i < len(text) and _is_type_token_part(text[i:i + 1]):
            i += 1
        out.append(text[start:i])
    return out


def _is_builtin_type_token(token: str) -> bool:
    return (
        token == "list"
        or token == "dict"
        or token == "set"
        or token == "tuple"
        or token == "Callable"
        or token == "Iterator"
        or token == "Iterable"
        or token == "Optional"
        or token == "None"
        or token == "none"
        or token == "object"
        or token == "Any"
        or token == "Obj"
        or token == "unknown"
        or token == "callable"
    )


def collect_cpp_type_vars(resolved_type: str) -> list[str]:
    """Collect generic type-variable names that should become C++ templates."""
    if resolved_type == "":
        return []
    out: list[str] = []
    seen: set[str] = set()
    for token in _iter_type_tokens(resolved_type):
        if token in _TYPE_MAP:
            continue
        if _is_builtin_type_token(token):
            continue
        if token.upper() != token:
            continue
        if token not in seen:
            seen.add(token)
            out.append(token)
    return out
