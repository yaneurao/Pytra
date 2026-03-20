"""EAST2 -> EAST3 lowering helpers."""

from __future__ import annotations

import copy
from typing import Any

from toolchain.ir.east2_to_east3_call_metadata import _decorate_call_metadata
from toolchain.ir.east2_to_east3_dispatch_orchestration import _lower_node_dispatch
from toolchain.ir.east2_to_east3_stmt_lowering import _const_int_node
from toolchain.ir.east2_to_east3_stmt_lowering import _tuple_element_types
from toolchain.ir.east2_to_east3_type_id_predicate import _lower_type_id_call_expr
from toolchain.ir.east2_to_east3_type_summary import _collect_nominal_adt_decl_summary_table
from toolchain.ir.east2_to_east3_type_summary import _expr_type_name
from toolchain.ir.east2_to_east3_type_summary import _expr_type_summary
from toolchain.ir.east2_to_east3_type_summary import _is_dynamic_like_summary
from toolchain.ir.east2_to_east3_type_summary import _normalize_type_name
from toolchain.ir.east2_to_east3_type_summary import _set_type_expr_summary
from toolchain.ir.east2_to_east3_type_summary import _swap_nominal_adt_decl_summary_table
from toolchain.ir.east2_to_east3_type_summary import _type_expr_summary_from_node
from toolchain.ir.east2_to_east3_type_summary import _type_expr_summary_from_payload


_LEGACY_COMPAT_BRIDGE_HOLDER: list[bool] = [True]

def _normalize_dispatch_mode(value: Any) -> str:
    if isinstance(value, str):
        s: str = value
        mode = s.strip()
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
    d: dict[str, Any] = node
    kind = d.get("kind")
    value = d.get("value")
    if kind == "Constant" and isinstance(value, str):
        return value
    if kind == "Call":
        func_obj = d.get("func")
        if isinstance(func_obj, dict):
            fd: dict[str, Any] = func_obj
            if fd.get("kind") == "Name" and fd.get("id") == "str":
                args_obj = d.get("args")
                args: list[Any] = args_obj if isinstance(args_obj, list) else []
                if len(args) == 1:
                    return _const_string_value(args[0])
    return ""


def _is_none_literal(node: Any) -> bool:
    if not isinstance(node, dict):
        return False
    nd: dict[str, Any] = node
    if nd.get("kind") != "Constant":
        return False
    return nd.get("value") is None


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


def _make_tuple_starred_index_expr(tuple_expr: dict[str, Any], index: int, elem_type: str, source_expr: Any) -> dict[str, Any]:
    idx_node = _const_int_node(index)
    tuple_node = copy.deepcopy(tuple_expr)
    out: dict[str, Any] = {
        "kind": "Subscript",
        "value": tuple_node,
        "slice": idx_node,
        "resolved_type": elem_type,
        "borrow_kind": "value",
        "casts": [],
    }
    span = _node_source_span(source_expr)
    if isinstance(span, dict):
        out["source_span"] = span
    repr_base = _node_repr(tuple_expr)
    if repr_base != "":
        out["repr"] = f"{repr_base}[{index}]"
    _set_type_expr_summary(out, _type_expr_summary_from_payload(None, elem_type))
    return out


def _expand_starred_call_args(call: dict[str, Any]) -> dict[str, Any]:
    args_obj = call.get("args")
    args: list[Any] = args_obj if isinstance(args_obj, list) else []
    expanded_args: list[Any] = []
    changed = False
    for arg in args:
        if not isinstance(arg, dict):
            expanded_args.append(arg)
            continue
        ad: dict[str, Any] = arg
        if ad.get("kind") != "Starred":
            expanded_args.append(arg)
            continue
        changed = True
        value_obj = ad.get("value")
        value = value_obj if isinstance(value_obj, dict) else None
        if value is None:
            raise RuntimeError("starred_call_contract_violation: call starred unpack requires expression value")
        vd: dict[str, Any] = value
        if vd.get("kind") != "Name":
            raise RuntimeError(
                "starred_call_contract_violation: representative v1 supports only named tuple starred call receivers"
            )
        tuple_types = _tuple_element_types(_expr_type_name(vd))
        if len(tuple_types) == 0:
            raise RuntimeError(
                "starred_call_contract_violation: call starred unpack requires fixed tuple receiver TypeExpr"
            )
        has_bad_type = False
        for t in tuple_types:
            nt = _normalize_type_name(t)
            if nt == "" or nt == "unknown" or _is_any_like_type(t):
                has_bad_type = True
                break
        if has_bad_type:
            raise RuntimeError(
                "starred_call_contract_violation: call starred unpack requires non-dynamic fixed tuple receiver TypeExpr"
            )
        for idx in range(len(tuple_types)):
            expanded_args.append(_make_tuple_starred_index_expr(vd, idx, tuple_types[idx], ad))
    if changed:
        call["args"] = expanded_args
    return call


def _lower_call_expr(call: dict[str, Any], *, dispatch_mode: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in call:
        out[key] = _lower_node(call[key], dispatch_mode=dispatch_mode)
    out = _expand_starred_call_args(out)

    out = _lower_type_id_call_expr(
        out,
        dispatch_mode=dispatch_mode,
        lower_node=lambda node: _lower_node(node, dispatch_mode=dispatch_mode),
        legacy_compat_bridge_enabled=_LEGACY_COMPAT_BRIDGE_HOLDER[0],
    )
    if not isinstance(out, dict):
        return out
    if out.get("kind") != "Call":
        return out
    _set_type_expr_summary(out, _type_expr_summary_from_node(out))
    out = _decorate_call_metadata(out, legacy_compat_bridge_enabled=_LEGACY_COMPAT_BRIDGE_HOLDER[0])

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
    if not _LEGACY_COMPAT_BRIDGE_HOLDER[0]:
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


def _lower_node(node: Any, *, dispatch_mode: str) -> Any:
    if isinstance(node, list):
        out_list: list[Any] = []
        for item in node:
            out_list.append(_lower_node(item, dispatch_mode=dispatch_mode))
        return out_list
    if isinstance(node, dict):
        return _lower_node_dispatch(
            node,
            dispatch_mode=dispatch_mode,
            lower_node=lambda value: _lower_node(value, dispatch_mode=dispatch_mode),
            lower_call_expr=lambda call: _lower_call_expr(call, dispatch_mode=dispatch_mode),
        )
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
        md: dict[str, Any] = meta_obj
        dispatch_mode = _normalize_dispatch_mode(md.get("dispatch_mode"))

    prev_legacy_compat = _LEGACY_COMPAT_BRIDGE_HOLDER[0]
    prev_nominal_adt_decl_table = _swap_nominal_adt_decl_summary_table(
        _collect_nominal_adt_decl_summary_table(east_module)
    )
    _LEGACY_COMPAT_BRIDGE_HOLDER[0] = True
    if isinstance(meta_obj, dict):
        md2: dict[str, Any] = meta_obj
        legacy_obj = md2.get("legacy_compat_bridge")
        if isinstance(legacy_obj, bool):
            _LEGACY_COMPAT_BRIDGE_HOLDER[0] = legacy_obj

    try:
        lowered = _lower_node(east_module, dispatch_mode=dispatch_mode)
    finally:
        _LEGACY_COMPAT_BRIDGE_HOLDER[0] = prev_legacy_compat
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
