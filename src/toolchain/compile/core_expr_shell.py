#!/usr/bin/env python3
"""Self-hosted expression parser shell for EAST core."""

from __future__ import annotations

from typing import Any

from toolchain.compile.core_builder_base import _sh_span
from toolchain.compile.core_entrypoints import _make_east_build_error
from toolchain.compile.core_expr_attr_subscript_annotation import _ShExprAttrSubscriptAnnotationMixin
from toolchain.compile.core_expr_attr_subscript_suffix import _ShExprPostfixSuffixParserMixin
from toolchain.compile.core_expr_attr_suffix import _ShExprAttrSuffixParserMixin
from toolchain.compile.core_expr_call_annotation import _ShExprCallAnnotationMixin
from toolchain.compile.core_expr_call_args import _ShExprCallArgParserMixin
from toolchain.compile.core_expr_call_suffix import _ShExprCallSuffixParserMixin
from toolchain.compile.core_expr_lowered import _sh_parse_expr_lowered_impl
from toolchain.compile.core_expr_parser_base import _ShExprParserBaseMixin
from toolchain.compile.core_expr_precedence import _ShExprPrecedenceParserMixin
from toolchain.compile.core_expr_primary import _make_bin_impl
from toolchain.compile.core_expr_primary import _ShExprPrimaryParserMixin
from toolchain.compile.core_expr_resolution_semantics import _ShExprResolutionSemanticsMixin
from toolchain.compile.core_expr_subscript_suffix import _ShExprSubscriptSuffixParserMixin


class _ShExprParser(
    _ShExprParserBaseMixin,
    _ShExprPrecedenceParserMixin,
    _ShExprPrimaryParserMixin,
    _ShExprResolutionSemanticsMixin,
    _ShExprCallArgParserMixin,
    _ShExprCallSuffixParserMixin,
    _ShExprAttrSuffixParserMixin,
    _ShExprSubscriptSuffixParserMixin,
    _ShExprPostfixSuffixParserMixin,
    _ShExprAttrSubscriptAnnotationMixin,
    _ShExprCallAnnotationMixin,
):
    src: str
    line_no: int
    col_base: int
    name_types: dict[str, str]
    fn_return_types: dict[str, str]
    class_method_return_types: dict[str, dict[str, str]]
    class_base: dict[str, str | None]
    tokens: list[dict[str, Any]]
    pos: int

    def __init__(
        self,
        text: str,
        line_no: int,
        col_base: int,
        name_types: dict[str, str],
        fn_return_types: dict[str, str],
        class_method_return_types: dict[str, dict[str, str]] = {},
        class_base: dict[str, str | None] = {},
    ) -> None:
        """式パースに必要な入力と型環境を初期化する。"""
        self.src = text
        self.line_no = line_no
        self.col_base = col_base
        self.name_types = name_types
        self.fn_return_types = fn_return_types
        self.class_method_return_types = class_method_return_types
        self.class_base = class_base
        self.tokens: list[dict[str, Any]] = self._tokenize(text)
        self.pos = 0

    def _raise_expr_build_error(
        self,
        *,
        kind: str,
        message: str,
        source_span: dict[str, Any],
        hint: str,
    ) -> RuntimeError:
        """expression mixin から共通の build error を生成する。"""
        return _make_east_build_error(kind=kind, message=message, source_span=source_span, hint=hint)

    def _parse_postfix(self) -> dict[str, Any]:
        """属性参照・呼び出し・添字・スライスなど後置構文を解析する。"""
        node = self._parse_primary()
        while True:
            next_node = self._parse_postfix_suffix(owner_expr=node)
            if next_node is None:
                return node
            node = next_node

    def _make_bin(self, left: dict[str, Any], op_sym: str, right: dict[str, Any]) -> dict[str, Any]:
        """二項演算ノードを構築し、数値昇格 cast も付与する。"""
        return _make_bin_impl(self, left, op_sym, right)


def _sh_parse_expr(
    text: str,
    line_no: int,
    col_base: int,
    name_types: dict[str, str],
    fn_return_types: dict[str, str],
    class_method_return_types: dict[str, dict[str, str]] = {},
    class_base: dict[str, str | None] = {},
) -> dict[str, Any]:
    """1つの式文字列を self-hosted 方式で EAST 式ノードに変換する。"""
    txt = text.strip()
    if txt == "":
        raise _make_east_build_error(
            kind="unsupported_syntax",
            message="empty expression in self_hosted backend",
            source_span=_sh_span(line_no, col_base, col_base),
            hint="Provide a non-empty expression.",
        )
    parser = _ShExprParser(
        txt,
        line_no,
        col_base + (len(text) - len(text.lstrip())),
        name_types,
        fn_return_types,
        class_method_return_types,
        class_base,
    )
    return parser.parse()


def _sh_parse_expr_lowered(expr_txt: str, *, ln_no: int, col: int, name_types: dict[str, str]) -> dict[str, Any]:
    return _sh_parse_expr_lowered_impl(expr_txt, ln_no=ln_no, col=col, name_types=name_types)
