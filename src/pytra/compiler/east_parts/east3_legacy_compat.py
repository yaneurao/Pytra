"""Normalize EAST3 nodes into legacy EAST2-like shapes for non-EAST3 emitters."""

from __future__ import annotations

from pytra.std.typing import Any


def _make_compat_call(name: str, args: list[Any], resolved_type: str = "") -> dict[str, Any]:
    call: dict[str, Any] = {
        "kind": "Call",
        "func": {"kind": "Name", "id": name},
        "args": args,
        "keywords": [],
    }
    if resolved_type != "":
        call["resolved_type"] = resolved_type
    return call


def _legacy_target_from_plan(plan_node: Any) -> dict[str, Any]:
    if not isinstance(plan_node, dict):
        return {"kind": "Name", "id": "_"}
    kind = str(plan_node.get("kind", ""))
    if kind == "NameTarget":
        return {"kind": "Name", "id": str(plan_node.get("id", "_"))}
    if kind == "TupleTarget":
        elements_obj = plan_node.get("elements")
        elements_raw: list[Any] = elements_obj if isinstance(elements_obj, list) else []
        elements: list[dict[str, Any]] = []
        for elem in elements_raw:
            elements.append(_legacy_target_from_plan(elem))
        return {"kind": "Tuple", "elements": elements}
    if kind == "ExprTarget":
        target_any = plan_node.get("target")
        if isinstance(target_any, dict):
            return target_any
    return {"kind": "Name", "id": "_"}


def _type_id_expr_to_type_ref(expr: Any) -> Any:
    if not isinstance(expr, dict):
        return expr
    if str(expr.get("kind", "")) != "Name":
        return expr
    name = str(expr.get("id", ""))
    type_map: dict[str, str] = {
        "PYTRA_TID_BOOL": "bool",
        "PYTRA_TID_INT": "int",
        "PYTRA_TID_FLOAT": "float",
        "PYTRA_TID_STR": "str",
        "PYTRA_TID_LIST": "list",
        "PYTRA_TID_DICT": "dict",
        "PYTRA_TID_SET": "set",
        "PYTRA_TID_TUPLE": "tuple",
        "PYTRA_TID_OBJECT": "object",
    }
    if name in type_map:
        return {"kind": "Name", "id": type_map[name]}
    return {"kind": "Name", "id": name}


def normalize_east3_to_legacy(node: Any, *, module_stage: int = 2) -> Any:
    if isinstance(node, list):
        out_list: list[Any] = []
        for item in node:
            out_list.append(normalize_east3_to_legacy(item, module_stage=module_stage))
        return out_list
    if not isinstance(node, dict):
        return node

    kind = str(node.get("kind", ""))
    out: dict[str, Any] = {}
    for key, value in node.items():
        out[key] = normalize_east3_to_legacy(value, module_stage=module_stage)

    if kind == "Module":
        out["east_stage"] = module_stage
        return out
    if kind == "Box":
        return out.get("value")
    if kind == "Unbox":
        return out.get("value")
    if kind == "ObjBool":
        return _make_compat_call("bool", [out.get("value")], str(out.get("resolved_type", "")))
    if kind == "ObjLen":
        return _make_compat_call("len", [out.get("value")], str(out.get("resolved_type", "")))
    if kind == "ObjStr":
        return _make_compat_call("str", [out.get("value")], str(out.get("resolved_type", "")))
    if kind == "ObjIterInit":
        return _make_compat_call("iter", [out.get("value")], str(out.get("resolved_type", "")))
    if kind == "ObjIterNext":
        return _make_compat_call("next", [out.get("iter")], str(out.get("resolved_type", "")))
    if kind == "ObjTypeId":
        return _make_compat_call("py_runtime_type_id", [out.get("value")], str(out.get("resolved_type", "")))
    if kind == "IsInstance":
        expected_ref = _type_id_expr_to_type_ref(out.get("expected_type_id"))
        return _make_compat_call(
            "isinstance",
            [out.get("value"), expected_ref],
            str(out.get("resolved_type", "")),
        )
    if kind == "IsSubclass":
        return _make_compat_call(
            "py_issubclass",
            [out.get("actual_type_id"), out.get("expected_type_id")],
            str(out.get("resolved_type", "")),
        )
    if kind == "IsSubtype":
        return _make_compat_call(
            "py_is_subtype",
            [out.get("actual_type_id"), out.get("expected_type_id")],
            str(out.get("resolved_type", "")),
        )
    if kind == "ForCore":
        iter_plan = out.get("iter_plan")
        target_plan = out.get("target_plan")
        body_obj = out.get("body")
        orelse_obj = out.get("orelse")
        body: list[dict[str, Any]] = body_obj if isinstance(body_obj, list) else []
        orelse: list[dict[str, Any]] = orelse_obj if isinstance(orelse_obj, list) else []
        target = _legacy_target_from_plan(target_plan)
        target_type = ""
        if isinstance(target_plan, dict):
            target_type = str(target_plan.get("target_type", ""))
        if isinstance(iter_plan, dict):
            plan_kind = str(iter_plan.get("kind", ""))
            if plan_kind == "StaticRangeForPlan":
                return {
                    "kind": "ForRange",
                    "target": target,
                    "target_type": target_type,
                    "start": iter_plan.get("start"),
                    "stop": iter_plan.get("stop"),
                    "step": iter_plan.get("step"),
                    "range_mode": str(iter_plan.get("range_mode", "ascending")),
                    "body": body,
                    "orelse": orelse,
                }
            if plan_kind == "RuntimeIterForPlan":
                return {
                    "kind": "For",
                    "target": target,
                    "target_type": target_type,
                    "iter_mode": "runtime_protocol",
                    "iter": iter_plan.get("iter_expr"),
                    "body": body,
                    "orelse": orelse,
                }
    return out
