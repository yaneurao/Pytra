#!/usr/bin/env python3
"""Self-hosted EAST expression parser helpers for attribute suffix parsing."""

from __future__ import annotations

from typing import Any


class _ShExprAttrSuffixParserMixin:
    def _parse_attr_suffix(self, *, owner_expr: dict[str, Any]) -> dict[str, Any]:
        """Attribute suffix の token 消費を parser helper へ寄せる。"""
        attr_name, source_span, repr_text = self._resolve_attr_suffix_state(
            owner_expr=owner_expr,
        )
        return self._apply_attr_suffix_state(
            owner_expr=owner_expr,
            attr_name=attr_name,
            source_span=source_span,
            repr_text=repr_text,
        )

    def _apply_attr_suffix_state(
        self,
        *,
        owner_expr: dict[str, Any],
        attr_name: str,
        source_span: dict[str, int],
        repr_text: str,
    ) -> dict[str, Any]:
        """Attribute suffix の apply を parser helper へ寄せる。"""
        return self._annotate_attr_expr(
            owner_expr=owner_expr,
            attr_name=attr_name,
            source_span=source_span,
            repr_text=repr_text,
        )

    def _consume_attr_suffix_dot_token(self) -> dict[str, Any]:
        """Attribute suffix の `.` token consume を helper へ寄せる。"""
        return self._eat(".")

    def _resolve_attr_suffix_name_token(self) -> dict[str, Any]:
        """Attribute suffix の `.` + NAME consume を helper へ寄せる。"""
        self._consume_attr_suffix_dot_token()
        return self._consume_attr_suffix_name_token()

    def _consume_attr_suffix_name_token(self) -> dict[str, Any]:
        """Attribute suffix の `NAME` token consume を helper へ寄せる。"""
        return self._eat("NAME")

    def _resolve_attr_suffix_state(
        self,
        *,
        owner_expr: dict[str, Any],
    ) -> tuple[str, dict[str, int], str]:
        """Attribute suffix の token/state resolve を helper へ寄せる。"""
        name_tok, attr_name = self._resolve_attr_suffix_name_state()
        return self._apply_attr_suffix_name_token_state(
            owner_expr=owner_expr,
            name_tok=name_tok,
            attr_name=attr_name,
        )

    def _apply_attr_suffix_name_token_state(
        self,
        *,
        owner_expr: dict[str, Any],
        name_tok: dict[str, Any],
        attr_name: str,
    ) -> tuple[str, dict[str, int], str]:
        """Attribute suffix の name token-state apply を helper へ寄せる。"""
        source_span, repr_text = self._resolve_attr_suffix_span_repr(
            owner_expr=owner_expr,
            end_tok=name_tok,
        )
        return self._apply_attr_suffix_span_repr_state(
            attr_name=attr_name,
            source_span=source_span,
            repr_text=repr_text,
        )

    def _apply_attr_suffix_span_repr_state(
        self,
        *,
        attr_name: str,
        source_span: dict[str, int],
        repr_text: str,
    ) -> tuple[str, dict[str, int], str]:
        """Attribute suffix の span/repr state apply を helper へ寄せる。"""
        return attr_name, source_span, repr_text

    def _resolve_attr_suffix_name_state(self) -> tuple[dict[str, Any], str]:
        """Attribute suffix の name token/value resolve を helper へ寄せる。"""
        name_tok = self._resolve_attr_suffix_token_state()
        return self._apply_attr_suffix_name_state(name_tok=name_tok)

    def _apply_attr_suffix_name_state(self, *, name_tok: dict[str, Any]) -> tuple[dict[str, Any], str]:
        """Attribute suffix の name token/value apply を helper へ寄せる。"""
        return name_tok, self._resolve_attr_suffix_name_value(name_tok=name_tok)

    def _resolve_attr_suffix_name_value(self, *, name_tok: dict[str, Any]) -> str:
        """Attribute suffix の attr 名 value 取得を helper へ寄せる。"""
        return str(name_tok["v"])

    def _resolve_attr_suffix_token_state(self) -> dict[str, Any]:
        """Attribute suffix の token-state resolve を helper へ寄せる。"""
        name_tok = self._resolve_attr_suffix_name_token()
        return self._apply_attr_suffix_token_state(name_tok=name_tok)

    def _apply_attr_suffix_token_state(self, *, name_tok: dict[str, Any]) -> dict[str, Any]:
        """Attribute suffix の token-state apply を helper へ寄せる。"""
        return name_tok

    def _resolve_attr_suffix_span_repr(
        self,
        *,
        owner_expr: dict[str, Any],
        end_tok: dict[str, Any],
    ) -> tuple[dict[str, int], str]:
        """Attribute suffix の postfix span/repr resolve を helper へ寄せる。"""
        return self._resolve_postfix_span_repr(
            owner_expr=owner_expr,
            end_tok=end_tok,
        )
