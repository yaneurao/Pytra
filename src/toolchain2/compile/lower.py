"""EAST2 → EAST3 lowering: main entry point.

Port of toolchain/compile/east2_to_east3_lowering.py for toolchain2.
§5.1: Any/object 禁止 — uses JsonVal throughout.
§5.3: Python 標準モジュール直接 import 禁止。
§5.6: グローバル可変状態禁止 — CompileContext 経由。
"""

from __future__ import annotations

from typing import Union, Callable

from toolchain2.compile.jv import JsonVal, Node, CompileContext, deep_copy_json
from toolchain2.compile.jv import jv_str, jv_dict, jv_list, jv_is_dict, jv_is_list
from toolchain2.compile.jv import nd_kind, nd_get_str, nd_get_dict, nd_get_list
from toolchain2.compile.jv import normalize_type_name
from toolchain2.compile.source_span import walk_normalize_spans
from toolchain2.common.kinds import (
    MODULE, FUNCTION_DEF, CLASS_DEF, ASSIGN, ANN_ASSIGN, AUG_ASSIGN,
    FOR, FOR_RANGE, FOR_CORE, CALL, ATTRIBUTE, NAME, CONSTANT,
    MATCH, VARIANT_PATTERN, PATTERN_BIND, PATTERN_WILDCARD,
    SUBSCRIPT, TUPLE, LIST, STARRED, BOOL_OP,
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
from toolchain2.compile.type_summary import (
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
from toolchain2.compile.passes import (
    lower_yield_generators,
    lower_listcomp,
    expand_default_arguments,
    expand_forcore_tuple_targets,
    expand_tuple_unpack,
    lower_enumerate,
    hoist_block_scope_variables,
    apply_integer_promotion,
    apply_guard_narrowing,
    apply_type_propagation,
    apply_yields_dynamic,
    detect_swap_patterns,
    detect_mutates_self,
    detect_unused_variables,
    mark_main_guard_discard,
)


def _normalize_dispatch_mode(value: JsonVal) -> str:
    if isinstance(value, str):
        s: str = value
        mode = s.strip()
        if mode == "native" or mode == "type_id":
            return mode
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


def _tuple_element_types(type_name: JsonVal) -> list[str]:
    norm = normalize_type_name(type_name)
    if not (norm.startswith("tuple[") and norm.endswith("]")):
        return []
    inner = norm[6:-1]
    if inner == "":
        return []
    return _split_generic_types(inner)


# ---------------------------------------------------------------------------
# AST node helpers
# ---------------------------------------------------------------------------

def _is_any_like_type(type_name: JsonVal, ctx: CompileContext) -> bool:
    return is_dynamic_like_summary(type_expr_summary_from_payload(ctx, None, type_name))


def _const_int_node(value: int) -> Node:
    return {
        "kind": CONSTANT,
        "resolved_type": "int64",
        "borrow_kind": "value",
        "casts": [],
        "repr": str(value),
        "value": value,
    }


def _const_bool_node(value: bool) -> Node:
    return {
        "kind": CONSTANT,
        "resolved_type": "bool",
        "borrow_kind": "value",
        "casts": [],
        "repr": "True" if value else "False",
        "value": value,
    }


def _make_name_node(name: str, resolved_type: str = "unknown") -> Node:
    return {
        "kind": NAME,
        "id": name,
        "resolved_type": resolved_type,
        "borrow_kind": "value",
        "casts": [],
        "repr": name,
    }


def _node_source_span(node: JsonVal) -> JsonVal:
    if isinstance(node, dict):
        dn: Node = node
        return dn.get("source_span")
    return None


def _node_repr(node: JsonVal) -> str:
    if isinstance(node, dict):
        dn: Node = node
        repr_obj = dn.get("repr")
        if isinstance(repr_obj, str):
            return repr_obj
    return ""


def _copy_source_span_and_repr(source_expr: JsonVal, out: Node) -> None:
    span = _node_source_span(source_expr)
    if isinstance(span, dict):
        out["source_span"] = span
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
    out: Node = {
        "kind": kind,
        "resolved_type": resolved_type,
        "borrow_kind": "value",
        "casts": [],
        value_key: value_node,
    }
    _copy_source_span_and_repr(source_expr, out)
    set_type_expr_summary(out, type_expr_summary_from_payload(ctx, None, resolved_type))
    return out


def _const_string_value(node: JsonVal) -> str:
    if not isinstance(node, dict):
        return ""
    d: Node = node
    kind = d.get("kind")
    value = d.get("value")
    if kind == CONSTANT and isinstance(value, str):
        return value
    if kind == CALL:
        func_obj = d.get("func")
        if isinstance(func_obj, dict):
            fd: Node = func_obj
            if fd.get("kind") == NAME and fd.get("id") == "str":
                args_obj = d.get("args")
                args: list[JsonVal] = args_obj if isinstance(args_obj, list) else []
                if len(args) == 1:
                    return _const_string_value(args[0])
    return ""


def _is_string_index_expr(node: JsonVal) -> bool:
    if not isinstance(node, dict):
        return False
    nd: Node = node
    if nd.get("kind") != SUBSCRIPT:
        return False
    value_node = nd.get("value")
    slice_node = nd.get("slice")
    if isinstance(slice_node, dict) and slice_node.get("kind") == "Slice":
        return False
    if not isinstance(value_node, dict):
        return False
    return normalize_type_name(value_node.get("resolved_type")) == "str"


def _make_named_type_expr(name: str) -> Node:
    return {"kind": NAMED_TYPE, "name": name}


def _assignment_storage_type_override(stmt: Node, value_expr: JsonVal, target_type: str) -> str:
    if stmt.get("kind") != ANN_ASSIGN:
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
    out: Node = {
        "kind": CALL,
        "func": _make_name_node(func_name, "callable"),
        "args": [value_expr],
        "keywords": [],
        "resolved_type": target_type,
        "borrow_kind": "value",
        "casts": [],
        "lowered_kind": BUILTIN_CALL,
        "builtin_name": func_name,
        "runtime_call": "static_cast",
    }
    _copy_source_span_and_repr(value_expr, out)
    set_type_expr_summary(out, type_expr_summary_from_payload(ctx, None, target_type))
    return out


def _is_none_literal(node: JsonVal) -> bool:
    if not isinstance(node, dict):
        return False
    nd: Node = node
    if nd.get("kind") != CONSTANT:
        return False
    return nd.get("value") is None


# ---------------------------------------------------------------------------
# Statement lowering helpers
# ---------------------------------------------------------------------------

def _normalize_iter_mode(value: JsonVal) -> str:
    if isinstance(value, str):
        s: str = value
        mode = s.strip()
        if mode == "static_fastpath" or mode == "runtime_protocol":
            return mode
    return "runtime_protocol"


def _copy_extra_fields(
    source: Node,
    out: Node,
    consumed: set[str],
    *,
    lower_node_fn: Callable[[JsonVal], JsonVal],
) -> None:
    for key in source:
        if key in consumed:
            continue
        out[key] = lower_node_fn(source[key])


def _wrap_value_for_target_type(
    value_expr: JsonVal, target_type: str,
    *,
    target_type_expr: JsonVal = None,
    ctx: CompileContext,
) -> JsonVal:
    target_summary = type_expr_summary_from_payload(ctx, target_type_expr, target_type)
    target_t = normalize_type_name(target_summary.get("mirror"))
    if target_t == "unknown":
        return value_expr
    value_summary = expr_type_summary(ctx, value_expr)
    target_contains_dynamic_lane = (
        "Any" in target_t or "object" in target_t or "unknown" in target_t
    )
    value_t = normalize_type_name(value_summary.get("mirror"))
    value_requires_runtime_unbox = isinstance(value_expr, dict) and value_expr.get("yields_dynamic") is True
    if (
        target_contains_dynamic_lane
        and not is_dynamic_like_summary(target_summary)
        and not is_dynamic_like_summary(value_summary)
        and not value_requires_runtime_unbox
        and value_t != "unknown"
        and value_t != target_t
    ):
        out = _make_boundary_expr(
            kind=BOX, value_key="value", value_node=value_expr,
            resolved_type=target_t, source_expr=value_expr,
            ctx=ctx,
        )
        out["target"] = target_t
        out["bridge_lane_v1"] = bridge_lane_payload(target_summary, value_summary)
        set_type_expr_summary(out, target_summary)
        return out
    if is_dynamic_like_summary(target_summary) and not is_dynamic_like_summary(value_summary):
        out = _make_boundary_expr(
            kind=BOX, value_key="value", value_node=value_expr,
            resolved_type="object", source_expr=value_expr,
            ctx=ctx,
        )
        out["bridge_lane_v1"] = bridge_lane_payload(target_summary, value_summary)
        set_type_expr_summary(out, target_summary)
        return out
    if not is_dynamic_like_summary(target_summary) and (
        is_dynamic_like_summary(value_summary) or value_requires_runtime_unbox
    ):
        bridge_value_summary = value_summary
        if value_requires_runtime_unbox and not is_dynamic_like_summary(value_summary):
            bridge_value_summary = unknown_type_summary()
        out = _make_boundary_expr(
            kind=UNBOX, value_key="value", value_node=value_expr,
            resolved_type=target_t, source_expr=value_expr,
            ctx=ctx,
        )
        out["target"] = target_t
        out["on_fail"] = "raise"
        out["bridge_lane_v1"] = bridge_lane_payload(target_summary, bridge_value_summary)
        set_type_expr_summary(out, target_summary)
        return out
    if _supports_static_scalar_cast(value_t, target_t):
        return _make_static_scalar_cast_expr(value_expr, target_t, ctx=ctx)
    return value_expr


def _resolve_assign_target_type_summary(stmt: Node, ctx: CompileContext) -> Node:
    decl_expr = stmt.get("decl_type_expr")
    summary = type_expr_summary_from_payload(ctx, decl_expr, stmt.get("decl_type"))
    if jv_str(summary.get("category", "unknown")) != "unknown":
        return summary
    ann_expr = stmt.get("annotation_type_expr")
    summary = type_expr_summary_from_payload(ctx, ann_expr, stmt.get("annotation"))
    if jv_str(summary.get("category", "unknown")) != "unknown":
        return summary
    target_obj = stmt.get("target")
    if isinstance(target_obj, dict):
        tod: Node = target_obj
        summary = type_expr_summary_from_payload(ctx, tod.get("type_expr"), tod.get("resolved_type"))
        if jv_str(summary.get("category", "unknown")) != "unknown":
            mirror = normalize_type_name(summary.get("mirror"))
            if tod.get("kind") != TUPLE or "unknown" not in mirror:
                return summary
        inferred_tuple_type = _infer_tuple_assign_target_type(stmt)
        if inferred_tuple_type != "unknown":
            return type_expr_summary_from_payload(ctx, None, inferred_tuple_type)
    return unknown_type_summary()


def _infer_tuple_assign_target_type(stmt: Node) -> str:
    target_obj = stmt.get("target")
    if not isinstance(target_obj, dict):
        return "unknown"
    target: Node = target_obj
    if target.get("kind") != TUPLE:
        return "unknown"

    elem_types: list[str] = []
    any_known = False
    elements_obj = target.get("elements")
    if isinstance(elements_obj, list):
        for elem in elements_obj:
            if not isinstance(elem, dict):
                elem_types.append("unknown")
                continue
            elem_type = normalize_type_name(elem.get("resolved_type"))
            if elem_type != "unknown":
                any_known = True
            elem_types.append(elem_type)
    if elem_types and all(elem_type != "unknown" for elem_type in elem_types):
        return "tuple[" + ",".join(elem_types) + "]"

    value_obj = stmt.get("value")
    if isinstance(value_obj, dict):
        value_type = normalize_type_name(value_obj.get("resolved_type"))
        if value_type.startswith("tuple[") and value_type.endswith("]"):
            return value_type

    if elem_types and any_known:
        return "tuple[" + ",".join(elem_types) + "]"
    return "unknown"


def _resolve_assign_target_type(stmt: Node, ctx: CompileContext) -> str:
    summary = _resolve_assign_target_type_summary(stmt, ctx)
    mirror = normalize_type_name(summary.get("mirror"))
    if mirror != "unknown":
        return mirror
    tuple_type = _infer_tuple_assign_target_type(stmt)
    if tuple_type != "unknown":
        return tuple_type
    decl_type = normalize_type_name(stmt.get("decl_type"))
    if decl_type != "unknown":
        return decl_type
    ann_type = normalize_type_name(stmt.get("annotation"))
    if ann_type != "unknown":
        return ann_type
    target_obj = stmt.get("target")
    if isinstance(target_obj, dict):
        tod: Node = target_obj
        target_t = normalize_type_name(tod.get("resolved_type"))
        if target_t != "unknown":
            return target_t
    return "unknown"


def _build_target_plan(
    target: JsonVal,
    target_type: JsonVal,
    *,
    lower_node_fn: Callable[[JsonVal], JsonVal],
    ctx: CompileContext,
) -> Node:
    tt_norm = normalize_type_name(target_type)
    if isinstance(target, dict):
        td: Node = target
        kind = td.get("kind")
        if kind == NAME:
            out: Node = {"kind": NAME_TARGET, "id": td.get("id", "")}
            if tt_norm != "unknown":
                out["target_type"] = tt_norm
            return out
        if kind == TUPLE:
            elems_obj = td.get("elements")
            elem_plans: list[JsonVal] = []
            elem_types = _tuple_element_types(tt_norm)
            if isinstance(elems_obj, list):
                for i in range(len(elems_obj)):
                    elem = elems_obj[i]
                    et = "unknown"
                    if i < len(elem_types):
                        et = elem_types[i]
                    elem_plans.append(_build_target_plan(elem, et, lower_node_fn=lower_node_fn, ctx=ctx))
            out = {"kind": TUPLE_TARGET, "elements": elem_plans}
            if tt_norm != "unknown":
                out["target_type"] = tt_norm
            return out
    out = {"kind": EXPR_TARGET, "target": lower_node_fn(target)}
    if tt_norm != "unknown":
        out["target_type"] = tt_norm
    return out


def _lower_assignment_like_stmt(stmt: Node, *, lower_node_fn: Callable[[JsonVal], JsonVal], ctx: CompileContext) -> Node:
    out: Node = {}
    for key in stmt:
        if key == "value":
            continue
        out[key] = lower_node_fn(stmt[key])
    if "value" not in stmt or stmt.get("value") is None:
        return out
    value_lowered = lower_node_fn(stmt.get("value"))
    target_summary = _resolve_assign_target_type_summary(stmt, ctx)
    target_type = normalize_type_name(target_summary.get("mirror"))
    if target_type == "unknown":
        target_type = _resolve_assign_target_type(stmt, ctx)
    target_obj = stmt.get("target")
    target_type_expr = stmt.get("decl_type_expr")
    if target_type_expr is None:
        target_type_expr = stmt.get("annotation_type_expr")
    if target_type_expr is None and isinstance(target_obj, dict):
        tod: Node = target_obj
        target_type_expr = tod.get("type_expr")
    storage_type = _assignment_storage_type_override(stmt, value_lowered, target_type)
    if storage_type != "":
        target_type = storage_type
        target_type_expr = _make_named_type_expr(storage_type)
        out["decl_type"] = storage_type
        out["decl_type_expr"] = target_type_expr
        target_out = out.get("target")
        if isinstance(target_out, dict):
            target_out["resolved_type"] = storage_type
            target_out["type_expr"] = target_type_expr
    out["value"] = _wrap_value_for_target_type(
        value_lowered, target_type, target_type_expr=target_type_expr,
        ctx=ctx,
    )
    set_type_expr_summary(out, type_expr_summary_from_payload(ctx, target_type_expr, target_type))
    return out


def _lower_for_stmt(stmt: Node, *, dispatch_mode: str, lower_node_fn: Callable[[JsonVal], JsonVal], ctx: CompileContext) -> Node:
    iter_expr = lower_node_fn(stmt.get("iter"))
    iter_plan: Node = {
        "kind": RUNTIME_ITER_FOR_PLAN,
        "iter_expr": iter_expr,
        "dispatch_mode": dispatch_mode,
        "init_op": OBJ_ITER_INIT,
        "next_op": OBJ_ITER_NEXT,
    }
    target_type = normalize_type_name(stmt.get("target_type"))
    if target_type == "unknown":
        target_type = normalize_type_name(stmt.get("iter_element_type"))
    out: Node = {
        "kind": FOR_CORE,
        "iter_mode": "runtime_protocol",
        "iter_plan": iter_plan,
        "target_plan": _build_target_plan(stmt.get("target"), target_type, lower_node_fn=lower_node_fn, ctx=ctx),
        "body": lower_node_fn(stmt.get("body", [])),
        "orelse": lower_node_fn(stmt.get("orelse", [])),
    }
    consumed = {"kind", "target", "target_type", "iter_mode", "iter_source_type", "iter_element_type", "iter", "body", "orelse"}
    _copy_extra_fields(stmt, out, consumed, lower_node_fn=lower_node_fn)
    return out


def _lower_forrange_stmt(stmt: Node, *, lower_node_fn: Callable[[JsonVal], JsonVal], ctx: CompileContext) -> Node:
    start_node = lower_node_fn(stmt.get("start"))
    stop_node = lower_node_fn(stmt.get("stop"))
    step_node = lower_node_fn(stmt.get("step"))
    if not isinstance(step_node, dict):
        step_node = _const_int_node(1)
    iter_plan: Node = {
        "kind": STATIC_RANGE_FOR_PLAN,
        "start": start_node,
        "stop": stop_node,
        "step": step_node,
    }
    out: Node = {
        "kind": FOR_CORE,
        "iter_mode": "static_fastpath",
        "iter_plan": iter_plan,
        "target_plan": _build_target_plan(stmt.get("target"), stmt.get("target_type"), lower_node_fn=lower_node_fn, ctx=ctx),
        "body": lower_node_fn(stmt.get("body", [])),
        "orelse": lower_node_fn(stmt.get("orelse", [])),
    }
    consumed = {"kind", "target", "target_type", "start", "stop", "step", "range_mode", "body", "orelse"}
    _copy_extra_fields(stmt, out, consumed, lower_node_fn=lower_node_fn)
    return out


def _lower_forcore_stmt(stmt: Node, *, dispatch_mode: str, lower_node_fn: Callable[[JsonVal], JsonVal], ctx: CompileContext) -> Node:
    out: Node = {}
    for key in stmt:
        out[key] = lower_node_fn(stmt[key])
    ip = out.get("iter_plan")
    if isinstance(ip, dict):
        ipd: Node = ip
        if ipd.get("kind") == RUNTIME_ITER_FOR_PLAN:
            ipd["dispatch_mode"] = dispatch_mode
    return out


# ---------------------------------------------------------------------------
# Nominal ADT metadata helpers
# ---------------------------------------------------------------------------

def _build_nominal_adt_ctor_meta(call: Node, ctx: CompileContext) -> Node | None:
    func_obj = call.get("func")
    if not isinstance(func_obj, dict) or func_obj.get("kind") != NAME:
        return None
    ctor_name = normalize_type_name(func_obj.get("id"))
    decl = lookup_nominal_adt_decl(ctx, ctor_name)
    if decl is None or jv_str(decl.get("role", "")).strip() != "variant":
        return None
    ps = jv_str(decl.get("payload_style", "")).strip()
    if ps == "":
        ps = "unit"
    return {
        "schema_version": 1,
        "ir_category": NOMINAL_ADT_CTOR_CALL,
        "family_name": jv_str(decl.get("family_name", ctor_name)),
        "variant_name": ctor_name,
        "payload_style": ps,
    }


def _decorate_nominal_adt_ctor_call(call: Node, ctx: CompileContext) -> Node:
    meta = _build_nominal_adt_ctor_meta(call, ctx)
    if meta is None:
        return call
    call["semantic_tag"] = "nominal_adt.variant_ctor"
    call["lowered_kind"] = NOMINAL_ADT_CTOR_CALL
    call["nominal_adt_ctor_v1"] = meta
    set_type_expr_summary(call, make_nominal_adt_type_summary(jv_str(meta["variant_name"]), jv_str(meta["family_name"])))
    return call


def _decorate_nominal_adt_projection_attr(attr_expr: Node, ctx: CompileContext) -> Node:
    attr_name = jv_str(attr_expr.get("attr", "")).strip()
    if attr_name == "":
        return attr_expr
    owner_summary = expr_type_summary(ctx, attr_expr.get("value"))
    if jv_str(owner_summary.get("category", "unknown")).strip() != "nominal_adt":
        return attr_expr
    variant_name = normalize_type_name(owner_summary.get("nominal_adt_name"))
    if variant_name == "unknown":
        variant_name = normalize_type_name(owner_summary.get("mirror"))
    decl = lookup_nominal_adt_decl(ctx, variant_name)
    if decl is None or jv_str(decl.get("role", "")).strip() != "variant":
        return attr_expr
    ft_obj = decl.get("field_types")
    ft = ft_obj if isinstance(ft_obj, dict) else {}
    field_type = normalize_type_name(ft.get(attr_name))
    if field_type == "unknown":
        return attr_expr
    meta: Node = {
        "schema_version": 1,
        "ir_category": NOMINAL_ADT_PROJECTION,
        "family_name": jv_str(decl.get("family_name", variant_name)),
        "variant_name": variant_name,
        "field_name": attr_name,
        "field_type": field_type,
    }
    ps = jv_str(decl.get("payload_style", "")).strip()
    if ps != "":
        meta["payload_style"] = ps
    attr_expr["semantic_tag"] = "nominal_adt.variant_projection"
    attr_expr["lowered_kind"] = NOMINAL_ADT_PROJECTION
    attr_expr["nominal_adt_projection_v1"] = meta
    attr_expr["resolved_type"] = field_type
    set_type_expr_summary(attr_expr, type_expr_summary_from_payload(ctx, None, field_type))
    return attr_expr


def _decorate_nominal_adt_variant_pattern(pattern: Node, ctx: CompileContext) -> Node:
    if pattern.get("kind") != VARIANT_PATTERN:
        return pattern
    variant_name = normalize_type_name(pattern.get("variant_name"))
    if variant_name == "unknown":
        return pattern
    decl = lookup_nominal_adt_decl(ctx, variant_name)
    if decl is None or jv_str(decl.get("role", "")).strip() != "variant":
        return pattern
    family_name = jv_str(pattern.get("family_name", "")).strip()
    decl_family = jv_str(decl.get("family_name", variant_name)).strip()
    if family_name == "":
        family_name = decl_family
    elif decl_family != "" and family_name != decl_family:
        return pattern
    ps = jv_str(decl.get("payload_style", "")).strip()
    if ps == "":
        ps = "unit"
    subs_obj = pattern.get("subpatterns")
    subs: list[JsonVal] = subs_obj if isinstance(subs_obj, list) else []
    bind_names: list[JsonVal] = []
    for item in subs:
        if isinstance(item, dict) and item.get("kind") == PATTERN_BIND:
            n = jv_str(item.get("name", "")).strip()
            if n != "":
                bind_names.append(n)
    meta: Node = {
        "schema_version": 1,
        "ir_category": NOMINAL_ADT_VARIANT_PATTERN,
        "family_name": family_name,
        "variant_name": variant_name,
        "payload_style": ps,
        "payload_arity": len(subs),
        "bind_names": bind_names,
    }
    pattern["lowered_kind"] = NOMINAL_ADT_VARIANT_PATTERN
    pattern["semantic_tag"] = "nominal_adt.variant_pattern"
    pattern["nominal_adt_pattern_v1"] = meta
    ft_obj2 = decl.get("field_types")
    ft2 = ft_obj2 if isinstance(ft_obj2, dict) else {}
    field_entries = list(ft2.items())
    for idx in range(len(subs)):
        sp = subs[idx]
        if not isinstance(sp, dict):
            continue
        spd: Node = sp
        field_name = ""
        field_type = "unknown"
        if idx < len(field_entries):
            field_name = str(field_entries[idx][0]).strip()
            field_type = normalize_type_name(field_entries[idx][1])
        if spd.get("kind") == PATTERN_BIND:
            spd["lowered_kind"] = NOMINAL_ADT_PATTERN_BIND
            spd["semantic_tag"] = "nominal_adt.pattern_bind"
            pb_meta: Node = {"schema_version": 1, "ir_category": NOMINAL_ADT_PATTERN_BIND,
                             "family_name": family_name, "variant_name": variant_name}
            if field_name != "":
                pb_meta["field_name"] = field_name
            if field_type != "unknown":
                pb_meta["field_type"] = field_type
            spd["nominal_adt_pattern_bind_v1"] = pb_meta
            if field_type != "unknown":
                spd["resolved_type"] = field_type
                set_type_expr_summary(spd, type_expr_summary_from_payload(ctx, None, field_type))
    return pattern


def _decorate_nominal_adt_match_stmt(match_stmt: Node, ctx: CompileContext) -> Node:
    subject_summary = expr_type_summary(ctx, match_stmt.get("subject"))
    family_cat = jv_str(subject_summary.get("category", "unknown")).strip()
    family_name = ""
    if family_cat == "nominal_adt":
        family_name = jv_str(subject_summary.get("nominal_adt_family", "")).strip()
        if family_name == "":
            family_name = jv_str(subject_summary.get("nominal_adt_name", "")).strip()
        if family_name == "":
            family_name = normalize_type_name(subject_summary.get("mirror"))
            if family_name == "unknown":
                family_name = ""
    if family_name == "":
        return match_stmt
    family_variants = collect_nominal_adt_family_variants(ctx, family_name)
    if len(family_variants) == 0:
        return match_stmt
    cases_obj = match_stmt.get("cases")
    cases: list[JsonVal] = cases_obj if isinstance(cases_obj, list) else []
    covered_set: set[str] = set()
    dup_idxs: list[JsonVal] = []
    unr_idxs: list[JsonVal] = []
    invalid = False
    wildcard_seen = False
    for idx in range(len(cases)):
        case = cases[idx]
        if not isinstance(case, dict):
            invalid = True
            continue
        cd: Node = case
        pat = cd.get("pattern")
        if not isinstance(pat, dict):
            invalid = True
            continue
        pd: Node = pat
        pk = jv_str(pd.get("kind", "")).strip()
        if pk == VARIANT_PATTERN:
            vf = jv_str(pd.get("family_name", "")).strip()
            vn = normalize_type_name(pd.get("variant_name"))
            if vf != family_name or vn not in family_variants:
                invalid = True
                continue
            ddecl = lookup_nominal_adt_decl(ctx, vn)
            if ddecl is None:
                invalid = True
                continue
            subs2 = pd.get("subpatterns")
            subs_l: list[JsonVal] = subs2 if isinstance(subs2, list) else []
            ft3 = ddecl.get("field_types")
            ft3d = ft3 if isinstance(ft3, dict) else {}
            if len(subs_l) != len(ft3d):
                invalid = True
            if wildcard_seen and idx not in [int(x) for x in unr_idxs if isinstance(x, int)]:
                unr_idxs.append(idx)
            if vn in covered_set:
                dup_idxs.append(idx)
                if idx not in [int(x) for x in unr_idxs if isinstance(x, int)]:
                    unr_idxs.append(idx)
                continue
            covered_set.add(vn)
        elif pk == PATTERN_WILDCARD:
            if wildcard_seen:
                dup_idxs.append(idx)
                if idx not in [int(x) for x in unr_idxs if isinstance(x, int)]:
                    unr_idxs.append(idx)
                continue
            wildcard_seen = True
        else:
            invalid = True
    covered_variants: list[JsonVal] = [v for v in family_variants if v in covered_set]
    if wildcard_seen:
        covered_variants = list(family_variants)
        uncovered_variants: list[JsonVal] = []
        coverage_kind = "wildcard_terminal"
    else:
        uncovered_variants = [v for v in family_variants if v not in covered_set]
        coverage_kind = "exhaustive" if len(uncovered_variants) == 0 else "partial"
    if invalid or len(dup_idxs) != 0 or len(unr_idxs) != 0:
        coverage_kind = "invalid"
    analysis: Node = {
        "schema_version": 1,
        "family_name": family_name,
        "coverage_kind": coverage_kind,
        "covered_variants": covered_variants,
        "uncovered_variants": uncovered_variants,
        "duplicate_case_indexes": dup_idxs,
        "unreachable_case_indexes": unr_idxs,
    }
    match_stmt["lowered_kind"] = NOMINAL_ADT_MATCH
    match_stmt["semantic_tag"] = "nominal_adt.match"
    match_stmt["nominal_adt_match_v1"] = {
        "schema_version": 1,
        "ir_category": NOMINAL_ADT_MATCH,
        "family_name": family_name,
        "coverage_kind": coverage_kind,
        "covered_variants": list(covered_variants),
        "uncovered_variants": list(uncovered_variants),
        "subject_type": dict(subject_summary),
    }
    m_obj = match_stmt.get("meta")
    m: Node = dict(m_obj) if isinstance(m_obj, dict) else {}
    m["match_analysis_v1"] = analysis
    match_stmt["meta"] = m
    # Decorate variant patterns in cases
    for case in cases:
        if not isinstance(case, dict):
            continue
        cd2: Node = case
        pat2 = cd2.get("pattern")
        if not isinstance(pat2, dict):
            continue
        pd2: Node = pat2
        if pd2.get("kind") != VARIANT_PATTERN:
            continue
        vn2 = normalize_type_name(pd2.get("variant_name"))
        ddecl2 = lookup_nominal_adt_decl(ctx, vn2)
        if ddecl2 is None:
            continue
        ps2 = jv_str(ddecl2.get("payload_style", "")).strip()
        if ps2 == "":
            ps2 = "unit"
        ft4 = ddecl2.get("field_types")
        ft4d = ft4 if isinstance(ft4, dict) else {}
        fn_list = list(ft4d.keys())
        bnames: list[JsonVal] = []
        pd2["lowered_kind"] = NOMINAL_ADT_VARIANT_PATTERN
        pd2["semantic_tag"] = "nominal_adt.variant_pattern"
        pd2["nominal_adt_pattern_v1"] = {
            "schema_version": 1,
            "ir_category": NOMINAL_ADT_VARIANT_PATTERN,
            "family_name": jv_str(ddecl2.get("family_name", vn2)),
            "variant_name": vn2,
            "payload_style": ps2,
            "bind_names": bnames,
        }
        subs3 = pd2.get("subpatterns")
        subs3l: list[JsonVal] = subs3 if isinstance(subs3, list) else []
        for si in range(len(subs3l)):
            sp2 = subs3l[si]
            if not isinstance(sp2, dict):
                continue
            spd2: Node = sp2
            if spd2.get("kind") != PATTERN_BIND:
                continue
            fn2 = fn_list[si] if si < len(fn_list) else ""
            ft5 = normalize_type_name(ft4d.get(fn2)) if fn2 != "" else "unknown"
            bn = jv_str(spd2.get("name", "")).strip()
            if bn != "":
                bnames.append(bn)
            spd2["lowered_kind"] = NOMINAL_ADT_PATTERN_BIND
            spd2["semantic_tag"] = "nominal_adt.pattern_bind"
            spd2["nominal_adt_pattern_bind_v1"] = {
                "schema_version": 1,
                "field_name": fn2,
                "field_type": ft5,
            }
            if ft5 != "unknown":
                spd2["resolved_type"] = ft5
                set_type_expr_summary(spd2, type_expr_summary_from_payload(ctx, None, ft5))
    return match_stmt


# ---------------------------------------------------------------------------
# Call metadata helpers
# ---------------------------------------------------------------------------

_JSON_DECODE_META_KEY: str = "json_decode_v1"


def _infer_json_semantic_tag(call: Node, *, legacy_compat_bridge_enabled: bool, ctx: CompileContext) -> str:
    st = jv_str(call.get("semantic_tag", "")).strip()
    if st.startswith("json."):
        return st
    mid = jv_str(call.get("runtime_module_id", "")).strip()
    rs = jv_str(call.get("runtime_symbol", "")).strip()
    if mid == "pytra.std.json":
        if rs == "loads":
            return "json.loads"
        if rs == "loads_obj":
            return "json.loads_obj"
        if rs == "loads_arr":
            return "json.loads_arr"
    func_obj = call.get("func")
    if isinstance(func_obj, dict) and func_obj.get("kind") == ATTRIBUTE:
        attr = jv_str(func_obj.get("attr", "")).strip()
        owner = func_obj.get("value")
        os = expr_type_summary(ctx, owner)
        on = json_nominal_type_name(os)
        if on == "JsonValue" and attr in ("as_obj", "as_arr", "as_str", "as_int", "as_float", "as_bool"):
            return "json.value." + attr
        if on == "JsonObj" and attr in ("get", "get_obj", "get_arr", "get_str", "get_int", "get_float", "get_bool"):
            return "json.obj." + attr
        if on == "JsonArr" and attr in ("get", "get_obj", "get_arr", "get_str", "get_int", "get_float", "get_bool"):
            return "json.arr." + attr
        if legacy_compat_bridge_enabled and attr in ("loads", "loads_obj", "loads_arr"):
            if isinstance(owner, dict) and owner.get("kind") == NAME:
                own = jv_str(owner.get("id", "")).strip()
                if own == "json":
                    return "json." + attr
    return ""


def _build_json_decode_meta(call: Node, semantic_tag: str, ctx: CompileContext) -> Node:
    meta: Node = {
        "schema_version": 1,
        "semantic_tag": semantic_tag,
        "result_type": type_expr_summary_from_node(ctx, call),
    }
    if semantic_tag.startswith("json.loads"):
        meta["decode_kind"] = "module_load"
        return meta
    func_obj = call.get("func")
    if not isinstance(func_obj, dict) or func_obj.get("kind") != ATTRIBUTE:
        meta["decode_kind"] = "helper_call"
        return meta
    owner = func_obj.get("value")
    os2 = expr_type_summary(ctx, owner)
    raise_json_contract_violation(semantic_tag, os2)
    meta["decode_kind"] = "narrow"
    meta["receiver_type"] = os2
    rc = jv_str(os2.get("category", "unknown"))
    if rc != "unknown":
        meta["receiver_category"] = rc
    nn = jv_str(os2.get("nominal_adt_name", "")).strip()
    if nn != "":
        meta["receiver_nominal_adt_name"] = nn
    nf = jv_str(os2.get("nominal_adt_family", ""))
    if nf != "":
        meta["receiver_nominal_adt_family"] = nf
    return meta


def _lower_representative_json_decode_call(out_call: Node, ctx: CompileContext) -> Node:
    st = jv_str(out_call.get("semantic_tag", "")).strip()
    if st != "json.value.as_obj":
        return out_call
    args = out_call.get("args")
    al: list[JsonVal] = args if isinstance(args, list) else []
    if len(al) != 0:
        return out_call
    func_obj = out_call.get("func")
    if not isinstance(func_obj, dict) or func_obj.get("kind") != ATTRIBUTE:
        return out_call
    receiver_node = func_obj.get("value")
    cs, rc, recc = representative_json_contract_metadata(ctx, out_call, receiver_node)
    out_call["lowered_kind"] = JSON_DECODE_CALL
    out_call["json_decode_receiver"] = receiver_node
    m_obj = out_call.get(_JSON_DECODE_META_KEY)
    meta: Node = dict(m_obj) if isinstance(m_obj, dict) else _build_json_decode_meta(out_call, st, ctx)
    meta["ir_category"] = JSON_DECODE_CALL
    meta["decode_entry"] = "json.value.as_obj"
    meta["contract_source"] = cs
    meta["result_type"] = rc
    meta["receiver_type"] = recc
    meta["receiver_category"] = recc.get("category", "unknown")
    nn2 = jv_str(recc.get("nominal_adt_name", ""))
    if nn2 != "":
        meta["receiver_nominal_adt_name"] = nn2
    nf2 = jv_str(recc.get("nominal_adt_family", ""))
    if nf2 != "":
        meta["receiver_nominal_adt_family"] = nf2
    out_call[_JSON_DECODE_META_KEY] = meta
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
        "None": "PYTRA_TID_NONE", "bool": "PYTRA_TID_BOOL",
        "int": "PYTRA_TID_INT", "float": "PYTRA_TID_FLOAT",
        "str": "PYTRA_TID_STR", "list": "PYTRA_TID_LIST",
        "dict": "PYTRA_TID_DICT", "set": "PYTRA_TID_SET",
        "object": "PYTRA_TID_OBJECT",
    }
    return table.get(type_name, "")


def _make_type_predicate_expr(
    *, kind: str, left_key: str, left_expr: JsonVal,
    expected_type_id_expr: JsonVal, source_expr: JsonVal,
    ctx: CompileContext,
) -> Node:
    out: Node = {
        "kind": kind, "resolved_type": "bool",
        "borrow_kind": "value", "casts": [],
        left_key: left_expr, "expected_type_id": expected_type_id_expr,
    }
    _copy_source_span_and_repr(source_expr, out)
    ls = expr_type_summary(ctx, left_expr)
    set_type_expr_summary(out, ls)
    mode = jv_str(ls.get("category", "unknown")).strip()
    if mode != "" and mode != "unknown":
        out["narrowing_lane_v1"] = {
            "schema_version": 1,
            "source_category": mode,
            "source_type": dict(ls),
        }
    return out


def _build_nominal_adt_type_test_meta(type_ref_expr: JsonVal, ctx: CompileContext) -> Node | None:
    if not isinstance(type_ref_expr, dict):
        return None
    trd: Node = type_ref_expr
    if trd.get("kind") != NAME:
        return None
    tn = normalize_type_name(trd.get("id"))
    decl = lookup_nominal_adt_decl(ctx, tn)
    if decl is None:
        return None
    meta: Node = {"schema_version": 1, "family_name": jv_str(decl.get("family_name", tn))}
    role = jv_str(decl.get("role", "")).strip()
    if role == "family":
        meta["predicate_kind"] = "family"
        return meta
    meta["predicate_kind"] = "variant"
    meta["variant_name"] = tn
    ps = jv_str(decl.get("payload_style", "")).strip()
    if ps != "":
        meta["payload_style"] = ps
    return meta


def _attach_nominal_adt_type_test_meta(check: Node, ttm: Node | None) -> Node:
    if not isinstance(ttm, dict):
        return check
    check["nominal_adt_test_v1"] = dict(ttm)
    lane = check.get("narrowing_lane_v1")
    l2: Node = dict(lane) if isinstance(lane, dict) else {"schema_version": 1}
    l2["predicate_category"] = "nominal_adt"
    l2["family_name"] = ttm.get("family_name", "")
    pk2 = ttm.get("predicate_kind", "")
    if pk2 != "":
        l2["predicate_kind"] = pk2
    vn3 = ttm.get("variant_name", "")
    if vn3 != "":
        l2["variant_name"] = vn3
    check["narrowing_lane_v1"] = l2
    return check


def _build_or_of_checks(checks: list[Node], source_expr: JsonVal) -> Node:
    if len(checks) == 1:
        return checks[0]
    out: Node = {
        "kind": BOOL_OP, "op": "Or", "values": checks,
        "resolved_type": "bool", "borrow_kind": "value", "casts": [],
    }
    _copy_source_span_and_repr(source_expr, out)
    return out


def _type_ref_to_type_id(
    type_ref_expr: JsonVal, *, dispatch_mode: str,
    lower_node_fn: Callable[[JsonVal], JsonVal],
) -> JsonVal:
    node = lower_node_fn(type_ref_expr)
    if not isinstance(node, dict) or node.get("kind") != NAME:
        return None
    tn = jv_str(node.get("id", "")).strip()
    if tn == "":
        return None
    bs = _builtin_type_id_symbol(tn)
    if bs != "":
        out = _make_name_node(bs, "int64")
        span = _node_source_span(type_ref_expr)
        if isinstance(span, dict):
            out["source_span"] = span
        return out
    return node


def _collect_expected_type_id_specs(
    type_spec_expr: JsonVal, *, dispatch_mode: str,
    lower_node_fn: Callable[[JsonVal], JsonVal],
    ctx: CompileContext,
) -> list[Node]:
    spec_node = lower_node_fn(type_spec_expr)
    out: list[Node] = []
    if isinstance(spec_node, dict) and spec_node.get("kind") == TUPLE:
        elems = spec_node.get("elements")
        el: list[JsonVal] = elems if isinstance(elems, list) else []
        for elem in el:
            lowered = _type_ref_to_type_id(elem, dispatch_mode=dispatch_mode, lower_node_fn=lower_node_fn)
            if lowered is not None:
                out.append({
                    "type_id_expr": lowered,
                    "type_ref_expr": elem,
                    "nominal_adt_test_v1": _build_nominal_adt_type_test_meta(elem, ctx),
                })
        return out
    lowered_one = _type_ref_to_type_id(spec_node, dispatch_mode=dispatch_mode, lower_node_fn=lower_node_fn)
    if lowered_one is not None:
        out.append({
            "type_id_expr": lowered_one,
            "type_ref_expr": spec_node,
            "nominal_adt_test_v1": _build_nominal_adt_type_test_meta(spec_node, ctx),
        })
    return out


def _lower_isinstance_call(
    out_call: Node, *, dispatch_mode: str,
    lower_node_fn: Callable[[JsonVal], JsonVal],
    ctx: CompileContext,
) -> Node:
    args = out_call.get("args")
    al: list[JsonVal] = args if isinstance(args, list) else []
    if len(al) != 2:
        return out_call
    value_expr = al[0]
    specs = _collect_expected_type_id_specs(al[1], dispatch_mode=dispatch_mode, lower_node_fn=lower_node_fn, ctx=ctx)
    expected = [s.get("type_id_expr") for s in specs if isinstance(s, dict)]
    if len(expected) == 0:
        fo = _const_bool_node(False)
        _copy_source_span_and_repr(out_call, fo)
        return fo
    checks: list[Node] = []
    for spec in specs:
        if not isinstance(spec, dict):
            continue
        tid = spec.get("type_id_expr")
        if tid is None:
            continue
        check = _make_type_predicate_expr(
            kind=IS_INSTANCE, left_key="value", left_expr=value_expr,
            expected_type_id_expr=tid, source_expr=out_call,
            ctx=ctx,
        )
        check = _attach_nominal_adt_type_test_meta(check, spec.get("nominal_adt_test_v1"))
        checks.append(check)
    return _build_or_of_checks(checks, out_call)


def _lower_issubclass_call(
    out_call: Node, *, dispatch_mode: str,
    lower_node_fn: Callable[[JsonVal], JsonVal],
    ctx: CompileContext,
) -> Node:
    args = out_call.get("args")
    al: list[JsonVal] = args if isinstance(args, list) else []
    if len(al) != 2:
        return out_call
    atid = _type_ref_to_type_id(al[0], dispatch_mode=dispatch_mode, lower_node_fn=lower_node_fn)
    if atid is None:
        fo = _const_bool_node(False)
        _copy_source_span_and_repr(out_call, fo)
        return fo
    specs = _collect_expected_type_id_specs(al[1], dispatch_mode=dispatch_mode, lower_node_fn=lower_node_fn, ctx=ctx)
    expected = [s.get("type_id_expr") for s in specs if isinstance(s, dict)]
    if len(expected) == 0:
        fo = _const_bool_node(False)
        _copy_source_span_and_repr(out_call, fo)
        return fo
    checks: list[Node] = []
    for spec in specs:
        if not isinstance(spec, dict):
            continue
        tid = spec.get("type_id_expr")
        if tid is None:
            continue
        check = _make_type_predicate_expr(
            kind=IS_SUBCLASS, left_key="actual_type_id", left_expr=atid,
            expected_type_id_expr=tid, source_expr=out_call,
            ctx=ctx,
        )
        check = _attach_nominal_adt_type_test_meta(check, spec.get("nominal_adt_test_v1"))
        checks.append(check)
    return _build_or_of_checks(checks, out_call)


def _lower_type_id_call_expr(
    out_call: Node, *, dispatch_mode: str,
    lower_node_fn: Callable[[JsonVal], JsonVal],
    legacy_compat: bool,
    ctx: CompileContext,
) -> Node:
    st = jv_str(out_call.get("semantic_tag", "")).strip()
    if st == "type.isinstance":
        return _lower_isinstance_call(out_call, dispatch_mode=dispatch_mode, lower_node_fn=lower_node_fn, ctx=ctx)
    if st == "type.issubclass":
        return _lower_issubclass_call(out_call, dispatch_mode=dispatch_mode, lower_node_fn=lower_node_fn, ctx=ctx)
    lk = jv_str(out_call.get("lowered_kind", "")).strip()
    bn = jv_str(out_call.get("builtin_name", "")).strip()
    if lk == TYPE_PREDICATE_CALL:
        if bn == "isinstance":
            return _lower_isinstance_call(out_call, dispatch_mode=dispatch_mode, lower_node_fn=lower_node_fn, ctx=ctx)
        if bn == "issubclass":
            return _lower_issubclass_call(out_call, dispatch_mode=dispatch_mode, lower_node_fn=lower_node_fn, ctx=ctx)
    func_obj = out_call.get("func")
    if not isinstance(func_obj, dict) or func_obj.get("kind") != NAME:
        return out_call
    fn = jv_str(func_obj.get("id", ""))
    if not legacy_compat:
        return out_call
    if fn == "isinstance":
        return _lower_isinstance_call(out_call, dispatch_mode=dispatch_mode, lower_node_fn=lower_node_fn, ctx=ctx)
    if fn == "issubclass":
        return _lower_issubclass_call(out_call, dispatch_mode=dispatch_mode, lower_node_fn=lower_node_fn, ctx=ctx)
    if fn == "py_isinstance" or fn == "py_tid_isinstance":
        al2 = out_call.get("args")
        a2: list[JsonVal] = al2 if isinstance(al2, list) else []
        if len(a2) == 2:
            return _make_type_predicate_expr(kind=IS_INSTANCE, left_key="value", left_expr=a2[0], expected_type_id_expr=a2[1], source_expr=out_call, ctx=ctx)
    if fn == "py_issubclass" or fn == "py_tid_issubclass":
        al2 = out_call.get("args")
        a2 = al2 if isinstance(al2, list) else []
        if len(a2) == 2:
            return _make_type_predicate_expr(kind=IS_SUBCLASS, left_key="actual_type_id", left_expr=a2[0], expected_type_id_expr=a2[1], source_expr=out_call, ctx=ctx)
    if fn == "py_is_subtype" or fn == "py_tid_is_subtype":
        al2 = out_call.get("args")
        a2 = al2 if isinstance(al2, list) else []
        if len(a2) == 2:
            return _make_type_predicate_expr(kind=IS_SUBTYPE, left_key="actual_type_id", left_expr=a2[0], expected_type_id_expr=a2[1], source_expr=out_call, ctx=ctx)
    if fn == "py_runtime_type_id" or fn == "py_tid_runtime_type_id":
        al2 = out_call.get("args")
        a2 = al2 if isinstance(al2, list) else []
        if len(a2) == 1:
            return _make_boundary_expr(kind=OBJ_TYPE_ID, value_key="value", value_node=a2[0], resolved_type="int64", source_expr=out_call, ctx=ctx)
    return out_call


def _wrap_call_args_for_target_types(call: Node, ctx: CompileContext) -> Node:
    args = call.get("args")
    if isinstance(args, list):
        wrapped_args: list[JsonVal] = []
        for arg in args:
            if not isinstance(arg, dict):
                wrapped_args.append(arg)
                continue
            call_arg_type = normalize_type_name(arg.get("call_arg_type"))
            if call_arg_type in ("", "unknown"):
                wrapped_args.append(arg)
                continue
            wrapped_args.append(_wrap_value_for_target_type(arg, call_arg_type, ctx=ctx))
        call["args"] = wrapped_args
    keywords = call.get("keywords")
    if isinstance(keywords, list):
        wrapped_keywords: list[JsonVal] = []
        for kw in keywords:
            if not isinstance(kw, dict):
                wrapped_keywords.append(kw)
                continue
            value = kw.get("value")
            if not isinstance(value, dict):
                wrapped_keywords.append(kw)
                continue
            call_arg_type2 = normalize_type_name(value.get("call_arg_type"))
            if call_arg_type2 in ("", "unknown"):
                wrapped_keywords.append(kw)
                continue
            kw2: Node = dict(kw)
            kw2["value"] = _wrap_value_for_target_type(value, call_arg_type2, ctx=ctx)
            wrapped_keywords.append(kw2)
        call["keywords"] = wrapped_keywords
    return call


# ---------------------------------------------------------------------------
# Starred call args expansion
# ---------------------------------------------------------------------------

def _make_tuple_starred_index_expr(tuple_expr: Node, index: int, elem_type: str, source_expr: JsonVal, ctx: CompileContext) -> Node:
    idx_node = _const_int_node(index)
    tuple_node = deep_copy_json(tuple_expr)
    out: Node = {
        "kind": SUBSCRIPT, "value": tuple_node, "slice": idx_node,
        "resolved_type": elem_type, "borrow_kind": "value", "casts": [],
    }
    span = _node_source_span(source_expr)
    if isinstance(span, dict):
        out["source_span"] = span
    rr = _node_repr(tuple_expr)
    if rr != "":
        out["repr"] = rr + "[" + str(index) + "]"
    set_type_expr_summary(out, type_expr_summary_from_payload(ctx, None, elem_type))
    return out


def _expand_starred_call_args(call: Node, ctx: CompileContext) -> Node:
    args_obj = call.get("args")
    args: list[JsonVal] = args_obj if isinstance(args_obj, list) else []
    expanded: list[JsonVal] = []
    changed = False
    for arg in args:
        if not isinstance(arg, dict):
            expanded.append(arg)
            continue
        ad: Node = arg
        if ad.get("kind") != STARRED:
            expanded.append(arg)
            continue
        changed = True
        value_obj = ad.get("value")
        if not isinstance(value_obj, dict):
            raise RuntimeError("starred_call_contract_violation")
        vd: Node = value_obj
        if vd.get("kind") != NAME:
            raise RuntimeError("starred_call_contract_violation: v1 supports only named tuple starred")
        tt = _tuple_element_types(expr_type_name(ctx, vd))
        if len(tt) == 0:
            raise RuntimeError("starred_call_contract_violation: requires fixed tuple TypeExpr")
        has_bad = False
        for t in tt:
            nt = normalize_type_name(t)
            if nt == "" or nt == "unknown" or _is_any_like_type(t, ctx):
                has_bad = True
                break
        if has_bad:
            raise RuntimeError("starred_call_contract_violation: requires non-dynamic tuple TypeExpr")
        for idx in range(len(tt)):
            expanded.append(_make_tuple_starred_index_expr(vd, idx, tt[idx], ad, ctx))
    if changed:
        call["args"] = expanded
    return call


# ---------------------------------------------------------------------------
# Vararg desugaring
# ---------------------------------------------------------------------------

def _collect_vararg_table(node: JsonVal, out: dict[str, Node]) -> None:
    if isinstance(node, list):
        for item in node:
            _collect_vararg_table(item, out)
        return
    if not isinstance(node, dict):
        return
    nd: Node = node
    kind = nd.get("kind")
    if kind == FUNCTION_DEF:
        vn = jv_str(nd.get("vararg_name", "")).strip()
        vt = jv_str(nd.get("vararg_type", "")).strip()
        if vn != "" and vt != "":
            fn = jv_str(nd.get("name", "")).strip()
            if fn != "":
                ao = nd.get("arg_order")
                al: list[JsonVal] = ao if isinstance(ao, list) else []
                out[fn] = {
                    "n_fixed": len(al),
                    "elem_type": vt,
                    "vararg_name": vn,
                    "list_type": "list[" + vt + "]",
                }
        body_obj = nd.get("body")
        _collect_vararg_table(body_obj, out)
    elif kind == CLASS_DEF:
        _collect_vararg_table(nd.get("body"), out)
    elif kind == MODULE:
        for v in nd.values():
            _collect_vararg_table(v, out)


def _make_vararg_list_node(elements: list[JsonVal], elem_type: str, list_type: str) -> Node:
    node: Node = {
        "kind": LIST, "resolved_type": list_type,
        "borrow_kind": "value", "casts": [], "elements": elements,
    }
    # NOTE: source_span is intentionally NOT added here.
    # The original toolchain's vararg desugaring runs on pre-span-normalized
    # nodes (col, not col_offset), so its col_offset check always fails and
    # no span is generated.  We replicate that behavior.
    return node


def _desugar_vararg_funcdef(nd: Node) -> Node:
    vn = jv_str(nd.get("vararg_name", "")).strip()
    vt = jv_str(nd.get("vararg_type", "")).strip()
    if vn == "" or vt == "":
        return nd
    lt = "list[" + vt + "]"
    ao = nd.get("arg_order")
    al: list[JsonVal] = ao if isinstance(ao, list) else []
    n_fixed = len(al)
    at_obj = nd.get("arg_types")
    at: Node = at_obj if isinstance(at_obj, dict) else {}
    nd["vararg_desugared_v1"] = {
        "n_fixed": n_fixed, "elem_type": vt,
        "vararg_name": vn, "list_type": lt,
    }
    nd["arg_order"] = list(al) + [vn]
    at[vn] = lt
    nd["arg_types"] = at
    vte = nd.get("vararg_type_expr")
    ate = nd.get("arg_type_exprs")
    if isinstance(ate, dict):
        ated: Node = ate
        if isinstance(vte, dict):
            ated[vn] = {"kind": GENERIC_TYPE, "base": "list", "args": [vte]}
        else:
            ated[vn] = {"kind": GENERIC_TYPE, "base": "list", "args": [{"kind": NAMED_TYPE, "name": vt}]}
    nd.pop("vararg_name", None)
    nd.pop("vararg_type", None)
    nd.pop("vararg_type_expr", None)
    return nd


def _pack_vararg_callsite(call: Node, vararg_table: dict[str, Node]) -> Node:
    func = call.get("func")
    if not isinstance(func, dict):
        return call
    fk = func.get("kind")
    fn_key = ""
    if fk == NAME:
        fn_key = jv_str(func.get("id", ""))
    elif fk == ATTRIBUTE:
        fn_key = jv_str(func.get("attr", ""))
    if fn_key.strip() == "" or fn_key not in vararg_table:
        return call
    info = vararg_table[fn_key]
    n_fixed_v = info.get("n_fixed")
    n_fixed: int = n_fixed_v if isinstance(n_fixed_v, int) else 0
    et = jv_str(info.get("elem_type", ""))
    lt = jv_str(info.get("list_type", ""))
    args = call.get("args")
    al: list[JsonVal] = args if isinstance(args, list) else []
    if len(al) <= n_fixed:
        if len(al) == n_fixed:
            packed = _make_vararg_list_node([], et, lt)
            call["args"] = list(al) + [packed]
        return call
    fixed = al[:n_fixed]
    va = al[n_fixed:]
    packed = _make_vararg_list_node(va, et, lt)
    call["args"] = list(fixed) + [packed]
    return call


def _apply_vararg_walk(node: JsonVal, vt: dict[str, Node]) -> JsonVal:
    if isinstance(node, list):
        return [_apply_vararg_walk(item, vt) for item in node]
    if not isinstance(node, dict):
        return node
    nd: Node = node
    kind = nd.get("kind")
    if kind == FUNCTION_DEF:
        _desugar_vararg_funcdef(nd)
        body = nd.get("body")
        if isinstance(body, list):
            nd["body"] = _apply_vararg_walk(body, vt)
        return nd
    if kind == CALL:
        _pack_vararg_callsite(nd, vt)
        for key in list(nd.keys()):
            if key != "kind":
                nd[key] = _apply_vararg_walk(nd[key], vt)
        return nd
    out: Node = {}
    for key in nd:
        out[key] = _apply_vararg_walk(nd[key], vt)
    return out


# ---------------------------------------------------------------------------
# Call expression lowering
# ---------------------------------------------------------------------------

def _lower_call_expr(call: Node, *, dispatch_mode: str, ctx: CompileContext) -> Node:
    out: Node = {}
    for key in call:
        out[key] = _lower_node(call[key], dispatch_mode=dispatch_mode, ctx=ctx)
    out = _expand_starred_call_args(out, ctx)
    out = _lower_type_id_call_expr(
        out, dispatch_mode=dispatch_mode,
        lower_node_fn=lambda node: _lower_node(node, dispatch_mode=dispatch_mode, ctx=ctx),
        legacy_compat=ctx.legacy_compat_bridge,
        ctx=ctx,
    )
    if not isinstance(out, dict):
        return out
    if out.get("kind") != CALL:
        return out
    set_type_expr_summary(out, type_expr_summary_from_node(ctx, out))
    out = _decorate_call_metadata(out, legacy_compat_bridge_enabled=ctx.legacy_compat_bridge, ctx=ctx)
    out = _wrap_call_args_for_target_types(out, ctx)
    # Boundary expressions for dynamic-typed arguments
    func_obj = out.get("func")
    if isinstance(func_obj, dict) and func_obj.get("kind") == NAME and func_obj.get("id") == "getattr":
        args = out.get("args")
        al: list[JsonVal] = args if isinstance(args, list) else []
        if len(al) == 3:
            a0 = al[0]
            if _is_any_like_type(expr_type_name(ctx, a0), ctx):
                an = _const_string_value(al[1])
                if an == "PYTRA_TYPE_ID" and _is_none_literal(al[2]):
                    return _make_boundary_expr(kind=OBJ_TYPE_ID, value_key="value", value_node=a0, resolved_type="int64", source_expr=out, ctx=ctx)
    args = out.get("args")
    al2: list[JsonVal] = args if isinstance(args, list) else []
    if len(al2) != 1:
        return out
    a0 = al2[0]
    a0t = expr_type_name(ctx, a0)
    if not _is_any_like_type(a0t, ctx):
        return out
    st = jv_str(out.get("semantic_tag", "")).strip()
    if st == "cast.bool":
        return _make_boundary_expr(kind=OBJ_BOOL, value_key="value", value_node=a0, resolved_type="bool", source_expr=out, ctx=ctx)
    if st == "core.len":
        return _make_boundary_expr(kind=OBJ_LEN, value_key="value", value_node=a0, resolved_type="int64", source_expr=out, ctx=ctx)
    if st == "cast.str":
        return _make_boundary_expr(kind=OBJ_STR, value_key="value", value_node=a0, resolved_type="str", source_expr=out, ctx=ctx)
    if st == "iter.init":
        return _make_boundary_expr(kind=OBJ_ITER_INIT, value_key="value", value_node=a0, resolved_type="object", source_expr=out, ctx=ctx)
    if st == "iter.next":
        return _make_boundary_expr(kind=OBJ_ITER_NEXT, value_key="iter", value_node=a0, resolved_type="object", source_expr=out, ctx=ctx)
    rc = jv_str(out.get("runtime_call", ""))
    if rc == "py_to_bool":
        return _make_boundary_expr(kind=OBJ_BOOL, value_key="value", value_node=a0, resolved_type="bool", source_expr=out, ctx=ctx)
    if rc == "py_len":
        return _make_boundary_expr(kind=OBJ_LEN, value_key="value", value_node=a0, resolved_type="int64", source_expr=out, ctx=ctx)
    if rc == "py_to_string":
        return _make_boundary_expr(kind=OBJ_STR, value_key="value", value_node=a0, resolved_type="str", source_expr=out, ctx=ctx)
    if rc == "py_iter_or_raise":
        return _make_boundary_expr(kind=OBJ_ITER_INIT, value_key="value", value_node=a0, resolved_type="object", source_expr=out, ctx=ctx)
    if rc == "py_next_or_stop":
        return _make_boundary_expr(kind=OBJ_ITER_NEXT, value_key="iter", value_node=a0, resolved_type="object", source_expr=out, ctx=ctx)
    if out.get("lowered_kind") != BUILTIN_CALL:
        return out
    if not ctx.legacy_compat_bridge:
        return out
    bn = jv_str(out.get("builtin_name", ""))
    if bn == "bool":
        return _make_boundary_expr(kind=OBJ_BOOL, value_key="value", value_node=a0, resolved_type="bool", source_expr=out, ctx=ctx)
    if bn == "len":
        return _make_boundary_expr(kind=OBJ_LEN, value_key="value", value_node=a0, resolved_type="int64", source_expr=out, ctx=ctx)
    if bn == "str":
        return _make_boundary_expr(kind=OBJ_STR, value_key="value", value_node=a0, resolved_type="str", source_expr=out, ctx=ctx)
    if isinstance(func_obj, dict) and func_obj.get("kind") == NAME:
        fn2 = func_obj.get("id")
        if fn2 == "iter":
            return _make_boundary_expr(kind=OBJ_ITER_INIT, value_key="value", value_node=a0, resolved_type="object", source_expr=out, ctx=ctx)
        if fn2 == "next":
            return _make_boundary_expr(kind=OBJ_ITER_NEXT, value_key="iter", value_node=a0, resolved_type="object", source_expr=out, ctx=ctx)
    return out


# ---------------------------------------------------------------------------
# Node dispatch
# ---------------------------------------------------------------------------

def _lower_node_dispatch(node: Node, *, dispatch_mode: str, ctx: CompileContext) -> JsonVal:
    lower_fn: Callable[[JsonVal], JsonVal] = lambda v: _lower_node(v, dispatch_mode=dispatch_mode, ctx=ctx)
    kind = node.get("kind")
    if kind == FOR:
        return _lower_for_stmt(node, dispatch_mode=dispatch_mode, lower_node_fn=lower_fn, ctx=ctx)
    if kind == FOR_RANGE:
        return _lower_forrange_stmt(node, lower_node_fn=lower_fn, ctx=ctx)
    if kind == ASSIGN or kind == ANN_ASSIGN or kind == AUG_ASSIGN:
        return _lower_assignment_like_stmt(node, lower_node_fn=lower_fn, ctx=ctx)
    if kind == CALL:
        return _lower_call_expr(node, dispatch_mode=dispatch_mode, ctx=ctx)
    if kind == ATTRIBUTE:
        out: Node = {}
        for key in node:
            out[key] = lower_fn(node[key])
        return _decorate_nominal_adt_projection_attr(out, ctx)
    if kind == VARIANT_PATTERN:
        out = {}
        for key in node:
            out[key] = lower_fn(node[key])
        return _decorate_nominal_adt_variant_pattern(out, ctx)
    if kind == MATCH:
        out = {}
        for key in node:
            out[key] = lower_fn(node[key])
        return _decorate_nominal_adt_match_stmt(out, ctx)
    if kind == FOR_CORE:
        return _lower_forcore_stmt(node, dispatch_mode=dispatch_mode, lower_node_fn=lower_fn, ctx=ctx)
    out = {}
    for key in node:
        out[key] = lower_fn(node[key])
    return out


def _lower_node(node: JsonVal, *, dispatch_mode: str, ctx: CompileContext) -> JsonVal:
    if isinstance(node, list):
        return [_lower_node(item, dispatch_mode=dispatch_mode, ctx=ctx) for item in node]
    if isinstance(node, dict):
        return _lower_node_dispatch(node, dispatch_mode=dispatch_mode, ctx=ctx)
    return node


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def lower_east2_to_east3(east_module: Node, object_dispatch_mode: str = "") -> Node:
    """EAST2 Module を EAST3 へ lower する。"""
    if not isinstance(east_module, dict):
        return east_module
    # 1. Normalize source spans (col → col_offset, remove Module source_span)
    normalized = walk_normalize_spans(east_module)
    if not isinstance(normalized, dict):
        return east_module
    east_module = normalized

    meta_obj = east_module.get("meta")
    dispatch_mode = "native"
    if object_dispatch_mode != "":
        dispatch_mode = _normalize_dispatch_mode(object_dispatch_mode)
    elif isinstance(meta_obj, dict):
        md: Node = meta_obj
        dispatch_mode = _normalize_dispatch_mode(md.get("dispatch_mode"))

    ctx = CompileContext()
    ctx.nominal_adt_table = collect_nominal_adt_table(east_module)
    ctx.legacy_compat_bridge = True
    if isinstance(meta_obj, dict):
        md2: Node = meta_obj
        lo = md2.get("legacy_compat_bridge")
        if isinstance(lo, bool):
            ctx.legacy_compat_bridge = lo

    lowered = _lower_node(east_module, dispatch_mode=dispatch_mode, ctx=ctx)

    if not isinstance(lowered, dict):
        return east_module
    if lowered.get("kind") != MODULE:
        return lowered

    # Vararg desugaring
    vt: dict[str, Node] = {}
    _collect_vararg_table(lowered, vt)
    if vt:
        lowered = _apply_vararg_walk(lowered, vt)
        if not isinstance(lowered, dict):
            return east_module

    # Post-lowering passes
    lower_yield_generators(lowered, ctx)
    lower_listcomp(lowered, ctx)
    expand_default_arguments(lowered, ctx)
    expand_forcore_tuple_targets(lowered, ctx)
    expand_tuple_unpack(lowered, ctx)
    lower_enumerate(lowered, ctx)
    hoist_block_scope_variables(lowered, ctx)
    apply_integer_promotion(lowered, ctx)
    apply_guard_narrowing(lowered, ctx)
    apply_type_propagation(lowered, ctx)
    apply_yields_dynamic(lowered, ctx)
    detect_swap_patterns(lowered, ctx)
    detect_mutates_self(lowered, ctx)
    detect_unused_variables(lowered, ctx)
    mark_main_guard_discard(lowered, ctx)

    lowered["east_stage"] = 3
    sv = lowered.get("schema_version")
    schema_version = 1
    if isinstance(sv, int) and sv > 0:
        schema_version = sv
    lowered["schema_version"] = schema_version

    mn = lowered.get("meta")
    meta_norm: Node = {}
    if isinstance(mn, dict):
        meta_norm = mn
    lowered["meta"] = meta_norm
    meta_norm["dispatch_mode"] = dispatch_mode
    return lowered
