"""EAST2 -> EAST3 lowering helpers."""

from __future__ import annotations

from typing import Any

from toolchain.ir.east2_to_east3_nominal_adt_meta import _decorate_nominal_adt_ctor_call
from toolchain.ir.east2_to_east3_nominal_adt_meta import _decorate_nominal_adt_match_stmt
from toolchain.ir.east2_to_east3_nominal_adt_meta import _decorate_nominal_adt_projection_attr
from toolchain.ir.east2_to_east3_nominal_adt_meta import _decorate_nominal_adt_variant_pattern
from toolchain.ir.east2_to_east3_type_id_predicate import _lower_type_id_call_expr
from toolchain.ir.east2_to_east3_type_summary import _JSON_DECODE_META_KEY
from toolchain.ir.east2_to_east3_type_summary import _bridge_lane_payload
from toolchain.ir.east2_to_east3_type_summary import _collect_nominal_adt_decl_summary_table
from toolchain.ir.east2_to_east3_type_summary import _expr_type_name
from toolchain.ir.east2_to_east3_type_summary import _expr_type_summary
from toolchain.ir.east2_to_east3_type_summary import _is_dynamic_like_summary
from toolchain.ir.east2_to_east3_type_summary import _json_nominal_type_name
from toolchain.ir.east2_to_east3_type_summary import _normalize_type_name
from toolchain.ir.east2_to_east3_type_summary import _raise_json_contract_violation
from toolchain.ir.east2_to_east3_type_summary import _representative_json_contract_metadata
from toolchain.ir.east2_to_east3_type_summary import _set_type_expr_summary
from toolchain.ir.east2_to_east3_type_summary import _structured_type_expr_summary_from_node
from toolchain.ir.east2_to_east3_type_summary import _swap_nominal_adt_decl_summary_table
from toolchain.ir.east2_to_east3_type_summary import _type_expr_summary_from_node
from toolchain.ir.east2_to_east3_type_summary import _type_expr_summary_from_payload
from toolchain.ir.east2_to_east3_type_summary import _unknown_type_summary


_LEGACY_COMPAT_BRIDGE_ENABLED = True

def _normalize_dispatch_mode(value: Any) -> str:
    if isinstance(value, str):
        mode = value.strip()
        if mode == "native" or mode == "type_id":
            return mode
    return "native"


def _normalize_iter_mode(value: Any) -> str:
    if isinstance(value, str):
        mode = value.strip()
        if mode == "static_fastpath" or mode == "runtime_protocol":
            return mode
    return "runtime_protocol"


def _split_union_types(type_name: str) -> list[str]:
    parts: list[str] = []
    cur = ""
    depth = 0
    for ch in type_name:
        if ch == "[":
            depth += 1
            cur += ch
            continue
        if ch == "]":
            if depth > 0:
                depth -= 1
            cur += ch
            continue
        if ch == "|" and depth == 0:
            part = cur.strip()
            if part != "":
                parts.append(part)
            cur = ""
            continue
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
            continue
        if ch == "]":
            if depth > 0:
                depth -= 1
            cur += ch
            continue
        if ch == "," and depth == 0:
            part = cur.strip()
            if part != "":
                parts.append(part)
            cur = ""
            continue
        cur += ch
    tail = cur.strip()
    if tail != "":
        parts.append(tail)
    return parts


def _tuple_element_types(type_name: Any) -> list[str]:
    norm = _normalize_type_name(type_name)
    if not (norm.startswith("tuple[") and norm.endswith("]")):
        return []
    inner = norm[6:-1]
    if inner == "":
        return []
    return _split_generic_types(inner)


def _is_any_like_type(type_name: Any) -> bool:
    return _is_dynamic_like_summary(_type_expr_summary_from_payload(None, type_name))


def _const_int_node(value: int) -> dict[str, Any]:
    return {
        "kind": "Constant",
        "resolved_type": "int64",
        "borrow_kind": "value",
        "casts": [],
        "repr": str(value),
        "value": value,
    }


def _const_string_value(node: Any) -> str:
    if not isinstance(node, dict):
        return ""
    kind = node.get("kind")
    value = node.get("value")
    if kind == "Constant" and isinstance(value, str):
        return value
    if kind == "Call":
        func_obj = node.get("func")
        if isinstance(func_obj, dict) and func_obj.get("kind") == "Name" and func_obj.get("id") == "str":
            args_obj = node.get("args")
            args: list[Any] = args_obj if isinstance(args_obj, list) else []
            if len(args) == 1:
                return _const_string_value(args[0])
    return ""


def _is_none_literal(node: Any) -> bool:
    if not isinstance(node, dict):
        return False
    if node.get("kind") != "Constant":
        return False
    return node.get("value") is None


def _copy_extra_fields(
    source: dict[str, Any],
    out: dict[str, Any],
    consumed: set[str],
    *,
    dispatch_mode: str,
) -> None:
    for key in source:
        if key in consumed:
            continue
        out[key] = _lower_node(source[key], dispatch_mode=dispatch_mode)


def _node_source_span(node: Any) -> Any:
    if isinstance(node, dict):
        return node.get("source_span")
    return None


def _node_repr(node: Any) -> str:
    if isinstance(node, dict):
        repr_obj = node.get("repr")
        if isinstance(repr_obj, str):
            return repr_obj
    return ""


def _make_boundary_expr(
    *,
    kind: str,
    value_key: str,
    value_node: Any,
    resolved_type: str,
    source_expr: Any,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "kind": kind,
        "resolved_type": resolved_type,
        "borrow_kind": "value",
        "casts": [],
        value_key: value_node,
    }
    span = _node_source_span(source_expr)
    if isinstance(span, dict):
        out["source_span"] = span
    repr_txt = _node_repr(source_expr)
    if repr_txt != "":
        out["repr"] = repr_txt
    _set_type_expr_summary(out, _type_expr_summary_from_payload(None, resolved_type))
    return out


def _wrap_value_for_target_type(value_expr: Any, target_type: Any, *, target_type_expr: Any = None) -> Any:
    target_summary = _type_expr_summary_from_payload(target_type_expr, target_type)
    target_t = _normalize_type_name(target_summary.get("mirror"))
    if target_t == "unknown":
        return value_expr
    value_summary = _expr_type_summary(value_expr)
    value_t = _normalize_type_name(value_summary.get("mirror"))
    if _is_dynamic_like_summary(target_summary) and not _is_dynamic_like_summary(value_summary):
        out = _make_boundary_expr(
            kind="Box",
            value_key="value",
            value_node=value_expr,
            resolved_type="object",
            source_expr=value_expr,
        )
        out["bridge_lane_v1"] = _bridge_lane_payload(target_summary, value_summary)
        _set_type_expr_summary(out, target_summary)
        return out
    if not _is_dynamic_like_summary(target_summary) and _is_dynamic_like_summary(value_summary):
        out = _make_boundary_expr(
            kind="Unbox",
            value_key="value",
            value_node=value_expr,
            resolved_type=target_t,
            source_expr=value_expr,
        )
        out["target"] = target_t
        out["on_fail"] = "raise"
        out["bridge_lane_v1"] = _bridge_lane_payload(target_summary, value_summary)
        _set_type_expr_summary(out, target_summary)
        return out
    return value_expr


def _resolve_assign_target_type_summary(stmt: dict[str, Any]) -> dict[str, Any]:
    decl_expr = stmt.get("decl_type_expr")
    summary = _type_expr_summary_from_payload(decl_expr, stmt.get("decl_type"))
    if str(summary.get("category", "unknown")) != "unknown":
        return summary
    ann_expr = stmt.get("annotation_type_expr")
    summary = _type_expr_summary_from_payload(ann_expr, stmt.get("annotation"))
    if str(summary.get("category", "unknown")) != "unknown":
        return summary
    target_obj = stmt.get("target")
    if isinstance(target_obj, dict):
        summary = _type_expr_summary_from_payload(target_obj.get("type_expr"), target_obj.get("resolved_type"))
        if str(summary.get("category", "unknown")) != "unknown":
            return summary
    return _unknown_type_summary()


def _resolve_assign_target_type(stmt: dict[str, Any]) -> str:
    summary = _resolve_assign_target_type_summary(stmt)
    mirror = _normalize_type_name(summary.get("mirror"))
    if mirror != "unknown":
        return mirror
    decl_type = _normalize_type_name(stmt.get("decl_type"))
    if decl_type != "unknown":
        return decl_type
    ann_type = _normalize_type_name(stmt.get("annotation"))
    if ann_type != "unknown":
        return ann_type
    target_obj = stmt.get("target")
    if isinstance(target_obj, dict):
        target_t = _normalize_type_name(target_obj.get("resolved_type"))
        if target_t != "unknown":
            return target_t
    return "unknown"


def _build_target_plan(target: Any, target_type: Any, *, dispatch_mode: str) -> dict[str, Any]:
    target_type_norm = _normalize_type_name(target_type)
    if isinstance(target, dict):
        kind = target.get("kind")
        if kind == "Name":
            out = {"kind": "NameTarget", "id": target.get("id", "")}
            if target_type_norm != "unknown":
                out["target_type"] = target_type_norm
            return out
        if kind == "Tuple":
            elements_obj = target.get("elements")
            elem_plans: list[dict[str, Any]] = []
            elem_types = _tuple_element_types(target_type_norm)
            if isinstance(elements_obj, list):
                for i, elem in enumerate(elements_obj):
                    elem_type = "unknown"
                    if i < len(elem_types):
                        elem_type = elem_types[i]
                    elem_plans.append(_build_target_plan(elem, elem_type, dispatch_mode=dispatch_mode))
            out = {"kind": "TupleTarget", "elements": elem_plans}
            if target_type_norm != "unknown":
                out["target_type"] = target_type_norm
            return out
    out = {"kind": "ExprTarget", "target": _lower_node(target, dispatch_mode=dispatch_mode)}
    if target_type_norm != "unknown":
        out["target_type"] = target_type_norm
    return out


def _lower_assignment_like_stmt(stmt: dict[str, Any], *, dispatch_mode: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in stmt:
        if key == "value":
            continue
        out[key] = _lower_node(stmt[key], dispatch_mode=dispatch_mode)
    if "value" not in stmt:
        return out
    if stmt.get("value") is None:
        return out
    value_lowered = _lower_node(stmt.get("value"), dispatch_mode=dispatch_mode)
    target_summary = _resolve_assign_target_type_summary(stmt)
    target_type = _normalize_type_name(target_summary.get("mirror"))
    if target_type == "unknown":
        target_type = _resolve_assign_target_type(stmt)
    target_obj = stmt.get("target")
    target_type_expr = stmt.get("decl_type_expr") or stmt.get("annotation_type_expr")
    if target_type_expr is None and isinstance(target_obj, dict):
        target_type_expr = target_obj.get("type_expr")
    out["value"] = _wrap_value_for_target_type(
        value_lowered,
        target_type,
        target_type_expr=target_type_expr,
    )
    _set_type_expr_summary(out, target_summary)
    return out


def _lower_for_stmt(stmt: dict[str, Any], *, dispatch_mode: str) -> dict[str, Any]:
    iter_expr = _lower_node(stmt.get("iter"), dispatch_mode=dispatch_mode)
    iter_mode = _normalize_iter_mode(stmt.get("iter_mode"))
    # EAST3 初期導入では、For は runtime protocol に統一して意味情報を落とさない。
    if iter_mode != "runtime_protocol":
        iter_mode = "runtime_protocol"
    iter_plan = {
        "kind": "RuntimeIterForPlan",
        "iter_expr": iter_expr,
        "dispatch_mode": dispatch_mode,
        "init_op": "ObjIterInit",
        "next_op": "ObjIterNext",
    }
    target_type = _normalize_type_name(stmt.get("target_type"))
    if target_type == "unknown":
        target_type = _normalize_type_name(stmt.get("iter_element_type"))
    out = {
        "kind": "ForCore",
        "iter_mode": iter_mode,
        "iter_plan": iter_plan,
        "target_plan": _build_target_plan(
            stmt.get("target"),
            target_type,
            dispatch_mode=dispatch_mode,
        ),
        "body": _lower_node(stmt.get("body", []), dispatch_mode=dispatch_mode),
        "orelse": _lower_node(stmt.get("orelse", []), dispatch_mode=dispatch_mode),
    }
    consumed = {
        "kind",
        "target",
        "target_type",
        "iter_mode",
        "iter_source_type",
        "iter_element_type",
        "iter",
        "body",
        "orelse",
    }
    _copy_extra_fields(stmt, out, consumed, dispatch_mode=dispatch_mode)
    return out


def _lower_forrange_stmt(stmt: dict[str, Any], *, dispatch_mode: str) -> dict[str, Any]:
    start_node = _lower_node(stmt.get("start"), dispatch_mode=dispatch_mode)
    stop_node = _lower_node(stmt.get("stop"), dispatch_mode=dispatch_mode)
    step_value = stmt.get("step")
    step_node = _lower_node(step_value, dispatch_mode=dispatch_mode)
    if not isinstance(step_node, dict):
        step_node = _const_int_node(1)
    iter_plan = {
        "kind": "StaticRangeForPlan",
        "start": start_node,
        "stop": stop_node,
        "step": step_node,
    }
    out = {
        "kind": "ForCore",
        "iter_mode": "static_fastpath",
        "iter_plan": iter_plan,
        "target_plan": _build_target_plan(
            stmt.get("target"),
            stmt.get("target_type"),
            dispatch_mode=dispatch_mode,
        ),
        "body": _lower_node(stmt.get("body", []), dispatch_mode=dispatch_mode),
        "orelse": _lower_node(stmt.get("orelse", []), dispatch_mode=dispatch_mode),
    }
    consumed = {
        "kind",
        "target",
        "target_type",
        "start",
        "stop",
        "step",
        "range_mode",
        "body",
        "orelse",
    }
    _copy_extra_fields(stmt, out, consumed, dispatch_mode=dispatch_mode)
    return out


def _infer_json_semantic_tag(call: dict[str, Any]) -> str:
    semantic_tag_obj = call.get("semantic_tag")
    semantic_tag = semantic_tag_obj.strip() if isinstance(semantic_tag_obj, str) else ""
    if semantic_tag.startswith("json."):
        return semantic_tag
    module_id_obj = call.get("runtime_module_id")
    runtime_symbol_obj = call.get("runtime_symbol")
    module_id = module_id_obj.strip() if isinstance(module_id_obj, str) else ""
    runtime_symbol = runtime_symbol_obj.strip() if isinstance(runtime_symbol_obj, str) else ""
    if module_id == "pytra.std.json":
        if runtime_symbol == "loads":
            return "json.loads"
        if runtime_symbol == "loads_obj":
            return "json.loads_obj"
        if runtime_symbol == "loads_arr":
            return "json.loads_arr"
    func_obj = call.get("func")
    if isinstance(func_obj, dict) and func_obj.get("kind") == "Attribute":
        attr_obj = func_obj.get("attr")
        attr = attr_obj.strip() if isinstance(attr_obj, str) else ""
        owner_obj = func_obj.get("value")
        owner_summary = _expr_type_summary(owner_obj)
        owner_nominal_name = _json_nominal_type_name(owner_summary)
        if owner_nominal_name == "JsonValue" and attr in {"as_obj", "as_arr", "as_str", "as_int", "as_float", "as_bool"}:
            return "json.value." + attr
        if owner_nominal_name == "JsonObj" and attr in {
            "get",
            "get_obj",
            "get_arr",
            "get_str",
            "get_int",
            "get_float",
            "get_bool",
        }:
            return "json.obj." + attr
        if owner_nominal_name == "JsonArr" and attr in {
            "get",
            "get_obj",
            "get_arr",
            "get_str",
            "get_int",
            "get_float",
            "get_bool",
        }:
            return "json.arr." + attr
        if _LEGACY_COMPAT_BRIDGE_ENABLED and attr in {"loads", "loads_obj", "loads_arr"}:
            owner_name = ""
            if isinstance(owner_obj, dict) and owner_obj.get("kind") == "Name":
                owner_name_obj = owner_obj.get("id")
                owner_name = owner_name_obj.strip() if isinstance(owner_name_obj, str) else ""
            if owner_name == "json":
                return "json." + attr
    return ""


def _build_json_decode_meta(call: dict[str, Any], semantic_tag: str) -> dict[str, Any]:
    meta: dict[str, Any] = {
        "schema_version": 1,
        "semantic_tag": semantic_tag,
        "result_type": _type_expr_summary_from_node(call),
    }
    if semantic_tag.startswith("json.loads"):
        meta["decode_kind"] = "module_load"
        return meta
    func_obj = call.get("func")
    if not isinstance(func_obj, dict) or func_obj.get("kind") != "Attribute":
        meta["decode_kind"] = "helper_call"
        return meta
    owner_obj = func_obj.get("value")
    owner_summary = _expr_type_summary(owner_obj)
    _raise_json_contract_violation(semantic_tag, owner_summary)
    meta["decode_kind"] = "narrow"
    meta["receiver_type"] = owner_summary
    receiver_category = str(owner_summary.get("category", "unknown"))
    if receiver_category != "unknown":
        meta["receiver_category"] = receiver_category
    nominal_name = str(owner_summary.get("nominal_adt_name", "")).strip()
    if nominal_name != "":
        meta["receiver_nominal_adt_name"] = nominal_name
    nominal_family = str(owner_summary.get("nominal_adt_family", ""))
    if nominal_family != "":
        meta["receiver_nominal_adt_family"] = nominal_family
    return meta


def _lower_representative_json_decode_call(out_call: dict[str, Any]) -> dict[str, Any]:
    semantic_tag_obj = out_call.get("semantic_tag")
    semantic_tag = semantic_tag_obj.strip() if isinstance(semantic_tag_obj, str) else ""
    if semantic_tag != "json.value.as_obj":
        return out_call
    args_obj = out_call.get("args")
    args: list[Any] = args_obj if isinstance(args_obj, list) else []
    if len(args) != 0:
        return out_call
    func_obj = out_call.get("func")
    if not isinstance(func_obj, dict) or func_obj.get("kind") != "Attribute":
        return out_call
    receiver_node = func_obj.get("value")
    contract_source, result_contract, receiver_contract = _representative_json_contract_metadata(out_call, receiver_node)
    out_call["lowered_kind"] = "JsonDecodeCall"
    out_call["json_decode_receiver"] = receiver_node
    meta_obj = out_call.get(_JSON_DECODE_META_KEY)
    meta = dict(meta_obj) if isinstance(meta_obj, dict) else _build_json_decode_meta(out_call, semantic_tag)
    meta["ir_category"] = "JsonDecodeCall"
    meta["decode_entry"] = "json.value.as_obj"
    meta["contract_source"] = contract_source
    meta["result_type"] = result_contract
    meta["receiver_type"] = receiver_contract
    meta["receiver_category"] = receiver_contract.get("category", "unknown")
    nominal_name = str(receiver_contract.get("nominal_adt_name", ""))
    if nominal_name != "":
        meta["receiver_nominal_adt_name"] = nominal_name
    nominal_family = str(receiver_contract.get("nominal_adt_family", ""))
    if nominal_family != "":
        meta["receiver_nominal_adt_family"] = nominal_family
    out_call[_JSON_DECODE_META_KEY] = meta
    return out_call


def _decorate_call_metadata(call: dict[str, Any]) -> dict[str, Any]:
    _set_type_expr_summary(call, _type_expr_summary_from_node(call))
    call = _decorate_nominal_adt_ctor_call(call)
    json_tag = _infer_json_semantic_tag(call)
    if json_tag != "":
        call["semantic_tag"] = json_tag
        call[_JSON_DECODE_META_KEY] = _build_json_decode_meta(call, json_tag)
        call = _lower_representative_json_decode_call(call)
    return call


def _lower_call_expr(call: dict[str, Any], *, dispatch_mode: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in call:
        out[key] = _lower_node(call[key], dispatch_mode=dispatch_mode)

    out = _lower_type_id_call_expr(
        out,
        dispatch_mode=dispatch_mode,
        lower_node=lambda node: _lower_node(node, dispatch_mode=dispatch_mode),
        legacy_compat_bridge_enabled=_LEGACY_COMPAT_BRIDGE_ENABLED,
    )
    if not isinstance(out, dict):
        return out
    if out.get("kind") != "Call":
        return out
    out = _decorate_call_metadata(out)

    func_obj = out.get("func")
    if isinstance(func_obj, dict) and func_obj.get("kind") == "Name" and func_obj.get("id") == "getattr":
        args_obj = out.get("args")
        args: list[Any] = args_obj if isinstance(args_obj, list) else []
        if len(args) == 3:
            arg0 = args[0]
            if _is_any_like_type(_expr_type_name(arg0)):
                attr_name = _const_string_value(args[1])
                if attr_name == "PYTRA_TYPE_ID" and _is_none_literal(args[2]):
                    return _make_boundary_expr(
                        kind="ObjTypeId",
                        value_key="value",
                        value_node=arg0,
                        resolved_type="int64",
                        source_expr=out,
                    )

    args_obj = out.get("args")
    args: list[Any] = args_obj if isinstance(args_obj, list) else []
    if len(args) != 1:
        return out
    arg0 = args[0]
    arg0_type = _expr_type_name(arg0)
    if not _is_any_like_type(arg0_type):
        return out

    semantic_tag_obj = out.get("semantic_tag")
    semantic_tag = semantic_tag_obj.strip() if isinstance(semantic_tag_obj, str) else ""
    if semantic_tag == "cast.bool":
        return _make_boundary_expr(
            kind="ObjBool",
            value_key="value",
            value_node=arg0,
            resolved_type="bool",
            source_expr=out,
        )
    if semantic_tag == "core.len":
        return _make_boundary_expr(
            kind="ObjLen",
            value_key="value",
            value_node=arg0,
            resolved_type="int64",
            source_expr=out,
        )
    if semantic_tag == "cast.str":
        return _make_boundary_expr(
            kind="ObjStr",
            value_key="value",
            value_node=arg0,
            resolved_type="str",
            source_expr=out,
        )
    if semantic_tag == "iter.init":
        return _make_boundary_expr(
            kind="ObjIterInit",
            value_key="value",
            value_node=arg0,
            resolved_type="object",
            source_expr=out,
        )
    if semantic_tag == "iter.next":
        return _make_boundary_expr(
            kind="ObjIterNext",
            value_key="iter",
            value_node=arg0,
            resolved_type="object",
            source_expr=out,
        )

    runtime_call = out.get("runtime_call")
    if runtime_call == "py_to_bool":
        return _make_boundary_expr(
            kind="ObjBool",
            value_key="value",
            value_node=arg0,
            resolved_type="bool",
            source_expr=out,
        )
    if runtime_call == "py_len":
        return _make_boundary_expr(
            kind="ObjLen",
            value_key="value",
            value_node=arg0,
            resolved_type="int64",
            source_expr=out,
        )
    if runtime_call == "py_to_string":
        return _make_boundary_expr(
            kind="ObjStr",
            value_key="value",
            value_node=arg0,
            resolved_type="str",
            source_expr=out,
        )
    if runtime_call == "py_iter_or_raise":
        return _make_boundary_expr(
            kind="ObjIterInit",
            value_key="value",
            value_node=arg0,
            resolved_type="object",
            source_expr=out,
        )
    if runtime_call == "py_next_or_stop":
        return _make_boundary_expr(
            kind="ObjIterNext",
            value_key="iter",
            value_node=arg0,
            resolved_type="object",
            source_expr=out,
        )

    if out.get("lowered_kind") != "BuiltinCall":
        return out

    # Legacy fallback for stage2 payloads that still encode builtin identity.
    if not _LEGACY_COMPAT_BRIDGE_ENABLED:
        return out
    builtin_name = out.get("builtin_name")
    if builtin_name == "bool":
        return _make_boundary_expr(
            kind="ObjBool",
            value_key="value",
            value_node=arg0,
            resolved_type="bool",
            source_expr=out,
        )
    if builtin_name == "len":
        return _make_boundary_expr(
            kind="ObjLen",
            value_key="value",
            value_node=arg0,
            resolved_type="int64",
            source_expr=out,
        )
    if builtin_name == "str":
        return _make_boundary_expr(
            kind="ObjStr",
            value_key="value",
            value_node=arg0,
            resolved_type="str",
            source_expr=out,
        )

    if isinstance(func_obj, dict) and func_obj.get("kind") == "Name":
        fn_name = func_obj.get("id")
        if fn_name == "iter":
            return _make_boundary_expr(
                kind="ObjIterInit",
                value_key="value",
                value_node=arg0,
                resolved_type="object",
                source_expr=out,
            )
        if fn_name == "next":
            return _make_boundary_expr(
                kind="ObjIterNext",
                value_key="iter",
                value_node=arg0,
                resolved_type="object",
                source_expr=out,
            )
    return out


def _lower_forcore_stmt(stmt: dict[str, Any], *, dispatch_mode: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in stmt:
        out[key] = _lower_node(stmt[key], dispatch_mode=dispatch_mode)
    iter_plan_obj = out.get("iter_plan")
    if isinstance(iter_plan_obj, dict) and iter_plan_obj.get("kind") == "RuntimeIterForPlan":
        iter_plan_obj["dispatch_mode"] = dispatch_mode
    return out


def _lower_attribute_expr(expr: dict[str, Any], *, dispatch_mode: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in expr:
        out[key] = _lower_node(expr[key], dispatch_mode=dispatch_mode)
    return _decorate_nominal_adt_projection_attr(out)


def _lower_variant_pattern(pattern: dict[str, Any], *, dispatch_mode: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in pattern:
        out[key] = _lower_node(pattern[key], dispatch_mode=dispatch_mode)
    return _decorate_nominal_adt_variant_pattern(out)


def _lower_match_stmt(stmt: dict[str, Any], *, dispatch_mode: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in stmt:
        out[key] = _lower_node(stmt[key], dispatch_mode=dispatch_mode)
    return _decorate_nominal_adt_match_stmt(out)


def _lower_node(node: Any, *, dispatch_mode: str) -> Any:
    if isinstance(node, list):
        out_list: list[Any] = []
        for item in node:
            out_list.append(_lower_node(item, dispatch_mode=dispatch_mode))
        return out_list
    if isinstance(node, dict):
        kind = node.get("kind")
        if kind == "For":
            return _lower_for_stmt(node, dispatch_mode=dispatch_mode)
        if kind == "ForRange":
            return _lower_forrange_stmt(node, dispatch_mode=dispatch_mode)
        if kind == "Assign" or kind == "AnnAssign" or kind == "AugAssign":
            return _lower_assignment_like_stmt(node, dispatch_mode=dispatch_mode)
        if kind == "Call":
            return _lower_call_expr(node, dispatch_mode=dispatch_mode)
        if kind == "Attribute":
            return _lower_attribute_expr(node, dispatch_mode=dispatch_mode)
        if kind == "VariantPattern":
            return _lower_variant_pattern(node, dispatch_mode=dispatch_mode)
        if kind == "Match":
            return _lower_match_stmt(node, dispatch_mode=dispatch_mode)
        if kind == "ForCore":
            return _lower_forcore_stmt(node, dispatch_mode=dispatch_mode)
        out_dict: dict[str, Any] = {}
        for key in node:
            out_dict[key] = _lower_node(node[key], dispatch_mode=dispatch_mode)
        return out_dict
    return node


def lower_east2_to_east3(east_module: dict[str, Any], object_dispatch_mode: str = "") -> dict[str, Any]:
    """`EAST2` Module を `EAST3` へ lower する。"""
    if not isinstance(east_module, dict):
        return east_module

    meta_obj = east_module.get("meta")
    dispatch_mode = "native"
    if object_dispatch_mode != "":
        dispatch_mode = _normalize_dispatch_mode(object_dispatch_mode)
    elif isinstance(meta_obj, dict):
        dispatch_mode = _normalize_dispatch_mode(meta_obj.get("dispatch_mode"))

    global _LEGACY_COMPAT_BRIDGE_ENABLED
    prev_legacy_compat = _LEGACY_COMPAT_BRIDGE_ENABLED
    prev_nominal_adt_decl_table = _swap_nominal_adt_decl_summary_table(
        _collect_nominal_adt_decl_summary_table(east_module)
    )
    _LEGACY_COMPAT_BRIDGE_ENABLED = True
    if isinstance(meta_obj, dict):
        legacy_obj = meta_obj.get("legacy_compat_bridge")
        if isinstance(legacy_obj, bool):
            _LEGACY_COMPAT_BRIDGE_ENABLED = legacy_obj

    try:
        lowered = _lower_node(east_module, dispatch_mode=dispatch_mode)
    finally:
        _LEGACY_COMPAT_BRIDGE_ENABLED = prev_legacy_compat
        _swap_nominal_adt_decl_summary_table(prev_nominal_adt_decl_table)
    if not isinstance(lowered, dict):
        return east_module
    if lowered.get("kind") != "Module":
        return lowered

    lowered["east_stage"] = 3
    schema_obj = lowered.get("schema_version")
    schema_version = 1
    if isinstance(schema_obj, int) and schema_obj > 0:
        schema_version = schema_obj
    lowered["schema_version"] = schema_version

    meta_norm_obj = lowered.get("meta")
    meta_norm: dict[str, Any] = {}
    if isinstance(meta_norm_obj, dict):
        meta_norm = meta_norm_obj
    lowered["meta"] = meta_norm
    meta_norm["dispatch_mode"] = dispatch_mode
    return lowered
