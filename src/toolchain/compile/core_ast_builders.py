#!/usr/bin/env python3
"""Shared EAST core AST/expression builder helpers."""

from __future__ import annotations

from typing import Any

from toolchain.compile.core_builder_base import _sh_make_name_expr
from toolchain.compile.core_builder_base import _sh_make_node
from toolchain.compile.core_builder_base import _sh_make_trivia_blank
from toolchain.compile.core_builder_base import _sh_make_value_expr
from toolchain.compile.core_builder_base import _sh_span
from toolchain.compile.core_runtime_call_semantics import _sh_annotate_runtime_call_expr


def _sh_make_constant_expr(
    source_span: dict[str, Any],
    value: Any,
    *,
    resolved_type: str = "",
    repr_text: str = "",
) -> dict[str, Any]:
    """`Constant` 式 node を構築する。"""
    constant_type = resolved_type
    if constant_type == "":
        if value is None:
            constant_type = "None"
        elif isinstance(value, bool):
            constant_type = "bool"
        elif isinstance(value, int):
            constant_type = "int64"
        elif isinstance(value, float):
            constant_type = "float64"
        else:
            constant_type = "str"
    node = _sh_make_value_expr(
        "Constant",
        source_span,
        resolved_type=constant_type,
        repr_text=repr_text if repr_text != "" else str(value),
    )
    node["value"] = value
    return node


def _sh_make_unaryop_expr(
    source_span: dict[str, Any],
    op: str,
    operand: dict[str, Any],
    *,
    resolved_type: str = "unknown",
    repr_text: str = "",
) -> dict[str, Any]:
    """`UnaryOp` 式 node を構築する。"""
    node = _sh_make_value_expr(
        "UnaryOp",
        source_span,
        resolved_type=resolved_type,
        repr_text=repr_text,
    )
    node["op"] = op
    node["operand"] = operand
    return node


def _sh_make_boolop_expr(
    source_span: dict[str, Any],
    op: str,
    values: list[dict[str, Any]],
    *,
    resolved_type: str = "bool",
    repr_text: str = "",
) -> dict[str, Any]:
    """`BoolOp` 式 node を構築する。"""
    node = _sh_make_value_expr(
        "BoolOp",
        source_span,
        resolved_type=resolved_type,
        repr_text=repr_text,
    )
    node["op"] = op
    node["values"] = values
    return node


def _sh_make_compare_expr(
    source_span: dict[str, Any],
    left: dict[str, Any],
    ops: list[str],
    comparators: list[dict[str, Any]],
    *,
    resolved_type: str = "bool",
    repr_text: str = "",
) -> dict[str, Any]:
    """`Compare` 式 node を構築する。"""
    node = _sh_make_value_expr(
        "Compare",
        source_span,
        resolved_type=resolved_type,
        repr_text=repr_text,
    )
    node["left"] = left
    node["ops"] = ops
    node["comparators"] = comparators
    return node


def _sh_make_binop_expr(
    source_span: dict[str, Any],
    left: dict[str, Any],
    op: str,
    right: dict[str, Any],
    *,
    resolved_type: str = "unknown",
    casts: list[dict[str, Any]] | None = None,
    repr_text: str = "",
) -> dict[str, Any]:
    """`BinOp` 式 node を構築する。"""
    node = _sh_make_value_expr(
        "BinOp",
        source_span,
        resolved_type=resolved_type,
        repr_text=repr_text,
        casts=casts,
    )
    node["left"] = left
    node["op"] = op
    node["right"] = right
    return node


def _sh_make_cast_entry(on: str, from_type: str, to_type: str, reason: str) -> dict[str, Any]:
    """`casts` metadata item を構築する。"""
    return {
        "on": on,
        "from": from_type,
        "to": to_type,
        "reason": reason,
    }


def _sh_make_ifexp_expr(
    source_span: dict[str, Any],
    test: dict[str, Any],
    body: dict[str, Any],
    orelse: dict[str, Any],
    *,
    resolved_type: str = "",
    repr_text: str = "",
) -> dict[str, Any]:
    """`IfExp` 式 node を構築する。"""
    out_type = resolved_type
    if out_type == "":
        body_type = str(body.get("resolved_type", "unknown"))
        orelse_type = str(orelse.get("resolved_type", "unknown"))
        out_type = body_type if body_type == orelse_type else "unknown"
    node = _sh_make_value_expr(
        "IfExp",
        source_span,
        resolved_type=out_type,
        repr_text=repr_text,
    )
    node["test"] = test
    node["body"] = body
    node["orelse"] = orelse
    return node


def _sh_make_attribute_expr(
    source_span: dict[str, Any],
    value: dict[str, Any],
    attr: str,
    *,
    resolved_type: str = "unknown",
    repr_text: str = "",
) -> dict[str, Any]:
    """`Attribute` 式 node を構築する。"""
    node = _sh_make_value_expr(
        "Attribute",
        source_span,
        resolved_type=resolved_type,
        repr_text=repr_text,
    )
    node["value"] = value
    node["attr"] = attr
    return node


def _sh_make_call_expr(
    source_span: dict[str, Any],
    func: dict[str, Any],
    args: list[dict[str, Any]],
    keywords: list[dict[str, Any]],
    *,
    resolved_type: str = "unknown",
    repr_text: str = "",
) -> dict[str, Any]:
    """`Call` 式 node を構築する。"""
    node = _sh_make_value_expr(
        "Call",
        source_span,
        resolved_type=resolved_type,
        repr_text=repr_text,
    )
    node["func"] = func
    node["args"] = args
    node["keywords"] = keywords
    return node


def _sh_make_starred_expr(
    source_span: dict[str, Any],
    value: dict[str, Any],
    *,
    resolved_type: str = "",
    repr_text: str = "",
) -> dict[str, Any]:
    """`Starred` 式 node を構築する。"""
    value_type = resolved_type if resolved_type != "" else str(value.get("resolved_type", "unknown"))
    node = _sh_make_value_expr(
        "Starred",
        source_span,
        resolved_type=value_type,
        repr_text=repr_text,
    )
    node["value"] = value
    return node


def _sh_make_keyword_arg(arg: str, value: dict[str, Any]) -> dict[str, Any]:
    """Call.keyword carrier を構築する。"""
    return {
        "arg": arg,
        "value": value,
    }


def _sh_make_slice_node(
    lower: dict[str, Any] | None,
    upper: dict[str, Any] | None,
    step: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """`Slice` node を構築する。"""
    return _sh_make_node("Slice", lower=lower, upper=upper, step=step)


def _sh_make_subscript_expr(
    source_span: dict[str, Any],
    value: dict[str, Any],
    slice_node: dict[str, Any],
    *,
    resolved_type: str = "unknown",
    repr_text: str = "",
    lowered_kind: str = "",
    lower: dict[str, Any] | None = None,
    upper: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """`Subscript` 式 node を構築する。"""
    node = _sh_make_value_expr(
        "Subscript",
        source_span,
        resolved_type=resolved_type,
        repr_text=repr_text,
    )
    node["value"] = value
    node["slice"] = slice_node
    if lowered_kind != "":
        node["lowered_kind"] = lowered_kind
    if lower is not None or lowered_kind == "SliceExpr":
        node["lower"] = lower
    if upper is not None or lowered_kind == "SliceExpr":
        node["upper"] = upper
    return node


def _sh_make_comp_generator(
    target: dict[str, Any],
    iter_expr: dict[str, Any],
    ifs: list[dict[str, Any]],
    *,
    is_async: bool = False,
) -> dict[str, Any]:
    """comprehension generator item を構築する。"""
    return {
        "target": target,
        "iter": iter_expr,
        "ifs": ifs,
        "is_async": is_async,
    }


def _sh_make_list_expr(
    source_span: dict[str, Any],
    elements: list[dict[str, Any]],
    *,
    resolved_type: str = "",
    repr_text: str = "",
) -> dict[str, Any]:
    """`List` 式 node を構築する。"""
    list_type = resolved_type
    if list_type == "":
        elem_type = "unknown"
        if len(elements) > 0:
            elem_type = str(elements[0].get("resolved_type", "unknown"))
            for elem in elements[1:]:
                if str(elem.get("resolved_type", "unknown")) != elem_type:
                    elem_type = "unknown"
                    break
        list_type = f"list[{elem_type}]"
    node = _sh_make_value_expr(
        "List",
        source_span,
        resolved_type=list_type,
        repr_text=repr_text,
    )
    node["elements"] = elements
    return node


def _sh_make_set_expr(
    source_span: dict[str, Any],
    elements: list[dict[str, Any]],
    *,
    resolved_type: str = "",
    repr_text: str = "",
) -> dict[str, Any]:
    """`Set` 式 node を構築する。"""
    set_type = resolved_type
    if set_type == "":
        elem_type = str(elements[0].get("resolved_type", "unknown")) if len(elements) > 0 else "unknown"
        set_type = f"set[{elem_type}]"
    node = _sh_make_value_expr(
        "Set",
        source_span,
        resolved_type=set_type,
        repr_text=repr_text,
    )
    node["elements"] = elements
    return node


def _sh_make_dict_entry(key: dict[str, Any], value: dict[str, Any]) -> dict[str, Any]:
    """`Dict` entry carrier を構築する。"""
    return {"key": key, "value": value}


def _sh_make_dict_expr(
    source_span: dict[str, Any],
    *,
    keys: list[dict[str, Any]] | None = None,
    values: list[dict[str, Any]] | None = None,
    entries: list[dict[str, Any]] | None = None,
    resolved_type: str = "",
    repr_text: str = "",
) -> dict[str, Any]:
    """`Dict` 式 node を構築する。"""
    dict_type = resolved_type
    if entries is not None:
        entry_nodes = entries
        if dict_type == "":
            key_type = "unknown"
            value_type = "unknown"
            if len(entry_nodes) > 0:
                first_key = entry_nodes[0].get("key", {})
                first_value = entry_nodes[0].get("value", {})
                key_type = str(first_key.get("resolved_type", "unknown"))
                value_type = str(first_value.get("resolved_type", "unknown"))
            dict_type = f"dict[{key_type},{value_type}]"
        node = _sh_make_value_expr(
            "Dict",
            source_span,
            resolved_type=dict_type,
            repr_text=repr_text,
        )
        node["entries"] = entry_nodes
        return node

    key_nodes = keys if keys is not None else []
    value_nodes = values if values is not None else []
    if dict_type == "":
        key_type = "unknown"
        value_type = "unknown"
        if len(key_nodes) > 0 and len(value_nodes) > 0:
            key_type = str(key_nodes[0].get("resolved_type", "unknown"))
            value_type = str(value_nodes[0].get("resolved_type", "unknown"))
        dict_type = f"dict[{key_type},{value_type}]"
    node = _sh_make_value_expr(
        "Dict",
        source_span,
        resolved_type=dict_type,
        repr_text=repr_text,
    )
    node["keys"] = key_nodes
    node["values"] = value_nodes
    return node


def _sh_make_list_comp_expr(
    source_span: dict[str, Any],
    elt: dict[str, Any],
    generators: list[dict[str, Any]],
    *,
    resolved_type: str = "",
    repr_text: str = "",
    lowered_kind: str | None = None,
) -> dict[str, Any]:
    """`ListComp` 式 node を構築する。"""
    list_type = resolved_type if resolved_type != "" else f"list[{str(elt.get('resolved_type', 'unknown'))}]"
    node = _sh_make_value_expr(
        "ListComp",
        source_span,
        resolved_type=list_type,
        repr_text=repr_text,
    )
    node["elt"] = elt
    node["generators"] = generators
    if lowered_kind is not None:
        node["lowered_kind"] = lowered_kind
    return node


def _sh_make_simple_name_list_comp_expr(
    source_span: dict[str, Any],
    *,
    line_no: int,
    base_col: int,
    elt_name: str,
    target_name: str,
    iter_expr: dict[str, Any],
    elem_type: str,
    repr_text: str = "",
) -> dict[str, Any]:
    """単純な `[x for x in items]` を helper 1 個で構築する。"""
    elt_node = _sh_make_name_expr(
        _sh_span(line_no, base_col, base_col + len(elt_name)),
        elt_name,
        resolved_type=elem_type if elt_name == target_name else "unknown",
    )
    return _sh_make_list_comp_expr(
        source_span,
        elt_node,
        [_sh_make_simple_name_comp_generator(line_no, base_col, target_name, iter_expr)],
        resolved_type=f"list[{elem_type}]",
        repr_text=repr_text,
        lowered_kind="ListCompSimple",
    )


def _sh_make_simple_name_comp_generator(
    line_no: int,
    base_col: int,
    target_name: str,
    iter_expr: dict[str, Any],
) -> dict[str, Any]:
    """simple list-comp 用の target `Name` + generator を構築する。"""
    return _sh_make_comp_generator(
        _sh_make_name_expr(
            _sh_span(line_no, base_col, base_col + len(target_name)),
            target_name,
            resolved_type="unknown",
        ),
        iter_expr,
        [],
    )


def _sh_make_builtin_listcomp_call_expr(
    source_span: dict[str, Any],
    *,
    line_no: int,
    base_col: int,
    func_name: str,
    arg: dict[str, Any],
    repr_text: str = "",
    runtime_call: str = "",
    semantic_tag: str | None = None,
) -> dict[str, Any]:
    """`any/all(<list-comp>)` の lowered builtin call を構築する。"""
    payload = _sh_make_call_expr(
        source_span,
        _sh_make_name_expr(
            _sh_span(line_no, base_col, base_col + len(func_name)),
            func_name,
            repr_text=func_name,
        ),
        [arg],
        [],
        resolved_type="bool",
        repr_text=repr_text,
    )
    return _sh_annotate_runtime_call_expr(
        payload,
        lowered_kind="BuiltinCall",
        builtin_name=func_name,
        runtime_call=runtime_call,
        semantic_tag=semantic_tag,
    )


def _sh_make_dict_comp_expr(
    source_span: dict[str, Any],
    key: dict[str, Any],
    value: dict[str, Any],
    generators: list[dict[str, Any]],
    *,
    resolved_type: str = "",
    repr_text: str = "",
) -> dict[str, Any]:
    """`DictComp` 式 node を構築する。"""
    dict_type = resolved_type
    if dict_type == "":
        dict_type = f"dict[{key.get('resolved_type', 'unknown')},{value.get('resolved_type', 'unknown')}]"
    node = _sh_make_value_expr(
        "DictComp",
        source_span,
        resolved_type=dict_type,
        repr_text=repr_text,
    )
    node["key"] = key
    node["value"] = value
    node["generators"] = generators
    return node


def _sh_make_set_comp_expr(
    source_span: dict[str, Any],
    elt: dict[str, Any],
    generators: list[dict[str, Any]],
    *,
    resolved_type: str = "",
    repr_text: str = "",
) -> dict[str, Any]:
    """`SetComp` 式 node を構築する。"""
    set_type = resolved_type if resolved_type != "" else f"set[{str(elt.get('resolved_type', 'unknown'))}]"
    node = _sh_make_value_expr(
        "SetComp",
        source_span,
        resolved_type=set_type,
        repr_text=repr_text,
    )
    node["elt"] = elt
    node["generators"] = generators
    return node


def _sh_make_range_expr(
    source_span: dict[str, Any] | None,
    start: dict[str, Any],
    stop: dict[str, Any],
    step: dict[str, Any],
    *,
    repr_text: str = "",
    range_mode: str = "",
) -> dict[str, Any]:
    """`RangeExpr` node を構築する。"""
    mode = range_mode
    if mode == "":
        step_const_obj: Any = None
        if isinstance(step, dict):
            step_const_obj = step.get("value")
        if step_const_obj == 1:
            mode = "ascending"
        elif step_const_obj == -1:
            mode = "descending"
        else:
            mode = "dynamic"
    node = _sh_make_value_expr(
        "RangeExpr",
        source_span,
        resolved_type="range",
        repr_text=repr_text if repr_text != "" else "range(...)",
    )
    node["start"] = start
    node["stop"] = stop
    node["step"] = step
    node["range_mode"] = mode
    return node


def _sh_make_arg_node(
    arg: str,
    *,
    annotation: str | None = None,
    resolved_type: str = "unknown",
    default: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """`arg` node を構築する。"""
    node = _sh_make_node(
        "arg",
        arg=arg,
        annotation=annotation,
        resolved_type=resolved_type,
    )
    if default is not None:
        node["default"] = default
    return node


def _sh_make_lambda_arg_entry(
    name: str,
    default: dict[str, Any] | None,
    resolved_type: str,
) -> dict[str, Any]:
    """lambda parameter の補助 carrier を構築する。"""
    return {
        "name": name,
        "default": default,
        "resolved_type": resolved_type,
    }


def _sh_make_lambda_expr(
    source_span: dict[str, Any],
    args: list[dict[str, Any]],
    body: dict[str, Any],
    *,
    return_type: str = "unknown",
    resolved_type: str = "",
    repr_text: str = "",
) -> dict[str, Any]:
    """`Lambda` 式 node を構築する。"""
    callable_type = resolved_type
    if callable_type == "":
        param_types: list[str] = []
        for arg in args:
            arg_type = str(arg.get("resolved_type", "unknown"))
            param_types.append(arg_type if arg_type != "" else "unknown")
        callable_type = f"callable[{','.join(param_types)}->{return_type}]"
    node = _sh_make_value_expr(
        "Lambda",
        source_span,
        resolved_type=callable_type,
        repr_text=repr_text,
    )
    node["args"] = args
    node["body"] = body
    node["return_type"] = return_type
    return node


def _sh_make_formatted_value_node(
    value: dict[str, Any],
    *,
    conversion: str = "",
    format_spec: str = "",
) -> dict[str, Any]:
    """`FormattedValue` node を構築する。"""
    node = _sh_make_node("FormattedValue", value=value)
    if conversion != "":
        node["conversion"] = conversion
    if format_spec != "":
        node["format_spec"] = format_spec
    return node


def _sh_make_joined_str_expr(
    source_span: dict[str, Any],
    values: list[dict[str, Any]],
    *,
    repr_text: str = "",
) -> dict[str, Any]:
    """`JoinedStr` 式 node を構築する。"""
    node = _sh_make_value_expr(
        "JoinedStr",
        source_span,
        resolved_type="str",
        repr_text=repr_text,
    )
    node["values"] = values
    return node


def _sh_make_def_sig_info(
    name: str,
    return_type: str,
    arg_types: dict[str, str],
    arg_type_exprs: dict[str, dict[str, Any]],
    return_type_expr: dict[str, Any],
    arg_order: list[str],
    arg_defaults: dict[str, str],
    *,
    vararg_name: str = "",
    vararg_type: str = "",
    vararg_type_expr: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """`_sh_parse_def_sig()` の戻り carrier を構築する。"""
    out = {
        "name": name,
        "ret": return_type,
        "arg_types": arg_types,
        "arg_type_exprs": arg_type_exprs,
        "return_type_expr": return_type_expr,
        "arg_order": arg_order,
        "arg_defaults": arg_defaults,
    }
    if vararg_name != "":
        out["vararg_name"] = vararg_name
    if vararg_type != "":
        out["vararg_type"] = vararg_type
    if vararg_type_expr is not None:
        out["vararg_type_expr"] = vararg_type_expr
    return out


def _sh_block_end_span(
    body_lines: list[tuple[int, str]],
    start_ln: int,
    start_col: int,
    fallback_end_col: int,
    end_idx_exclusive: int,
) -> dict[str, int]:
    """複数行文の終端まで含む source_span を生成する。"""
    if end_idx_exclusive > 0 and end_idx_exclusive - 1 < len(body_lines):
        end_ln, end_txt = body_lines[end_idx_exclusive - 1]
        return _sh_span(start_ln, start_col, len(end_txt), end_lineno=end_ln)
    return _sh_span(start_ln, start_col, fallback_end_col)


def _sh_stmt_span(
    merged_line_end: dict[int, tuple[int, int]],
    start_ln: int,
    start_col: int,
    fallback_end_col: int,
) -> dict[str, int]:
    """単文の source_span を論理行終端まで含めて生成する。"""
    end_pair: tuple[int, int] = merged_line_end.get(start_ln, (start_ln, fallback_end_col))
    end_ln: int = int(end_pair[0])
    end_col: int = int(end_pair[1])
    return _sh_span(start_ln, start_col, end_col, end_lineno=end_ln)


def _sh_push_stmt_with_trivia(
    stmts: list[dict[str, Any]],
    pending_leading_trivia: list[dict[str, Any]],
    pending_blank_count: int,
    stmt: dict[str, Any],
) -> int:
    """保留中 trivia を付与して文リストへ追加し、更新後 blank 数を返す。"""
    stmt_copy: dict[str, Any] = dict(stmt)
    if pending_blank_count > 0:
        pending_leading_trivia.append(_sh_make_trivia_blank(pending_blank_count))
        pending_blank_count = 0
    if len(pending_leading_trivia) > 0:
        stmt_copy["leading_trivia"] = list(pending_leading_trivia)
        comments = [x.get("text") for x in pending_leading_trivia if x.get("kind") == "comment" and isinstance(x.get("text"), str)]
        if len(comments) > 0:
            stmt_copy["leading_comments"] = comments
        pending_leading_trivia.clear()
    stmts.append(stmt_copy)
    return pending_blank_count
