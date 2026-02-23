"""EAST2 -> EAST3 lowering helpers."""

from __future__ import annotations

from pytra.std.typing import Any


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
    dispatch_mode: str,
) -> None:
    for key in source:
        if key in consumed:
            continue
        out[key] = _lower_node(source[key], dispatch_mode=dispatch_mode)


def _build_target_plan(target: Any, target_type: Any, *, dispatch_mode: str) -> dict[str, Any]:
    if isinstance(target, dict):
        kind = target.get("kind")
        if kind == "Name":
            out = {"kind": "NameTarget", "id": target.get("id", "")}
            if isinstance(target_type, str) and target_type != "":
                out["target_type"] = target_type
            return out
        if kind == "Tuple":
            elements_obj = target.get("elements")
            elem_plans: list[dict[str, Any]] = []
            if isinstance(elements_obj, list):
                for elem in elements_obj:
                    elem_plans.append(_build_target_plan(elem, "unknown", dispatch_mode=dispatch_mode))
            out = {"kind": "TupleTarget", "elements": elem_plans}
            if isinstance(target_type, str) and target_type != "":
                out["target_type"] = target_type
            return out
    out = {"kind": "ExprTarget", "target": _lower_node(target, dispatch_mode=dispatch_mode)}
    if isinstance(target_type, str) and target_type != "":
        out["target_type"] = target_type
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
    out = {
        "kind": "ForCore",
        "iter_mode": iter_mode,
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
        out_dict: dict[str, Any] = {}
        for key in node:
            out_dict[key] = _lower_node(node[key], dispatch_mode=dispatch_mode)
        return out_dict
    return node


def lower_east2_to_east3(east_module: dict[str, Any]) -> dict[str, Any]:
    """`EAST2` Module を `EAST3` へ lower する。"""
    if not isinstance(east_module, dict):
        return east_module

    meta_obj = east_module.get("meta")
    dispatch_mode = "native"
    if isinstance(meta_obj, dict):
        dispatch_mode = _normalize_dispatch_mode(meta_obj.get("dispatch_mode"))

    lowered = _lower_node(east_module, dispatch_mode=dispatch_mode)
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

