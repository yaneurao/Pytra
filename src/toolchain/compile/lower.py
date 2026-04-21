"""EAST2 → EAST3 lowering: main entry point.

Port of toolchain/compile/east2_to_east3_lowering.py for toolchain.
§5.1: Any/object 禁止 — uses JsonVal throughout.
§5.3: Python 標準モジュール直接 import 禁止。
§5.6: グローバル可変状態禁止 — CompileContext 経由。
"""

from __future__ import annotations

from typing import Union

from pytra.typing import cast
from toolchain.compile.jv import JsonVal, Node, CompileContext, deep_copy_json
from toolchain.compile.jv import jv_str, jv_int, jv_bool, jv_dict, jv_list, jv_is_dict, jv_is_list, jv_is_int, jv_is_bool
from toolchain.compile.jv import nd_kind, nd_get_str, nd_get_str_or, nd_get_dict, nd_get_list, nd_get_int, nd_get_bool, nd_source_span
from toolchain.compile.source_span import walk_normalize_spans
from toolchain.compile.validate_east3 import validate_east3, format_result
from toolchain.common.kinds import (
    MODULE, FUNCTION_DEF, CLOSURE_DEF, CLASS_DEF, ASSIGN, ANN_ASSIGN, AUG_ASSIGN, RETURN,
    FOR, FOR_RANGE, FOR_CORE, CALL, ATTRIBUTE, NAME, CONSTANT,
    MATCH, VARIANT_PATTERN, PATTERN_BIND, PATTERN_WILDCARD,
    SUBSCRIPT, TUPLE, LIST, DICT, STARRED, BOOL_OP,
    BOX, UNBOX, IS_INSTANCE, IS_SUBCLASS, IS_SUBTYPE,
    OBJ_TYPE_ID, OBJ_BOOL, OBJ_LEN, OBJ_STR, OBJ_ITER_INIT, OBJ_ITER_NEXT,
    TYPE_PREDICATE_CALL, BUILTIN_CALL,
    NOMINAL_ADT_CTOR_CALL, NOMINAL_ADT_PROJECTION,
    NOMINAL_ADT_VARIANT_PATTERN, NOMINAL_ADT_PATTERN_BIND, NOMINAL_ADT_MATCH,
    JSON_DECODE_CALL,
    STATIC_RANGE_FOR_PLAN, RUNTIME_ITER_FOR_PLAN,
    NAME_TARGET, TUPLE_TARGET, EXPR_TARGET,
    NAMED_TYPE, GENERIC_TYPE, DYNAMIC_TYPE, NOMINAL_ADT_TYPE, OPTIONAL_TYPE, UNION_TYPE,
)
from toolchain.compile.type_summary import (
    type_expr_summary_from_payload,
    type_expr_summary_from_node,
    expr_type_summary,
    expr_type_name,
    set_type_expr_summary,
    is_dynamic_like_summary,
    bridge_lane_payload,
    unknown_type_summary,
    collect_nominal_adt_table,
    lookup_nominal_adt_decl,
    make_nominal_adt_type_summary,
    collect_nominal_adt_family_variants,
    json_nominal_type_name,
    raise_json_contract_violation,
    representative_json_contract_metadata,
    structured_type_expr_summary_from_node,
)
from toolchain.emit.common.profile_loader import load_lowering_profile
from toolchain.compile.passes import (
    lower_yield_generators,
    lower_listcomp,
    lower_nested_function_defs,
    expand_default_arguments,
    expand_forcore_tuple_targets,
    expand_tuple_unpack,
    lower_enumerate,
    lower_reversed,
    hoist_block_scope_variables,
    apply_integer_promotion,
    apply_guard_narrowing,
    apply_type_propagation,
    apply_yields_dynamic,
    apply_profile_lowering,
    detect_swap_patterns,
    detect_mutates_self,
    detect_unused_variables,
    mark_main_guard_discard,
)


def _normalize_dispatch_mode(value: JsonVal) -> str:
    if jv_str(value) == "native":
        return "native"
    if jv_str(value) == "type_id":
        return "type_id"
    return "native"


# ---------------------------------------------------------------------------
# Generic type splitting helpers
# ---------------------------------------------------------------------------

def _split_union_types(type_name: str) -> list[str]:
    parts: list[str] = []
    cur = ""
    depth = 0
    for ch in type_name:
        if ch == "[":
            depth += 1
            cur += ch
        elif ch == "]":
            if depth > 0:
                depth -= 1
            cur += ch
        elif ch == "|" and depth == 0:
            part = cur.strip()
            if part != "":
                parts.append(part)
            cur = ""
        else:
            cur += ch
    tail = cur.strip()
    if tail != "":
        parts.append(tail)
    return parts


def _split_generic_types(type_name: str) -> list[str]:
    parts: list[str] = []
    cur = ""
    depth = 0
    for ch in type_name:
        if ch == "[":
            depth += 1
            cur += ch
        elif ch == "]":
            if depth > 0:
                depth -= 1
            cur += ch
        elif ch == "," and depth == 0:
            part = cur.strip()
            if part != "":
                parts.append(part)
            cur = ""
        else:
            cur += ch
    tail = cur.strip()
    if tail != "":
        parts.append(tail)
    return parts


def _normalize_type_name_local(value: JsonVal) -> str:
    text = jv_str(value)
    if text == "":
        return ""
    return "" + text


def _normalize_type_name(value: JsonVal) -> str:
    return _normalize_type_name_local(value)


def _canonical_type_name(ctx: CompileContext, value: JsonVal) -> str:
    norm = _normalize_type_name(value)
    if norm in ("", "unknown"):
        return norm
    summary = type_expr_summary_from_payload(ctx, None, norm)
    mirror = _normalize_type_name(nd_get_str(summary, "mirror"))
    if mirror not in ("", "unknown"):
        return mirror
    return norm


def _copy_node(node: Node) -> Node:
    out: Node = {}
    for key, value in node.items():
        out[key] = deep_copy_json(value)
    return out


def _empty_casts() -> list[JsonVal]:
    return []


def _empty_jv_list() -> list[JsonVal]:
    return []


def _drop_last_char(text: str) -> str:
    if text == "":
        return ""
    return text[0 : len(text) - 1]


def _tuple_element_types(type_name: JsonVal) -> list[str]:
    norm = _normalize_type_name_local(type_name)
    if not norm.startswith("tuple["):
        return []
    if not norm.endswith("]"):
        return []
    inner = _drop_last_char(norm[6:])
    if inner == "":
        return []
    return _split_generic_types(inner)


# ---------------------------------------------------------------------------
# AST node helpers
# ---------------------------------------------------------------------------

def _is_any_like_type(type_name: JsonVal, ctx: CompileContext) -> bool:
    summary = type_expr_summary_from_payload(ctx, None, type_name)
    category = nd_get_str(summary, "category")
    if category == "dynamic" or category == "dynamic_union":
        return True
    mirror = nd_get_str(summary, "mirror")
    return mirror == "Any" or mirror == "object" or mirror == "unknown"


def _const_int_node(value: int) -> Node:
    out: Node = {}
    out["kind"] = CONSTANT
    out["resolved_type"] = "int64"
    out["borrow_kind"] = "value"
    out["casts"] = _empty_casts()
    out["repr"] = str(value)
    out["value"] = value
    return out


def _const_bool_node(value: bool) -> Node:
    out: Node = {}
    out["kind"] = CONSTANT
    out["resolved_type"] = "bool"
    out["borrow_kind"] = "value"
    out["casts"] = _empty_casts()
    out["repr"] = "True" if value else "False"
    out["value"] = value
    return out


def _make_name_node(name: str, resolved_type: str = "unknown") -> Node:
    out: Node = {}
    out["kind"] = NAME
    out["id"] = name
    out["resolved_type"] = resolved_type
    out["borrow_kind"] = "value"
    out["casts"] = _empty_casts()
    out["repr"] = name
    return out


def _node_source_span(node: JsonVal) -> JsonVal:
    return nd_source_span(node)


def _node_repr(node: JsonVal) -> str:
    if nd_get_str_or(node, "repr", "") == "":
        return ""
    return "" + nd_get_str_or(node, "repr", "")


def _copy_source_span_and_repr(source_expr: JsonVal, out: Node) -> None:
    span = _node_source_span(source_expr)
    if jv_is_dict(span):
        out["source_span"] = jv_dict(span)
    repr_txt = _node_repr(source_expr)
    if repr_txt != "":
        out["repr"] = repr_txt


def _make_boundary_expr(
    *,
    kind: str,
    value_key: str,
    value_node: JsonVal,
    resolved_type: str,
    source_expr: JsonVal,
    ctx: CompileContext,
) -> Node:
    out: Node = {}
    out["kind"] = kind
    out["resolved_type"] = resolved_type
    out["borrow_kind"] = "value"
    out["casts"] = _empty_casts()
    out[value_key] = value_node
    _copy_source_span_and_repr(source_expr, out)
    set_type_expr_summary(out, type_expr_summary_from_payload(ctx, None, resolved_type))
    return out


def _const_string_value(node: JsonVal) -> str:
    if not jv_is_dict(node):
        return ""
    d = jv_dict(node)
    kind = nd_kind(d)
    if kind == CONSTANT:
        if nd_get_str(d, "value") != "":
            return "" + nd_get_str(d, "value")
    if kind == CALL:
        func = nd_get_dict(d, "func")
        if len(func) > 0:
            fd = func
            fd_kind = nd_kind(fd)
            fd_id = nd_get_str(fd, "id")
            if fd_kind == NAME and fd_id == "str":
                args = nd_get_list(d, "args")
                if len(args) == 1:
                    for arg in args:
                        return _const_string_value(arg)
    return ""


def _is_string_index_expr(node: JsonVal) -> bool:
    if not jv_is_dict(node):
        return False
    nd = jv_dict(node)
    if nd_kind(nd) != SUBSCRIPT:
        return False
    value_node = nd_get_dict(nd, "value")
    slice_node = nd_get_dict(nd, "slice")
    if len(slice_node) > 0:
        slice_kind = nd_kind(slice_node)
        if slice_kind == "Slice":
            return False
    if len(value_node) == 0:
        return False
    return _normalize_type_name(nd_get_str(value_node, "resolved_type")) == "str"


def _make_named_type_expr(name: str) -> Node:
    out: Node = {}
    out["kind"] = NAMED_TYPE
    out["name"] = name
    return out


def _assignment_storage_type_override(stmt: Node, value_expr: JsonVal, target_type: str) -> str:
    stmt_kind = nd_kind(stmt)
    if stmt_kind != ANN_ASSIGN:
        return ""
    if target_type not in ("uint8", "byte"):
        return ""
    if not _is_string_index_expr(value_expr):
        return ""
    return "str"


_STATIC_CAST_SCALAR_TYPES: set[str] = {
    "int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64",
    "float32", "float64",
}


def _supports_static_scalar_cast(source_type: str, target_type: str) -> bool:
    if source_type == "" or target_type == "":
        return False
    if source_type == target_type:
        return False
    return source_type in _STATIC_CAST_SCALAR_TYPES and target_type in _STATIC_CAST_SCALAR_TYPES


def _make_static_scalar_cast_expr(value_expr: JsonVal, target_type: str, *, ctx: CompileContext) -> Node:
    func_name = "int"
    if target_type == "float32" or target_type == "float64":
        func_name = "float"
    out: Node = {}
    out["kind"] = CALL
    out["func"] = _make_name_node(func_name, "callable")
    out["args"] = [value_expr]
    out["keywords"] = _empty_jv_list()
    out["resolved_type"] = target_type
    out["borrow_kind"] = "value"
    out["casts"] = _empty_casts()
    out["lowered_kind"] = BUILTIN_CALL
    out["runtime_call"] = "static_cast"
    _copy_source_span_and_repr(value_expr, out)
    set_type_expr_summary(out, type_expr_summary_from_payload(ctx, None, target_type))
    return out


def _optional_inner_target_type(type_name: str) -> str:
    parts = _split_union_types(type_name)
    if len(parts) != 2:
        return ""
    if parts[0] == "None":
        return parts[1]
    if parts[1] == "None":
        return parts[0]
    return ""


def _split_dict_types(type_name: str) -> tuple[str, str]:
    norm = _normalize_type_name(type_name)
    if not (norm.startswith("dict[") and norm.endswith("]")):
        return "", ""
    parts = _split_generic_types(_drop_last_char(norm[5:]))
    if len(parts) != 2:
        return "", ""
    return parts[0], parts[1]


def _list_inner_type(type_name: str) -> str:
    norm = _normalize_type_name(type_name)
    if not (norm.startswith("list[") and norm.endswith("]")):
        return ""
    return _drop_last_char(norm[5:])


def _wrap_list_literal_for_target_type(value_expr: JsonVal, target_type: str, *, ctx: CompileContext) -> JsonVal:
    if not jv_is_dict(value_expr):
        return value_expr
    node: Node = jv_dict(value_expr)
    node_kind = nd_kind(node)
    if node_kind != LIST:
        return value_expr
    inner_type = _list_inner_type(target_type)
    if inner_type == "":
        return value_expr
    out: Node = _copy_node(node)
    elems_obj = nd_get_list(node, "elements")
    if len(elems_obj) > 0 or "elements" in node:
        elems_out: list[JsonVal] = []
        for item in elems_obj:
            if jv_is_dict(item):
                elems_out.append(_wrap_value_for_target_type(item, inner_type, ctx=ctx))
            else:
                elems_out.append(item)
        out["elements"] = elems_out
    out["resolved_type"] = target_type
    set_type_expr_summary(out, type_expr_summary_from_payload(ctx, None, target_type))
    return out


def _wrap_dict_literal_for_target_type(value_expr: JsonVal, target_type: str, *, ctx: CompileContext) -> JsonVal:
    if not jv_is_dict(value_expr):
        return value_expr
    node: Node = jv_dict(value_expr)
    node_kind = nd_kind(node)
    if node_kind != DICT:
        return value_expr
    key_type, val_type = _split_dict_types(target_type)
    if key_type == "" or val_type == "":
        return value_expr
    out: Node = _copy_node(node)
    entries_obj = nd_get_list(node, "entries")
    if len(entries_obj) > 0 or "entries" in node:
        wrapped_entries: list[JsonVal] = []
        for entry in entries_obj:
            if not jv_is_dict(entry):
                wrapped_entries.append(entry)
                continue
            entry_node: Node = jv_dict(entry)
            entry_out: Node = _copy_node(entry_node)
            key_node = entry_node.get("key")
            value_node = entry_node.get("value")
            if jv_is_dict(key_node):
                entry_out["key"] = _wrap_value_for_target_type(key_node, key_type, ctx=ctx)
            if jv_is_dict(value_node):
                entry_out["value"] = _wrap_value_for_target_type(value_node, val_type, ctx=ctx)
            wrapped_entries.append(entry_out)
        out["entries"] = wrapped_entries
    else:
        keys_obj = nd_get_list(node, "keys")
        values_obj = nd_get_list(node, "values")
        if len(keys_obj) > 0 or "keys" in node:
            keys_out: list[JsonVal] = []
            for item in keys_obj:
                if jv_is_dict(item):
                    keys_out.append(_wrap_value_for_target_type(item, key_type, ctx=ctx))
                else:
                    keys_out.append(item)
            out["keys"] = keys_out
        if len(values_obj) > 0 or "values" in node:
            values_out: list[JsonVal] = []
            for item in values_obj:
                if jv_is_dict(item):
                    values_out.append(_wrap_value_for_target_type(item, val_type, ctx=ctx))
                else:
                    values_out.append(item)
            out["values"] = values_out
    out["resolved_type"] = target_type
    set_type_expr_summary(out, type_expr_summary_from_payload(ctx, None, target_type))
    return out


def _is_none_literal(node: JsonVal) -> bool:
    if not jv_is_dict(node):
        return False
    nd: Node = jv_dict(node)
    if nd_kind(nd) != CONSTANT:
        return False
    value = nd.get("value")
    return value is None


# ---------------------------------------------------------------------------
# Statement lowering helpers
# ---------------------------------------------------------------------------

def _normalize_iter_mode(value: JsonVal) -> str:
    if jv_str(value) == "static_fastpath":
        return "static_fastpath"
    if jv_str(value) == "runtime_protocol":
        return "runtime_protocol"
    return "runtime_protocol"


def _copy_extra_fields(
    source: Node,
    out: Node,
    consumed: set[str],
    *,
    dispatch_mode: str,
    ctx: CompileContext,
) -> None:
    for key in source.keys():
        key_s = jv_str(key)
        if key_s in consumed:
            continue
        value = source[key_s]
        out[key_s] = _lower_node(value, dispatch_mode=dispatch_mode, ctx=ctx)


def _wrap_value_for_target_type(
    value_expr: JsonVal,
    target_type: str,
    ctx: CompileContext,
    *,
    target_type_expr: JsonVal = None,
) -> JsonVal:
    target_summary: Node = type_expr_summary_from_payload(ctx, target_type_expr, target_type)
    target_t = _normalize_type_name(nd_get_str(target_summary, "mirror"))
    if target_t == "unknown":
        return value_expr
    value_summary: Node = expr_type_summary(ctx, value_expr)
    target_contains_dynamic_lane = (
        "Any" in target_t or "object" in target_t or "unknown" in target_t
    )
    value_t = _normalize_type_name(nd_get_str(value_summary, "mirror"))
    if target_t in ("dict", "list", "set", "tuple") and value_t.startswith(target_t + "["):
        target_t = value_t
        target_summary = type_expr_summary_from_payload(ctx, None, target_t)
    value_requires_runtime_unbox = jv_is_dict(value_expr) and nd_get_bool(jv_dict(value_expr), "yields_dynamic")
    storage_type = ""
    if jv_is_dict(value_expr) and nd_kind(jv_dict(value_expr)) == NAME:
        storage_type = _canonical_type_name(ctx, ctx.lookup_storage_type(nd_get_str(jv_dict(value_expr), "id")))
    storage_requires_runtime_unbox = (
        storage_type not in ("", "unknown")
        and storage_type != target_t
        and (
            storage_type.endswith(" | None")
            or storage_type.endswith("|None")
            or "|" in storage_type
            or "Any" in storage_type
            or "object" in storage_type
            or storage_type == "Obj"
        )
        and not is_dynamic_like_summary(target_summary)
    )
    target_optional_inner = _optional_inner_target_type(target_t)
    unbox_target = ""
    if value_t == target_t:
        unbox_target = target_t
    elif target_optional_inner != "" and value_t == target_optional_inner:
        unbox_target = target_optional_inner
    if (
        storage_requires_runtime_unbox
        and unbox_target != ""
        and storage_type != unbox_target
    ):
        storage_summary: Node = type_expr_summary_from_payload(ctx, None, storage_type)
        unbox_summary: Node = type_expr_summary_from_payload(ctx, None, unbox_target)
        out = _make_boundary_expr(
            kind="Unbox", value_key="value", value_node=value_expr,
            resolved_type=unbox_target, source_expr=value_expr,
            ctx=ctx,
        )
        out["target"] = unbox_target
        out["on_fail"] = "raise"
        out["bridge_lane_v1"] = bridge_lane_payload(unbox_summary, storage_summary)
        set_type_expr_summary(out, unbox_summary)
        return out
    if storage_requires_runtime_unbox:
        storage_summary: Node = type_expr_summary_from_payload(ctx, None, storage_type)
        out = _make_boundary_expr(
            kind="Unbox", value_key="value", value_node=value_expr,
            resolved_type=target_t, source_expr=value_expr,
            ctx=ctx,
        )
        out["target"] = target_t
        out["on_fail"] = "raise"
        out["bridge_lane_v1"] = bridge_lane_payload(target_summary, storage_summary)
        set_type_expr_summary(out, target_summary)
        return out
    if (
        target_contains_dynamic_lane
        and not is_dynamic_like_summary(target_summary)
        and not is_dynamic_like_summary(value_summary)
        and not value_requires_runtime_unbox
        and value_t != "unknown"
        and value_t != target_t
    ):
        out = _make_boundary_expr(
            kind="Box", value_key="value", value_node=value_expr,
            resolved_type=target_t, source_expr=value_expr,
            ctx=ctx,
        )
        out["target"] = target_t
        out["bridge_lane_v1"] = bridge_lane_payload(target_summary, value_summary)
        set_type_expr_summary(out, target_summary)
        return out
    if is_dynamic_like_summary(target_summary) and not is_dynamic_like_summary(value_summary):
        box_resolved_type = "object"
        if ctx.target_language == "cpp" and target_t not in ("", "unknown"):
            box_resolved_type = target_t
        out = _make_boundary_expr(
            kind="Box", value_key="value", value_node=value_expr,
            resolved_type=box_resolved_type, source_expr=value_expr,
            ctx=ctx,
        )
        out["bridge_lane_v1"] = bridge_lane_payload(target_summary, value_summary)
        set_type_expr_summary(out, target_summary)
        return out
    if not is_dynamic_like_summary(target_summary) and (
        is_dynamic_like_summary(value_summary) or value_requires_runtime_unbox
    ):
        bridge_value_summary: Node = value_summary
        if value_requires_runtime_unbox and not is_dynamic_like_summary(value_summary):
            bridge_value_summary = unknown_type_summary()
        out = _make_boundary_expr(
            kind="Unbox", value_key="value", value_node=value_expr,
            resolved_type=target_t, source_expr=value_expr,
            ctx=ctx,
        )
        out["target"] = target_t
        out["on_fail"] = "raise"
        out["bridge_lane_v1"] = bridge_lane_payload(target_summary, bridge_value_summary)
        set_type_expr_summary(out, target_summary)
        return out
    optional_inner = _optional_inner_target_type(target_t)
    if _supports_static_scalar_cast(value_t, optional_inner):
        return _make_static_scalar_cast_expr(value_expr, optional_inner, ctx=ctx)
    if not is_dynamic_like_summary(target_summary) and jv_is_dict(value_expr):
        value_kind = nd_kind(value_expr)
        if value_kind == LIST:
            return _wrap_list_literal_for_target_type(value_expr, target_t, ctx=ctx)
        if value_kind == DICT:
            return _wrap_dict_literal_for_target_type(value_expr, target_t, ctx=ctx)
    if _supports_static_scalar_cast(value_t, target_t):
        return _make_static_scalar_cast_expr(value_expr, target_t, ctx=ctx)
    return value_expr


def _resolve_assign_target_type_summary(stmt: Node, ctx: CompileContext) -> JsonVal:
    decl_expr = stmt.get("decl_type_expr")
    summary: Node = type_expr_summary_from_payload(ctx, decl_expr, stmt.get("decl_type"))
    if nd_get_str(summary, "category") != "unknown":
        return summary
    ann_expr = stmt.get("annotation_type_expr")
    summary = type_expr_summary_from_payload(ctx, ann_expr, stmt.get("annotation"))
    if nd_get_str(summary, "category") != "unknown":
        return summary
    target_obj = stmt.get("target")
    if jv_is_dict(target_obj):
        tod: Node = jv_dict(target_obj)
        summary = type_expr_summary_from_payload(ctx, tod.get("type_expr"), tod.get("resolved_type"))
        if nd_get_str(summary, "category") != "unknown":
            mirror = _normalize_type_name(nd_get_str(summary, "mirror"))
            if nd_kind(tod) != TUPLE or "unknown" not in mirror:
                return summary
        inferred_tuple_type = _infer_tuple_assign_target_type(stmt)
        if inferred_tuple_type != "unknown":
            return type_expr_summary_from_payload(ctx, None, inferred_tuple_type)
    return unknown_type_summary()


def _infer_tuple_assign_target_type(stmt: Node) -> str:
    target_obj = stmt.get("target")
    if not jv_is_dict(target_obj):
        return "unknown"
    target: Node = jv_dict(target_obj)
    if nd_kind(target) != TUPLE:
        return "unknown"

    elem_types: list[str] = []
    any_known = False
    elements_obj = target.get("elements")
    if jv_is_list(elements_obj):
        for elem in jv_list(elements_obj):
            if not jv_is_dict(elem):
                elem_types.append("unknown")
                continue
            elem_type = _normalize_type_name(nd_get_str(elem, "resolved_type"))
            if elem_type != "unknown":
                any_known = True
            elem_types.append(elem_type)
    all_known = len(elem_types) > 0
    for elem_type in elem_types:
        if elem_type == "unknown":
            all_known = False
            break
    if all_known:
        return "tuple[" + ",".join(elem_types) + "]"

    value_obj = stmt.get("value")
    if jv_is_dict(value_obj):
        value_node: Node = jv_dict(value_obj)
        value_type = _normalize_type_name(value_node.get("resolved_type"))
        if value_type.startswith("tuple[") and value_type.endswith("]"):
            return value_type

    if len(elem_types) > 0 and any_known:
        return "tuple[" + ",".join(elem_types) + "]"
    return "unknown"


def _resolve_assign_target_type(stmt: Node, ctx: CompileContext) -> str:
    summary = jv_dict(_resolve_assign_target_type_summary(stmt, ctx))
    mirror = _normalize_type_name(nd_get_str(summary, "mirror"))
    if mirror != "unknown":
        return mirror
    tuple_type = _infer_tuple_assign_target_type(stmt)
    if tuple_type != "unknown":
        return tuple_type
    decl_type = _normalize_type_name(stmt.get("decl_type"))
    if decl_type != "unknown":
        return decl_type
    ann_type = _normalize_type_name(stmt.get("annotation"))
    if ann_type != "unknown":
        return ann_type
    target_obj = stmt.get("target")
    if jv_is_dict(target_obj):
        tod: Node = jv_dict(target_obj)
        target_t = _normalize_type_name(tod.get("resolved_type"))
        if target_t != "unknown":
            return target_t
    return "unknown"


def _build_target_plan(
    target: JsonVal,
    target_type: JsonVal,
    *,
    dispatch_mode: str,
    ctx: CompileContext,
) -> Node:
    tt_norm = _normalize_type_name(target_type)
    if jv_is_dict(target):
        td: Node = jv_dict(target)
        kind = nd_kind(td)
        if kind == NAME:
            name_plan: Node = {}
            name_plan["kind"] = NAME_TARGET
            name_plan["id"] = td.get("id", "")
            if tt_norm != "unknown":
                name_plan["target_type"] = tt_norm
            return name_plan
        if kind == TUPLE:
            elems_obj = td.get("elements")
            elem_plans: list[JsonVal] = []
            elem_types = _tuple_element_types(tt_norm)
            if jv_is_list(elems_obj):
                elems = jv_list(elems_obj)
                i = 0
                for elem in elems:
                    et = "unknown"
                    if i < len(elem_types):
                        et = elem_types[i]
                    elem_plans.append(_build_target_plan(elem, et, dispatch_mode=dispatch_mode, ctx=ctx))
                    i += 1
            tuple_plan: Node = {}
            tuple_plan["kind"] = TUPLE_TARGET
            tuple_plan["elements"] = elem_plans
            if tt_norm != "unknown":
                tuple_plan["target_type"] = tt_norm
            return tuple_plan
    expr_plan: Node = {}
    expr_plan["kind"] = EXPR_TARGET
    expr_plan["target"] = _lower_node(target, dispatch_mode=dispatch_mode, ctx=ctx)
    if tt_norm != "unknown":
        expr_plan["target_type"] = tt_norm
    return expr_plan


def _lower_assignment_like_stmt(stmt: Node, *, dispatch_mode: str, ctx: CompileContext) -> Node:
    out: Node = {}
    for key_s, value in stmt.items():
        if key_s == "value":
            continue
        out[key_s] = _lower_node(value, dispatch_mode=dispatch_mode, ctx=ctx)
    if "value" not in stmt or stmt.get("value") is None:
        return out
    value_lowered = _lower_node(stmt.get("value"), dispatch_mode=dispatch_mode, ctx=ctx)
    target_summary = jv_dict(_resolve_assign_target_type_summary(stmt, ctx))
    target_type = _normalize_type_name(nd_get_str(target_summary, "mirror"))
    if target_type == "unknown":
        target_type = _resolve_assign_target_type(stmt, ctx)
    target_obj = stmt.get("target")
    target_type_expr = stmt.get("decl_type_expr")
    if target_type_expr is None:
        target_type_expr = stmt.get("annotation_type_expr")
    if target_type_expr is None and jv_is_dict(target_obj):
        tod: Node = jv_dict(target_obj)
        target_type_expr = tod.get("type_expr")
    value_lowered_node: Node = {}
    has_value_lowered_node = False
    if jv_is_dict(value_lowered):
        value_lowered_node = jv_dict(value_lowered)
        has_value_lowered_node = True
    if target_type_expr is None and has_value_lowered_node and nd_kind(value_lowered_node) == UNBOX:
        unboxed_type = _normalize_type_name(value_lowered_node.get("resolved_type"))
        if unboxed_type not in ("", "unknown"):
            optional_inner = _optional_inner_target_type(target_type)
            if target_type in ("", "unknown") or optional_inner == unboxed_type:
                target_type = unboxed_type
                target_type_expr = _make_named_type_expr(unboxed_type)
                out["decl_type"] = unboxed_type
                out["decl_type_expr"] = target_type_expr
                target_out: JsonVal = out.get("target")
                if jv_is_dict(target_out):
                    target_dict: Node = jv_dict(target_out)
                    target_dict["resolved_type"] = unboxed_type
                    target_dict["type_expr"] = target_type_expr
    storage_type = _assignment_storage_type_override(stmt, value_lowered, target_type)
    if storage_type != "":
        target_type = storage_type
        target_type_expr = _make_named_type_expr(storage_type)
        out["decl_type"] = storage_type
        out["decl_type_expr"] = target_type_expr
        target_out: JsonVal = out.get("target")
        if jv_is_dict(target_out):
            target_dict: Node = jv_dict(target_out)
            target_dict["resolved_type"] = storage_type
            target_dict["type_expr"] = target_type_expr
    out["value"] = _wrap_value_for_target_type(
        value_lowered, target_type, target_type_expr=target_type_expr,
        ctx=ctx,
    )
    set_type_expr_summary(out, type_expr_summary_from_payload(ctx, target_type_expr, target_type))
    target_out: JsonVal = out.get("target")
    target_dict: Node = {}
    has_target_dict = False
    if jv_is_dict(target_out):
        target_dict = jv_dict(target_out)
        has_target_dict = True
    if has_target_dict and nd_kind(target_dict) == NAME:
        target_name = jv_str(target_dict.get("id", ""))
        storage_type = _normalize_type_name(out.get("decl_type"))
        if storage_type == "unknown":
            storage_type = target_type
        if storage_type != "unknown":
            ctx.set_storage_type(target_name, storage_type)
    return out


def _lower_return_stmt(stmt: Node, *, dispatch_mode: str, ctx: CompileContext) -> Node:
    out: Node = {}
    for key_s, value in stmt.items():
        if key_s == "value":
            continue
        out[key_s] = _lower_node(value, dispatch_mode=dispatch_mode, ctx=ctx)
    if "value" not in stmt or stmt.get("value") is None:
        return out
    value_lowered = _lower_node(stmt.get("value"), dispatch_mode=dispatch_mode, ctx=ctx)
    target_type = _normalize_type_name(ctx.current_return_type)
    if target_type not in ("", "unknown", "None"):
        value_lowered = _wrap_value_for_target_type(value_lowered, target_type, ctx=ctx)
    out["value"] = value_lowered
    return out


def _lower_function_def_stmt(
    stmt: Node,
    *,
    dispatch_mode: str,
    ctx: CompileContext,
) -> Node:
    prev_return_type: str = ctx.current_return_type
    ctx.push_storage_scope()
    ctx.current_return_type = _normalize_type_name(stmt.get("return_type"))
    try:
        arg_types_obj = stmt.get("arg_types")
        arg_order_obj = stmt.get("arg_order")
        if jv_is_dict(arg_types_obj) and jv_is_list(arg_order_obj):
            for arg_name_jv in jv_list(arg_order_obj):
                arg_name = jv_str(arg_name_jv)
                arg_type_s = nd_get_str(arg_types_obj, arg_name)
                if arg_name != "" and arg_type_s != "":
                    ctx.set_storage_type(arg_name, arg_type_s)
        vararg_name = jv_str(stmt.get("vararg_name", ""))
        vararg_type = jv_str(stmt.get("vararg_type", ""))
        if vararg_name != "" and vararg_type != "":
            ctx.set_storage_type(vararg_name, vararg_type)
        out: Node = {}
        for key_s, value in stmt.items():
            out[key_s] = _lower_node(value, dispatch_mode=dispatch_mode, ctx=ctx)
        return out
    finally:
        ctx.current_return_type = prev_return_type
        ctx.pop_storage_scope()


def _lower_for_stmt(stmt: Node, *, dispatch_mode: str, ctx: CompileContext) -> Node:
    iter_expr = _lower_node(stmt.get("iter"), dispatch_mode=dispatch_mode, ctx=ctx)
    iter_plan: Node = {}
    iter_plan["kind"] = RUNTIME_ITER_FOR_PLAN
    iter_plan["iter_expr"] = iter_expr
    iter_plan["dispatch_mode"] = dispatch_mode
    iter_plan["init_op"] = OBJ_ITER_INIT
    iter_plan["next_op"] = OBJ_ITER_NEXT
    target_type = _normalize_type_name(stmt.get("target_type"))
    if target_type == "unknown":
        target_type = _normalize_type_name(stmt.get("iter_element_type"))
    out: Node = {}
    out["kind"] = FOR_CORE
    out["iter_mode"] = "runtime_protocol"
    out["iter_plan"] = iter_plan
    out["target_plan"] = _build_target_plan(stmt.get("target"), target_type, dispatch_mode=dispatch_mode, ctx=ctx)
    body_obj = stmt.get("body")
    if jv_is_list(body_obj):
        out["body"] = _lower_node(body_obj, dispatch_mode=dispatch_mode, ctx=ctx)
    else:
        out["body"] = _lower_node(_empty_jv_list(), dispatch_mode=dispatch_mode, ctx=ctx)
    orelse_obj = stmt.get("orelse")
    if jv_is_list(orelse_obj):
        out["orelse"] = _lower_node(orelse_obj, dispatch_mode=dispatch_mode, ctx=ctx)
    else:
        out["orelse"] = _lower_node(_empty_jv_list(), dispatch_mode=dispatch_mode, ctx=ctx)
    consumed = {"kind", "target", "target_type", "iter_mode", "iter_source_type", "iter_element_type", "iter", "body", "orelse"}
    _copy_extra_fields(stmt, out, consumed, dispatch_mode=dispatch_mode, ctx=ctx)
    return out


def _lower_forrange_stmt(stmt: Node, *, dispatch_mode: str, ctx: CompileContext) -> Node:
    start_node = _lower_node(stmt.get("start"), dispatch_mode=dispatch_mode, ctx=ctx)
    stop_node = _lower_node(stmt.get("stop"), dispatch_mode=dispatch_mode, ctx=ctx)
    step_node = _lower_node(stmt.get("step"), dispatch_mode=dispatch_mode, ctx=ctx)
    if not jv_is_dict(step_node):
        step_node = _const_int_node(1)
    iter_plan: Node = {}
    iter_plan["kind"] = STATIC_RANGE_FOR_PLAN
    iter_plan["start"] = start_node
    iter_plan["stop"] = stop_node
    iter_plan["step"] = step_node
    out: Node = {}
    out["kind"] = FOR_CORE
    out["iter_mode"] = "static_fastpath"
    out["iter_plan"] = iter_plan
    out["target_plan"] = _build_target_plan(stmt.get("target"), stmt.get("target_type"), dispatch_mode=dispatch_mode, ctx=ctx)
    body_obj = stmt.get("body")
    if jv_is_list(body_obj):
        out["body"] = _lower_node(body_obj, dispatch_mode=dispatch_mode, ctx=ctx)
    else:
        out["body"] = _lower_node(_empty_jv_list(), dispatch_mode=dispatch_mode, ctx=ctx)
    orelse_obj = stmt.get("orelse")
    if jv_is_list(orelse_obj):
        out["orelse"] = _lower_node(orelse_obj, dispatch_mode=dispatch_mode, ctx=ctx)
    else:
        out["orelse"] = _lower_node(_empty_jv_list(), dispatch_mode=dispatch_mode, ctx=ctx)
    consumed = {"kind", "target", "target_type", "start", "stop", "step", "range_mode", "body", "orelse"}
    _copy_extra_fields(stmt, out, consumed, dispatch_mode=dispatch_mode, ctx=ctx)
    return out


def _lower_forcore_stmt(stmt: Node, *, dispatch_mode: str, ctx: CompileContext) -> Node:
    out: Node = {}
    for key_s, value in stmt.items():
        out[key_s] = _lower_node(value, dispatch_mode=dispatch_mode, ctx=ctx)
    ip = out.get("iter_plan")
    if jv_is_dict(ip):
        ipd: Node = jv_dict(ip)
        if nd_kind(ipd) == RUNTIME_ITER_FOR_PLAN:
            ipd["dispatch_mode"] = dispatch_mode
    return out


# ---------------------------------------------------------------------------
# Nominal ADT metadata helpers
# ---------------------------------------------------------------------------

def _build_nominal_adt_ctor_meta(call: Node, ctx: CompileContext) -> JsonVal:
    func_obj = call.get("func")
    if not jv_is_dict(func_obj):
        return None
    func_node: Node = jv_dict(func_obj)
    if nd_kind(func_node) != NAME:
        return None
    ctor_name = _normalize_type_name(func_node.get("id"))
    decl_obj = lookup_nominal_adt_decl(ctx, ctor_name)
    if not jv_is_dict(decl_obj):
        return None
    decl: Node = jv_dict(decl_obj)
    decl_role = jv_str(decl["role"] if "role" in decl else "")
    if decl_role != "variant":
        return None
    ps = jv_str(decl["payload_style"] if "payload_style" in decl else "")
    if ps == "":
        ps = "unit"
    meta: Node = {}
    meta["schema_version"] = 1
    meta["ir_category"] = NOMINAL_ADT_CTOR_CALL
    meta["family_name"] = jv_str(decl["family_name"] if "family_name" in decl else ctor_name)
    meta["variant_name"] = ctor_name
    meta["payload_style"] = ps
    return meta


def _decorate_nominal_adt_ctor_call(call: Node, ctx: CompileContext) -> Node:
    meta_obj = _build_nominal_adt_ctor_meta(call, ctx)
    if not jv_is_dict(meta_obj):
        return call
    meta: Node = jv_dict(meta_obj)
    call["semantic_tag"] = "nominal_adt.variant_ctor"
    call["lowered_kind"] = NOMINAL_ADT_CTOR_CALL
    call["nominal_adt_ctor_v1"] = meta
    set_type_expr_summary(call, make_nominal_adt_type_summary(jv_str(meta["variant_name"]), jv_str(meta["family_name"])))
    return call


def _decorate_nominal_adt_projection_attr(attr_expr: Node, ctx: CompileContext) -> Node:
    attr_name = jv_str(attr_expr.get("attr", ""))
    if attr_name == "":
        return attr_expr
    owner_summary: Node = expr_type_summary(ctx, attr_expr.get("value"))
    owner_category = jv_str(owner_summary["category"] if "category" in owner_summary else "unknown")
    if owner_category != "nominal_adt":
        return attr_expr
    variant_name = _normalize_type_name(nd_get_str(owner_summary, "nominal_adt_name"))
    if variant_name == "unknown":
        variant_name = _normalize_type_name(nd_get_str(owner_summary, "mirror"))
    decl_obj = lookup_nominal_adt_decl(ctx, variant_name)
    if not jv_is_dict(decl_obj):
        return attr_expr
    decl: Node = jv_dict(decl_obj)
    decl_role = jv_str(decl["role"] if "role" in decl else "")
    if decl_role != "variant":
        return attr_expr
    ft: Node = {}
    ft_obj = decl.get("field_types")
    if jv_is_dict(ft_obj):
        ft = jv_dict(ft_obj)
    field_type = _normalize_type_name(ft.get(attr_name))
    if field_type == "unknown":
        return attr_expr
    meta: Node = {}
    meta["schema_version"] = 1
    meta["ir_category"] = NOMINAL_ADT_PROJECTION
    meta["family_name"] = jv_str(decl["family_name"] if "family_name" in decl else variant_name)
    meta["variant_name"] = variant_name
    meta["field_name"] = attr_name
    meta["field_type"] = field_type
    ps = jv_str(decl["payload_style"] if "payload_style" in decl else "")
    if ps != "":
        meta["payload_style"] = ps
    attr_expr["semantic_tag"] = "nominal_adt.variant_projection"
    attr_expr["lowered_kind"] = NOMINAL_ADT_PROJECTION
    attr_expr["nominal_adt_projection_v1"] = meta
    attr_expr["resolved_type"] = field_type
    set_type_expr_summary(attr_expr, type_expr_summary_from_payload(ctx, None, field_type))
    return attr_expr


def _decorate_nominal_adt_variant_pattern(pattern: Node, ctx: CompileContext) -> Node:
    _ = ctx
    return pattern


def _decorate_nominal_adt_match_stmt(match_stmt: Node, ctx: CompileContext) -> Node:
    _ = ctx
    return match_stmt


# ---------------------------------------------------------------------------
# Call metadata helpers
# ---------------------------------------------------------------------------

_JSON_DECODE_META_KEY: str = "json_decode_v1"


def _infer_json_semantic_tag(call: Node, *, legacy_compat_bridge_enabled: bool, ctx: CompileContext) -> str:
    st = jv_str(call.get("semantic_tag", ""))
    if st.startswith("json."):
        return "" + st
    mid = jv_str(call.get("runtime_module_id", ""))
    rs = jv_str(call.get("runtime_symbol", ""))
    if mid == "pytra.std.json":
        if rs == "loads":
            return "json.loads"
        if rs == "loads_obj":
            return "json.loads_obj"
        if rs == "loads_arr":
            return "json.loads_arr"
    func_obj = call.get("func")
    if jv_is_dict(func_obj):
        func_node: Node = jv_dict(func_obj)
        if nd_kind(func_node) != ATTRIBUTE:
            return ""
        attr = jv_str(func_node.get("attr", ""))
        owner = func_node.get("value")
        os: Node = expr_type_summary(ctx, owner)
        on = json_nominal_type_name(os)
        if on == "JsonValue" and attr in ("as_obj", "as_arr", "as_str", "as_int", "as_float", "as_bool"):
            return "json.value." + attr
        if on == "JsonObj" and attr in ("get", "get_obj", "get_arr", "get_str", "get_int", "get_float", "get_bool"):
            return "json.obj." + attr
        if on == "JsonArr" and attr in ("get", "get_obj", "get_arr", "get_str", "get_int", "get_float", "get_bool"):
            return "json.arr." + attr
        if legacy_compat_bridge_enabled and attr in ("loads", "loads_obj", "loads_arr"):
            if jv_is_dict(owner):
                owner_node: Node = jv_dict(owner)
                if nd_kind(owner_node) != NAME:
                    return ""
                own = jv_str(owner_node.get("id", ""))
                if own == "json":
                    return "json." + attr
    return ""


def _build_json_decode_meta(call: Node, semantic_tag: str, ctx: CompileContext) -> Node:
    meta: Node = {}
    meta["schema_version"] = 1
    meta["semantic_tag"] = semantic_tag
    meta["result_type"] = type_expr_summary_from_node(ctx, call)
    if semantic_tag.startswith("json.loads"):
        meta["decode_kind"] = "module_load"
        return meta
    func_obj = call.get("func")
    if not jv_is_dict(func_obj):
        meta["decode_kind"] = "helper_call"
        return meta
    func_node: Node = jv_dict(func_obj)
    if nd_kind(func_node) != ATTRIBUTE:
        meta["decode_kind"] = "helper_call"
        return meta
    owner = func_node.get("value")
    os2: Node = expr_type_summary(ctx, owner)
    raise_json_contract_violation(semantic_tag, os2)
    meta["decode_kind"] = "narrow"
    meta["receiver_type"] = os2
    rc = jv_str(os2.get("category", "unknown"))
    if rc != "unknown":
        meta["receiver_category"] = rc
    nn = jv_str(os2.get("nominal_adt_name", ""))
    if nn != "":
        meta["receiver_nominal_adt_name"] = nn
    nf = jv_str(os2.get("nominal_adt_family", ""))
    if nf != "":
        meta["receiver_nominal_adt_family"] = nf
    return meta


def _lower_representative_json_decode_call(out_call: Node, ctx: CompileContext) -> Node:
    _ctx = ctx
    _ = _ctx
    return out_call


def _decorate_call_metadata(call: Node, *, legacy_compat_bridge_enabled: bool, ctx: CompileContext) -> Node:
    call = _decorate_nominal_adt_ctor_call(call, ctx)
    json_tag = _infer_json_semantic_tag(call, legacy_compat_bridge_enabled=legacy_compat_bridge_enabled, ctx=ctx)
    if json_tag != "":
        call["semantic_tag"] = json_tag
        call[_JSON_DECODE_META_KEY] = _build_json_decode_meta(call, json_tag, ctx)
        call = _lower_representative_json_decode_call(call, ctx)
    return call


# ---------------------------------------------------------------------------
# Type ID predicate lowering
# ---------------------------------------------------------------------------

def _builtin_type_id_symbol(type_name: str) -> str:
    table: dict[str, str] = {
        "None": "PYTRA_TID_NONE",
        "str": "PYTRA_TID_STR", "list": "PYTRA_TID_LIST",
        "dict": "PYTRA_TID_DICT", "set": "PYTRA_TID_SET",
    }
    return table.get(type_name, "")


_POD_EXACT_TYPE_NAMES: set[str] = {
    "bool",
    "int8", "uint8",
    "int16", "uint16",
    "int32", "uint32",
    "int64", "uint64",
    "float32", "float64",
}


def _normalize_type_predicate_target_name(type_name: str) -> str:
    tn = _normalize_type_name(type_name)
    if tn == "int":
        return "int64"
    if tn == "float":
        return "float64"
    return tn


def _make_type_predicate_expr(
    kind: str,
    left_key: str,
    left_expr: JsonVal,
    source_expr: JsonVal,
    ctx: CompileContext,
    expected_type_id_expr: JsonVal = None,
    expected_type_name: str = "",
) -> Node:
    out: Node = {}
    out["kind"] = kind
    out["resolved_type"] = "bool"
    out["borrow_kind"] = "value"
    out["casts"] = _empty_casts()
    out[left_key] = left_expr
    if kind == IS_INSTANCE:
        out["expected_type_name"] = expected_type_name
    else:
        out["expected_type_id"] = expected_type_id_expr
    _copy_source_span_and_repr(source_expr, out)
    ls: Node = expr_type_summary(ctx, left_expr)
    set_type_expr_summary(out, ls)
    mode = jv_str(ls.get("category", "unknown"))
    if mode != "" and mode != "unknown":
        lane: Node = {}
        lane["schema_version"] = 1
        lane["source_category"] = mode
        lane["source_type"] = ls
        out["narrowing_lane_v1"] = lane
    return out


def _build_nominal_adt_type_test_meta(type_ref_expr: JsonVal, ctx: CompileContext) -> JsonVal:
    if not jv_is_dict(type_ref_expr):
        return None
    trd: Node = jv_dict(type_ref_expr)
    if nd_kind(trd) != NAME:
        return None
    tn = _normalize_type_name(trd.get("id"))
    decl_obj = lookup_nominal_adt_decl(ctx, tn)
    if not jv_is_dict(decl_obj):
        return None
    decl: Node = jv_dict(decl_obj)
    meta: Node = {}
    meta["schema_version"] = 1
    meta["family_name"] = jv_str(decl.get("family_name", tn))
    role = jv_str(decl.get("role", ""))
    if role == "family":
        meta["predicate_kind"] = "family"
        return meta
    meta["predicate_kind"] = "variant"
    meta["variant_name"] = tn
    ps = jv_str(decl.get("payload_style", ""))
    if ps != "":
        meta["payload_style"] = ps
    return meta


def _attach_nominal_adt_type_test_meta(check: Node, ttm: Node | None) -> Node:
    if not jv_is_dict(ttm):
        return check
    ttm_node: Node = jv_dict(ttm)
    check["nominal_adt_test_v1"] = ttm_node
    lane = check.get("narrowing_lane_v1")
    l2: Node = {}
    if jv_is_dict(lane):
        _ = lane
    if "schema_version" not in l2:
        l2["schema_version"] = 1
    l2["predicate_category"] = "nominal_adt"
    l2["family_name"] = jv_str(ttm_node.get("family_name", ""))
    pk2 = jv_str(ttm_node.get("predicate_kind", ""))
    if pk2 != "":
        l2["predicate_kind"] = pk2
    vn3 = jv_str(ttm_node.get("variant_name", ""))
    if vn3 != "":
        l2["variant_name"] = vn3
    check["narrowing_lane_v1"] = l2
    return check


def _build_or_of_checks(checks: list[Node], source_expr: JsonVal) -> Node:
    if len(checks) == 1:
        return checks[0]
    out: Node = {}
    out["kind"] = BOOL_OP
    out["op"] = "Or"
    check_values: list[JsonVal] = _empty_jv_list()
    for check in checks:
        check_values.append(check)
    out["values"] = check_values
    out["resolved_type"] = "bool"
    out["borrow_kind"] = "value"
    out["casts"] = _empty_casts()
    _copy_source_span_and_repr(source_expr, out)
    return out


def _type_ref_to_type_id(
    type_ref_expr: JsonVal, *, dispatch_mode: str,
    ctx: CompileContext,
) -> JsonVal:
    node = _lower_node(type_ref_expr, dispatch_mode=dispatch_mode, ctx=ctx)
    if not jv_is_dict(node):
        return None
    node_dict: Node = jv_dict(node)
    if nd_kind(node_dict) != NAME:
        return None
    tn = _normalize_type_predicate_target_name(jv_str(node_dict.get("id", "")))
    if tn == "":
        return None
    if tn in _POD_EXACT_TYPE_NAMES:
        out = _make_name_node(tn, "unknown")
        span = _node_source_span(type_ref_expr)
        if jv_is_dict(span):
            out["source_span"] = span
        return out
    bs = _builtin_type_id_symbol(tn)
    if bs != "":
        out = _make_name_node(bs, "int64")
        span = _node_source_span(type_ref_expr)
        if jv_is_dict(span):
            out["source_span"] = span
        return out
    return node_dict


def _type_ref_to_type_name(type_ref_expr: JsonVal, *, dispatch_mode: str, ctx: CompileContext) -> str:
    """Return the canonical type name for IsInstance's expected_type_name field."""
    node = _lower_node(type_ref_expr, dispatch_mode=dispatch_mode, ctx=ctx)
    if not jv_is_dict(node):
        return ""
    node_dict: Node = jv_dict(node)
    if nd_kind(node_dict) != NAME:
        return ""
    return _normalize_type_predicate_target_name(jv_str(node_dict.get("id", "")))


def _collect_expected_type_id_specs(
    type_spec_expr: JsonVal, *, dispatch_mode: str,
    ctx: CompileContext,
) -> list[Node]:
    spec_node = _lower_node(type_spec_expr, dispatch_mode=dispatch_mode, ctx=ctx)
    out: list[Node] = []
    if jv_is_dict(spec_node):
        spec_dict: Node = jv_dict(spec_node)
        if nd_kind(spec_dict) == TUPLE:
            elems = spec_dict.get("elements")
            el: list[JsonVal] = _empty_jv_list()
            if jv_is_list(elems):
                for e in jv_list(elems):
                    el.append(e)
            for elem in el:
                lowered = _type_ref_to_type_id(elem, dispatch_mode=dispatch_mode, ctx=ctx)
                if lowered is not None:
                    spec: Node = {}
                    spec["type_id_expr"] = lowered
                    spec["type_name_str"] = _type_ref_to_type_name(elem, dispatch_mode=dispatch_mode, ctx=ctx)
                    spec["type_ref_expr"] = elem
                    spec["nominal_adt_test_v1"] = _build_nominal_adt_type_test_meta(elem, ctx)
                    out.append(spec)
            return out
    lowered_one = _type_ref_to_type_id(spec_node, dispatch_mode=dispatch_mode, ctx=ctx)
    if lowered_one is not None:
        spec1: Node = {}
        spec1["type_id_expr"] = lowered_one
        spec1["type_name_str"] = _type_ref_to_type_name(spec_node, dispatch_mode=dispatch_mode, ctx=ctx)
        spec1["type_ref_expr"] = spec_node
        spec1["nominal_adt_test_v1"] = _build_nominal_adt_type_test_meta(spec_node, ctx)
        out.append(spec1)
    return out


def _lower_isinstance_call(
    out_call: Node, *, dispatch_mode: str,
    ctx: CompileContext,
) -> Node:
    return out_call


def _lower_issubclass_call(
    out_call: Node, *, dispatch_mode: str,
    ctx: CompileContext,
) -> Node:
    return out_call


def _lower_type_id_call_expr(
    out_call: Node, *, dispatch_mode: str,
    legacy_compat: bool,
    ctx: CompileContext,
) -> Node:
    st = jv_str(out_call.get("semantic_tag", ""))
    if st == "type.isinstance":
        return _lower_isinstance_call(out_call, dispatch_mode=dispatch_mode, ctx=ctx)
    if st == "type.issubclass":
        return _lower_issubclass_call(out_call, dispatch_mode=dispatch_mode, ctx=ctx)
    lk = jv_str(out_call.get("lowered_kind", ""))
    if lk == TYPE_PREDICATE_CALL:
        pk = jv_str(out_call.get("predicate_kind", ""))
        if pk == "isinstance":
            return _lower_isinstance_call(out_call, dispatch_mode=dispatch_mode, ctx=ctx)
        if pk == "issubclass":
            return _lower_issubclass_call(out_call, dispatch_mode=dispatch_mode, ctx=ctx)
    func_obj = out_call.get("func")
    if not jv_is_dict(func_obj):
        return out_call
    func_node: Node = jv_dict(func_obj)
    if nd_kind(func_node) != NAME:
        return out_call
    fn = jv_str(func_node.get("id", ""))
    if not legacy_compat:
        return out_call
    if fn == "isinstance":
        return _lower_isinstance_call(out_call, dispatch_mode=dispatch_mode, ctx=ctx)
    if fn == "issubclass":
        return _lower_issubclass_call(out_call, dispatch_mode=dispatch_mode, ctx=ctx)
    if fn == "py_isinstance" or fn == "py_tid_isinstance":
        al2_obj: JsonVal = out_call.get("args")
        if jv_is_list(al2_obj):
            left_expr: JsonVal = None
            _tid_expr: JsonVal = None
            idx = 0
            for arg_jv in jv_list(al2_obj):
                if idx == 0:
                    left_expr = arg_jv
                elif idx == 1:
                    _tid_expr = arg_jv
                    break
                idx += 1
            if idx == 1:
                _tid_map = {"PYTRA_TID_NONE": "None", "PYTRA_TID_STR": "str", "PYTRA_TID_LIST": "list", "PYTRA_TID_DICT": "dict", "PYTRA_TID_SET": "set"}
                _raw_id = nd_get_str_or(jv_dict(_tid_expr), "id", "") if jv_is_dict(_tid_expr) else ""
                _type_name = _tid_map.get(_raw_id, _raw_id)
                return _make_type_predicate_expr(kind=jv_str(IS_INSTANCE), left_key="value", left_expr=left_expr, expected_type_name=_type_name, source_expr=out_call, ctx=ctx)
    if fn == "py_issubclass" or fn == "py_tid_issubclass":
        al2_obj: JsonVal = out_call.get("args")
        if jv_is_list(al2_obj):
            left_expr: JsonVal = None
            right_expr: JsonVal = None
            idx = 0
            for arg_jv in jv_list(al2_obj):
                if idx == 0:
                    left_expr = arg_jv
                elif idx == 1:
                    right_expr = arg_jv
                    break
                idx += 1
            if idx == 1:
                return _make_type_predicate_expr(kind=jv_str(IS_SUBCLASS), left_key="actual_type_id", left_expr=left_expr, expected_type_id_expr=right_expr, source_expr=out_call, ctx=ctx)
    if fn == "py_is_subtype" or fn == "py_tid_is_subtype":
        al2_obj: JsonVal = out_call.get("args")
        if jv_is_list(al2_obj):
            left_expr: JsonVal = None
            right_expr: JsonVal = None
            idx = 0
            for arg_jv in jv_list(al2_obj):
                if idx == 0:
                    left_expr = arg_jv
                elif idx == 1:
                    right_expr = arg_jv
                    break
                idx += 1
            if idx == 1:
                return _make_type_predicate_expr(kind=jv_str(IS_SUBTYPE), left_key="actual_type_id", left_expr=left_expr, expected_type_id_expr=right_expr, source_expr=out_call, ctx=ctx)
    if fn == "py_runtime_type_id" or fn == "py_tid_runtime_type_id":
        al2_obj: JsonVal = out_call.get("args")
        if jv_is_list(al2_obj):
            for arg_jv in jv_list(al2_obj):
                return _make_boundary_expr(kind=jv_str(OBJ_TYPE_ID), value_key="value", value_node=arg_jv, resolved_type="int64", source_expr=out_call, ctx=ctx)
    return out_call


def _wrap_call_args_for_target_types(call: Node, ctx: CompileContext) -> Node:
    _ctx = ctx
    _ = _ctx
    return call


def _collect_vararg_table(node: JsonVal, out: dict[str, Node]) -> None:
    return None


def _desugar_vararg_funcdef(nd: Node) -> Node:
    return nd


def _pack_vararg_callsite(call: Node, vararg_table: dict[str, Node]) -> Node:
    _ = vararg_table
    return call


def _apply_vararg_walk(node: JsonVal, vt: dict[str, Node]) -> JsonVal:
    _ = vt
    return node


def _lower_call_expr(call: Node, *, dispatch_mode: str, ctx: CompileContext) -> Node:
    out: Node = {}
    for key_s, value_jv in call.items():
        out[key_s] = _lower_node(value_jv, dispatch_mode=dispatch_mode, ctx=ctx)
    if not jv_is_dict(out):
        return out
    if nd_kind(out) != CALL:
        return out
    set_type_expr_summary(out, type_expr_summary_from_node(ctx, out))
    return out


# ---------------------------------------------------------------------------
# Node dispatch
# ---------------------------------------------------------------------------

def _lower_node_dispatch(node: Node, *, dispatch_mode: str, ctx: CompileContext) -> JsonVal:
    kind = nd_kind(node)
    if kind == FUNCTION_DEF or kind == CLOSURE_DEF:
        return _lower_function_def_stmt(node, dispatch_mode=dispatch_mode, ctx=ctx)
    if kind == RETURN:
        return _lower_return_stmt(node, dispatch_mode=dispatch_mode, ctx=ctx)
    if kind == FOR:
        return _lower_for_stmt(node, dispatch_mode=dispatch_mode, ctx=ctx)
    if kind == FOR_RANGE:
        return _lower_forrange_stmt(node, dispatch_mode=dispatch_mode, ctx=ctx)
    if kind == ASSIGN or kind == ANN_ASSIGN or kind == AUG_ASSIGN:
        return _lower_assignment_like_stmt(node, dispatch_mode=dispatch_mode, ctx=ctx)
    if kind == CALL:
        return _lower_call_expr(node, dispatch_mode=dispatch_mode, ctx=ctx)
    if kind == ATTRIBUTE:
        out = _copy_node(node)
        return _decorate_nominal_adt_projection_attr(out, ctx)
    if kind == VARIANT_PATTERN:
        out = _copy_node(node)
        return _decorate_nominal_adt_variant_pattern(out, ctx)
    if kind == MATCH:
        out = _copy_node(node)
        return _decorate_nominal_adt_match_stmt(out, ctx)
    if kind == FOR_CORE:
        return _lower_forcore_stmt(node, dispatch_mode=dispatch_mode, ctx=ctx)
    out: Node = {}
    for key_s in node:
        out[key_s] = _lower_node(node[key_s], dispatch_mode=dispatch_mode, ctx=ctx)
    return out


def _lower_node(node: JsonVal, *, dispatch_mode: str, ctx: CompileContext) -> JsonVal:
    if jv_is_list(node):
        out_list: list[JsonVal] = []
        for item in jv_list(node):
            out_list.append(_lower_node(item, dispatch_mode=dispatch_mode, ctx=ctx))
        return out_list
    if jv_is_dict(node):
        return _lower_node_dispatch(jv_dict(node), dispatch_mode=dispatch_mode, ctx=ctx)
    return node


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def lower_east2_to_east3(
    east_module: dict[str, JsonVal],
    object_dispatch_mode: str = "",
    target_language: str = "core",
) -> Node:
    """EAST2 Module を EAST3 へ lower する。"""
    module_input: Node = {}
    for key_s in east_module:
        module_input[key_s] = east_module[key_s]
    # 1. Normalize source spans (col → col_offset, remove Module source_span)
    normalized = walk_normalize_spans(east_module)
    if not jv_is_dict(normalized):
        return module_input
    normalized_node: Node = jv_dict(normalized)
    module_node: Node = {}
    for key_s in normalized_node:
        module_node[key_s] = normalized_node[key_s]

    meta_obj = module_node.get("meta")
    dispatch_mode = "native"
    if object_dispatch_mode != "":
        dispatch_mode = _normalize_dispatch_mode(object_dispatch_mode)
    elif jv_is_dict(meta_obj):
        md: Node = jv_dict(meta_obj)
        dispatch_mode = _normalize_dispatch_mode(md.get("dispatch_mode"))

    ctx: CompileContext = CompileContext()
    ctx.lowering_profile = load_lowering_profile(target_language)
    ctx.target_language = target_language
    ctx.nominal_adt_table = collect_nominal_adt_table(module_node)
    ctx.legacy_compat_bridge = True
    if jv_is_dict(meta_obj):
        md2: Node = jv_dict(meta_obj)
        lo = md2.get("legacy_compat_bridge")
        lo_b = jv_bool(lo)
        if jv_is_bool(lo):
            ctx.legacy_compat_bridge = lo_b

    lowered = _lower_node(module_node, dispatch_mode=dispatch_mode, ctx=ctx)

    if not jv_is_dict(lowered):
        return module_input
    lowered_node: Node = jv_dict(lowered)
    if nd_kind(lowered_node) != MODULE:
        return lowered_node

    # Vararg desugaring
    vt: dict[str, Node] = {}
    _collect_vararg_table(lowered_node, vt)
    if len(vt) != 0:
        lowered = _apply_vararg_walk(lowered_node, vt)
        if not jv_is_dict(lowered):
            return module_input
        lowered_node = jv_dict(lowered)

    module_out: Node = {}
    for key_s in lowered_node:
        module_out[key_s] = lowered_node[key_s]

    # Post-lowering passes
    lower_yield_generators(module_out, ctx)
    lower_listcomp(module_out, ctx)
    lower_nested_function_defs(module_out, ctx)
    expand_default_arguments(module_out, ctx)
    expand_forcore_tuple_targets(module_out, ctx)
    expand_tuple_unpack(module_out, ctx)
    lower_enumerate(module_out, ctx)
    lower_reversed(module_out, ctx)
    hoist_block_scope_variables(module_out, ctx)
    apply_integer_promotion(module_out, ctx)
    apply_guard_narrowing(module_out, ctx)
    apply_type_propagation(module_out, ctx)
    apply_yields_dynamic(module_out, ctx)
    apply_profile_lowering(module_out, ctx)
    detect_swap_patterns(module_out, ctx)
    detect_mutates_self(module_out, ctx)
    detect_unused_variables(module_out, ctx)
    mark_main_guard_discard(module_out, ctx)

    module_out["east_stage"] = 3
    sv = module_out.get("schema_version")
    if jv_is_int(sv):
        schema_version = jv_int(sv)
        if schema_version > 0:
            module_out["schema_version"] = schema_version
        else:
            module_out["schema_version"] = 1
    else:
        module_out["schema_version"] = 1

    mn = module_out.get("meta")
    meta_norm: Node = {}
    if jv_is_dict(mn):
        mn_dict: Node = jv_dict(mn)
        for key_s in mn_dict:
            meta_norm[key_s] = mn_dict[key_s]
    meta_norm["dispatch_mode"] = dispatch_mode
    module_out["meta"] = meta_norm
    validation = validate_east3(module_out)
    if len(validation.errors) != 0:
        raise RuntimeError("EAST3 validation failed\n" + format_result(validation))
    return module_out
