"""EAST2 -> EAST3 lowering helpers."""

from __future__ import annotations

from typing import Any

from toolchain.frontends.type_expr import summarize_type_expr
from toolchain.frontends.type_expr import summarize_type_text


_LEGACY_COMPAT_BRIDGE_ENABLED = True
_TYPE_EXPR_SUMMARY_KEY = "type_expr_summary_v1"
_JSON_DECODE_META_KEY = "json_decode_v1"
_JSON_RECEIVER_NAME_PREFIXES = {
    "json.value.": "JsonValue",
    "json.obj.": "JsonObj",
    "json.arr.": "JsonArr",
}


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


def _unknown_type_summary() -> dict[str, Any]:
    return {"kind": "unknown", "category": "unknown", "mirror": "unknown"}


def _type_expr_summary_from_payload(type_expr: Any, mirror: Any) -> dict[str, Any]:
    summary = summarize_type_expr(type_expr)
    if str(summary.get("category", "unknown")) != "unknown":
        return dict(summary)
    return dict(summarize_type_text(mirror))


def _type_expr_summary_from_node(node: Any) -> dict[str, Any]:
    if not isinstance(node, dict):
        return _unknown_type_summary()
    return _type_expr_summary_from_payload(node.get("type_expr"), node.get("resolved_type"))


def _set_type_expr_summary(node: dict[str, Any], summary: dict[str, Any]) -> None:
    category = str(summary.get("category", "unknown")).strip()
    if category == "" or category == "unknown":
        return
    payload = {"schema_version": 1}
    for key, value in summary.items():
        payload[key] = value
    node[_TYPE_EXPR_SUMMARY_KEY] = payload


def _bridge_lane_payload(target_summary: dict[str, Any], value_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "target": dict(target_summary),
        "target_category": target_summary.get("category", "unknown"),
        "value": dict(value_summary),
        "value_category": value_summary.get("category", "unknown"),
    }


def _is_dynamic_like_summary(summary: dict[str, Any]) -> bool:
    category = str(summary.get("category", "unknown")).strip()
    if category == "dynamic" or category == "dynamic_union":
        return True
    mirror = str(summary.get("mirror", "unknown")).strip()
    return mirror == "Any" or mirror == "object" or mirror == "unknown"


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


def _const_bool_node(value: bool) -> dict[str, Any]:
    return {
        "kind": "Constant",
        "resolved_type": "bool",
        "borrow_kind": "value",
        "casts": [],
        "repr": "True" if value else "False",
        "value": value,
    }


def _make_name_node(name: str, resolved_type: str = "unknown") -> dict[str, Any]:
    return {
        "kind": "Name",
        "id": name,
        "resolved_type": resolved_type,
        "borrow_kind": "value",
        "casts": [],
        "repr": name,
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


def _builtin_type_id_symbol(type_name: str) -> str:
    table = {
        "None": "PYTRA_TID_NONE",
        "bool": "PYTRA_TID_BOOL",
        "int": "PYTRA_TID_INT",
        "float": "PYTRA_TID_FLOAT",
        "str": "PYTRA_TID_STR",
        "list": "PYTRA_TID_LIST",
        "dict": "PYTRA_TID_DICT",
        "set": "PYTRA_TID_SET",
        "object": "PYTRA_TID_OBJECT",
    }
    return table.get(type_name, "")


def _copy_source_span_and_repr(source_expr: Any, out: dict[str, Any]) -> None:
    span = _node_source_span(source_expr)
    if isinstance(span, dict):
        out["source_span"] = span
    repr_txt = _node_repr(source_expr)
    if repr_txt != "":
        out["repr"] = repr_txt


def _make_type_predicate_expr(
    *,
    kind: str,
    left_key: str,
    left_expr: Any,
    expected_type_id_expr: Any,
    source_expr: Any,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "kind": kind,
        "resolved_type": "bool",
        "borrow_kind": "value",
        "casts": [],
        left_key: left_expr,
        "expected_type_id": expected_type_id_expr,
    }
    _copy_source_span_and_repr(source_expr, out)
    left_summary = _expr_type_summary(left_expr)
    _set_type_expr_summary(out, left_summary)
    mode = str(left_summary.get("category", "unknown")).strip()
    if mode != "" and mode != "unknown":
        out["narrowing_lane_v1"] = {
            "schema_version": 1,
            "source_category": mode,
            "source_type": dict(left_summary),
        }
    return out


def _build_or_of_checks(checks: list[dict[str, Any]], source_expr: Any) -> dict[str, Any]:
    if len(checks) == 1:
        return checks[0]
    out: dict[str, Any] = {
        "kind": "BoolOp",
        "op": "Or",
        "values": checks,
        "resolved_type": "bool",
        "borrow_kind": "value",
        "casts": [],
    }
    _copy_source_span_and_repr(source_expr, out)
    return out


def _type_ref_expr_to_type_id_expr(type_ref_expr: Any, *, dispatch_mode: str) -> Any:
    node = _lower_node(type_ref_expr, dispatch_mode=dispatch_mode)
    if not isinstance(node, dict):
        return None
    if node.get("kind") != "Name":
        return None
    type_name_obj = node.get("id")
    if not isinstance(type_name_obj, str):
        return None
    type_name = type_name_obj.strip()
    if type_name == "":
        return None
    builtin_symbol = _builtin_type_id_symbol(type_name)
    if builtin_symbol != "":
        out = _make_name_node(builtin_symbol, "int64")
        span = _node_source_span(type_ref_expr)
        if isinstance(span, dict):
            out["source_span"] = span
        return out
    return node


def _collect_expected_type_id_exprs(type_spec_expr: Any, *, dispatch_mode: str) -> list[Any]:
    spec_node = _lower_node(type_spec_expr, dispatch_mode=dispatch_mode)
    if isinstance(spec_node, dict) and spec_node.get("kind") == "Tuple":
        out: list[Any] = []
        elems_obj = spec_node.get("elements")
        elems: list[Any] = elems_obj if isinstance(elems_obj, list) else []
        for elem in elems:
            lowered = _type_ref_expr_to_type_id_expr(elem, dispatch_mode=dispatch_mode)
            if lowered is not None:
                out.append(lowered)
        return out
    lowered_one = _type_ref_expr_to_type_id_expr(spec_node, dispatch_mode=dispatch_mode)
    if lowered_one is None:
        return []
    return [lowered_one]


def _lower_isinstance_call_expr(out_call: dict[str, Any], *, dispatch_mode: str) -> dict[str, Any]:
    args_obj = out_call.get("args")
    args: list[Any] = args_obj if isinstance(args_obj, list) else []
    if len(args) != 2:
        return out_call
    value_expr = args[0]
    expected = _collect_expected_type_id_exprs(args[1], dispatch_mode=dispatch_mode)
    if len(expected) == 0:
        false_out = _const_bool_node(False)
        _copy_source_span_and_repr(out_call, false_out)
        return false_out
    checks: list[dict[str, Any]] = []
    for expected_type_id_expr in expected:
        checks.append(
            _make_type_predicate_expr(
                kind="IsInstance",
                left_key="value",
                left_expr=value_expr,
                expected_type_id_expr=expected_type_id_expr,
                source_expr=out_call,
            )
        )
    return _build_or_of_checks(checks, out_call)


def _lower_issubclass_call_expr(out_call: dict[str, Any], *, dispatch_mode: str) -> dict[str, Any]:
    args_obj = out_call.get("args")
    args: list[Any] = args_obj if isinstance(args_obj, list) else []
    if len(args) != 2:
        return out_call
    actual_type_id_expr = _type_ref_expr_to_type_id_expr(args[0], dispatch_mode=dispatch_mode)
    if actual_type_id_expr is None:
        false_out = _const_bool_node(False)
        _copy_source_span_and_repr(out_call, false_out)
        return false_out
    expected = _collect_expected_type_id_exprs(args[1], dispatch_mode=dispatch_mode)
    if len(expected) == 0:
        false_out = _const_bool_node(False)
        _copy_source_span_and_repr(out_call, false_out)
        return false_out
    checks: list[dict[str, Any]] = []
    for expected_type_id_expr in expected:
        checks.append(
            _make_type_predicate_expr(
                kind="IsSubclass",
                left_key="actual_type_id",
                left_expr=actual_type_id_expr,
                expected_type_id_expr=expected_type_id_expr,
                source_expr=out_call,
            )
        )
    return _build_or_of_checks(checks, out_call)


def _lower_py_isinstance_call_expr(out_call: dict[str, Any]) -> dict[str, Any]:
    args_obj = out_call.get("args")
    args: list[Any] = args_obj if isinstance(args_obj, list) else []
    if len(args) != 2:
        return out_call
    return _make_type_predicate_expr(
        kind="IsInstance",
        left_key="value",
        left_expr=args[0],
        expected_type_id_expr=args[1],
        source_expr=out_call,
    )


def _lower_py_issubclass_call_expr(out_call: dict[str, Any]) -> dict[str, Any]:
    args_obj = out_call.get("args")
    args: list[Any] = args_obj if isinstance(args_obj, list) else []
    if len(args) != 2:
        return out_call
    return _make_type_predicate_expr(
        kind="IsSubclass",
        left_key="actual_type_id",
        left_expr=args[0],
        expected_type_id_expr=args[1],
        source_expr=out_call,
    )


def _lower_py_issubtype_call_expr(out_call: dict[str, Any]) -> dict[str, Any]:
    args_obj = out_call.get("args")
    args: list[Any] = args_obj if isinstance(args_obj, list) else []
    if len(args) != 2:
        return out_call
    return _make_type_predicate_expr(
        kind="IsSubtype",
        left_key="actual_type_id",
        left_expr=args[0],
        expected_type_id_expr=args[1],
        source_expr=out_call,
    )


def _lower_py_runtime_type_id_call_expr(out_call: dict[str, Any]) -> dict[str, Any]:
    args_obj = out_call.get("args")
    args: list[Any] = args_obj if isinstance(args_obj, list) else []
    if len(args) != 1:
        return out_call
    out = _make_boundary_expr(
        kind="ObjTypeId",
        value_key="value",
        value_node=args[0],
        resolved_type="int64",
        source_expr=out_call,
    )
    return out


def _lower_type_id_call_expr(out_call: dict[str, Any], *, dispatch_mode: str) -> dict[str, Any]:
    semantic_tag_obj = out_call.get("semantic_tag")
    semantic_tag = semantic_tag_obj.strip() if isinstance(semantic_tag_obj, str) else ""
    if semantic_tag == "type.isinstance":
        return _lower_isinstance_call_expr(out_call, dispatch_mode=dispatch_mode)
    if semantic_tag == "type.issubclass":
        return _lower_issubclass_call_expr(out_call, dispatch_mode=dispatch_mode)

    lowered_kind_obj = out_call.get("lowered_kind")
    lowered_kind = lowered_kind_obj.strip() if isinstance(lowered_kind_obj, str) else ""
    builtin_name_obj = out_call.get("builtin_name")
    builtin_name = builtin_name_obj.strip() if isinstance(builtin_name_obj, str) else ""
    if lowered_kind == "TypePredicateCall":
        if builtin_name == "isinstance":
            return _lower_isinstance_call_expr(out_call, dispatch_mode=dispatch_mode)
        if builtin_name == "issubclass":
            return _lower_issubclass_call_expr(out_call, dispatch_mode=dispatch_mode)

    func_obj = out_call.get("func")
    if not isinstance(func_obj, dict) or func_obj.get("kind") != "Name":
        return out_call
    fn_name_obj = func_obj.get("id")
    fn_name = fn_name_obj if isinstance(fn_name_obj, str) else ""
    # Legacy fallback for stage2 payloads that still rely on Python function names.
    if not _LEGACY_COMPAT_BRIDGE_ENABLED:
        return out_call
    if fn_name == "isinstance":
        return _lower_isinstance_call_expr(out_call, dispatch_mode=dispatch_mode)
    if fn_name == "issubclass":
        return _lower_issubclass_call_expr(out_call, dispatch_mode=dispatch_mode)
    if fn_name == "py_isinstance" or fn_name == "py_tid_isinstance":
        return _lower_py_isinstance_call_expr(out_call)
    if fn_name == "py_issubclass" or fn_name == "py_tid_issubclass":
        return _lower_py_issubclass_call_expr(out_call)
    if fn_name == "py_is_subtype" or fn_name == "py_tid_is_subtype":
        return _lower_py_issubtype_call_expr(out_call)
    if fn_name == "py_runtime_type_id" or fn_name == "py_tid_runtime_type_id":
        return _lower_py_runtime_type_id_call_expr(out_call)
    return out_call


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
    summary = _expr_type_summary(expr)
    mirror = _normalize_type_name(summary.get("mirror"))
    if mirror != "unknown":
        return mirror
    if isinstance(expr, dict):
        return _normalize_type_name(expr.get("resolved_type"))
    return "unknown"


def _expr_type_summary(expr: Any) -> dict[str, Any]:
    return _type_expr_summary_from_node(expr)


def _json_nominal_type_name(summary: dict[str, Any]) -> str:
    category = str(summary.get("category", "unknown")).strip()
    if category != "nominal_adt":
        return ""
    family = str(summary.get("nominal_adt_family", "")).strip()
    if family != "json":
        return ""
    nominal_name = str(summary.get("nominal_adt_name", "")).strip()
    if nominal_name != "":
        return nominal_name
    mirror = _normalize_type_name(summary.get("mirror"))
    if mirror in {"JsonValue", "JsonObj", "JsonArr"}:
        return mirror
    return ""


def _expected_json_receiver_type_name(semantic_tag: str) -> str:
    for prefix, nominal_name in _JSON_RECEIVER_NAME_PREFIXES.items():
        if semantic_tag.startswith(prefix):
            return nominal_name
    return ""


def _raise_json_contract_violation(semantic_tag: str, owner_summary: dict[str, Any]) -> None:
    expected = _expected_json_receiver_type_name(semantic_tag)
    if expected == "":
        return
    actual = _json_nominal_type_name(owner_summary)
    if actual == expected:
        return
    mirror = _normalize_type_name(owner_summary.get("mirror"))
    category = str(owner_summary.get("category", "unknown")).strip()
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


def _structured_type_expr_summary_from_node(node: Any) -> dict[str, Any]:
    if not isinstance(node, dict):
        return _unknown_type_summary()
    return dict(summarize_type_expr(node.get("type_expr")))


def _representative_json_contract_metadata(call: dict[str, Any], receiver_node: Any) -> tuple[str, dict[str, Any], dict[str, Any]]:
    result_summary = _structured_type_expr_summary_from_node(call)
    receiver_summary = _structured_type_expr_summary_from_node(receiver_node)
    result_category = str(result_summary.get("category", "unknown"))
    result_family = str(result_summary.get("nominal_adt_family", ""))
    result_name = str(result_summary.get("nominal_adt_name", ""))
    receiver_category = str(receiver_summary.get("category", "unknown"))
    receiver_family = str(receiver_summary.get("nominal_adt_family", ""))
    receiver_name = str(receiver_summary.get("nominal_adt_name", ""))
    if (
        result_category == "optional"
        and result_family == "json"
        and result_name == "JsonObj"
        and receiver_category == "nominal_adt"
        and receiver_family == "json"
        and receiver_name == "JsonValue"
    ):
        return "type_expr", result_summary, receiver_summary
    compat_result = _type_expr_summary_from_node(call)
    compat_receiver = _expr_type_summary(receiver_node)
    compat_result_category = str(compat_result.get("category", "unknown"))
    compat_result_family = str(compat_result.get("nominal_adt_family", ""))
    compat_result_name = str(compat_result.get("nominal_adt_name", ""))
    compat_receiver_category = str(compat_receiver.get("category", "unknown"))
    compat_receiver_family = str(compat_receiver.get("nominal_adt_family", ""))
    compat_receiver_name = str(compat_receiver.get("nominal_adt_name", ""))
    if (
        compat_result_category == "optional"
        and compat_result_family == "json"
        and compat_result_name == "JsonObj"
        and compat_receiver_category == "nominal_adt"
        and compat_receiver_family == "json"
        and compat_receiver_name == "JsonValue"
    ):
        return "resolved_type_compat", compat_result, compat_receiver
    raise RuntimeError(
        "json.value.as_obj representative lane requires json nominal contract: "
        + "receiver="
        + compat_receiver_category
        + "/"
        + compat_receiver_family
        + "/"
        + compat_receiver_name
        + ", result="
        + compat_result_category
        + "/"
        + compat_result_family
        + "/"
        + compat_result_name
    )


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

    out = _lower_type_id_call_expr(out, dispatch_mode=dispatch_mode)
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
    _LEGACY_COMPAT_BRIDGE_ENABLED = True
    if isinstance(meta_obj, dict):
        legacy_obj = meta_obj.get("legacy_compat_bridge")
        if isinstance(legacy_obj, bool):
            _LEGACY_COMPAT_BRIDGE_ENABLED = legacy_obj

    try:
        lowered = _lower_node(east_module, dispatch_mode=dispatch_mode)
    finally:
        _LEGACY_COMPAT_BRIDGE_ENABLED = prev_legacy_compat
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
