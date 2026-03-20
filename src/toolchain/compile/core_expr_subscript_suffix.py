#!/usr/bin/env python3
"""Self-hosted EAST expression parser helpers for subscript/slice suffix parsing."""

from __future__ import annotations

from typing import Any


class _ShExprSubscriptSuffixParserMixin:
    def _parse_subscript_slice_tail(
        self,
        *,
        lower: dict[str, Any] | None,
    ) -> tuple[
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any],
    ]:
        """Subscript slice tail の `:` 以降 parse を helper へ寄せる。"""
        upper, rtok = self._resolve_subscript_slice_tail_state()
        return self._apply_subscript_slice_tail_parse_state(lower=lower, upper=upper, rtok=rtok)

    def _apply_subscript_slice_tail_parse_state(
        self,
        *,
        lower: dict[str, Any] | None,
        upper: dict[str, Any] | None,
        rtok: dict[str, Any],
    ) -> tuple[
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any],
    ]:
        """Subscript slice tail の parse-state apply を helper へ寄せる。"""
        return None, lower, upper, rtok

    def _resolve_subscript_slice_tail_state(
        self,
    ) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        """Subscript slice tail の token/state resolve を helper へ寄せる。"""
        upper, rtok = self._resolve_subscript_slice_tail_token_state()
        return self._apply_subscript_slice_tail_state(upper=upper, rtok=rtok)

    def _resolve_subscript_slice_tail_token_state(
        self,
    ) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        """Subscript slice tail の token-state resolve を helper へ寄せる。"""
        return self._consume_subscript_slice_tail_tokens()

    def _apply_subscript_slice_tail_state(
        self,
        *,
        upper: dict[str, Any] | None,
        rtok: dict[str, Any],
    ) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        """Subscript slice tail の state apply を helper へ寄せる。"""
        return self._apply_subscript_slice_tail_state_result(upper=upper, rtok=rtok)

    def _apply_subscript_slice_tail_state_result(
        self,
        *,
        upper: dict[str, Any] | None,
        rtok: dict[str, Any],
    ) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        """Subscript slice tail の state-result apply を helper へ寄せる。"""
        return upper, rtok

    def _resolve_subscript_slice_upper_expr_state(self) -> bool:
        """Subscript slice tail の upper expr state resolve を helper へ寄せる。"""
        return self._resolve_subscript_slice_upper_expr_kind()

    def _resolve_subscript_slice_upper_expr_kind(self) -> bool:
        """Subscript slice tail の upper expr kind resolve を helper へ寄せる。"""
        return self._cur()["k"] == "]"

    def _parse_subscript_slice_upper_expr(self) -> dict[str, Any] | None:
        """Subscript slice tail の upper expr parse を helper へ寄せる。"""
        is_empty = self._resolve_subscript_slice_upper_expr_state()
        return self._apply_subscript_slice_upper_expr_state(is_empty=is_empty)

    def _apply_subscript_slice_upper_expr_state(
        self,
        *,
        is_empty: bool,
    ) -> dict[str, Any] | None:
        """Subscript slice tail の upper expr apply を helper へ寄せる。"""
        if is_empty:
            return None
        return self._parse_ifexp()

    def _consume_subscript_slice_tail_colon_token(self) -> dict[str, Any]:
        """Subscript slice tail の `:` token consume を helper へ寄せる。"""
        return self._eat(":")

    def _resolve_subscript_slice_tail_colon_token_state(self) -> dict[str, Any]:
        """Subscript slice tail の colon-token state resolve を helper へ寄せる。"""
        return self._consume_subscript_slice_tail_colon_token()

    def _consume_subscript_slice_tail_close_token(self) -> dict[str, Any]:
        """Subscript slice tail の `]` token consume を helper へ寄せる。"""
        return self._eat("]")

    def _consume_subscript_slice_tail_tokens(
        self,
    ) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        """Subscript slice tail の token consume を helper へ寄せる。"""
        ctok = self._resolve_subscript_slice_tail_colon_token_state()
        return self._apply_subscript_slice_tail_colon_token_state(ctok=ctok)

    def _apply_subscript_slice_tail_colon_token_state(
        self,
        *,
        ctok: dict[str, Any],
    ) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        """Subscript slice tail の colon-token state apply を helper へ寄せる。"""
        _ = ctok
        return self._apply_subscript_slice_tail_colon_state()

    def _apply_subscript_slice_tail_colon_state(
        self,
    ) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        """Subscript slice tail の colon-state apply を helper へ寄せる。"""
        upper = self._resolve_subscript_slice_tail_colon_state()
        return self._apply_subscript_slice_tail_upper_state(upper=upper)

    def _resolve_subscript_slice_tail_colon_state(self) -> dict[str, Any] | None:
        """Subscript slice tail の colon-state resolve を helper へ寄せる。"""
        upper = self._resolve_subscript_slice_tail_upper_state()
        return self._apply_subscript_slice_tail_colon_state_result(upper=upper)

    def _apply_subscript_slice_tail_colon_state_result(
        self,
        *,
        upper: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        """Subscript slice tail の colon-state result apply を helper へ寄せる。"""
        return upper

    def _resolve_subscript_slice_tail_upper_state(self) -> dict[str, Any] | None:
        """Subscript slice tail の upper-state resolve を helper へ寄せる。"""
        upper = self._parse_subscript_slice_upper_expr()
        return self._apply_subscript_slice_tail_upper_state_result(upper=upper)

    def _apply_subscript_slice_tail_upper_state_result(
        self,
        *,
        upper: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        """Subscript slice tail の upper-state result apply を helper へ寄せる。"""
        return upper

    def _apply_subscript_slice_tail_upper_state(
        self,
        *,
        upper: dict[str, Any] | None,
    ) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        """Subscript slice tail の upper-state apply を helper へ寄せる。"""
        rtok = self._resolve_subscript_slice_tail_close_state()
        return self._apply_subscript_slice_tail_close_state(upper=upper, rtok=rtok)

    def _apply_subscript_slice_tail_close_state(
        self,
        *,
        upper: dict[str, Any] | None,
        rtok: dict[str, Any],
    ) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        """Subscript slice tail の close-state apply を helper へ寄せる。"""
        return self._apply_subscript_slice_tail_close_state_result(upper=upper, rtok=rtok)

    def _apply_subscript_slice_tail_close_state_result(
        self,
        *,
        upper: dict[str, Any] | None,
        rtok: dict[str, Any],
    ) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        """Subscript slice tail の close-state result apply を helper へ寄せる。"""
        return upper, rtok

    def _resolve_subscript_slice_tail_close_state(self) -> dict[str, Any]:
        """Subscript slice tail の close-token state resolve を helper へ寄せる。"""
        rtok = self._resolve_subscript_slice_tail_close_token_state()
        return self._apply_subscript_slice_tail_close_token_state(rtok=rtok)

    def _resolve_subscript_slice_tail_close_token_state(self) -> dict[str, Any]:
        """Subscript slice tail の close-token token-state resolve を helper へ寄せる。"""
        return self._consume_subscript_slice_tail_close_token()

    def _apply_subscript_slice_tail_close_token_state(
        self,
        *,
        rtok: dict[str, Any],
    ) -> dict[str, Any]:
        """Subscript slice tail の close-token token-state apply を helper へ寄せる。"""
        return self._apply_subscript_slice_tail_close_token_state_result(rtok=rtok)

    def _apply_subscript_slice_tail_close_token_state_result(
        self,
        *,
        rtok: dict[str, Any],
    ) -> dict[str, Any]:
        """Subscript slice tail の close-token token-state result apply を helper へ寄せる。"""
        return rtok

    def _parse_subscript_suffix_components(
        self,
    ) -> tuple[
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any],
    ]:
        """Subscript / slice suffix の component parse を helper へ寄せる。"""
        starts_with_slice = self._resolve_subscript_suffix_component_state()
        return self._apply_subscript_suffix_component_state(
            starts_with_slice=starts_with_slice,
        )

    def _resolve_subscript_suffix_component_state(self) -> bool:
        """Subscript suffix の component 先頭 state resolve を helper へ寄せる。"""
        return self._cur()["k"] == ":"

    def _apply_subscript_suffix_component_state(
        self,
        *,
        starts_with_slice: bool,
    ) -> tuple[
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any],
    ]:
        """Subscript suffix の component apply を helper へ寄せる。"""
        if starts_with_slice:
            return self._parse_subscript_slice_tail(lower=None)
        return self._parse_subscript_suffix_first_component()

    def _parse_subscript_suffix_first_component(
        self,
    ) -> tuple[
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any],
    ]:
        """Subscript suffix の first expr 側 parse を helper へ寄せる。"""
        first, is_slice = self._resolve_subscript_suffix_first_component_state()
        return self._apply_subscript_suffix_first_component_state(
            first=first,
            is_slice=is_slice,
        )

    def _resolve_subscript_suffix_first_component_state(
        self,
    ) -> tuple[dict[str, Any], bool]:
        """Subscript suffix の first expr 側 state resolve を helper へ寄せる。"""
        first = self._parse_ifexp()
        return self._apply_subscript_suffix_first_component_kind_state(first=first)

    def _apply_subscript_suffix_first_component_kind_state(
        self,
        *,
        first: dict[str, Any],
    ) -> tuple[dict[str, Any], bool]:
        """Subscript suffix の first expr 側 kind apply を helper へ寄せる。"""
        return first, self._resolve_subscript_suffix_first_component_kind()

    def _resolve_subscript_suffix_first_component_kind(self) -> bool:
        """Subscript suffix の first expr 側 kind resolve を helper へ寄せる。"""
        return self._cur()["k"] == ":"

    def _apply_subscript_suffix_first_component_state(
        self,
        *,
        first: dict[str, Any],
        is_slice: bool,
    ) -> tuple[
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any],
    ]:
        """Subscript suffix の first expr 側 apply を helper へ寄せる。"""
        if is_slice:
            return self._apply_subscript_slice_first_component(first=first)
        return self._apply_subscript_index_first_component(first=first)

    def _apply_subscript_slice_first_component(
        self,
        *,
        first: dict[str, Any],
    ) -> tuple[
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any],
    ]:
        """Subscript suffix の first expr 側 slice apply を helper へ寄せる。"""
        return self._parse_subscript_slice_tail(lower=first)

    def _apply_subscript_index_first_component(
        self,
        *,
        first: dict[str, Any],
    ) -> tuple[
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any],
    ]:
        """Subscript suffix の first expr 側 index apply を helper へ寄せる。"""
        return self._parse_subscript_index_tail(index_expr=first)

    def _parse_subscript_index_tail(
        self,
        *,
        index_expr: dict[str, Any],
    ) -> tuple[
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any],
    ]:
        """Subscript index tail の `]` close を helper へ寄せる。
        `,` が来た場合は残りの型引数を Tuple として束ねる。"""
        # generic type subscript: dict[str, Any] → Tuple(str, Any) as index
        tok = self._cur()
        tok_kind = tok.get("k", "") if isinstance(tok, dict) else ""
        if tok_kind == ",":
            elements: list[dict[str, Any]] = [index_expr]
            while tok_kind == ",":
                self._eat(",")
                next_expr = self._parse_ifexp()
                elements.append(next_expr)
                tok = self._cur()
                tok_kind = tok.get("k", "") if isinstance(tok, dict) else ""
            rtok = self._eat("]")
            tuple_node: dict[str, Any] = {
                "kind": "Tuple",
                "elements": elements,
                "resolved_type": "unknown",
                "borrow_kind": "value",
                "casts": [],
            }
            return tuple_node, None, None, rtok
        rtok = self._eat("]")
        return index_expr, None, None, rtok

    def _resolve_subscript_index_tail_state(self) -> dict[str, Any]:
        """Subscript index tail の close-token state resolve を helper へ寄せる。"""
        return self._consume_subscript_index_tail_close_token()

    def _consume_subscript_index_tail_close_token(self) -> dict[str, Any]:
        """Subscript index tail の `]` close token consume を helper へ寄せる。"""
        return self._eat("]")

    def _resolve_subscript_suffix_state(
        self,
        *,
        owner_expr: dict[str, Any],
    ) -> tuple[
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, int],
        str,
    ]:
        """Subscript / slice suffix の token/state resolve を helper へ寄せる。"""
        index_expr, lower, upper, rtok = self._resolve_subscript_suffix_token_state()
        return self._apply_subscript_suffix_token_state(
            owner_expr=owner_expr,
            index_expr=index_expr,
            lower=lower,
            upper=upper,
            end_tok=rtok,
        )

    def _apply_subscript_suffix_token_state(
        self,
        *,
        owner_expr: dict[str, Any],
        index_expr: dict[str, Any] | None,
        lower: dict[str, Any] | None,
        upper: dict[str, Any] | None,
        end_tok: dict[str, Any],
    ) -> tuple[
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, int],
        str,
    ]:
        """Subscript / slice suffix の token-state apply を helper へ寄せる。"""
        source_span, repr_text = self._resolve_subscript_suffix_span_repr(
            owner_expr=owner_expr,
            end_tok=end_tok,
        )
        return self._apply_subscript_suffix_span_repr_state(
            index_expr=index_expr,
            lower=lower,
            upper=upper,
            source_span=source_span,
            repr_text=repr_text,
        )

    def _apply_subscript_suffix_span_repr_state(
        self,
        *,
        index_expr: dict[str, Any] | None,
        lower: dict[str, Any] | None,
        upper: dict[str, Any] | None,
        source_span: dict[str, int],
        repr_text: str,
    ) -> tuple[
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, int],
        str,
    ]:
        """Subscript suffix の span/repr apply を helper へ寄せる。"""
        return index_expr, lower, upper, source_span, repr_text

    def _resolve_subscript_suffix_span_repr(
        self,
        *,
        owner_expr: dict[str, Any],
        end_tok: dict[str, Any],
    ) -> tuple[dict[str, int], str]:
        """Subscript suffix の postfix span/repr resolve を helper へ寄せる。"""
        return self._resolve_postfix_span_repr(
            owner_expr=owner_expr,
            end_tok=end_tok,
        )

    def _consume_subscript_suffix_open_token(self) -> dict[str, Any]:
        """Subscript suffix の `[` open token consume を helper へ寄せる。"""
        return self._eat("[")

    def _apply_subscript_suffix_open_token_state(
        self,
    ) -> tuple[
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any],
    ]:
        """Subscript suffix の open-token state apply を helper へ寄せる。"""
        return self._parse_subscript_suffix_components()

    def _consume_subscript_suffix_tokens(
        self,
    ) -> tuple[
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any],
    ]:
        """Subscript / slice suffix の token consume を helper へ寄せる。"""
        self._consume_subscript_suffix_open_token()
        return self._apply_subscript_suffix_open_token_state()

    def _resolve_subscript_suffix_token_state(
        self,
    ) -> tuple[
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any],
    ]:
        """Subscript / slice suffix の token-state resolve を helper へ寄せる。"""
        return self._consume_subscript_suffix_tokens()

    def _parse_subscript_suffix(self, *, owner_expr: dict[str, Any]) -> dict[str, Any]:
        """Subscript / slice suffix の token 消費を parser helper へ寄せる。"""
        index_expr, lower, upper, source_span, repr_text = self._resolve_subscript_suffix_state(
            owner_expr=owner_expr,
        )
        return self._apply_subscript_suffix_state(
            owner_expr=owner_expr,
            index_expr=index_expr,
            lower=lower,
            upper=upper,
            source_span=source_span,
            repr_text=repr_text,
        )

    def _apply_subscript_suffix_state(
        self,
        *,
        owner_expr: dict[str, Any],
        index_expr: dict[str, Any] | None,
        lower: dict[str, Any] | None,
        upper: dict[str, Any] | None,
        source_span: dict[str, int],
        repr_text: str,
    ) -> dict[str, Any]:
        """Subscript suffix の apply を helper へ寄せる。"""
        return self._annotate_subscript_expr(
            owner_expr=owner_expr,
            index_expr=index_expr,
            lower=lower,
            upper=upper,
            source_span=source_span,
            repr_text=repr_text,
        )
