#!/usr/bin/env python3
"""Shared EAST core builder primitives."""

from __future__ import annotations

from typing import Any


def _sh_span(line: int, col: int, end_col: int, *, end_lineno: int | None = None) -> dict[str, int]:
    """self-hosted parser 用の source_span を生成する。"""
    return {"lineno": line, "col": col, "end_lineno": line if end_lineno is None else end_lineno, "end_col": end_col}


def _sh_make_kind_carrier(kind: str) -> dict[str, Any]:
    """`kind` だけを持つ薄い carrier を生成する。"""
    return {"kind": kind}


def _sh_make_node(kind: str, **fields: Any) -> dict[str, Any]:
    """`kind` 付き node の共通 envelope を構築する。"""
    node = _sh_make_kind_carrier(kind)
    node.update(fields)
    return node


def _sh_make_stmt_node(kind: str, source_span: dict[str, Any]) -> dict[str, Any]:
    """statement node の共通 envelope を構築する。"""
    return _sh_make_node(kind, source_span=source_span)


def _sh_make_trivia_blank(count: int) -> dict[str, Any]:
    """blank trivia item を生成する。"""
    return _sh_make_node("blank", count=count)


def _sh_make_trivia_comment(text: str) -> dict[str, Any]:
    """comment trivia item を生成する。"""
    return _sh_make_node("comment", text=text)


def _sh_make_expr_token(kind: str, value: str, start: int, end: int) -> dict[str, Any]:
    """self-hosted 式 parser 用の token carrier を構築する。"""
    return {
        "k": kind,
        "v": value,
        "s": start,
        "e": end,
    }


def _sh_make_expr_stmt(value: dict[str, Any], source_span: dict[str, Any]) -> dict[str, Any]:
    """`Expr` 文 node を構築する。"""
    node = _sh_make_stmt_node("Expr", source_span)
    node["value"] = value
    return node


def _sh_make_value_expr(
    kind: str,
    source_span: dict[str, Any] | None,
    *,
    resolved_type: str = "unknown",
    repr_text: str = "",
    casts: list[dict[str, Any]] | None = None,
    borrow_kind: str = "value",
) -> dict[str, Any]:
    """値を返す式 node の共通 envelope を構築する。"""
    return _sh_make_node(
        kind,
        source_span=source_span,
        resolved_type=resolved_type,
        casts=[] if casts is None else casts,
        borrow_kind=borrow_kind,
        repr=repr_text,
    )


def _sh_make_name_expr(
    source_span: dict[str, Any],
    name: str,
    resolved_type: str = "unknown",
    *,
    borrow_kind: str = "value",
    type_expr: dict[str, Any] | None = None,
    repr_text: str = "",
) -> dict[str, Any]:
    """`Name` 式 node を構築する。"""
    node = _sh_make_value_expr(
        "Name",
        source_span,
        resolved_type=resolved_type,
        repr_text=repr_text if repr_text != "" else name,
        borrow_kind=borrow_kind,
    )
    node["id"] = name
    if type_expr is not None:
        node["type_expr"] = type_expr
    return node


def _sh_make_tuple_expr(
    source_span: dict[str, Any],
    elements: list[dict[str, Any]],
    *,
    resolved_type: str = "",
    repr_text: str = "",
) -> dict[str, Any]:
    """`Tuple` 式 node を構築する。"""
    tuple_type = resolved_type
    if tuple_type == "":
        elem_types = [str(elem.get("resolved_type", "unknown")) for elem in elements]
        tuple_type = f"tuple[{', '.join(elem_types)}]" if len(elem_types) > 0 else "tuple[]"
    tuple_repr = repr_text
    if tuple_repr == "":
        tuple_repr = ", ".join(str(elem.get("repr", "")) for elem in elements)
    node = _sh_make_value_expr(
        "Tuple",
        source_span,
        resolved_type=tuple_type,
        repr_text=tuple_repr,
    )
    node["elements"] = elements
    return node
