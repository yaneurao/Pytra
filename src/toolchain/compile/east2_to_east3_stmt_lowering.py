"""Statement lowering helpers for EAST2 -> EAST3."""

from __future__ import annotations

from typing import Any
from typing import Callable

from toolchain.compile.east2_to_east3_type_id_predicate import _make_boundary_expr
from toolchain.compile.east2_to_east3_type_summary import _bridge_lane_payload
from toolchain.compile.east2_to_east3_type_summary import _expr_type_summary
from toolchain.compile.east2_to_east3_type_summary import _is_dynamic_like_summary
from toolchain.compile.east2_to_east3_type_summary import _normalize_type_name
from toolchain.compile.east2_to_east3_type_summary import _set_type_expr_summary
from toolchain.compile.east2_to_east3_type_summary import _type_expr_summary_from_payload
from toolchain.compile.east2_to_east3_type_summary import _unknown_type_summary


def _normalize_iter_mode(value: Any) -> str:
    if isinstance(value, str):
        s: str = value
        mode = s.strip()
        if mode == "static_fastpath" or mode == "runtime_protocol":
            return mode
    return "runtime_protocol"


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


def _const_int_node(value: int) -> dict[str, Any]:
    return {
        "kind": "Constant",
        "resolved_type": "int64",
        "borrow_kind": "value",
        "casts": [],
        "repr": str(value),
        "value": value,
    }


def _copy_extra_fields(
    source: dict[str, Any],
    out: dict[str, Any],
    consumed: set[str],
    *,
    lower_node: Callable[[Any], Any],
) -> None:
    for key in source:
        if key in consumed:
            continue
        out[key] = lower_node(source[key])


def _wrap_value_for_target_type(value_expr: Any, target_type: Any, *, target_type_expr: Any = None) -> Any:
    target_summary = _type_expr_summary_from_payload(target_type_expr, target_type)
    target_t = _normalize_type_name(target_summary.get("mirror"))
    if target_t == "unknown":
        return value_expr
    value_summary = _expr_type_summary(value_expr)
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
        tod: dict[str, Any] = target_obj
        summary = _type_expr_summary_from_payload(tod.get("type_expr"), tod.get("resolved_type"))
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
        tod2: dict[str, Any] = target_obj
        target_t = _normalize_type_name(tod2.get("resolved_type"))
        if target_t != "unknown":
            return target_t
    return "unknown"


def _build_target_plan(
    target: Any,
    target_type: Any,
    *,
    lower_node: Callable[[Any], Any],
) -> dict[str, Any]:
    target_type_norm = _normalize_type_name(target_type)
    if isinstance(target, dict):
        td: dict[str, Any] = target
        kind = td.get("kind")
        if kind == "Name":
            out = {"kind": "NameTarget", "id": td.get("id", "")}
            if target_type_norm != "unknown":
                out["target_type"] = target_type_norm
            return out
        if kind == "Tuple":
            elements_obj = td.get("elements")
            elem_plans: list[dict[str, Any]] = []
            elem_types = _tuple_element_types(target_type_norm)
            if isinstance(elements_obj, list):
                for i in range(len(elements_obj)):
                    elem = elements_obj[i]
                    elem_type = "unknown"
                    if i < len(elem_types):
                        elem_type = elem_types[i]
                    elem_plans.append(_build_target_plan(elem, elem_type, lower_node=lower_node))
            out = {"kind": "TupleTarget", "elements": elem_plans}
            if target_type_norm != "unknown":
                out["target_type"] = target_type_norm
            return out
    out = {"kind": "ExprTarget", "target": lower_node(target)}
    if target_type_norm != "unknown":
        out["target_type"] = target_type_norm
    return out


def _lower_assignment_like_stmt(
    stmt: dict[str, Any],
    *,
    lower_node: Callable[[Any], Any],
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in stmt:
        if key == "value":
            continue
        out[key] = lower_node(stmt[key])
    if "value" not in stmt or stmt.get("value") is None:
        return out
    value_lowered = lower_node(stmt.get("value"))
    target_summary = _resolve_assign_target_type_summary(stmt)
    target_type = _normalize_type_name(target_summary.get("mirror"))
    if target_type == "unknown":
        target_type = _resolve_assign_target_type(stmt)
    target_obj = stmt.get("target")
    target_type_expr = stmt.get("decl_type_expr") or stmt.get("annotation_type_expr")
    if target_type_expr is None and isinstance(target_obj, dict):
        tod3: dict[str, Any] = target_obj
        target_type_expr = tod3.get("type_expr")
    out["value"] = _wrap_value_for_target_type(
        value_lowered,
        target_type,
        target_type_expr=target_type_expr,
    )
    _set_type_expr_summary(out, target_summary)
    return out


def _lower_for_stmt(
    stmt: dict[str, Any],
    *,
    dispatch_mode: str,
    lower_node: Callable[[Any], Any],
) -> dict[str, Any]:
    iter_expr = lower_node(stmt.get("iter"))
    iter_mode = _normalize_iter_mode(stmt.get("iter_mode"))
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
            lower_node=lower_node,
        ),
        "body": lower_node(stmt.get("body", [])),
        "orelse": lower_node(stmt.get("orelse", [])),
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
    _copy_extra_fields(stmt, out, consumed, lower_node=lower_node)
    return out


def _lower_forrange_stmt(
    stmt: dict[str, Any],
    *,
    lower_node: Callable[[Any], Any],
) -> dict[str, Any]:
    start_node = lower_node(stmt.get("start"))
    stop_node = lower_node(stmt.get("stop"))
    step_node = lower_node(stmt.get("step"))
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
            lower_node=lower_node,
        ),
        "body": lower_node(stmt.get("body", [])),
        "orelse": lower_node(stmt.get("orelse", [])),
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
    _copy_extra_fields(stmt, out, consumed, lower_node=lower_node)
    return out


def _lower_forcore_stmt(stmt: dict[str, Any], *, dispatch_mode: str, lower_node: Callable[[Any], Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in stmt:
        out[key] = lower_node(stmt[key])
    iter_plan_obj = out.get("iter_plan")
    if isinstance(iter_plan_obj, dict):
        ipd: dict[str, Any] = iter_plan_obj
        if ipd.get("kind") == "RuntimeIterForPlan":
            ipd["dispatch_mode"] = dispatch_mode
    return out
