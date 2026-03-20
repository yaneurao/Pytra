#!/usr/bin/env python3
"""Self-hosted EAST if/elif/else tail semantics."""

from __future__ import annotations

from typing import Any


def _sh_parse_if_tail(
    *,
    start_idx: int,
    parent_indent: int,
    body_lines: list[tuple[int, str]],
    name_types: dict[str, str],
    scope_label: str,
    strip_inline_comment: Any,
    raise_if_trailing_stmt_terminator: Any,
    make_east_build_error: Any,
    make_span: Any,
    collect_indented_block: Any,
    parse_expr_lowered: Any,
    parse_stmt_block: Any,
    make_if_stmt: Any,
    block_end_span: Any,
) -> tuple[list[dict[str, Any]], int]:
    """if/elif/else 連鎖の後続ブロックを再帰的に解析する。"""
    if start_idx >= len(body_lines):
        return [], start_idx
    idx = start_idx
    while idx < len(body_lines):
        t_no, t_ln = body_lines[idx]
        t_indent = len(t_ln) - len(t_ln.lstrip(" "))
        if t_indent != parent_indent:
            return [], idx
        t_s = strip_inline_comment(t_ln.strip())
        raise_if_trailing_stmt_terminator(
            t_s,
            line_no=t_no,
            line_text=t_ln,
            make_east_build_error=make_east_build_error,
            make_span=make_span,
        )
        if t_s == "":
            idx += 1
            continue
        break
    if idx >= len(body_lines):
        return [], idx
    t_no, t_ln = body_lines[idx]
    t_indent = len(t_ln) - len(t_ln.lstrip(" "))
    t_s = strip_inline_comment(t_ln.strip())
    if t_indent != parent_indent:
        return [], idx
    if t_s == "else:":
        else_block, k2 = collect_indented_block(body_lines, idx + 1, parent_indent)
        if len(else_block) == 0:
            raise make_east_build_error(
                kind="unsupported_syntax",
                message=f"else body is missing in '{scope_label}'",
                source_span=make_span(t_no, 0, len(t_ln)),
                hint="Add indented else-body.",
            )
        return parse_stmt_block(else_block, name_types=dict(name_types), scope_label=scope_label), k2
    if t_s.startswith("elif ") and t_s.endswith(":"):
        cond_txt2 = t_s[len("elif ") : -1].strip()
        cond_col2 = t_ln.find(cond_txt2)
        cond_expr2 = parse_expr_lowered(cond_txt2, ln_no=t_no, col=cond_col2, name_types=dict(name_types))
        elif_block, k2 = collect_indented_block(body_lines, idx + 1, parent_indent)
        if len(elif_block) == 0:
            raise make_east_build_error(
                kind="unsupported_syntax",
                message=f"elif body is missing in '{scope_label}'",
                source_span=make_span(t_no, 0, len(t_ln)),
                hint="Add indented elif-body.",
            )
        nested_orelse, k3 = _sh_parse_if_tail(
            start_idx=k2,
            parent_indent=parent_indent,
            body_lines=body_lines,
            name_types=dict(name_types),
            scope_label=scope_label,
            strip_inline_comment=strip_inline_comment,
            raise_if_trailing_stmt_terminator=raise_if_trailing_stmt_terminator,
            make_east_build_error=make_east_build_error,
            make_span=make_span,
            collect_indented_block=collect_indented_block,
            parse_expr_lowered=parse_expr_lowered,
            parse_stmt_block=parse_stmt_block,
            make_if_stmt=make_if_stmt,
            block_end_span=block_end_span,
        )
        return [
            make_if_stmt(
                block_end_span(body_lines, t_no, t_ln.find("elif "), len(t_ln), k3),
                cond_expr2,
                parse_stmt_block(elif_block, name_types=dict(name_types), scope_label=scope_label),
                orelse=nested_orelse,
            )
        ], k3
    return [], idx
