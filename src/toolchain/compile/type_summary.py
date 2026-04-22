"""Type expression summary for EAST2 → EAST3 lowering.

Implements type_expr_summary_v1 generation, nominal ADT tracking,
and related helpers.

§5.1: Any/object 禁止。
§5.3: Python 標準モジュール直接 import 禁止。
§5.6: グローバル可変状態禁止 — CompileContext 経由。
"""

from __future__ import annotations

from pytra.typing import cast

from toolchain.compile.jv import JsonVal, Node, CompileContext
from toolchain.compile.jv import jv_str, jv_dict, jv_list, jv_is_dict, jv_is_list, deep_copy_json
from toolchain.compile.jv import nd_kind, nd_get_str, nd_get_dict
from toolchain.compile.jv import normalize_type_name
from toolchain.common.kinds import (
    CLASS_DEF, NAMED_TYPE, GENERIC_TYPE, DYNAMIC_TYPE, NOMINAL_ADT_TYPE,
    OPTIONAL_TYPE, UNION_TYPE, NAME,
)


_TYPE_EXPR_SUMMARY_KEY: str = "type_expr_summary_v1"

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

_JSON_NOMINALS: list[str] = ["JsonValue", "JsonObj", "JsonArr"]

_JSON_RECEIVER_PREFIXES: list[tuple[str, str]] = [
    ("json.value.", "JsonValue"),
    ("json.obj.", "JsonObj"),
    ("json.arr.", "JsonArr"),
]


def _copy_node(node: Node) -> Node:
    copied = deep_copy_json(node)
    if jv_is_dict(copied):
        return jv_dict(copied)
    empty: dict[str, JsonVal] = {}
    return empty


# ---------------------------------------------------------------------------
# Type expression parsing (simplified re-implementation of type_expr.py)
# ---------------------------------------------------------------------------

def _strip_quotes(text: str) -> str:
    txt = text.strip()
    if len(txt) >= 2:
        last = len(txt) - 1
        if (txt[0] == "'" and txt[last] == "'") or (txt[0] == '"' and txt[last] == '"'):
            return txt[1:-1].strip()
    return txt


def _strip_typing_prefix(text: str) -> str:
    txt = text.strip()
    if txt.startswith("typing."):
        return txt[7:].strip()
    return txt


def _split_top_level(text: str, sep: str) -> list[str]:
    out: list[str] = []
    buf: str = ""
    depth: int = 0
    sep_len = len(sep)
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "[":
            depth += 1
            buf += ch
            i += 1
        elif ch == "]":
            if depth > 0:
                depth -= 1
            buf += ch
            i += 1
        elif depth == 0 and text[i:i + sep_len] == sep:
            item = buf.strip()
            if item != "":
                out.append(item)
            buf = ""
            i += sep_len
        else:
            buf += ch
            i += 1
    tail = buf.strip()
    if tail != "":
        out.append(tail)
    return out


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


def _is_named_ellipsis(expr: JsonVal) -> bool:
    if not jv_is_dict(expr):
        return False
    d: Node = jv_dict(expr)
    return jv_str(d.get("kind", "")) == NAMED_TYPE and jv_str(d.get("name", "")) == "..."


def _is_homogeneous_tuple_ellipsis(expr: JsonVal) -> bool:
    if not jv_is_dict(expr):
        return False
    d: Node = jv_dict(expr)
    base = jv_str(d.get("base", ""))
    if jv_str(d.get("kind", "")) != GENERIC_TYPE or base != "tuple":
        return False
    ts = jv_str(d.get("tuple_shape", ""))
    if ts == "homogeneous_ellipsis":
        return True
    args_obj = d.get("args")
    if not jv_is_list(args_obj):
        return False
    al = jv_list(args_obj)
    if len(al) != 2:
        return False
    idx = 0
    second_items: list[JsonVal] = []
    for item in al:
        if idx == 1:
            second_items.append(item)
            break
        idx += 1
    return len(second_items) == 1 and _is_named_ellipsis(second_items[0])


def _make_named_like(name: str) -> Node:
    if name == "Any" or name == "object" or name == "unknown":
        dyn: dict[str, JsonVal] = {}
        dyn["kind"] = DYNAMIC_TYPE
        dyn["name"] = name
        return dyn
    if name == "JsonValue" or name == "JsonObj" or name == "JsonArr":
        nominal: dict[str, JsonVal] = {}
        nominal["kind"] = NOMINAL_ADT_TYPE
        nominal["name"] = name
        nominal["adt_family"] = "json"
        nominal["variant_domain"] = "closed"
        return nominal
    named: dict[str, JsonVal] = {}
    named["kind"] = NAMED_TYPE
    named["name"] = name
    return named


def _make_union_type_expr(options: list[Node]) -> Node:
    non_none: list[Node] = []
    has_none = False
    for option in options:
        if ("" + jv_str(option.get("kind", ""))) == NAMED_TYPE and ("" + jv_str(option.get("name", ""))) == "None":
            has_none = True
        else:
            non_none.append(option)
    if has_none and len(non_none) == 1:
        opt: dict[str, JsonVal] = {}
        opt["kind"] = OPTIONAL_TYPE
        opt["inner"] = non_none[0]
        return opt
    union_opts: list[JsonVal] = []
    for item in non_none:
        union_opts.append(item)
    if has_none:
        none_type: dict[str, JsonVal] = {}
        none_type["kind"] = NAMED_TYPE
        none_type["name"] = "None"
        union_opts.append(none_type)
    mode = "general"
    for opt_item in union_opts:
        if jv_is_dict(opt_item) and nd_get_str(jv_dict(opt_item), "kind") == DYNAMIC_TYPE:
            mode = "dynamic"
            break
    out: dict[str, JsonVal] = {}
    out["kind"] = UNION_TYPE
    out["union_mode"] = mode
    out["options"] = union_opts
    return out


def _parse_type_expr(raw: str) -> Node:
    txt = _strip_typing_prefix(_strip_quotes(raw))
    if txt == "":
        unknown: dict[str, JsonVal] = {}
        unknown["kind"] = DYNAMIC_TYPE
        unknown["name"] = "unknown"
        return unknown
    union_parts = _split_top_level(txt, "|")
    if len(union_parts) > 1:
        return _make_union_type_expr([_parse_type_expr(p) for p in union_parts])
    if txt in _PRIMITIVE_NAMES:
        return _make_named_like(_PRIMITIVE_NAMES[txt])
    lb = txt.find("[")
    if lb > 0 and txt.endswith("]"):
        head_raw = txt[:lb].strip()
        head = _strip_typing_prefix(_strip_quotes(head_raw))
        if head in _GENERIC_BASES:
            head = _GENERIC_BASES[head]
        inner = txt[lb + 1:-1].strip()
        args: list[JsonVal] = []
        for p in _split_top_level(inner, ","):
            args.append(_parse_type_expr(p))
        if head == "Optional" and len(args) == 1:
            opt: dict[str, JsonVal] = {}
            opt["kind"] = OPTIONAL_TYPE
            opt["inner"] = args[0]
            return opt
        if head == "Union" and len(args) > 0:
            return _make_union_type_expr(args)
        if head == "tuple" and len(args) == 2 and _is_named_ellipsis(args[1]):
            tuple_expr: dict[str, JsonVal] = {}
            tuple_expr["kind"] = GENERIC_TYPE
            tuple_expr["base"] = head
            tuple_expr["args"] = args
            tuple_expr["tuple_shape"] = "homogeneous_ellipsis"
            return tuple_expr
        generic: dict[str, JsonVal] = {}
        generic["kind"] = GENERIC_TYPE
        generic["base"] = head
        generic["args"] = args
        return generic
    return _make_named_like(txt)


def _type_expr_to_string(expr: JsonVal) -> str:
    if not jv_is_dict(expr):
        return "unknown"
    d: Node = jv_dict(expr)
    kind = jv_str(d.get("kind", ""))
    if kind == DYNAMIC_TYPE or kind == NAMED_TYPE or kind == NOMINAL_ADT_TYPE:
        return "" + jv_str(d.get("name", "unknown"))
    if kind == OPTIONAL_TYPE:
        inner = d.get("inner")
        if jv_is_dict(inner):
            return _type_expr_to_string(inner) + " | None"
        return "unknown | None"
    if kind == GENERIC_TYPE:
        base = "" + jv_str(d.get("base", "unknown"))
        args_obj = d.get("args")
        parts: list[str] = []
        if jv_is_list(args_obj):
            for arg in jv_list(args_obj):
                parts.append(_type_expr_to_string(arg))
        return base + "[" + ",".join(parts) + "]"
    if kind == UNION_TYPE:
        opts_obj = d.get("options")
        opts: list[str] = []
        if jv_is_list(opts_obj):
            for opt in jv_list(opts_obj):
                opts.append(_type_expr_to_string(opt))
        return "|".join(opts)
    return "unknown"


# ---------------------------------------------------------------------------
# summarize_type_expr / summarize_type_text  (ADT テーブル不要 — 純粋関数)
# ---------------------------------------------------------------------------

def _is_type_expr_payload(value: JsonVal) -> bool:
    if not jv_is_dict(value):
        return False
    d: Node = jv_dict(value)
    return jv_str(d.get("kind", "")) != ""


def summarize_type_expr(expr: JsonVal) -> Node:
    out: dict[str, JsonVal] = {}
    out["kind"] = "unknown"
    out["category"] = "unknown"
    out["mirror"] = "unknown"
    if not _is_type_expr_payload(expr):
        return out
    if not jv_is_dict(expr):
        return out
    d: Node = jv_dict(expr)
    kind = jv_str(d.get("kind", "unknown"))
    out["kind"] = kind
    out["mirror"] = _type_expr_to_string(d)
    if kind == DYNAMIC_TYPE:
        out["category"] = "dynamic"
        out["dynamic_name"] = jv_str(d.get("name", "unknown"))
        return out
    if kind == NOMINAL_ADT_TYPE:
        out["category"] = "nominal_adt"
        nn = jv_str(d.get("name", ""))
        if nn != "":
            out["nominal_adt_name"] = nn
        af = jv_str(d.get("adt_family", ""))
        vd = jv_str(d.get("variant_domain", ""))
        if af != "":
            out["nominal_adt_family"] = af
        if vd != "":
            out["nominal_variant_domain"] = vd
        return out
    if kind == OPTIONAL_TYPE:
        out["category"] = "optional"
        inner_summary = summarize_type_expr(d.get("inner"))
        im = jv_str(inner_summary.get("mirror", "unknown"))
        if im != "" and im != "unknown":
            out["inner_mirror"] = im
        ic = jv_str(inner_summary.get("category", "unknown"))
        if ic != "unknown":
            out["inner_category"] = ic
        nn2 = jv_str(inner_summary.get("nominal_adt_name", ""))
        if nn2 != "":
            out["nominal_adt_name"] = nn2
        nf2 = jv_str(inner_summary.get("nominal_adt_family", ""))
        if nf2 != "":
            out["nominal_adt_family"] = nf2
        vd2 = jv_str(inner_summary.get("nominal_variant_domain", ""))
        if vd2 != "":
            out["nominal_variant_domain"] = vd2
        return out
    if kind == UNION_TYPE:
        um = jv_str(d.get("union_mode", ""))
        out["union_mode"] = um
        if um == "dynamic":
            out["category"] = "dynamic_union"
        else:
            out["category"] = "general_union"
        return out
    if kind == GENERIC_TYPE and _is_homogeneous_tuple_ellipsis(d):
        out["category"] = "homogeneous_tuple"
        out["tuple_shape"] = "homogeneous_ellipsis"
        args = d.get("args")
        if jv_is_list(args):
            for arg0 in jv_list(args):
                if not jv_is_dict(arg0):
                    break
                item_s = summarize_type_expr(arg0)
                im_homo: str = "" + jv_str(item_s.get("mirror", "unknown"))
                ic_homo: str = "" + jv_str(item_s.get("category", "unknown"))
                if im_homo != "" and im_homo != "unknown":
                    out["item_mirror"] = im_homo
                if ic_homo != "" and ic_homo != "unknown":
                    out["item_category"] = ic_homo
                break
        return out
    if kind == NAMED_TYPE or kind == GENERIC_TYPE:
        out["category"] = "static"
        return out
    return out


def summarize_type_text(raw: JsonVal) -> Node:
    txt = jv_str(raw).strip()
    if txt == "":
        return summarize_type_expr(None)
    return summarize_type_expr(_parse_type_expr(txt))


# ---------------------------------------------------------------------------
# Type summary from EAST node payloads  (ctx 必須 — ADT テーブル参照)
# ---------------------------------------------------------------------------

def unknown_type_summary() -> Node:
    out: dict[str, JsonVal] = {}
    out["kind"] = "unknown"
    out["category"] = "unknown"
    out["mirror"] = "unknown"
    return out


def type_expr_summary_from_payload(ctx: CompileContext, type_expr: JsonVal, mirror: JsonVal) -> Node:
    summary = summarize_type_expr(type_expr)
    if jv_str(summary.get("category", "unknown")) != "unknown":
        summary_copy = _copy_node(summary)
        return hydrate_nominal_adt_summary(ctx, summary_copy, mirror)
    text_summary = summarize_type_text(mirror)
    text_copy = _copy_node(text_summary)
    return hydrate_nominal_adt_summary(ctx, text_copy, mirror)


def type_expr_summary_from_node(ctx: CompileContext, node: JsonVal) -> Node:
    if not jv_is_dict(node):
        return unknown_type_summary()
    nd: Node = jv_dict(node)
    return type_expr_summary_from_payload(ctx, nd.get("type_expr"), nd.get("resolved_type"))


def structured_type_expr_summary_from_node(node: JsonVal) -> Node:
    """ADT テーブル不要 — type_expr のみから要約。"""
    if not jv_is_dict(node):
        return unknown_type_summary()
    nd: Node = jv_dict(node)
    summary = summarize_type_expr(nd.get("type_expr"))
    return _copy_node(summary)


def expr_type_summary(ctx: CompileContext, expr: JsonVal) -> Node:
    return type_expr_summary_from_node(ctx, expr)


def expr_type_name(ctx: CompileContext, expr: JsonVal) -> str:
    summary = expr_type_summary(ctx, expr)
    mirror = "" + normalize_type_name(summary.get("mirror"))
    if mirror != "unknown":
        return mirror
    if jv_is_dict(expr):
        ed: Node = jv_dict(expr)
        return "" + normalize_type_name(ed.get("resolved_type"))
    return "unknown"


# ---------------------------------------------------------------------------
# Nominal ADT helpers  (ctx 経由でテーブルにアクセス)
# ---------------------------------------------------------------------------

def lookup_nominal_adt_decl(ctx: CompileContext, name: JsonVal) -> Node:
    type_name = "" + normalize_type_name(name)
    if type_name == "unknown":
        empty: dict[str, JsonVal] = {}
        return empty
    if type_name not in ctx.nominal_adt_table:
        empty2: dict[str, JsonVal] = {}
        return empty2
    entry = ctx.nominal_adt_table[type_name]
    return _copy_node(entry)


def collect_nominal_adt_table(east_module: Node) -> dict[str, Node]:
    """Module body から nominal ADT 宣言を収集する (純粋関数)。"""
    out: dict[str, Node] = {}
    body_obj = east_module.get("body")
    if not jv_is_list(body_obj):
        return out
    for item in jv_list(body_obj):
        if not jv_is_dict(item):
            continue
        nd: Node = jv_dict(item)
        if jv_str(nd.get("kind", "")) != CLASS_DEF:
            continue
        class_name = normalize_type_name(nd.get("name"))
        if class_name == "unknown":
            continue
        meta_obj = nd.get("meta")
        if not jv_is_dict(meta_obj):
            continue
        meta: Node = jv_dict(meta_obj)
        nom_obj = meta.get("nominal_adt_v1")
        if not jv_is_dict(nom_obj):
            continue
        nominal: Node = jv_dict(nom_obj)
        role = jv_str(nominal.get("role", ""))
        family_name = jv_str(nominal.get("family_name", ""))
        if (role != "family" and role != "variant") or family_name == "":
            continue
        entry: dict[str, JsonVal] = {}
        entry["role"] = role
        entry["family_name"] = family_name
        vn = jv_str(nominal.get("variant_name", ""))
        if vn != "":
            entry["variant_name"] = vn
        ps = jv_str(nominal.get("payload_style", ""))
        if ps != "":
            entry["payload_style"] = ps
        ft_obj = nd.get("field_types")
        if jv_is_dict(ft_obj):
            ftd: Node = jv_dict(ft_obj)
            fts: dict[str, JsonVal] = {}
            for fn_raw, ft_raw in ftd.items():
                fn = str(fn_raw).strip()
                if fn == "":
                    continue
                ft = normalize_type_name(ft_raw)
                if ft == "unknown":
                    continue
                fts[fn] = ft
            if len(fts) != 0:
                entry["field_types"] = fts
        out[class_name] = entry
    return out


def collect_nominal_adt_family_variants(ctx: CompileContext, family_name: str) -> list[str]:
    variants: list[str] = []
    for type_name, entry_node in ctx.nominal_adt_table.items():
        if jv_str(entry_node.get("role", "")) != "variant":
            continue
        if jv_str(entry_node.get("family_name", "")) != family_name:
            continue
        if type_name not in variants:
            variants.append(type_name)
    return variants


def make_nominal_adt_type_summary(name: str, family_name: str) -> Node:
    out: dict[str, JsonVal] = {}
    out["kind"] = NOMINAL_ADT_TYPE
    out["category"] = "nominal_adt"
    out["mirror"] = name
    out["nominal_adt_name"] = name
    out["nominal_adt_family"] = family_name
    out["nominal_variant_domain"] = "closed"
    return out


def hydrate_nominal_adt_summary(ctx: CompileContext, summary: Node, mirror: JsonVal) -> Node:
    category = jv_str(summary.get("category", "unknown"))
    summary_mirror = normalize_type_name(summary.get("mirror"))
    if summary_mirror == "unknown":
        summary_mirror = normalize_type_name(mirror)
    if category == "nominal_adt":
        return summary
    if category == "static":
        decl = lookup_nominal_adt_decl(ctx, summary_mirror)
        if "family_name" not in decl:
            return summary
        return make_nominal_adt_type_summary(summary_mirror, jv_str(decl.get("family_name", summary_mirror)))
    if category == "optional" and jv_str(summary.get("nominal_adt_name", "")) == "":
        inner_name = normalize_type_name(summary.get("inner_mirror"))
        if inner_name == "unknown":
            return summary
        decl = lookup_nominal_adt_decl(ctx, inner_name)
        if "family_name" not in decl:
            return summary
        out = _copy_node(summary)
        out["nominal_adt_name"] = inner_name
        out["nominal_adt_family"] = jv_str(decl.get("family_name", inner_name))
        out["nominal_variant_domain"] = "closed"
        out["inner_category"] = "nominal_adt"
        return out
    return summary


def is_dynamic_like_summary(summary: Node) -> bool:
    category = jv_str(summary.get("category", "unknown"))
    if category == "dynamic" or category == "dynamic_union":
        return True
    mirror = jv_str(summary.get("mirror", "unknown"))
    return mirror == "Any" or mirror == "object" or mirror == "unknown"


def set_type_expr_summary(node: Node, summary: Node) -> None:
    category = jv_str(summary.get("category", "unknown"))
    if category == "" or category == "unknown":
        return
    payload: dict[str, JsonVal] = {}
    payload["schema_version"] = 1
    for key, value in summary.items():
        skey = cast(str, key)
        payload[skey] = value
    node[_TYPE_EXPR_SUMMARY_KEY] = payload


def bridge_lane_payload(target_summary: Node, value_summary: Node) -> Node:
    target_copy = _copy_node(target_summary)
    value_copy = _copy_node(value_summary)
    out: dict[str, JsonVal] = {}
    out["schema_version"] = 1
    out["target"] = target_copy
    out["target_category"] = target_summary.get("category", "unknown")
    out["value"] = value_copy
    out["value_category"] = value_summary.get("category", "unknown")
    return out


# ---------------------------------------------------------------------------
# JSON contract helpers
# ---------------------------------------------------------------------------

def json_nominal_type_name(summary: Node) -> str:
    category = jv_str(summary.get("category", "unknown"))
    if category != "nominal_adt":
        return ""
    family = "" + jv_str(summary.get("nominal_adt_family", ""))
    if family != "json":
        return ""
    nn = "" + jv_str(summary.get("nominal_adt_name", ""))
    if nn != "":
        return nn
    mirror = "" + normalize_type_name(summary.get("mirror"))
    if mirror == "JsonValue" or mirror == "JsonObj" or mirror == "JsonArr":
        return mirror
    return ""


def expected_json_receiver_type_name(semantic_tag: str) -> str:
    for prefix, nominal in _JSON_RECEIVER_PREFIXES:
        if semantic_tag.startswith(prefix):
            return nominal
    return ""


def raise_json_contract_violation(semantic_tag: str, owner_summary: Node) -> None:
    expected = expected_json_receiver_type_name(semantic_tag)
    if expected == "":
        return
    actual = json_nominal_type_name(owner_summary)
    if actual == expected:
        return
    mirror = normalize_type_name(owner_summary.get("mirror"))
    category = jv_str(owner_summary.get("category", "unknown"))
    actual_desc = actual if actual != "" else mirror
    if actual_desc == "":
        actual_desc = "unknown"
    raise RuntimeError(
        "json_decode_contract_violation: "
        + semantic_tag
        + " requires "
        + expected
        + " nominal receiver TypeExpr, got "
        + actual_desc
        + " ("
        + category
        + ")"
    )


def representative_json_contract_metadata(ctx: CompileContext, call: Node, receiver_node: JsonVal) -> tuple[str, Node, Node]:
    result_summary = structured_type_expr_summary_from_node(call)
    receiver_summary = structured_type_expr_summary_from_node(receiver_node)
    rc = jv_str(result_summary.get("category", "unknown"))
    rf = jv_str(result_summary.get("nominal_adt_family", ""))
    rn = jv_str(result_summary.get("nominal_adt_name", ""))
    recc = jv_str(receiver_summary.get("category", "unknown"))
    recf = jv_str(receiver_summary.get("nominal_adt_family", ""))
    recn = jv_str(receiver_summary.get("nominal_adt_name", ""))
    if (
        rc == "optional"
        and rf == "json"
        and rn == "JsonObj"
        and recc == "nominal_adt"
        and recf == "json"
        and recn == "JsonValue"
    ):
        return ("type_expr", result_summary, receiver_summary)
    compat_result = type_expr_summary_from_node(ctx, call)
    compat_receiver = expr_type_summary(ctx, receiver_node)
    crc = jv_str(compat_result.get("category", "unknown"))
    crf = jv_str(compat_result.get("nominal_adt_family", ""))
    crn = jv_str(compat_result.get("nominal_adt_name", ""))
    crec = jv_str(compat_receiver.get("category", "unknown"))
    crecf = jv_str(compat_receiver.get("nominal_adt_family", ""))
    crecn = jv_str(compat_receiver.get("nominal_adt_name", ""))
    if (
        crc == "optional"
        and crf == "json"
        and crn == "JsonObj"
        and crec == "nominal_adt"
        and crecf == "json"
        and crecn == "JsonValue"
    ):
        return ("resolved_type_compat", compat_result, compat_receiver)
    raise RuntimeError(
        "json.value.as_obj representative lane requires json nominal contract: "
        + "receiver="
        + crec + "/" + crecf + "/" + crecn
        + ", result="
        + crc + "/" + crf + "/" + crn
    )
