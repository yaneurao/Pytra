#!/usr/bin/env python3
"""Self-hosted EAST expression parser helpers for call argument parsing."""

from __future__ import annotations

from typing import Any


class _ShExprCallArgParserMixin:
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
