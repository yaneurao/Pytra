#!/usr/bin/env python3
"""Self-hosted EAST expression parser base helpers."""

from __future__ import annotations

from typing import Any

from toolchain.ir.core_builder_base import _sh_make_expr_token
from toolchain.ir.core_builder_base import _sh_span
from toolchain.ir.core_string_semantics import _sh_scan_string_token

_SH_STR_PREFIX_CHARS = {"r", "R", "b", "B", "u", "U", "f", "F"}


class _ShExprParserBaseMixin:
    def _tokenize(self, text: str) -> list[dict[str, Any]]:
        """式テキストを self-hosted 用トークン列へ変換する。"""
        out: list[dict[str, Any]] = []
        skip = 0
        text_len = len(text)
        for i, ch in enumerate(text):
            if skip > 0:
                skip -= 1
                continue
            if ch.isspace():
                continue
            pref_len = 0
            if i + 1 < text_len:
                p1 = text[i]
                if p1 in _SH_STR_PREFIX_CHARS and text[i + 1] in {"'", '"'}:
                    pref_len = 1
                elif i + 2 < text_len:
                    p2 = text[i : i + 2]
                    if all(c in _SH_STR_PREFIX_CHARS for c in p2) and text[i + 2] in {"'", '"'}:
                        pref_len = 2
            if pref_len > 0:
                end = _sh_scan_string_token(
                    text,
                    i,
                    i + pref_len,
                    self.line_no,
                    self.col_base,
                    make_east_build_error=lambda *, kind, message, source_span, hint: self._raise_expr_build_error(
                        kind=kind,
                        message=message,
                        source_span=source_span,
                        hint=hint,
                    ),
                    make_span=_sh_span,
                )
                out.append(_sh_make_expr_token("STR", text[i:end], i, end))
                skip = end - i - 1
                continue
            if ch.isdigit():
                if ch == "0" and i + 2 < text_len and text[i + 1] in {"x", "X"}:
                    j = i + 2
                    while j < text_len and (text[j].isdigit() or text[j].lower() in {"a", "b", "c", "d", "e", "f"}):
                        j += 1
                    if j > i + 2:
                        out.append(_sh_make_expr_token("INT", text[i:j], i, j))
                        skip = j - i - 1
                        continue
                j = i + 1
                while j < text_len and text[j].isdigit():
                    j += 1
                has_float = False
                if j < text_len and text[j] == ".":
                    k = j + 1
                    while k < text_len and text[k].isdigit():
                        k += 1
                    if k > j + 1:
                        j = k
                        has_float = True
                if j < text_len and text[j] in {"e", "E"}:
                    k = j + 1
                    if k < text_len and text[k] in {"+", "-"}:
                        k += 1
                    d0 = k
                    while k < text_len and text[k].isdigit():
                        k += 1
                    if k > d0:
                        j = k
                        has_float = True
                if has_float:
                    out.append(_sh_make_expr_token("FLOAT", text[i:j], i, j))
                    skip = j - i - 1
                    continue
                out.append(_sh_make_expr_token("INT", text[i:j], i, j))
                skip = j - i - 1
                continue
            if ch.isalpha() or ch == "_":
                j = i + 1
                while j < text_len and (text[j].isalnum() or text[j] == "_"):
                    j += 1
                out.append(_sh_make_expr_token("NAME", text[i:j], i, j))
                skip = j - i - 1
                continue
            if i + 2 < text_len and text[i : i + 3] in {"'''", '"""'}:
                end = _sh_scan_string_token(
                    text,
                    i,
                    i,
                    self.line_no,
                    self.col_base,
                    make_east_build_error=lambda *, kind, message, source_span, hint: self._raise_expr_build_error(
                        kind=kind,
                        message=message,
                        source_span=source_span,
                        hint=hint,
                    ),
                    make_span=_sh_span,
                )
                out.append(_sh_make_expr_token("STR", text[i:end], i, end))
                skip = end - i - 1
                continue
            if ch in {"'", '"'}:
                end = _sh_scan_string_token(
                    text,
                    i,
                    i,
                    self.line_no,
                    self.col_base,
                    make_east_build_error=lambda *, kind, message, source_span, hint: self._raise_expr_build_error(
                        kind=kind,
                        message=message,
                        source_span=source_span,
                        hint=hint,
                    ),
                    make_span=_sh_span,
                )
                out.append(_sh_make_expr_token("STR", text[i:end], i, end))
                skip = end - i - 1
                continue
            if i + 1 < text_len and text[i : i + 2] in {"<=", ">=", "==", "!=", "//", "<<", ">>", "**"}:
                out.append(_sh_make_expr_token(text[i : i + 2], text[i : i + 2], i, i + 2))
                skip = 1
                continue
            if ch in {"<", ">"}:
                out.append(_sh_make_expr_token(ch, ch, i, i + 1))
                continue
            if ch in {"+", "-", "*", "/", "%", "&", "|", "^", "(", ")", ",", ".", "[", "]", ":", "=", "{", "}"}:
                out.append(_sh_make_expr_token(ch, ch, i, i + 1))
                continue
            raise self._raise_expr_build_error(
                kind="unsupported_syntax",
                message=f"unsupported token '{ch}' in self_hosted parser",
                source_span=_sh_span(self.line_no, self.col_base + i, self.col_base + i + 1),
                hint="Extend tokenizer for this syntax.",
            )
        out.append(_sh_make_expr_token("EOF", "", len(text), len(text)))
        return out

    def _cur(self) -> dict[str, Any]:
        """現在トークンを返す。"""
        return self.tokens[self.pos]

    def _eat(self, kind: str | None = None) -> dict[str, Any]:
        """現在トークンを消費して返す。kind 指定時は一致を検証する。"""
        tok = self._cur()
        if kind is not None and tok["k"] != kind:
            raise self._raise_expr_build_error(
                kind="unsupported_syntax",
                message=f"expected token {kind}, got {tok['k']}",
                source_span=_sh_span(self.line_no, self.col_base + tok["s"], self.col_base + tok["e"]),
                hint="Fix expression syntax for self_hosted parser.",
            )
        self.pos += 1
        return tok

    def _node_span(self, s: int, e: int) -> dict[str, int]:
        """式内相対位置をファイル基準の source_span へ変換する。"""
        return _sh_span(self.line_no, self.col_base + s, self.col_base + e)

    def _src_slice(self, s: int, e: int) -> str:
        """元ソースから該当区間の repr 用文字列を取り出す。"""
        return self.src[s:e].strip()

    def parse(self) -> dict[str, Any]:
        """式を最後まで解析し、EAST 式ノードを返す。"""
        node = self._parse_ifexp()
        self._eat("EOF")
        return node
