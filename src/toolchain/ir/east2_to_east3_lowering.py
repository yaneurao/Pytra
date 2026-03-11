"""EAST2 -> EAST3 lowering helpers."""

from __future__ import annotations

from typing import Any

from toolchain.ir.east2_to_east3_call_metadata import _decorate_call_metadata
from toolchain.ir.east2_to_east3_nominal_adt_meta import _decorate_nominal_adt_match_stmt
from toolchain.ir.east2_to_east3_nominal_adt_meta import _decorate_nominal_adt_projection_attr
from toolchain.ir.east2_to_east3_nominal_adt_meta import _decorate_nominal_adt_variant_pattern
from toolchain.ir.east2_to_east3_stmt_lowering import _lower_assignment_like_stmt
from toolchain.ir.east2_to_east3_stmt_lowering import _lower_for_stmt
from toolchain.ir.east2_to_east3_stmt_lowering import _lower_forcore_stmt
from toolchain.ir.east2_to_east3_stmt_lowering import _lower_forrange_stmt
from toolchain.ir.east2_to_east3_type_id_predicate import _lower_type_id_call_expr
from toolchain.ir.east2_to_east3_type_summary import _bridge_lane_payload
from toolchain.ir.east2_to_east3_type_summary import _collect_nominal_adt_decl_summary_table
from toolchain.ir.east2_to_east3_type_summary import _expr_type_name
from toolchain.ir.east2_to_east3_type_summary import _expr_type_summary
from toolchain.ir.east2_to_east3_type_summary import _is_dynamic_like_summary
from toolchain.ir.east2_to_east3_type_summary import _normalize_type_name
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
    return _is_dynamic_like_summary(_type_expr_summary_from_payload(None, type_name))


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
    _set_type_expr_summary(out, _type_expr_summary_from_node(out))
    out = _decorate_call_metadata(out, legacy_compat_bridge_enabled=_LEGACY_COMPAT_BRIDGE_ENABLED)

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
            return _lower_for_stmt(
                node,
                dispatch_mode=dispatch_mode,
                lower_node=lambda value: _lower_node(value, dispatch_mode=dispatch_mode),
            )
        if kind == "ForRange":
            return _lower_forrange_stmt(
                node,
                lower_node=lambda value: _lower_node(value, dispatch_mode=dispatch_mode),
            )
        if kind == "Assign" or kind == "AnnAssign" or kind == "AugAssign":
            return _lower_assignment_like_stmt(
                node,
                lower_node=lambda value: _lower_node(value, dispatch_mode=dispatch_mode),
            )
        if kind == "Call":
            return _lower_call_expr(node, dispatch_mode=dispatch_mode)
        if kind == "Attribute":
            return _lower_attribute_expr(node, dispatch_mode=dispatch_mode)
        if kind == "VariantPattern":
            return _lower_variant_pattern(node, dispatch_mode=dispatch_mode)
        if kind == "Match":
            return _lower_match_stmt(node, dispatch_mode=dispatch_mode)
        if kind == "ForCore":
            return _lower_forcore_stmt(
                node,
                dispatch_mode=dispatch_mode,
                lower_node=lambda value: _lower_node(value, dispatch_mode=dispatch_mode),
            )
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
