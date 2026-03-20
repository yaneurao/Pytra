"""Dispatch and attribute/match lowering helpers for EAST2 -> EAST3."""

from __future__ import annotations

from typing import Any
from typing import Callable

from toolchain.compile.east2_to_east3_nominal_adt_meta import _decorate_nominal_adt_match_stmt
from toolchain.compile.east2_to_east3_nominal_adt_meta import _decorate_nominal_adt_projection_attr
from toolchain.compile.east2_to_east3_nominal_adt_meta import _decorate_nominal_adt_variant_pattern
from toolchain.compile.east2_to_east3_stmt_lowering import _lower_assignment_like_stmt
from toolchain.compile.east2_to_east3_stmt_lowering import _lower_for_stmt
from toolchain.compile.east2_to_east3_stmt_lowering import _lower_forcore_stmt
from toolchain.compile.east2_to_east3_stmt_lowering import _lower_forrange_stmt


def _lower_attribute_expr(expr: dict[str, Any], *, lower_node: Callable[[Any], Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in expr:
        out[key] = lower_node(expr[key])
    return _decorate_nominal_adt_projection_attr(out)


def _lower_variant_pattern(pattern: dict[str, Any], *, lower_node: Callable[[Any], Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in pattern:
        out[key] = lower_node(pattern[key])
    return _decorate_nominal_adt_variant_pattern(out)


def _lower_match_stmt(stmt: dict[str, Any], *, lower_node: Callable[[Any], Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in stmt:
        out[key] = lower_node(stmt[key])
    return _decorate_nominal_adt_match_stmt(out)


def _lower_node_dispatch(
    node: dict[str, Any],
    *,
    dispatch_mode: str,
    lower_node: Callable[[Any], Any],
    lower_call_expr: Callable[[dict[str, Any]], Any],
) -> Any:
    kind = node.get("kind")
    if kind == "For":
        return _lower_for_stmt(node, dispatch_mode=dispatch_mode, lower_node=lower_node)
    if kind == "ForRange":
        return _lower_forrange_stmt(node, lower_node=lower_node)
    if kind == "Assign" or kind == "AnnAssign" or kind == "AugAssign":
        return _lower_assignment_like_stmt(node, lower_node=lower_node)
    if kind == "Call":
        return lower_call_expr(node)
    if kind == "Attribute":
        return _lower_attribute_expr(node, lower_node=lower_node)
    if kind == "VariantPattern":
        return _lower_variant_pattern(node, lower_node=lower_node)
    if kind == "Match":
        return _lower_match_stmt(node, lower_node=lower_node)
    if kind == "ForCore":
        return _lower_forcore_stmt(node, dispatch_mode=dispatch_mode, lower_node=lower_node)
    out_dict: dict[str, Any] = {}
    for key in node:
        out_dict[key] = lower_node(node[key])
    return out_dict
