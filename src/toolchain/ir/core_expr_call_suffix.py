#!/usr/bin/env python3
"""Self-hosted EAST expression parser helpers for call suffix parsing."""

from __future__ import annotations

from typing import Any


class _ShExprCallSuffixParserMixin:
    def _consume_call_arg_loop_comma_token(self) -> dict[str, Any]:
        """call argument loop の `,` consume を helper へ寄せる。"""
        return self._eat(",")

    def _apply_call_arg_loop_continue_state(self) -> bool:
        """call argument loop の continue state apply を helper へ寄せる。"""
        return self._resolve_call_arg_loop_continue_kind()

    def _resolve_call_arg_loop_continue_kind(self) -> bool:
        """call argument loop の continue kind 判定を helper へ寄せる。"""
        return self._cur()["k"] != ")"

    def _parse_call_args(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Call expr の位置引数と keyword 引数を parser helper へ寄せる。"""
        args: list[dict[str, Any]] = []
        keywords: list[dict[str, Any]] = []
        if self._resolve_call_args_empty_state():
            return self._apply_call_args_empty_state(
                args=args,
                keywords=keywords,
            )
        return self._consume_call_arg_entries(
            args=args,
            keywords=keywords,
        )

    def _consume_call_arg_entries(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """call argument 非空 loop を helper へ寄せる。"""
        self._consume_call_arg_entries_loop(
            args=args,
            keywords=keywords,
        )
        args, keywords = self._resolve_call_arg_entries_result_state(
            args=args,
            keywords=keywords,
        )
        return self._apply_call_arg_entries_result_state(
            args=args,
            keywords=keywords,
        )

    def _resolve_call_arg_entries_result_state(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """call argument 非空 loop の result state resolve を helper へ寄せる。"""
        return self._resolve_call_arg_entries_result_state_value(
            args=args,
            keywords=keywords,
        )

    def _resolve_call_arg_entries_result_state_value(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """call argument 非空 loop の result state value を helper へ寄せる。"""
        return self._apply_call_args_empty_state(
            args=args,
            keywords=keywords,
        )

    def _apply_call_arg_entries_result_state(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """call argument 非空 loop の result state apply を helper へ寄せる。"""
        return self._apply_call_arg_entries_result_state_result(
            args=args,
            keywords=keywords,
        )

    def _apply_call_arg_entries_result_state_result(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """call argument 非空 loop の result return を helper へ寄せる。"""
        return args, keywords

    def _consume_call_arg_entries_loop(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
    ) -> None:
        """call argument 非空 loop 本体を helper へ寄せる。"""
        while True:
            should_continue = self._resolve_call_arg_entries_loop_state(
                args=args,
                keywords=keywords,
            )
            if not self._apply_call_arg_entries_loop_state(should_continue=should_continue):
                break

    def _resolve_call_arg_entries_loop_state(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
    ) -> bool:
        """call argument 非空 loop の continue state を helper へ寄せる。"""
        return self._resolve_call_arg_entries_loop_state_value(
            args=args,
            keywords=keywords,
        )

    def _resolve_call_arg_entries_loop_state_value(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
    ) -> bool:
        """call argument 非空 loop の continue state value を helper へ寄せる。"""
        return self._consume_call_arg_loop_entry(
            args=args,
            keywords=keywords,
        )

    def _apply_call_arg_entries_loop_state(self, *, should_continue: bool) -> bool:
        """call argument 非空 loop の continue apply を helper へ寄せる。"""
        return self._apply_call_arg_entries_loop_state_result(
            should_continue=should_continue,
        )

    def _apply_call_arg_entries_loop_state_result(
        self,
        *,
        should_continue: bool,
    ) -> bool:
        """call argument 非空 loop の continue result を helper へ寄せる。"""
        return should_continue

    def _consume_call_arg_loop_entry(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
    ) -> bool:
        """call argument loop 1周分の処理を helper へ寄せる。"""
        arg_entry, keyword_entry = self._resolve_call_arg_loop_entry_state()
        return self._apply_call_arg_loop_entry_state(
            args=args,
            keywords=keywords,
            arg_entry=arg_entry,
            keyword_entry=keyword_entry,
        )

    def _resolve_call_arg_loop_entry_state(
        self,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """call argument loop 1周分の state resolve を helper へ寄せる。"""
        return self._resolve_call_arg_loop_entry_state_value()

    def _resolve_call_arg_loop_entry_state_value(
        self,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """call argument loop 1周分の state value を helper へ寄せる。"""
        return self._parse_call_arg_entry()

    def _apply_call_arg_loop_entry_state(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
        arg_entry: dict[str, Any] | None,
        keyword_entry: dict[str, Any] | None,
    ) -> bool:
        """call argument loop 1周分の state apply を helper へ寄せる。"""
        return self._apply_call_arg_loop_entry_state_result(
            args=args,
            keywords=keywords,
            arg_entry=arg_entry,
            keyword_entry=keyword_entry,
        )

    def _apply_call_arg_loop_entry_state_result(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
        arg_entry: dict[str, Any] | None,
        keyword_entry: dict[str, Any] | None,
    ) -> bool:
        """call argument loop 1周分の state result apply を helper へ寄せる。"""
        self._apply_call_arg_entry(
            args=args,
            keywords=keywords,
            arg_entry=arg_entry,
            keyword_entry=keyword_entry,
        )
        return self._advance_call_arg_loop()

    def _resolve_call_args_empty_state(self) -> bool:
        """call argument list の空 `)` 判定を helper へ寄せる。"""
        return self._resolve_call_args_empty_kind()

    def _resolve_call_args_empty_kind(self) -> bool:
        """call argument list の空 `)` kind probe を helper へ寄せる。"""
        return self._cur()["k"] == ")"

    def _apply_call_args_empty_state(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """call argument list の空-state apply を helper へ寄せる。"""
        return self._apply_call_args_empty_state_result(
            args=args,
            keywords=keywords,
        )

    def _apply_call_args_empty_state_result(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """call argument list の空-state result return を helper へ寄せる。"""
        return args, keywords

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
