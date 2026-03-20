"""Shared helpers for structured frontend type expressions."""

from __future__ import annotations

from typing import Any


_PRIMITIVE_NAMES: dict[str, str] = {
    "int": "int64",
    "float": "float64",
    "byte": "uint8",
    "bool": "bool",
    "str": "str",
    "None": "None",
    "bytes": "bytes",
    "bytearray": "bytearray",
    "Any": "Any",
    "any": "Any",
    "object": "object",
    "unknown": "unknown",
    "Path": "Path",
}

_GENERIC_BASES: dict[str, str] = {
    "list": "list",
    "List": "list",
    "set": "set",
    "Set": "set",
    "dict": "dict",
    "Dict": "dict",
    "tuple": "tuple",
    "Tuple": "tuple",
    "callable": "callable",
    "Callable": "callable",
}

_JSON_NOMINALS: set[str] = {"JsonValue", "JsonObj", "JsonArr"}


def _strip_quotes(text: str) -> str:
    txt = text.strip()
    if len(txt) >= 2 and ((txt[0] == "'" and txt[-1] == "'") or (txt[0] == '"' and txt[-1] == '"')):
        return txt[1:-1].strip()
    return txt


def _strip_typing_prefix(text: str) -> str:
    txt = text.strip()
    if txt.startswith("typing."):
        return txt[len("typing.") :].strip()
    return txt


def _split_top_level(text: str, sep: str) -> list[str]:
    out: list[str] = []
    buf = ""
    depth = 0
    sep_len = len(sep)
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "[":
            depth += 1
            buf += ch
            i += 1
            continue
        if ch == "]":
            if depth > 0:
                depth -= 1
            buf += ch
            i += 1
            continue
        if depth == 0 and text.startswith(sep, i):
            item = buf.strip()
            if item != "":
                out.append(item)
            buf = ""
            i += sep_len
            continue
        buf += ch
        i += 1
    tail = buf.strip()
    if tail != "":
        out.append(tail)
    return out


def split_type_args(text: str) -> list[str]:
    """Split generic arguments at top-level commas."""
    return _split_top_level(text, ",")


def split_top_level_union(text: str) -> list[str]:
    """Split union arms at top-level `|` tokens."""
    return _split_top_level(text, "|")


def _is_simple_identifier(text: str) -> bool:
    if text == "":
        return False
    first = text[0]
    if not (first == "_" or ("A" <= first <= "Z") or ("a" <= first <= "z")):
        return False
    for ch in text[1:]:
        if not (ch == "_" or ("A" <= ch <= "Z") or ("a" <= ch <= "z") or ("0" <= ch <= "9")):
            return False
    return True


def _normalize_head_name(text: str, aliases: dict[str, str], seen_aliases: set[str]) -> str:
    head = _strip_typing_prefix(_strip_quotes(text))
    if head in aliases and head not in seen_aliases:
        alias_txt = _strip_typing_prefix(_strip_quotes(aliases[head]))
        if _is_simple_identifier(alias_txt):
            return alias_txt
    if head in _GENERIC_BASES:
        return _GENERIC_BASES[head]
    return head


def _is_none_expr(expr: dict[str, Any]) -> bool:
    return expr.get("kind") == "NamedType" and expr.get("name") == "None"


def _is_dynamic_expr(expr: dict[str, Any]) -> bool:
    return expr.get("kind") == "DynamicType"


def _is_named_ellipsis_expr(expr: object) -> bool:
    return isinstance(expr, dict) and expr.get("kind") == "NamedType" and expr.get("name") == "..."


def _is_homogeneous_tuple_ellipsis_expr(expr: object) -> bool:
    if not isinstance(expr, dict):
        return False
    if expr.get("kind") != "GenericType" or str(expr.get("base", "")).strip() != "tuple":
        return False
    tuple_shape = str(expr.get("tuple_shape", "")).strip()
    if tuple_shape == "homogeneous_ellipsis":
        return True
    args_obj = expr.get("args")
    return isinstance(args_obj, list) and len(args_obj) == 2 and _is_named_ellipsis_expr(args_obj[1])


def _make_named_like(name: str) -> dict[str, Any]:
    if name in {"Any", "object", "unknown"}:
        return {"kind": "DynamicType", "name": name}
    if name in _JSON_NOMINALS:
        return {"kind": "NominalAdtType", "name": name, "adt_family": "json", "variant_domain": "closed"}
    return {"kind": "NamedType", "name": name}


def _make_union_type_expr(options: list[dict[str, Any]]) -> dict[str, Any]:
    non_none: list[dict[str, Any]] = []
    has_none = False
    for option in options:
        if _is_none_expr(option):
            has_none = True
        else:
            non_none.append(option)
    if has_none and len(non_none) == 1:
        return {"kind": "OptionalType", "inner": non_none[0]}
    union_options = list(non_none)
    if has_none:
        union_options.append({"kind": "NamedType", "name": "None"})
    mode = "dynamic" if any(_is_dynamic_expr(option) for option in union_options) else "general"
    return {"kind": "UnionType", "union_mode": mode, "options": union_options}


def _parse_type_expr_inner(raw_text: str, aliases: dict[str, str], seen_aliases: set[str]) -> dict[str, Any]:
    txt = _strip_typing_prefix(_strip_quotes(raw_text))
    if txt == "":
        return {"kind": "DynamicType", "name": "unknown"}
    if txt in aliases and txt not in seen_aliases:
        return _parse_type_expr_inner(aliases[txt], aliases, seen_aliases | {txt})
    union_parts = split_top_level_union(txt)
    if len(union_parts) > 1:
        return _make_union_type_expr(
            [_parse_type_expr_inner(part, aliases, seen_aliases) for part in union_parts]
        )
    if txt in _PRIMITIVE_NAMES:
        return _make_named_like(_PRIMITIVE_NAMES[txt])
    lb = txt.find("[")
    if lb > 0 and txt.endswith("]"):
        head = _normalize_head_name(txt[:lb].strip(), aliases, seen_aliases)
        inner = txt[lb + 1 : -1].strip()
        args = [_parse_type_expr_inner(part, aliases, seen_aliases) for part in split_type_args(inner)]
        if head == "Optional" and len(args) == 1:
            return {"kind": "OptionalType", "inner": args[0]}
        if head == "Union" and len(args) > 0:
            return _make_union_type_expr(args)
        if head == "tuple" and len(args) == 2 and _is_named_ellipsis_expr(args[1]):
            return {"kind": "GenericType", "base": head, "args": args, "tuple_shape": "homogeneous_ellipsis"}
        return {"kind": "GenericType", "base": head, "args": args}
    return _make_named_like(txt)


def parse_type_expr_text(raw_text: str, *, type_aliases: dict[str, str] | None = None) -> dict[str, Any]:
    """Parse an annotation string into a structured type-expression dict."""
    aliases = type_aliases if type_aliases is not None else {}
    return _parse_type_expr_inner(raw_text, aliases, set())


def type_expr_to_string(expr: dict[str, Any]) -> str:
    """Render a structured type expression into the legacy normalized mirror."""
    kind = str(expr.get("kind", ""))
    if kind == "NamedType":
        return str(expr.get("name", "unknown"))
    if kind == "DynamicType":
        return str(expr.get("name", "unknown"))
    if kind == "NominalAdtType":
        return str(expr.get("name", "unknown"))
    if kind == "OptionalType":
        inner = expr.get("inner", {"kind": "DynamicType", "name": "unknown"})
        if isinstance(inner, dict):
            return type_expr_to_string(inner) + " | None"
        return "unknown | None"
    if kind == "GenericType":
        base = str(expr.get("base", "unknown"))
        args_obj = expr.get("args", [])
        args: list[str] = []
        if isinstance(args_obj, list):
            for arg in args_obj:
                if isinstance(arg, dict):
                    args.append(type_expr_to_string(arg))
                else:
                    args.append("unknown")
        return base + "[" + ",".join(args) + "]"
    if kind == "UnionType":
        options_obj = expr.get("options", [])
        options: list[str] = []
        if isinstance(options_obj, list):
            for option in options_obj:
                if isinstance(option, dict):
                    options.append(type_expr_to_string(option))
                else:
                    options.append("unknown")
        return "|".join(options)
    return "unknown"


def normalize_type_text(raw_text: str, *, type_aliases: dict[str, str] | None = None) -> str:
    """Normalize an annotation string into the existing legacy type-text mirror."""
    return type_expr_to_string(parse_type_expr_text(raw_text, type_aliases=type_aliases))


def _is_type_expr_payload(value: object) -> bool:
    return isinstance(value, dict) and isinstance(value.get("kind"), str)


def summarize_type_expr(expr: object) -> dict[str, Any]:
    """Summarize a structured TypeExpr for lowering / validation metadata."""
    out: dict[str, Any] = {
        "kind": "unknown",
        "category": "unknown",
        "mirror": "unknown",
    }
    if not _is_type_expr_payload(expr):
        return out
    expr_obj = expr
    kind = str(expr_obj.get("kind", "unknown"))
    out["kind"] = kind
    out["mirror"] = type_expr_to_string(expr_obj)
    if kind == "DynamicType":
        out["category"] = "dynamic"
        out["dynamic_name"] = str(expr_obj.get("name", "unknown"))
        return out
    if kind == "NominalAdtType":
        out["category"] = "nominal_adt"
        nominal_name = str(expr_obj.get("name", "")).strip()
        if nominal_name != "":
            out["nominal_adt_name"] = nominal_name
        adt_family = str(expr_obj.get("adt_family", "")).strip()
        variant_domain = str(expr_obj.get("variant_domain", "")).strip()
        if adt_family != "":
            out["nominal_adt_family"] = adt_family
        if variant_domain != "":
            out["nominal_variant_domain"] = variant_domain
        return out
    if kind == "OptionalType":
        out["category"] = "optional"
        inner_obj = expr_obj.get("inner")
        inner_summary = summarize_type_expr(inner_obj)
        inner_category = str(inner_summary.get("category", "unknown"))
        if inner_category != "unknown":
            out["inner_category"] = inner_category
        nominal_name = str(inner_summary.get("nominal_adt_name", ""))
        if nominal_name != "":
            out["nominal_adt_name"] = nominal_name
        nominal_family = str(inner_summary.get("nominal_adt_family", ""))
        if nominal_family != "":
            out["nominal_adt_family"] = nominal_family
        variant_domain = str(inner_summary.get("nominal_variant_domain", ""))
        if variant_domain != "":
            out["nominal_variant_domain"] = variant_domain
        return out
    if kind == "UnionType":
        union_mode = str(expr_obj.get("union_mode", "")).strip()
        out["union_mode"] = union_mode
        if union_mode == "dynamic":
            out["category"] = "dynamic_union"
        else:
            out["category"] = "general_union"
        return out
    if kind == "GenericType" and _is_homogeneous_tuple_ellipsis_expr(expr_obj):
        out["category"] = "homogeneous_tuple"
        out["tuple_shape"] = "homogeneous_ellipsis"
        args_obj = expr_obj.get("args")
        if isinstance(args_obj, list) and len(args_obj) >= 1 and isinstance(args_obj[0], dict):
            item_summary = summarize_type_expr(args_obj[0])
            item_mirror = str(item_summary.get("mirror", "unknown")).strip()
            item_category = str(item_summary.get("category", "unknown")).strip()
            if item_mirror != "" and item_mirror != "unknown":
                out["item_mirror"] = item_mirror
            if item_category != "" and item_category != "unknown":
                out["item_category"] = item_category
        return out
    if kind in {"NamedType", "GenericType"}:
        out["category"] = "static"
        return out
    return out


def summarize_type_text(raw_text: object, *, type_aliases: dict[str, str] | None = None) -> dict[str, Any]:
    """Summarize a legacy type-text mirror via the shared TypeExpr parser."""
    if not isinstance(raw_text, str):
        return summarize_type_expr(None)
    txt = raw_text.strip()
    if txt == "":
        return summarize_type_expr(None)
    return summarize_type_expr(parse_type_expr_text(txt, type_aliases=type_aliases))


def _sync_type_expr_pair(node: dict[str, Any], expr_key: str, mirror_key: str, path: str) -> None:
    expr_obj = node.get(expr_key)
    if not _is_type_expr_payload(expr_obj):
        return
    expected = type_expr_to_string(expr_obj)
    mirror_obj = node.get(mirror_key)
    if mirror_obj is None:
        node[mirror_key] = expected
        return
    if not isinstance(mirror_obj, str):
        raise RuntimeError(path + "." + mirror_key + " must be a string when " + expr_key + " is present")
    actual = mirror_obj.strip()
    if actual == "" or actual == "unknown":
        node[mirror_key] = expected
        return
    if actual != expected:
        raise RuntimeError(path + "." + mirror_key + " mismatch: " + actual + " != " + expected)


def _sync_arg_type_expr_mirrors(node: dict[str, Any], path: str) -> None:
    exprs_obj = node.get("arg_type_exprs")
    if not isinstance(exprs_obj, dict):
        return
    arg_types_obj = node.get("arg_types")
    if arg_types_obj is None:
        arg_types_obj = {}
        node["arg_types"] = arg_types_obj
    if not isinstance(arg_types_obj, dict):
        raise RuntimeError(path + ".arg_types must be a dict when arg_type_exprs is present")
    for arg_name, expr_obj in exprs_obj.items():
        if not isinstance(arg_name, str):
            continue
        if not _is_type_expr_payload(expr_obj):
            continue
        expected = type_expr_to_string(expr_obj)
        mirror_obj = arg_types_obj.get(arg_name)
        if mirror_obj is None:
            arg_types_obj[arg_name] = expected
            continue
        if not isinstance(mirror_obj, str):
            raise RuntimeError(path + ".arg_types." + arg_name + " must be a string")
        actual = mirror_obj.strip()
        if actual == "" or actual == "unknown":
            arg_types_obj[arg_name] = expected
            continue
        if actual != expected:
            raise RuntimeError(path + ".arg_types." + arg_name + " mismatch: " + actual + " != " + expected)


def sync_type_expr_mirrors(doc: object, *, path: str = "$") -> object:
    """Fill/validate legacy string mirrors from structured TypeExpr payloads in-place."""
    if isinstance(doc, dict):
        _sync_type_expr_pair(doc, "type_expr", "resolved_type", path)
        _sync_type_expr_pair(doc, "annotation_type_expr", "annotation", path)
        _sync_type_expr_pair(doc, "decl_type_expr", "decl_type", path)
        _sync_type_expr_pair(doc, "return_type_expr", "return_type", path)
        _sync_type_expr_pair(doc, "vararg_type_expr", "vararg_type", path)
        _sync_arg_type_expr_mirrors(doc, path)
        for key, value in list(doc.items()):
            if isinstance(key, str):
                sync_type_expr_mirrors(value, path=path + "." + key)
        return doc
    if isinstance(doc, list):
        for idx, item in enumerate(doc):
            sync_type_expr_mirrors(item, path=path + "[" + str(idx) + "]")
    return doc
