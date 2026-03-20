#!/usr/bin/env python3
"""Self-hosted EAST expression parser helpers for postfix suffix dispatch."""

from __future__ import annotations

from typing import Any

from toolchain.compile.core_expr_attr_suffix import _ShExprAttrSuffixParserMixin
from toolchain.compile.core_expr_subscript_suffix import _ShExprSubscriptSuffixParserMixin


class _ShExprPostfixSuffixParserMixin:
    def _resolve_postfix_span_repr(
        self,
        *,
        owner_expr: dict[str, Any],
        end_tok: dict[str, Any],
    ) -> tuple[dict[str, int], str]:
        """postfix suffix 共通の source_span / repr 計算を helper へ寄せる。"""
        s = int(owner_expr["source_span"]["col"]) - self.col_base
        e = end_tok["e"]
        return self._node_span(s, e), self._src_slice(s, e)

    def _parse_postfix_suffix(self, *, owner_expr: dict[str, Any]) -> dict[str, Any] | None:
        """postfix suffix dispatch を parser helper へ寄せる。"""
        tok_kind = str(self._cur()["k"])
        return self._apply_postfix_suffix_kind(
            owner_expr=owner_expr,
            tok_kind=tok_kind,
        )

    def _apply_postfix_suffix_kind(
        self,
        *,
        owner_expr: dict[str, Any],
        tok_kind: str,
    ) -> dict[str, Any] | None:
        """postfix suffix kind dispatch を parser helper へ寄せる。"""
        if tok_kind == ".":
            return self._parse_attr_suffix(owner_expr=owner_expr)
        if tok_kind == "(":
            return self._parse_call_suffix(callee=owner_expr)
        if tok_kind == "[":
            return self._parse_subscript_suffix(owner_expr=owner_expr)
        return None


class _ShExprAttrSubscriptSuffixParserMixin(
    _ShExprAttrSuffixParserMixin,
    _ShExprSubscriptSuffixParserMixin,
    _ShExprPostfixSuffixParserMixin,
):
    """Backward-compatible facade for callers still importing the combined mixin."""

    pass
