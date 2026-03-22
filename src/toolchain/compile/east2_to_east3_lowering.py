"""EAST2 -> EAST3 lowering helpers."""

from __future__ import annotations

import copy
from typing import Any

from toolchain.compile.east2_to_east3_block_scope_hoist import hoist_block_scope_variables
from toolchain.compile.east2_to_east3_default_arg_expansion import expand_default_arguments
from toolchain.compile.east2_to_east3_integer_promotion import apply_integer_promotion
from toolchain.compile.east2_to_east3_type_propagation import apply_type_propagation
from toolchain.compile.east2_to_east3_yield_lowering import lower_yield_generators
from toolchain.compile.east2_to_east3_call_metadata import _decorate_call_metadata
from toolchain.compile.east2_to_east3_dispatch_orchestration import _lower_node_dispatch
from toolchain.compile.east2_to_east3_stmt_lowering import _const_int_node
from toolchain.compile.east2_to_east3_stmt_lowering import _tuple_element_types
from toolchain.compile.east2_to_east3_type_id_predicate import _lower_type_id_call_expr
from toolchain.compile.east2_to_east3_type_summary import _collect_nominal_adt_decl_summary_table
from toolchain.compile.east2_to_east3_type_summary import _expr_type_name
from toolchain.compile.east2_to_east3_type_summary import _expr_type_summary
from toolchain.compile.east2_to_east3_type_summary import _is_dynamic_like_summary
from toolchain.compile.east2_to_east3_type_summary import _normalize_type_name
from toolchain.compile.east2_to_east3_type_summary import _set_type_expr_summary
from toolchain.compile.east2_to_east3_type_summary import _swap_nominal_adt_decl_summary_table
from toolchain.compile.east2_to_east3_type_summary import _type_expr_summary_from_node
from toolchain.compile.east2_to_east3_type_summary import _type_expr_summary_from_payload


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


def _collect_vararg_table(node: Any, out: dict[str, dict[str, Any]]) -> None:
    """Walk the AST and collect all typed vararg FunctionDef signatures into *out*.

    Key = function/method short name.
    Value = {"n_fixed": int, "elem_type": str, "vararg_name": str, "list_type": str}.
    Both top-level functions and class methods are recorded under their short name.
    """
    if isinstance(node, list):
        nl: list[Any] = node
        for item in nl:
            _collect_vararg_table(item, out)
        return
    if not isinstance(node, dict):
        return
    nd: dict[str, Any] = node
    kind = nd.get("kind")
    if kind == "FunctionDef":
        vararg_name_any = nd.get("vararg_name")
        vararg_name = vararg_name_any if isinstance(vararg_name_any, str) else ""
        vararg_type_any = nd.get("vararg_type")
        vararg_type = vararg_type_any if isinstance(vararg_type_any, str) else ""
        if vararg_name.strip() != "" and vararg_type.strip() != "":
            fn_name_any = nd.get("name")
            fn_name = fn_name_any if isinstance(fn_name_any, str) else ""
            if fn_name.strip() != "":
                arg_order_any = nd.get("arg_order")
                arg_order: list[Any] = arg_order_any if isinstance(arg_order_any, list) else []
                out[fn_name] = {
                    "n_fixed": len(arg_order),
                    "elem_type": vararg_type,
                    "vararg_name": vararg_name,
                    "list_type": "list[" + vararg_type + "]",
                }
        # recurse into body to catch nested/method FunctionDefs
        body_any = nd.get("body")
        _collect_vararg_table(body_any, out)
    elif kind == "ClassDef":
        body_any = nd.get("body")
        _collect_vararg_table(body_any, out)
    elif kind == "Module":
        for v in nd.values():
            _collect_vararg_table(v, out)


def _make_vararg_list_node(elements: list[Any], elem_type: str, list_type: str) -> dict[str, Any]:
    """Build a List AST node packing *elements* into a typed list."""
    node: dict[str, Any] = {
        "kind": "List",
        "resolved_type": list_type,
        "borrow_kind": "value",
        "casts": [],
        "elements": elements,
    }
    if elements:
        first_el: dict[str, object] = elements[0] if isinstance(elements[0], dict) else {}
        last_el: dict[str, object] = elements[-1] if isinstance(elements[-1], dict) else {}
        first_span = first_el.get("source_span") if len(first_el) > 0 else None
        last_span = last_el.get("source_span") if len(last_el) > 0 else None
        if isinstance(first_span, dict) and isinstance(last_span, dict):
            lineno = first_span.get("lineno")
            col_offset = first_span.get("col_offset")
            end_lineno = last_span.get("end_lineno")
            end_col_offset = last_span.get("end_col_offset")
            if isinstance(lineno, int) and isinstance(col_offset, int) and isinstance(end_lineno, int) and isinstance(end_col_offset, int):
                node["source_span"] = {
                    "lineno": lineno,
                    "col_offset": col_offset,
                    "end_lineno": end_lineno,
                    "end_col_offset": end_col_offset,
                }
    return node


def _desugar_vararg_funcdef(nd: dict[str, Any]) -> dict[str, Any]:
    """Transform a vararg FunctionDef in-place: remove vararg fields, add list param."""
    vararg_name_any = nd.get("vararg_name")
    vararg_name = vararg_name_any if isinstance(vararg_name_any, str) else ""
    vararg_type_any = nd.get("vararg_type")
    vararg_type = vararg_type_any if isinstance(vararg_type_any, str) else ""
    if vararg_name.strip() == "" or vararg_type.strip() == "":
        return nd
    list_type = "list[" + vararg_type + "]"
    arg_order_any = nd.get("arg_order")
    arg_order: list[Any] = arg_order_any if isinstance(arg_order_any, list) else []
    n_fixed = len(arg_order)
    arg_types_any = nd.get("arg_types")
    arg_types: dict[str, Any] = arg_types_any if isinstance(arg_types_any, dict) else {}
    nd["vararg_desugared_v1"] = {
        "n_fixed": n_fixed,
        "elem_type": vararg_type,
        "vararg_name": vararg_name,
        "list_type": list_type,
    }
    nd["arg_order"] = arg_order + [vararg_name]
    arg_types[vararg_name] = list_type
    nd["arg_types"] = arg_types
    vararg_type_expr_any = nd.get("vararg_type_expr")
    arg_type_exprs_any = nd.get("arg_type_exprs")
    if isinstance(arg_type_exprs_any, dict):
        arg_type_exprs: dict[str, Any] = arg_type_exprs_any
        if isinstance(vararg_type_expr_any, dict):
            arg_type_exprs[vararg_name] = {"kind": "GenericType", "base": "list", "args": [vararg_type_expr_any]}
        else:
            arg_type_exprs[vararg_name] = {"kind": "GenericType", "base": "list", "args": [{"kind": "NamedType", "name": vararg_type}]}
    nd.pop("vararg_name", None)
    nd.pop("vararg_type", None)
    nd.pop("vararg_type_expr", None)
    return nd


def _pack_vararg_callsite(call: dict[str, Any], vararg_table: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Pack trailing positional args of a vararg Call into a List node."""
    func_any = call.get("func")
    if not isinstance(func_any, dict):
        return call
    func: dict[str, Any] = func_any
    func_kind = func.get("kind")
    fn_key = ""
    if func_kind == "Name":
        id_any = func.get("id")
        fn_key = id_any if isinstance(id_any, str) else ""
    elif func_kind == "Attribute":
        attr_any = func.get("attr")
        fn_key = attr_any if isinstance(attr_any, str) else ""
    if fn_key.strip() == "" or fn_key not in vararg_table:
        return call
    info = vararg_table[fn_key]
    n_fixed: int = info["n_fixed"]
    elem_type: str = info["elem_type"]
    list_type: str = info["list_type"]
    args_any = call.get("args")
    args: list[Any] = args_any if isinstance(args_any, list) else []
    if len(args) <= n_fixed:
        # No trailing varargs — pass empty list
        if len(args) == n_fixed:
            packed = _make_vararg_list_node([], elem_type, list_type)
            call["args"] = args + [packed]
        return call
    fixed_args = args[:n_fixed]
    vararg_args = args[n_fixed:]
    packed = _make_vararg_list_node(vararg_args, elem_type, list_type)
    call["args"] = fixed_args + [packed]
    return call


def _apply_vararg_desugaring_walk(node: Any, vararg_table: dict[str, dict[str, Any]]) -> Any:
    """Recursively walk *node*, desugaring vararg FunctionDefs and packing Call sites."""
    if isinstance(node, list):
        nl: list[Any] = node
        return [_apply_vararg_desugaring_walk(item, vararg_table) for item in nl]
    if not isinstance(node, dict):
        return node
    nd: dict[str, Any] = node
    kind = nd.get("kind")
    if kind == "FunctionDef":
        _desugar_vararg_funcdef(nd)
        # Recurse into body after desugaring this node
        body_any = nd.get("body")
        if isinstance(body_any, list):
            nd["body"] = _apply_vararg_desugaring_walk(body_any, vararg_table)
        return nd
    if kind == "Call":
        _pack_vararg_callsite(nd, vararg_table)
        # Recurse into children
        for key in list(nd.keys()):
            if key != "kind":
                nd[key] = _apply_vararg_desugaring_walk(nd[key], vararg_table)
        return nd
    out: dict[str, Any] = {}
    for key in nd:
        out[key] = _apply_vararg_desugaring_walk(nd[key], vararg_table)
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

    # Vararg desugaring post-pass: desugar typed *args to list[T] and pack call sites.
    vararg_table: dict[str, dict[str, Any]] = {}
    _collect_vararg_table(lowered, vararg_table)
    if vararg_table:
        lowered = _apply_vararg_desugaring_walk(lowered, vararg_table)
        if not isinstance(lowered, dict):
            return east_module

    # Yield lowering: convert generator functions to list accumulation.
    lower_yield_generators(lowered)

    # Default argument expansion: fill in missing default values at call sites.
    expand_default_arguments(lowered)

    # Block-scope variable hoist: insert VarDecl nodes before blocks
    # that assign variables used in the enclosing scope.
    hoist_block_scope_variables(lowered)

    # Integer promotion: promote small int types (int8/uint8/int16/uint16)
    # to int32 in arithmetic operations and bytes iteration variables.
    apply_integer_promotion(lowered)

    # Type propagation: fill in missing resolved_type on Assign targets,
    # BinOp results, tuple unpacking elements, etc.
    apply_type_propagation(lowered)

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
