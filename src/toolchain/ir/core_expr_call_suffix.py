#!/usr/bin/env python3
"""Self-hosted EAST expression parser helpers for call suffix parsing."""

from __future__ import annotations

from typing import Any


class _ShExprCallSuffixParserMixin:
    def _resolve_call_suffix_state(
        self,
        *,
        callee: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int], str]:
        """call suffix の token/state resolve を parser helper へ寄せる。"""
        args, keywords, rtok = self._resolve_call_suffix_token_state()
        return self._apply_call_suffix_token_state(
            callee=callee,
            args=args,
            keywords=keywords,
            end_tok=rtok,
        )

    def _apply_call_suffix_token_state(
        self,
        *,
        callee: dict[str, Any],
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
        end_tok: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int], str]:
        """call suffix の token-state apply を parser helper へ寄せる。"""
        source_span, repr_text = self._resolve_call_suffix_span_repr(
            callee=callee,
            end_tok=end_tok,
        )
        return self._apply_call_suffix_span_repr_state(
            args=args,
            keywords=keywords,
            source_span=source_span,
            repr_text=repr_text,
        )

    def _apply_call_suffix_span_repr_state(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
        source_span: dict[str, int],
        repr_text: str,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int], str]:
        """call suffix の span/repr apply を helper へ寄せる。"""
        return args, keywords, source_span, repr_text

    def _resolve_call_suffix_span_repr(
        self,
        *,
        callee: dict[str, Any],
        end_tok: dict[str, Any],
    ) -> tuple[dict[str, int], str]:
        """call suffix の postfix span/repr resolve を helper へ寄せる。"""
        return self._resolve_postfix_span_repr(
            owner_expr=callee,
            end_tok=end_tok,
        )

    def _resolve_call_suffix_token_state(
        self,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
        """call suffix の token-state resolve を parser helper へ寄せる。"""
        return self._consume_call_suffix_tokens()

    def _consume_call_suffix_open_token(self) -> dict[str, Any]:
        """call suffix の `(` open token consume を helper へ寄せる。"""
        return self._eat("(")

    def _consume_call_suffix_close_token(self) -> dict[str, Any]:
        """call suffix の `)` close token consume を helper へ寄せる。"""
        return self._eat(")")

    def _consume_call_suffix_arg_entries(
        self,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """call suffix の argument parse を helper へ寄せる。"""
        return self._parse_call_args()

    def _apply_call_suffix_open_token_state(
        self,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
        """call suffix の open-token state apply を helper へ寄せる。"""
        args, keywords = self._resolve_call_suffix_arg_entries_state()
        return self._apply_call_suffix_arg_entries_state(
            args=args,
            keywords=keywords,
        )

    def _resolve_call_suffix_arg_entries_state(
        self,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """call suffix の arg-entry state resolve を helper へ寄せる。"""
        return self._consume_call_suffix_arg_entries()

    def _apply_call_suffix_arg_entries_state(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
        """call suffix の arg-entry state apply を helper へ寄せる。"""
        rtok = self._resolve_call_suffix_close_token_state()
        return self._apply_call_suffix_close_token_state(
            args=args,
            keywords=keywords,
            rtok=rtok,
        )

    def _resolve_call_suffix_close_token_state(self) -> dict[str, Any]:
        """call suffix の close-token state resolve を helper へ寄せる。"""
        rtok = self._resolve_call_suffix_close_token_token_state()
        return self._apply_call_suffix_close_token_token_state(rtok=rtok)

    def _resolve_call_suffix_close_token_token_state(self) -> dict[str, Any]:
        """call suffix の close-token token-state resolve を helper へ寄せる。"""
        return self._consume_call_suffix_close_token()

    def _apply_call_suffix_close_token_token_state(
        self,
        *,
        rtok: dict[str, Any],
    ) -> dict[str, Any]:
        """call suffix の close-token token-state apply を helper へ寄せる。"""
        return self._apply_call_suffix_close_token_token_state_result(rtok=rtok)

    def _apply_call_suffix_close_token_token_state_result(
        self,
        *,
        rtok: dict[str, Any],
    ) -> dict[str, Any]:
        """call suffix の close-token token-state result return を helper へ寄せる。"""
        return rtok

    def _apply_call_suffix_close_token_state(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
        rtok: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
        """call suffix の close-token state apply を helper へ寄せる。"""
        return self._apply_call_suffix_close_token_state_result(
            args=args,
            keywords=keywords,
            rtok=rtok,
        )

    def _apply_call_suffix_close_token_state_result(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
        rtok: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
        """call suffix の close-token state result apply を helper へ寄せる。"""
        return args, keywords, rtok

    def _consume_call_suffix_tokens(
        self,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
        """call suffix の token consume を parser helper へ寄せる。"""
        self._consume_call_suffix_open_token()
        return self._apply_call_suffix_open_token_state()

    def _parse_call_suffix(self, *, callee: dict[str, Any]) -> dict[str, Any]:
        """`(` postfix 全体の token 消費と call annotation を parser helper へ寄せる。"""
        args, keywords, source_span, repr_text = self._resolve_call_suffix_state(
            callee=callee,
        )
        return self._apply_call_suffix_state(
            callee=callee,
            args=args,
            keywords=keywords,
            source_span=source_span,
            repr_text=repr_text,
        )

    def _apply_call_suffix_state(
        self,
        *,
        callee: dict[str, Any],
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
        source_span: dict[str, int],
        repr_text: str,
    ) -> dict[str, Any]:
        """call suffix の apply を parser helper へ寄せる。"""
        return self._apply_call_suffix_state_result(
            callee=callee,
            args=args,
            keywords=keywords,
            source_span=source_span,
            repr_text=repr_text,
        )

    def _apply_call_suffix_state_result(
        self,
        *,
        callee: dict[str, Any],
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
        source_span: dict[str, int],
        repr_text: str,
    ) -> dict[str, Any]:
        """call suffix の apply result を parser helper へ寄せる。"""
        return self._annotate_call_expr(
            callee=callee,
            args=args,
            keywords=keywords,
            source_span=source_span,
            repr_text=repr_text,
        )
