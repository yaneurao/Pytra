"""Shared type-id predicate lowering helpers for EAST2 -> EAST3."""

from __future__ import annotations

from typing import Any
from typing import Callable

from toolchain.compile.east2_to_east3_type_summary import _expr_type_summary
from toolchain.compile.east2_to_east3_type_summary import _lookup_nominal_adt_decl
from toolchain.compile.east2_to_east3_type_summary import _normalize_type_name
from toolchain.compile.east2_to_east3_type_summary import _set_type_expr_summary
from toolchain.compile.east2_to_east3_type_summary import _type_expr_summary_from_payload


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


def _node_source_span(node: Any) -> Any:
    if isinstance(node, dict):
        dn: dict[str, Any] = node
        return dn.get("source_span")
    return None


def _node_repr(node: Any) -> str:
    if isinstance(node, dict):
        dn: dict[str, Any] = node
        repr_obj = dn.get("repr")
        if isinstance(repr_obj, str):
            return repr_obj
    return ""


def _copy_source_span_and_repr(source_expr: Any, out: dict[str, Any]) -> None:
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
    _copy_source_span_and_repr(source_expr, out)
    _set_type_expr_summary(out, _type_expr_summary_from_payload(None, resolved_type))
    return out


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


def _build_nominal_adt_type_test_meta(type_ref_expr: Any) -> dict[str, Any] | None:
    if not isinstance(type_ref_expr, dict):
        return None
    trd: dict[str, Any] = type_ref_expr
    if trd.get("kind") != "Name":
        return None
    type_name = _normalize_type_name(trd.get("id"))
    decl = _lookup_nominal_adt_decl(type_name)
    if decl is None:
        return None
    meta: dict[str, Any] = {
        "schema_version": 1,
        "family_name": str(decl.get("family_name", type_name)),
    }
    role = str(decl.get("role", "")).strip()
    if role == "family":
        meta["predicate_kind"] = "family"
        return meta
    meta["predicate_kind"] = "variant"
    meta["variant_name"] = type_name
    payload_style = str(decl.get("payload_style", "")).strip()
    if payload_style != "":
        meta["payload_style"] = payload_style
    return meta


def _attach_nominal_adt_type_test_meta(check: dict[str, Any], type_test_meta: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(type_test_meta, dict):
        return check
    check["nominal_adt_test_v1"] = dict(type_test_meta)
    lane_obj = check.get("narrowing_lane_v1")
    lane = dict(lane_obj) if isinstance(lane_obj, dict) else {"schema_version": 1}
    lane["predicate_category"] = "nominal_adt"
    lane["family_name"] = type_test_meta.get("family_name", "")
    predicate_kind = type_test_meta.get("predicate_kind", "")
    if predicate_kind != "":
        lane["predicate_kind"] = predicate_kind
    variant_name = type_test_meta.get("variant_name", "")
    if variant_name != "":
        lane["variant_name"] = variant_name
    check["narrowing_lane_v1"] = lane
    return check


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


def _type_ref_expr_to_type_id_expr(
    type_ref_expr: Any,
    *,
    dispatch_mode: str,
    lower_node: Callable[[Any], Any],
) -> Any:
    node = lower_node(type_ref_expr)
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


def _collect_expected_type_id_specs(
    type_spec_expr: Any,
    *,
    dispatch_mode: str,
    lower_node: Callable[[Any], Any],
) -> list[dict[str, Any]]:
    spec_node = lower_node(type_spec_expr)
    out: list[dict[str, Any]] = []
    if isinstance(spec_node, dict) and spec_node.get("kind") == "Tuple":
        elems_obj = spec_node.get("elements")
        elems: list[Any] = elems_obj if isinstance(elems_obj, list) else []
        for elem in elems:
            lowered = _type_ref_expr_to_type_id_expr(elem, dispatch_mode=dispatch_mode, lower_node=lower_node)
            if lowered is not None:
                out.append(
                    {
                        "type_id_expr": lowered,
                        "type_ref_expr": elem,
                        "nominal_adt_test_v1": _build_nominal_adt_type_test_meta(elem),
                    }
                )
        return out
    lowered_one = _type_ref_expr_to_type_id_expr(spec_node, dispatch_mode=dispatch_mode, lower_node=lower_node)
    if lowered_one is not None:
        out.append(
            {
                "type_id_expr": lowered_one,
                "type_ref_expr": spec_node,
                "nominal_adt_test_v1": _build_nominal_adt_type_test_meta(spec_node),
            }
        )
    return out


def _lower_isinstance_call_expr(
    out_call: dict[str, Any],
    *,
    dispatch_mode: str,
    lower_node: Callable[[Any], Any],
) -> dict[str, Any]:
    args_obj = out_call.get("args")
    args: list[Any] = args_obj if isinstance(args_obj, list) else []
    if len(args) != 2:
        return out_call
    value_expr = args[0]
    expected_specs = _collect_expected_type_id_specs(args[1], dispatch_mode=dispatch_mode, lower_node=lower_node)
    expected = [spec.get("type_id_expr") for spec in expected_specs if isinstance(spec, dict)]
    if len(expected) == 0:
        false_out = _const_bool_node(False)
        _copy_source_span_and_repr(out_call, false_out)
        return false_out
    checks: list[dict[str, Any]] = []
    for expected_spec in expected_specs:
        if not isinstance(expected_spec, dict):
            continue
        expected_type_id_expr = expected_spec.get("type_id_expr")
        if expected_type_id_expr is None:
            continue
        check = _make_type_predicate_expr(
            kind="IsInstance",
            left_key="value",
            left_expr=value_expr,
            expected_type_id_expr=expected_type_id_expr,
            source_expr=out_call,
        )
        check = _attach_nominal_adt_type_test_meta(check, expected_spec.get("nominal_adt_test_v1"))
        checks.append(check)
    return _build_or_of_checks(checks, out_call)


def _lower_issubclass_call_expr(
    out_call: dict[str, Any],
    *,
    dispatch_mode: str,
    lower_node: Callable[[Any], Any],
) -> dict[str, Any]:
    args_obj = out_call.get("args")
    args: list[Any] = args_obj if isinstance(args_obj, list) else []
    if len(args) != 2:
        return out_call
    actual_type_id_expr = _type_ref_expr_to_type_id_expr(args[0], dispatch_mode=dispatch_mode, lower_node=lower_node)
    if actual_type_id_expr is None:
        false_out = _const_bool_node(False)
        _copy_source_span_and_repr(out_call, false_out)
        return false_out
    expected_specs = _collect_expected_type_id_specs(args[1], dispatch_mode=dispatch_mode, lower_node=lower_node)
    expected = [spec.get("type_id_expr") for spec in expected_specs if isinstance(spec, dict)]
    if len(expected) == 0:
        false_out = _const_bool_node(False)
        _copy_source_span_and_repr(out_call, false_out)
        return false_out
    checks: list[dict[str, Any]] = []
    for expected_spec in expected_specs:
        if not isinstance(expected_spec, dict):
            continue
        expected_type_id_expr = expected_spec.get("type_id_expr")
        if expected_type_id_expr is None:
            continue
        check = _make_type_predicate_expr(
            kind="IsSubclass",
            left_key="actual_type_id",
            left_expr=actual_type_id_expr,
            expected_type_id_expr=expected_type_id_expr,
            source_expr=out_call,
        )
        check = _attach_nominal_adt_type_test_meta(check, expected_spec.get("nominal_adt_test_v1"))
        checks.append(check)
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
    return _make_boundary_expr(
        kind="ObjTypeId",
        value_key="value",
        value_node=args[0],
        resolved_type="int64",
        source_expr=out_call,
    )


def _lower_type_id_call_expr(
    out_call: dict[str, Any],
    *,
    dispatch_mode: str,
    lower_node: Callable[[Any], Any],
    legacy_compat_bridge_enabled: bool,
) -> dict[str, Any]:
    semantic_tag_obj = out_call.get("semantic_tag")
    semantic_tag = semantic_tag_obj.strip() if isinstance(semantic_tag_obj, str) else ""
    if semantic_tag == "type.isinstance":
        return _lower_isinstance_call_expr(out_call, dispatch_mode=dispatch_mode, lower_node=lower_node)
    if semantic_tag == "type.issubclass":
        return _lower_issubclass_call_expr(out_call, dispatch_mode=dispatch_mode, lower_node=lower_node)

    lowered_kind_obj = out_call.get("lowered_kind")
    lowered_kind = lowered_kind_obj.strip() if isinstance(lowered_kind_obj, str) else ""
    builtin_name_obj = out_call.get("builtin_name")
    builtin_name = builtin_name_obj.strip() if isinstance(builtin_name_obj, str) else ""
    if lowered_kind == "TypePredicateCall":
        if builtin_name == "isinstance":
            return _lower_isinstance_call_expr(out_call, dispatch_mode=dispatch_mode, lower_node=lower_node)
        if builtin_name == "issubclass":
            return _lower_issubclass_call_expr(out_call, dispatch_mode=dispatch_mode, lower_node=lower_node)

    func_obj = out_call.get("func")
    if not isinstance(func_obj, dict) or func_obj.get("kind") != "Name":
        return out_call
    fn_name_obj = func_obj.get("id")
    fn_name = fn_name_obj if isinstance(fn_name_obj, str) else ""
    if not legacy_compat_bridge_enabled:
        return out_call
    if fn_name == "isinstance":
        return _lower_isinstance_call_expr(out_call, dispatch_mode=dispatch_mode, lower_node=lower_node)
    if fn_name == "issubclass":
        return _lower_issubclass_call_expr(out_call, dispatch_mode=dispatch_mode, lower_node=lower_node)
    if fn_name == "py_isinstance" or fn_name == "py_tid_isinstance":
        return _lower_py_isinstance_call_expr(out_call)
    if fn_name == "py_issubclass" or fn_name == "py_tid_issubclass":
        return _lower_py_issubclass_call_expr(out_call)
    if fn_name == "py_is_subtype" or fn_name == "py_tid_is_subtype":
        return _lower_py_issubtype_call_expr(out_call)
    if fn_name == "py_runtime_type_id" or fn_name == "py_tid_runtime_type_id":
        return _lower_py_runtime_type_id_call_expr(out_call)
    return out_call
