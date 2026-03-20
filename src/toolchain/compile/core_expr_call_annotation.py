#!/usr/bin/env python3
"""Self-hosted EAST expression parser helpers for shared call annotation orchestration."""

from __future__ import annotations

from typing import Any

from toolchain.compile.core_ast_builders import _sh_make_call_expr
from toolchain.compile.core_expr_attr_call_annotation import _ShExprAttrCallAnnotationMixin
from toolchain.compile.core_expr_callee_call_annotation import _ShExprCalleeCallAnnotationMixin
from toolchain.compile.core_expr_named_call_annotation import _ShExprNamedCallAnnotationMixin


class _ShExprCallAnnotationMixin(
    _ShExprNamedCallAnnotationMixin,
    _ShExprAttrCallAnnotationMixin,
    _ShExprCalleeCallAnnotationMixin,
):
    def _resolve_call_expr_annotation_state(
        self,
        *,
        callee: dict[str, Any],
        args: list[dict[str, Any]],
        source_span: dict[str, int],
    ) -> tuple[str, str]:
        """call annotation 前段の return-type 推論と guard を helper へ寄せる。"""
        call_ret, fn_name = self._infer_call_expr_return_type(callee, args)
        self._guard_named_call_args(
            fn_name=fn_name,
            args=args,
            source_span=source_span,
        )
        return call_ret, fn_name

    def _guard_named_call_args(
        self,
        *,
        fn_name: str,
        args: list[dict[str, Any]],
        source_span: dict[str, int],
    ) -> None:
        """decode-first 制約がある named-call 引数検査を helper へ寄せる。"""
        if fn_name in {"sum", "zip", "sorted", "min", "max"}:
            self._guard_dynamic_helper_args(
                helper_name=fn_name,
                args=args,
                source_span=source_span,
            )

    def _build_call_expr_payload(
        self,
        *,
        callee: dict[str, Any],
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
        source_span: dict[str, int],
        repr_text: str,
        call_ret: str,
    ) -> dict[str, Any]:
        """Call expr payload 組み立てを helper へ寄せる。"""
        return _sh_make_call_expr(
            source_span,
            callee,
            args,
            keywords,
            resolved_type=call_ret,
            repr_text=repr_text,
        )

    def _apply_call_expr_annotation(
        self,
        *,
        callee: dict[str, Any],
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
        source_span: dict[str, int],
        repr_text: str,
        call_ret: str,
        fn_name: str,
    ) -> dict[str, Any]:
        """Call expr annotation 適用を helper へ寄せる。"""
        payload = self._build_call_expr_payload(
            callee=callee,
            args=args,
            keywords=keywords,
            source_span=source_span,
            repr_text=repr_text,
            call_ret=call_ret,
        )
        return self._annotate_callee_call_expr(
            payload,
            callee=callee,
            fn_name=fn_name,
            args=args,
        )

    def _annotate_call_expr(
        self,
        *,
        callee: dict[str, Any],
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
        source_span: dict[str, int],
        repr_text: str,
    ) -> dict[str, Any]:
        """Call expr の payload 構築と annotation を parser helper へ寄せる。"""
        call_ret, fn_name = self._resolve_call_expr_annotation_state(
            callee=callee,
            args=args,
            source_span=source_span,
        )
        return self._apply_call_expr_annotation(
            callee=callee,
            args=args,
            keywords=keywords,
            source_span=source_span,
            repr_text=repr_text,
            call_ret=call_ret,
            fn_name=fn_name,
        )
