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


def _normalize_type_name(value: Any) -> str:
    if isinstance(value, str):
        t = value.strip()
        if t != "":
            return t
    return "unknown"


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


def _is_any_like_type(type_name: Any) -> bool:
    norm = _normalize_type_name(type_name)
    if norm == "Any" or norm == "object" or norm == "unknown":
        return True
    union_parts = _split_union_types(norm)
    if len(union_parts) <= 1:
        return False
    for part in union_parts:
        if part == "Any" or part == "object" or part == "unknown":
            return True
    return False


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


def _expr_type_name(expr: Any) -> str:
    if isinstance(expr, dict):
        return _normalize_type_name(expr.get("resolved_type"))
    return "unknown"


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
    return out


def _wrap_value_for_target_type(value_expr: Any, target_type: Any) -> Any:
    target_t = _normalize_type_name(target_type)
    if target_t == "unknown":
        return value_expr
    value_t = _expr_type_name(value_expr)
    if _is_any_like_type(target_t) and not _is_any_like_type(value_t):
        return _make_boundary_expr(
            kind="Box",
            value_key="value",
            value_node=value_expr,
            resolved_type="object",
            source_expr=value_expr,
        )
    if not _is_any_like_type(target_t) and _is_any_like_type(value_t):
        out = _make_boundary_expr(
            kind="Unbox",
            value_key="value",
            value_node=value_expr,
            resolved_type=target_t,
            source_expr=value_expr,
        )
        out["target"] = target_t
        out["on_fail"] = "raise"
        return out
    return value_expr


def _resolve_assign_target_type(stmt: dict[str, Any]) -> str:
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


def _lower_assignment_like_stmt(stmt: dict[str, Any], *, dispatch_mode: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in stmt:
        if key == "value":
            continue
        out[key] = _lower_node(stmt[key], dispatch_mode=dispatch_mode)
    if "value" not in stmt:
        return out
    value_lowered = _lower_node(stmt.get("value"), dispatch_mode=dispatch_mode)
    target_type = _resolve_assign_target_type(stmt)
    out["value"] = _wrap_value_for_target_type(value_lowered, target_type)
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


def _lower_call_expr(call: dict[str, Any], *, dispatch_mode: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in call:
        out[key] = _lower_node(call[key], dispatch_mode=dispatch_mode)

    args_obj = out.get("args")
    args: list[Any] = args_obj if isinstance(args_obj, list) else []
    if len(args) != 1:
        return out
    arg0 = args[0]
    arg0_type = _expr_type_name(arg0)
    if not _is_any_like_type(arg0_type):
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

    func_obj = out.get("func")
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
