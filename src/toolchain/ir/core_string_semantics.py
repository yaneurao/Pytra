#!/usr/bin/env python3
"""Self-hosted EAST string/f-string helper semantics."""

from __future__ import annotations

from typing import Any


def _sh_scan_string_token(
    text: str,
    start: int,
    quote_start: int,
    line_no: int,
    col_base: int,
    *,
    make_east_build_error: Any,
    make_span: Any,
) -> int:
    quote = text[quote_start]
    is_triple = quote_start + 2 < len(text) and text[quote_start : quote_start + 3] == quote * 3
    i = quote_start + (3 if is_triple else 1)
    while i < len(text):
        if is_triple:
            if text[i : i + 3] == quote * 3:
                return i + 3
            if text[i] == "\\" and i + 1 < len(text):
                i += 2
                continue
            i += 1
            continue
        if text[i] == "\n":
            break
        if text[i] == "\\" and i + 1 < len(text):
            i += 2
            continue
        if text[i] == quote:
            return i + 1
        i += 1
    raise make_east_build_error(
        kind="unsupported_syntax",
        message="unterminated string literal in self_hosted parser",
        source_span=make_span(line_no, col_base + start, col_base + len(text)),
        hint="Close the string literal on the same line or terminate the triple-quoted literal.",
    )


def _sh_decode_py_string_body(text: str, raw_mode: bool) -> str:
    if raw_mode:
        return text
    out: list[str] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch != "\\" or i + 1 >= len(text):
            out.append(ch)
            i += 1
            continue
        esc = text[i + 1]
        if esc == "n":
            out.append("\n")
            i += 2
            continue
        if esc == "t":
            out.append("\t")
            i += 2
            continue
        if esc == "r":
            out.append("\r")
            i += 2
            continue
        if esc == "\\":
            out.append("\\")
            i += 2
            continue
        if esc == "'":
            out.append("'")
            i += 2
            continue
        if esc == '"':
            out.append('"')
            i += 2
            continue
        if esc == "0":
            out.append("\0")
            i += 2
            continue
        if esc == "x" and i + 3 < len(text):
            try:
                out.append(chr(int(text[i + 2 : i + 4], 16)))
                i += 4
                continue
            except ValueError:
                pass
        if esc == "u" and i + 5 < len(text):
            try:
                out.append(chr(int(text[i + 2 : i + 6], 16)))
                i += 6
                continue
            except ValueError:
                pass
        out.append(esc)
        i += 2
    return "".join(out)


def _sh_append_fstring_literal(
    values: list[dict[str, Any]],
    segment: str,
    source_span: dict[str, Any],
    *,
    raw_mode: bool,
) -> None:
    if segment == "":
        return
    lit = segment.replace("{{", "{").replace("}}", "}")
    lit = _sh_decode_py_string_body(lit, raw_mode)
    if lit == "":
        return
    values.append(
        {
            "kind": "Constant",
            "source_span": dict(source_span),
            "resolved_type": "str",
            "repr": lit,
            "value": lit,
        }
    )
