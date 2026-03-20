#!/usr/bin/env python3
"""Shared EAST core statement/declaration builders."""

from __future__ import annotations

from typing import Any

from toolchain.compile.core_builder_base import _sh_make_name_expr
from toolchain.compile.core_builder_base import _sh_make_node
from toolchain.compile.core_builder_base import _sh_make_stmt_node
from toolchain.compile.core_builder_base import _sh_make_tuple_expr
from toolchain.compile.core_builder_base import _sh_span


def _sh_make_assign_stmt(
    source_span: dict[str, Any],
    target: dict[str, Any],
    value: dict[str, Any],
    *,
    declare: bool,
    declare_init: bool = False,
    decl_type: str | None = None,
) -> dict[str, Any]:
    """`Assign` 文 node を構築する。"""
    node = _sh_make_stmt_node("Assign", source_span)
    node["target"] = target
    node["value"] = value
    node["declare"] = declare
    node["decl_type"] = decl_type
    if declare_init:
        node["declare_init"] = True
    return node


def _sh_make_tuple_destructure_assign_stmt(
    source_span: dict[str, Any],
    *,
    line_no: int,
    first_name: str,
    first_col: int,
    first_type: str,
    second_name: str,
    second_col: int,
    second_type: str,
    value: dict[str, Any],
) -> dict[str, Any]:
    """2 要素 tuple destructuring の代入文 node を構築する。"""
    return _sh_make_assign_stmt(
        source_span,
        _sh_make_tuple_expr(
            _sh_span(line_no, first_col, second_col + len(second_name)),
            [
                _sh_make_name_expr(
                    _sh_span(line_no, first_col, first_col + len(first_name)),
                    first_name,
                    resolved_type=first_type,
                ),
                _sh_make_name_expr(
                    _sh_span(line_no, second_col, second_col + len(second_name)),
                    second_name,
                    resolved_type=second_type,
                ),
            ],
            resolved_type="unknown",
            repr_text=f"{first_name}, {second_name}",
        ),
        value,
        declare=False,
        decl_type=None,
    )


def _sh_make_ann_assign_stmt(
    source_span: dict[str, Any],
    target: dict[str, Any],
    annotation: str,
    *,
    annotation_type_expr: dict[str, Any] | None = None,
    value: dict[str, Any] | None = None,
    declare: bool = True,
    decl_type: str | None = None,
    decl_type_expr: dict[str, Any] | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """`AnnAssign` 文 node を構築する。"""
    node = _sh_make_stmt_node("AnnAssign", source_span)
    node["target"] = target
    node["annotation"] = annotation
    node["value"] = value
    node["declare"] = declare
    node["decl_type"] = decl_type
    if annotation_type_expr is not None:
        node["annotation_type_expr"] = annotation_type_expr
    if decl_type_expr is not None:
        node["decl_type_expr"] = decl_type_expr
    if meta is not None:
        node["meta"] = meta
    return node


def _sh_make_raise_stmt(
    source_span: dict[str, Any],
    exc: dict[str, Any],
    *,
    cause: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """`Raise` 文 node を構築する。"""
    node = _sh_make_stmt_node("Raise", source_span)
    node["exc"] = exc
    node["cause"] = cause
    return node


def _sh_make_pass_stmt(source_span: dict[str, Any]) -> dict[str, Any]:
    """`Pass` 文 node を構築する。"""
    return _sh_make_stmt_node("Pass", source_span)


def _sh_make_return_stmt(
    source_span: dict[str, Any],
    value: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """`Return` 文 node を構築する。"""
    node = _sh_make_stmt_node("Return", source_span)
    node["value"] = value
    return node


def _sh_make_yield_stmt(
    source_span: dict[str, Any],
    value: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """`Yield` 文 node を構築する。"""
    node = _sh_make_stmt_node("Yield", source_span)
    node["value"] = value
    return node


def _sh_make_augassign_stmt(
    source_span: dict[str, Any],
    target: dict[str, Any],
    op: str,
    value: dict[str, Any],
    *,
    declare: bool = False,
    decl_type: str | None = None,
) -> dict[str, Any]:
    """`AugAssign` 文 node を構築する。"""
    node = _sh_make_stmt_node("AugAssign", source_span)
    node["target"] = target
    node["op"] = op
    node["value"] = value
    node["declare"] = declare
    node["decl_type"] = decl_type
    return node


def _sh_make_swap_stmt(
    source_span: dict[str, Any],
    left: dict[str, Any],
    right: dict[str, Any],
) -> dict[str, Any]:
    """`Swap` 文 node を構築する。"""
    node = _sh_make_stmt_node("Swap", source_span)
    node["left"] = left
    node["right"] = right
    return node


def _sh_make_if_stmt(
    source_span: dict[str, Any],
    test: dict[str, Any],
    body: list[dict[str, Any]],
    *,
    orelse: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """`If` 文 node を構築する。"""
    node = _sh_make_stmt_node("If", source_span)
    node["test"] = test
    node["body"] = body
    node["orelse"] = [] if orelse is None else orelse
    return node


def _sh_make_while_stmt(
    source_span: dict[str, Any],
    test: dict[str, Any],
    body: list[dict[str, Any]],
    *,
    orelse: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """`While` 文 node を構築する。"""
    node = _sh_make_stmt_node("While", source_span)
    node["test"] = test
    node["body"] = body
    node["orelse"] = [] if orelse is None else orelse
    return node


def _sh_make_except_handler(
    type_expr: dict[str, Any],
    body: list[dict[str, Any]],
    *,
    name: str | None = None,
) -> dict[str, Any]:
    """`ExceptHandler` node を構築する。"""
    return _sh_make_node("ExceptHandler", type=type_expr, name=name, body=body)


def _sh_make_try_stmt(
    source_span: dict[str, Any],
    body: list[dict[str, Any]],
    *,
    handlers: list[dict[str, Any]] | None = None,
    orelse: list[dict[str, Any]] | None = None,
    finalbody: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """`Try` 文 node を構築する。"""
    node = _sh_make_stmt_node("Try", source_span)
    node["body"] = body
    node["handlers"] = [] if handlers is None else handlers
    node["orelse"] = [] if orelse is None else orelse
    node["finalbody"] = [] if finalbody is None else finalbody
    return node


def _sh_make_for_stmt(
    source_span: dict[str, Any],
    target: dict[str, Any],
    iter_expr: dict[str, Any],
    body: list[dict[str, Any]],
    *,
    target_type: str = "unknown",
    iter_mode: str = "static_fastpath",
    iter_source_type: str = "unknown",
    iter_element_type: str = "unknown",
    orelse: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """`For` 文 node を構築する。"""
    node = _sh_make_stmt_node("For", source_span)
    node["target"] = target
    node["target_type"] = target_type
    node["iter_mode"] = iter_mode
    node["iter_source_type"] = iter_source_type
    node["iter_element_type"] = iter_element_type
    node["iter"] = iter_expr
    node["body"] = body
    node["orelse"] = [] if orelse is None else orelse
    return node


def _sh_make_for_range_stmt(
    source_span: dict[str, Any],
    target: dict[str, Any],
    start: dict[str, Any],
    stop: dict[str, Any],
    step: dict[str, Any],
    body: list[dict[str, Any]],
    *,
    target_type: str = "int64",
    range_mode: str = "",
    orelse: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """`ForRange` 文 node を構築する。"""
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
    node = _sh_make_stmt_node("ForRange", source_span)
    node["target"] = target
    node["target_type"] = target_type
    node["start"] = start
    node["stop"] = stop
    node["step"] = step
    node["range_mode"] = mode
    node["body"] = body
    node["orelse"] = [] if orelse is None else orelse
    return node


def _sh_make_function_def_stmt(
    name: str,
    source_span: dict[str, Any],
    arg_types: dict[str, str],
    arg_order: list[str],
    return_type: str,
    body: list[dict[str, Any]],
    *,
    original_name: str = "",
    arg_type_exprs: dict[str, Any] | None = None,
    arg_defaults: dict[str, Any] | None = None,
    arg_index: dict[str, int] | None = None,
    return_type_expr: dict[str, Any] | None = None,
    arg_usage: dict[str, Any] | None = None,
    renamed_symbols: dict[str, str] | None = None,
    decorators: list[str] | None = None,
    leading_comments: list[str] | None = None,
    leading_trivia: list[dict[str, Any]] | None = None,
    docstring: str | None = None,
    meta: dict[str, Any] | None = None,
    is_generator: bool = False,
    yield_value_type: str = "unknown",
    vararg_name: str = "",
    vararg_type: str = "",
    vararg_type_expr: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """`FunctionDef` 文 node を構築する。"""
    node = _sh_make_stmt_node("FunctionDef", source_span)
    node["name"] = name
    node["original_name"] = original_name if original_name != "" else name
    node["arg_types"] = arg_types
    node["arg_order"] = arg_order
    node["arg_defaults"] = {} if arg_defaults is None else arg_defaults
    node["arg_index"] = {} if arg_index is None else arg_index
    node["return_type"] = return_type
    node["arg_usage"] = {} if arg_usage is None else arg_usage
    node["renamed_symbols"] = {} if renamed_symbols is None else renamed_symbols
    node["docstring"] = docstring
    node["body"] = body
    node["is_generator"] = 1 if is_generator else 0
    node["yield_value_type"] = yield_value_type
    if vararg_name != "":
        node["vararg_name"] = vararg_name
    if vararg_type != "":
        node["vararg_type"] = vararg_type
    if vararg_type_expr is not None:
        node["vararg_type_expr"] = vararg_type_expr
    if arg_type_exprs is not None:
        node["arg_type_exprs"] = arg_type_exprs
    if return_type_expr is not None:
        node["return_type_expr"] = return_type_expr
    if decorators is not None:
        node["decorators"] = decorators
    if leading_comments is not None:
        node["leading_comments"] = leading_comments
    if leading_trivia is not None:
        node["leading_trivia"] = leading_trivia
    if meta is not None:
        node["meta"] = meta
    return node


def _sh_make_class_def_stmt(
    name: str,
    source_span: dict[str, Any],
    field_types: dict[str, str],
    body: list[dict[str, Any]],
    *,
    original_name: str = "",
    base: str | None = None,
    dataclass: bool = False,
    dataclass_options: dict[str, Any] | None = None,
    decorators: list[str] | None = None,
    meta: dict[str, Any] | None = None,
    mixin_bases: list[str] | None = None,
) -> dict[str, Any]:
    """`ClassDef` 文 node を構築する。"""
    node = _sh_make_stmt_node("ClassDef", source_span)
    node["name"] = name
    node["original_name"] = original_name if original_name != "" else name
    node["base"] = base
    node["dataclass"] = dataclass
    node["field_types"] = field_types
    node["body"] = body
    if dataclass_options is not None:
        node["dataclass_options"] = dataclass_options
    if decorators is not None:
        node["decorators"] = decorators
    if meta is not None:
        node["meta"] = meta
    if mixin_bases is not None:
        node["mixin_bases"] = mixin_bases
    return node
