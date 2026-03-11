#!/usr/bin/env python3
"""EAST parser core (self-hosted)."""

from __future__ import annotations

from pytra.std import argparse
from pytra.std import json
from pytra.std import re
from dataclasses import dataclass
from typing import Any
from pytra.std import sys
from toolchain.frontends.signature_registry import is_stdlib_path_type
from toolchain.frontends.signature_registry import lookup_stdlib_attribute_type
from toolchain.frontends.signature_registry import lookup_stdlib_function_return_type
from toolchain.frontends.signature_registry import lookup_stdlib_function_runtime_call
from toolchain.frontends.signature_registry import lookup_stdlib_function_runtime_binding
from toolchain.frontends.signature_registry import lookup_stdlib_imported_symbol_return_type
from toolchain.frontends.signature_registry import lookup_stdlib_imported_symbol_runtime_call
from toolchain.frontends.signature_registry import lookup_stdlib_imported_symbol_runtime_binding
from toolchain.frontends.signature_registry import lookup_noncpp_imported_symbol_runtime_call
from toolchain.frontends.signature_registry import lookup_noncpp_module_attr_runtime_call
from toolchain.frontends.signature_registry import lookup_stdlib_method_runtime_binding
from toolchain.frontends.signature_registry import lookup_stdlib_method_runtime_call
from toolchain.frontends.frontend_semantics import lookup_builtin_semantic_tag
from toolchain.frontends.frontend_semantics import lookup_owner_method_semantic_tag
from toolchain.frontends.frontend_semantics import lookup_runtime_binding_semantic_tag
from toolchain.frontends.frontend_semantics import lookup_stdlib_function_semantic_tag
from toolchain.frontends.frontend_semantics import lookup_stdlib_method_semantic_tag
from toolchain.frontends.frontend_semantics import lookup_stdlib_symbol_semantic_tag
from toolchain.frontends.runtime_abi import validate_runtime_abi_module
from toolchain.frontends.runtime_template import validate_template_module
from toolchain.frontends.runtime_symbol_index import lookup_runtime_call_adapter_kind
from toolchain.frontends.type_expr import sync_type_expr_mirrors
from toolchain.ir.core_entrypoints import EastBuildError
from toolchain.ir.core_entrypoints import _make_east_build_error
from toolchain.ir.core_entrypoints import convert_path
from toolchain.ir.core_entrypoints import convert_source_to_east
from toolchain.ir.core_entrypoints import convert_source_to_east_with_backend
from toolchain.ir.core_ast_builders import _sh_block_end_span
from toolchain.ir.core_ast_builders import _sh_make_arg_node
from toolchain.ir.core_ast_builders import _sh_make_attribute_expr
from toolchain.ir.core_ast_builders import _sh_make_binop_expr
from toolchain.ir.core_ast_builders import _sh_make_boolop_expr
from toolchain.ir.core_ast_builders import _sh_make_call_expr
from toolchain.ir.core_ast_builders import _sh_make_cast_entry
from toolchain.ir.core_ast_builders import _sh_make_comp_generator
from toolchain.ir.core_ast_builders import _sh_make_compare_expr
from toolchain.ir.core_ast_builders import _sh_make_constant_expr
from toolchain.ir.core_ast_builders import _sh_make_def_sig_info
from toolchain.ir.core_ast_builders import _sh_make_dict_comp_expr
from toolchain.ir.core_ast_builders import _sh_make_dict_entry
from toolchain.ir.core_ast_builders import _sh_make_dict_expr
from toolchain.ir.core_ast_builders import _sh_make_formatted_value_node
from toolchain.ir.core_ast_builders import _sh_make_ifexp_expr
from toolchain.ir.core_ast_builders import _sh_make_joined_str_expr
from toolchain.ir.core_ast_builders import _sh_make_keyword_arg
from toolchain.ir.core_ast_builders import _sh_make_lambda_arg_entry
from toolchain.ir.core_ast_builders import _sh_make_lambda_expr
from toolchain.ir.core_ast_builders import _sh_make_list_comp_expr
from toolchain.ir.core_ast_builders import _sh_make_list_expr
from toolchain.ir.core_ast_builders import _sh_make_range_expr
from toolchain.ir.core_ast_builders import _sh_make_set_comp_expr
from toolchain.ir.core_ast_builders import _sh_make_set_expr
from toolchain.ir.core_ast_builders import _sh_make_simple_name_comp_generator
from toolchain.ir.core_ast_builders import _sh_make_simple_name_list_comp_expr
from toolchain.ir.core_ast_builders import _sh_make_slice_node
from toolchain.ir.core_ast_builders import _sh_make_subscript_expr
from toolchain.ir.core_ast_builders import _sh_make_unaryop_expr
from toolchain.ir.core_ast_builders import _sh_push_stmt_with_trivia
from toolchain.ir.core_ast_builders import _sh_stmt_span
from toolchain.ir.core_class_semantics import _sh_collect_nominal_adt_class_metadata
from toolchain.ir.core_class_semantics import _sh_is_value_safe_dataclass_candidate
from toolchain.ir.core_class_semantics import _sh_make_decl_meta
from toolchain.ir.core_class_semantics import _sh_make_nominal_adt_v1_meta
from toolchain.ir.core_builder_base import _sh_make_expr_stmt
from toolchain.ir.core_builder_base import _sh_make_expr_token
from toolchain.ir.core_builder_base import _sh_make_kind_carrier
from toolchain.ir.core_builder_base import _sh_make_name_expr
from toolchain.ir.core_builder_base import _sh_make_node
from toolchain.ir.core_builder_base import _sh_make_stmt_node
from toolchain.ir.core_builder_base import _sh_make_trivia_blank
from toolchain.ir.core_builder_base import _sh_make_trivia_comment
from toolchain.ir.core_builder_base import _sh_make_tuple_expr
from toolchain.ir.core_builder_base import _sh_make_value_expr
from toolchain.ir.core_builder_base import _sh_span
from toolchain.ir.core_decorator_semantics import _sh_is_abi_decorator
from toolchain.ir.core_decorator_semantics import _sh_is_dataclass_decorator
from toolchain.ir.core_decorator_semantics import _sh_is_sealed_decorator
from toolchain.ir.core_decorator_semantics import _sh_is_template_decorator
from toolchain.ir.core_decorator_semantics import _sh_parse_decorator_head_and_args
from toolchain.ir.core_extern_semantics import _sh_collect_extern_var_metadata
from toolchain.ir.core_import_module_builders import _sh_make_import_alias
from toolchain.ir.core_import_module_builders import _sh_make_import_binding
from toolchain.ir.core_import_module_builders import _sh_make_import_from_stmt
from toolchain.ir.core_import_module_builders import _sh_make_import_resolution_meta
from toolchain.ir.core_import_module_builders import _sh_make_import_stmt
from toolchain.ir.core_import_module_builders import _sh_make_import_symbol_binding
from toolchain.ir.core_import_module_builders import _sh_make_module_meta
from toolchain.ir.core_import_module_builders import _sh_make_module_root
from toolchain.ir.core_import_module_builders import _sh_make_module_source_span
from toolchain.ir.core_import_module_builders import _sh_make_qualified_symbol_ref
from toolchain.ir.core_import_semantics import _sh_append_import_binding
from toolchain.ir.core_import_semantics import _sh_import_binding_fields
from toolchain.ir.core_import_semantics import _sh_is_host_only_alias
from toolchain.ir.core_import_semantics import _sh_make_import_resolution_binding
from toolchain.ir.core_import_semantics import _sh_register_import_module
from toolchain.ir.core_import_semantics import _sh_register_import_symbol
from toolchain.ir.core_expr_parser_base import _ShExprParserBaseMixin
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_anyall_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_collection_ctor_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_enumerate_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_exception_ctor_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_fixed_runtime_builtin_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_iterator_builtin_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_minmax_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_noncpp_attr_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_noncpp_symbol_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_open_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_ordchr_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_resolved_runtime_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_runtime_attr_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_runtime_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_runtime_method_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_scalar_ctor_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_stdlib_function_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_stdlib_symbol_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_type_predicate_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_infer_enumerate_item_type
from toolchain.ir.core_runtime_call_semantics import _sh_infer_known_name_call_return_type
from toolchain.ir.core_runtime_call_semantics import _sh_lookup_noncpp_attr_runtime_call
from toolchain.ir.core_runtime_call_semantics import _sh_lookup_named_call_dispatch
from toolchain.ir.core_runtime_decl_semantics import _sh_collect_function_runtime_decl_metadata
from toolchain.ir.core_runtime_decl_semantics import _sh_reject_runtime_decl_class_decorators
from toolchain.ir.core_runtime_decl_semantics import _sh_reject_runtime_decl_method_decorator
from toolchain.ir.core_runtime_decl_semantics import _sh_reject_runtime_decl_nonfunction_decorators
from toolchain.ir.core_expr_precedence import _ShExprPrecedenceParserMixin
from toolchain.ir.core_signature_semantics import _sh_parse_augassign
from toolchain.ir.core_signature_semantics import _sh_parse_def_sig
from toolchain.ir.core_signature_semantics import _sh_parse_typed_binding
from toolchain.ir.core_stmt_builders import _sh_make_ann_assign_stmt
from toolchain.ir.core_stmt_builders import _sh_make_assign_stmt
from toolchain.ir.core_stmt_builders import _sh_make_augassign_stmt
from toolchain.ir.core_stmt_builders import _sh_make_class_def_stmt
from toolchain.ir.core_stmt_builders import _sh_make_except_handler
from toolchain.ir.core_stmt_builders import _sh_make_for_range_stmt
from toolchain.ir.core_stmt_builders import _sh_make_for_stmt
from toolchain.ir.core_stmt_builders import _sh_make_function_def_stmt
from toolchain.ir.core_stmt_builders import _sh_make_if_stmt
from toolchain.ir.core_stmt_builders import _sh_make_pass_stmt
from toolchain.ir.core_stmt_builders import _sh_make_raise_stmt
from toolchain.ir.core_stmt_builders import _sh_make_return_stmt
from toolchain.ir.core_stmt_builders import _sh_make_swap_stmt
from toolchain.ir.core_stmt_builders import _sh_make_try_stmt
from toolchain.ir.core_stmt_builders import _sh_make_tuple_destructure_assign_stmt
from toolchain.ir.core_stmt_builders import _sh_make_while_stmt
from toolchain.ir.core_stmt_builders import _sh_make_yield_stmt
from toolchain.ir.core_stmt_analysis import _sh_build_arg_usage_map
from toolchain.ir.core_stmt_analysis import _sh_collect_reassigned_names
from toolchain.ir.core_stmt_analysis import _sh_collect_return_value_types
from toolchain.ir.core_stmt_analysis import _sh_collect_store_name_ids
from toolchain.ir.core_stmt_analysis import _sh_collect_yield_value_types
from toolchain.ir.core_stmt_analysis import _sh_extract_leading_docstring
from toolchain.ir.core_stmt_analysis import _sh_infer_return_type_for_untyped_def
from toolchain.ir.core_stmt_analysis import _sh_make_generator_return_type
from toolchain.ir.core_string_semantics import _sh_append_fstring_literal
from toolchain.ir.core_string_semantics import _sh_decode_py_string_body
from toolchain.ir.core_stmt_text_semantics import _sh_bind_comp_target_types
from toolchain.ir.core_stmt_text_semantics import _sh_collect_indented_block
from toolchain.ir.core_stmt_text_semantics import _sh_find_top_char
from toolchain.ir.core_stmt_text_semantics import _sh_has_explicit_line_continuation
from toolchain.ir.core_stmt_text_semantics import _sh_infer_item_type
from toolchain.ir.core_stmt_text_semantics import _sh_merge_logical_lines
from toolchain.ir.core_stmt_text_semantics import _sh_parse_class_header
from toolchain.ir.core_stmt_text_semantics import _sh_parse_class_header_base_list
from toolchain.ir.core_stmt_text_semantics import _sh_parse_except_clause
from toolchain.ir.core_stmt_text_semantics import _sh_raise_if_trailing_stmt_terminator
from toolchain.ir.core_stmt_text_semantics import _sh_scan_logical_line_state
from toolchain.ir.core_stmt_text_semantics import _sh_split_def_header_and_inline_stmt
from toolchain.ir.core_stmt_text_semantics import _sh_split_top_commas
from toolchain.ir.core_stmt_text_semantics import _sh_split_top_plus
from toolchain.ir.core_stmt_text_semantics import _sh_split_top_level_assign
from toolchain.ir.core_stmt_text_semantics import _sh_split_top_level_colon
from toolchain.ir.core_stmt_text_semantics import _sh_split_top_level_from
from toolchain.ir.core_stmt_text_semantics import _sh_split_top_level_in
from toolchain.ir.core_stmt_text_semantics import _sh_strip_inline_comment
from toolchain.ir.core_text_semantics import _sh_is_dotted_identifier
from toolchain.ir.core_text_semantics import _sh_is_identifier
from toolchain.ir.core_text_semantics import _sh_parse_dataclass_decorator_options
from toolchain.ir.core_text_semantics import _sh_parse_import_alias
from toolchain.ir.core_text_semantics import _sh_split_top_keyword
from toolchain.ir.core_text_semantics import _sh_split_top_level_as
from toolchain.ir.core_text_semantics import _sh_strip_utf8_bom
from toolchain.ir.core_type_semantics import _sh_ann_to_type
from toolchain.ir.core_type_semantics import _sh_ann_to_type_expr
from toolchain.ir.core_type_semantics import _sh_default_type_aliases
from toolchain.ir.core_type_semantics import _sh_is_type_expr_text
from toolchain.ir.core_type_semantics import _sh_register_type_alias
from toolchain.ir.core_type_semantics import _sh_typing_alias_to_type_name
from toolchain.ir.core_expr_attr_subscript_annotation import _ShExprAttrSubscriptAnnotationMixin
from toolchain.ir.core_expr_call_annotation import _ShExprCallAnnotationMixin
from toolchain.ir.core_expr_call_args import _ShExprCallArgParserMixin
from toolchain.ir.core_expr_attr_subscript_suffix import _ShExprAttrSubscriptSuffixParserMixin
from toolchain.ir.core_expr_call_suffix import _ShExprCallSuffixParserMixin


# `BorrowKind` は実体のない型エイリアス用途のみなので、
# selfhost 生成コードでは値として生成しない。
INT_TYPES = {
    "int8",
    "uint8",
    "int16",
    "uint16",
    "int32",
    "uint32",
    "int64",
    "uint64",
}
FLOAT_TYPES = {"float32", "float64"}

# `_sh_parse_expr_lowered` が参照する self-hosted 解析コンテキスト。
_SH_FN_RETURNS: dict[str, str] = {}
_SH_CLASS_METHOD_RETURNS: dict[str, dict[str, str]] = {}
_SH_CLASS_BASE: dict[str, str | None] = {}
_SH_IMPORT_SYMBOLS: dict[str, dict[str, str]] = {}
_SH_IMPORT_MODULES: dict[str, str] = {}
_SH_TYPE_ALIASES: dict[str, str] = {
    "List": "list",
    "Dict": "dict",
    "Tuple": "tuple",
    "Set": "set",
}
_SH_EMPTY_SPAN: dict[str, Any] = {}
_SH_RUNTIME_ABI_ARG_MODES = {"default", "value", "value_mut"}
_SH_RUNTIME_ABI_RET_MODES = {"default", "value"}
_SH_RUNTIME_ABI_MODE_ALIASES = {"value_readonly": "value"}
_SH_TEMPLATE_SCOPE = "runtime_helper"
_SH_TEMPLATE_INSTANTIATION_MODE = "linked_implicit"


def _sh_set_parse_context(
    fn_returns: dict[str, str],
    class_method_returns: dict[str, dict[str, str]],
    class_base: dict[str, str | None],
    type_aliases: dict[str, str] | None = None,
) -> None:
    """式解析で使う関数戻り値/クラス情報のコンテキストを更新する。"""
    _SH_FN_RETURNS.clear()
    _SH_FN_RETURNS.update(fn_returns)
    _SH_CLASS_METHOD_RETURNS.clear()
    _SH_CLASS_METHOD_RETURNS.update(class_method_returns)
    _SH_CLASS_BASE.clear()
    _SH_CLASS_BASE.update(class_base)
    _SH_TYPE_ALIASES.clear()
    if type_aliases is None:
        _SH_TYPE_ALIASES.update(_sh_default_type_aliases())
    else:
        _SH_TYPE_ALIASES.update(type_aliases)


def _sh_extract_adjacent_string_parts(
    text: str,
    line_no: int,
    col_base: int,
    name_types: dict[str, str],
) -> list[tuple[str, int]] | None:
    """トップレベルで `STR STR ...` のみで構成される式を、文字列トークン分割して返す。

    タプルを構成する `("a", "b")` のようなケースは除外し、括弧付きでも
    外側が1組の `()` で全体を包む形式に対応する。
    """
    parser = _ShExprParser(
        text,
        line_no,
        col_base,
        dict(name_types),
        _SH_FN_RETURNS,
        _SH_CLASS_METHOD_RETURNS,
        _SH_CLASS_BASE,
    )
    toks = parser._tokenize(text)
    if len(toks) <= 1:
        return None
    if toks[-1].get("k") != "EOF":
        return None
    end = len(toks) - 1
    start = 0
    if end > 1 and toks[0].get("k") == "(" and toks[end - 1].get("k") == ")":
        start = 1
        end -= 1
    inner = toks[start:end]
    if len(inner) == 0:
        return None
    for tok in inner:
        if tok.get("k") != "STR":
            return None
    if len(inner) < 2:
        return None
    return [(str(tok.get("v", "")), int(tok.get("s", 0)) + col_base) for tok in inner]


def _sh_parse_if_tail(
    *,
    start_idx: int,
    parent_indent: int,
    body_lines: list[tuple[int, str]],
    name_types: dict[str, str],
    scope_label: str,
) -> tuple[list[dict[str, Any]], int]:
    """if/elif/else 連鎖の後続ブロックを再帰的に解析する。"""
    if start_idx >= len(body_lines):
        return [], start_idx
    idx = start_idx
    while idx < len(body_lines):
        t_no, t_ln = body_lines[idx]
        t_indent = len(t_ln) - len(t_ln.lstrip(" "))
        if t_indent != parent_indent:
            return [], idx
        t_s = _sh_strip_inline_comment(t_ln.strip())
        _sh_raise_if_trailing_stmt_terminator(
            t_s,
            line_no=t_no,
            line_text=t_ln,
            make_east_build_error=_make_east_build_error,
            make_span=_sh_span,
        )
        if t_s == "":
            idx += 1
            continue
        break
    if idx >= len(body_lines):
        return [], idx
    t_no, t_ln = body_lines[idx]
    t_indent = len(t_ln) - len(t_ln.lstrip(" "))
    t_s = _sh_strip_inline_comment(t_ln.strip())
    if t_indent != parent_indent:
        return [], idx
    if t_s == "else:":
        else_block, k2 = _sh_collect_indented_block(body_lines, idx + 1, parent_indent)
        if len(else_block) == 0:
            raise _make_east_build_error(
                kind="unsupported_syntax",
                message=f"else body is missing in '{scope_label}'",
                source_span=_sh_span(t_no, 0, len(t_ln)),
                hint="Add indented else-body.",
            )
        return _sh_parse_stmt_block(else_block, name_types=dict(name_types), scope_label=scope_label), k2
    if t_s.startswith("elif ") and t_s.endswith(":"):
        cond_txt2 = t_s[len("elif ") : -1].strip()
        cond_col2 = t_ln.find(cond_txt2)
        cond_expr2 = _sh_parse_expr_lowered(cond_txt2, ln_no=t_no, col=cond_col2, name_types=dict(name_types))
        elif_block, k2 = _sh_collect_indented_block(body_lines, idx + 1, parent_indent)
        if len(elif_block) == 0:
            raise _make_east_build_error(
                kind="unsupported_syntax",
                message=f"elif body is missing in '{scope_label}'",
                source_span=_sh_span(t_no, 0, len(t_ln)),
                hint="Add indented elif-body.",
            )
        nested_orelse, k3 = _sh_parse_if_tail(
            start_idx=k2,
            parent_indent=parent_indent,
            body_lines=body_lines,
            name_types=dict(name_types),
            scope_label=scope_label,
        )
        return [
            _sh_make_if_stmt(
                _sh_block_end_span(body_lines, t_no, t_ln.find("elif "), len(t_ln), k3),
                cond_expr2,
                _sh_parse_stmt_block(elif_block, name_types=dict(name_types), scope_label=scope_label),
                orelse=nested_orelse,
            )
        ], k3
    return [], idx


class _ShExprParser(
    _ShExprParserBaseMixin,
    _ShExprPrecedenceParserMixin,
    _ShExprCallArgParserMixin,
    _ShExprCallSuffixParserMixin,
    _ShExprAttrSubscriptSuffixParserMixin,
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

    def _callable_return_type(self, t: str) -> str:
        """`callable[...]` 型文字列から戻り型だけを抽出する。"""
        if not (t.startswith("callable[") and t.endswith("]")):
            return "unknown"
        core = t[len("callable[") : -1]
        p = core.rfind("->")
        if p < 0:
            return "unknown"
        out = core[p + 2 :].strip()
        return out if out != "" else "unknown"


    def _lookup_method_return(self, cls_name: str, method: str) -> str:
        """クラス継承を辿ってメソッド戻り型を解決する。"""
        cur: str = cls_name
        while True:
            methods: dict[str, str] = {}
            if cur in self.class_method_return_types:
                methods = self.class_method_return_types[cur]
            if method in methods:
                value_obj: Any = methods[method]
                if isinstance(value_obj, str):
                    return value_obj
                return str(value_obj)
            next_cur_obj: Any = None
            if cur in self.class_base:
                next_cur_obj = self.class_base[cur]
            if not isinstance(next_cur_obj, str):
                break
            cur = next_cur_obj
        return "unknown"

    def _lookup_builtin_method_return(self, cls_name: str, method: str) -> str:
        """既知の組み込み型メソッドの戻り型を補助的に解決する。"""
        methods: dict[str, str] = {}
        if cls_name == "str":
            methods = {
                "strip": "str",
                "lstrip": "str",
                "rstrip": "str",
                "upper": "str",
                "lower": "str",
                "capitalize": "str",
                "split": "list[str]",
                "splitlines": "list[str]",
            }
        return methods.get(method, "unknown")

    def _resolve_named_call_declared_return_type(
        self,
        *,
        fn_name: str,
    ) -> str:
        """named-call の declared fallback 戻り型を helper へ寄せる。"""
        if fn_name in self.fn_return_types:
            return self.fn_return_types[fn_name]
        if fn_name in self.class_method_return_types:
            return fn_name
        return self._callable_return_type(str(self.name_types.get(fn_name, "unknown")))

    def _resolve_named_call_return_state(
        self,
        *,
        fn_name: str,
        args: list[dict[str, Any]],
    ) -> tuple[str, str]:
        """named-call の imported/declaration return state を helper へ寄せる。"""
        stdlib_imported_ret = (
            lookup_stdlib_imported_symbol_return_type(fn_name, _SH_IMPORT_SYMBOLS)
            if fn_name != ""
            else ""
        )
        call_ret = _sh_infer_known_name_call_return_type(
            fn_name,
            args,
            stdlib_imported_ret,
            infer_item_type=_sh_infer_item_type,
        )
        declared_ret = self._resolve_named_call_declared_return_type(
            fn_name=fn_name,
        )
        return call_ret, declared_ret

    def _infer_named_call_return_type(
        self,
        *,
        fn_name: str,
        args: list[dict[str, Any]],
    ) -> str:
        """Name callee の戻り型推論を helper へ寄せる。"""
        call_ret, declared_ret = self._resolve_named_call_return_state(
            fn_name=fn_name,
            args=args,
        )
        if call_ret != "":
            return call_ret
        return declared_ret

    def _lookup_attr_expr_metadata(
        self,
        owner_expr: dict[str, Any] | None,
        owner_type: str,
        attr_name: str,
    ) -> dict[str, str]:
        """属性アクセスの型と runtime metadata lookup を共有 helper へ寄せる。"""
        attr_t = "unknown"
        if (
            isinstance(owner_expr, dict)
            and owner_expr.get("kind") == "Name"
            and owner_expr.get("id") == "self"
        ):
            maybe_field_t = self.name_types.get(attr_name)
            if isinstance(maybe_field_t, str) and maybe_field_t != "":
                attr_t = maybe_field_t
        runtime_call = ""
        semantic_tag = ""
        module_id = ""
        runtime_symbol = ""
        std_attr_t = lookup_stdlib_attribute_type(owner_type, attr_name)
        if std_attr_t != "":
            attr_t = std_attr_t
            runtime_call = lookup_stdlib_method_runtime_call(owner_type, attr_name)
            semantic_tag = lookup_stdlib_method_semantic_tag(attr_name)
            if runtime_call != "":
                module_id, runtime_symbol = lookup_stdlib_method_runtime_binding(owner_type, attr_name)
        noncpp_module_id, noncpp_runtime_call = _sh_lookup_noncpp_attr_runtime_call(
            owner_expr,
            attr_name,
            import_modules=_SH_IMPORT_MODULES,
            import_symbols=_SH_IMPORT_SYMBOLS,
        )
        return {
            "resolved_type": attr_t,
            "runtime_call": runtime_call,
            "semantic_tag": semantic_tag,
            "module_id": module_id,
            "runtime_symbol": runtime_symbol,
            "noncpp_module_id": noncpp_module_id,
            "noncpp_runtime_call": noncpp_runtime_call,
        }

    def _split_generic_types(self, s: str) -> list[str]:
        """ジェネリック型引数をトップレベルカンマで分割する。"""
        out: list[str] = []
        depth = 0
        start = 0
        for i, ch in enumerate(s):
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
            elif ch == "," and depth == 0:
                out.append(s[start:i].strip())
                start = i + 1
        out.append(s[start:].strip())
        return out

    def _split_union_types(self, s: str) -> list[str]:
        """Union 型引数をトップレベル `|` で分割する。"""
        out: list[str] = []
        depth = 0
        start = 0
        for i, ch in enumerate(s):
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
            elif ch == "|" and depth == 0:
                out.append(s[start:i].strip())
                start = i + 1
        out.append(s[start:].strip())
        return out

    def _is_forbidden_object_receiver_type(self, t: str) -> bool:
        """object レシーバ禁止ルールに該当する型か判定する。"""
        s = t.strip()
        if s in {"object", "Any", "any"}:
            return True
        if "|" in s:
            parts = self._split_union_types(s)
            return any(p in {"object", "Any", "any"} for p in parts if p != "None")
        return False

    def _is_forbidden_dynamic_helper_type(self, t: str) -> bool:
        """decode-first helper に直接渡してはいけない動的型か判定する。"""
        s = t.strip()
        if s in {"object", "Any", "any"}:
            return True
        if "|" in s:
            parts = self._split_union_types(s)
            return any(p in {"object", "Any", "any"} for p in parts if p != "None")
        return False

    def _guard_dynamic_helper_receiver(self, helper_name: str, owner_t: str, source_span: dict[str, int]) -> None:
        """dynamic helper の receiver が decode-first 契約に違反していないか検査する。"""
        if not self._is_forbidden_dynamic_helper_type(owner_t):
            return
        raise _make_east_build_error(
            kind="unsupported_syntax",
            message=f"{helper_name}() does not accept object/Any receivers under decode-first constraints",
            source_span=source_span,
            hint=f"Decode JSON values to a concrete type before calling {helper_name}().",
        )

    def _guard_dynamic_helper_args(
        self,
        helper_name: str,
        args: list[dict[str, Any]],
        source_span: dict[str, int],
    ) -> None:
        """dynamic helper に object/Any 引数が直接渡っていないか検査する。"""
        for arg in args:
            if not isinstance(arg, dict):
                continue
            arg_t = str(arg.get("resolved_type", "unknown")).strip()
            if arg_t == "":
                arg_t = "unknown"
            if self._is_forbidden_dynamic_helper_type(arg_t):
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"{helper_name}() does not accept object/Any values under decode-first constraints",
                    source_span=source_span,
                    hint=f"Decode JSON values to a concrete type before calling {helper_name}().",
                )

    def _parse_call_arg_entry(
        self,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """call argument 1件分の positional/keyword 分岐を parser helper へ寄せる。"""
        save_pos, name_tok, is_keyword = self._resolve_call_arg_entry_state()
        return self._apply_call_arg_entry_state(
            save_pos=save_pos,
            name_tok=name_tok,
            is_keyword=is_keyword,
        )

    def _resolve_call_arg_entry_state(
        self,
    ) -> tuple[int | None, dict[str, Any] | None, bool]:
        """call argument 1件分の token/state resolve を helper へ寄せる。"""
        if not self._resolve_call_arg_entry_has_name():
            return None, None, False
        save_pos = self._resolve_call_arg_entry_save_pos()
        name_tok = self._consume_call_arg_entry_name_token()
        return save_pos, name_tok, self._resolve_call_arg_entry_kind()

    def _resolve_call_arg_entry_has_name(self) -> bool:
        """call argument entry の `NAME` 開始判定を helper へ寄せる。"""
        return self._cur()["k"] == "NAME"

    def _resolve_call_arg_entry_save_pos(self) -> int:
        """call argument entry の save pos 取得を helper へ寄せる。"""
        return self.pos

    def _resolve_call_arg_entry_kind(self) -> bool:
        """call argument 1件分の keyword 判定を helper へ寄せる。"""
        return self._resolve_call_arg_entry_is_keyword()

    def _resolve_call_arg_entry_is_keyword(self) -> bool:
        """call argument entry の keyword kind 判定を helper へ寄せる。"""
        return self._cur()["k"] == "="

    def _consume_call_arg_entry_name_token(self) -> dict[str, Any]:
        """call argument entry の `NAME` consume を helper へ寄せる。"""
        return self._eat("NAME")

    def _resolve_call_arg_entry_name_value(self, *, name_tok: dict[str, Any]) -> str:
        """call argument entry の `NAME` value 取得を helper へ寄せる。"""
        return str(name_tok["v"])

    def _apply_call_arg_entry_state(
        self,
        *,
        save_pos: int | None,
        name_tok: dict[str, Any] | None,
        is_keyword: bool,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """call argument 1件分の positional/keyword apply を helper へ寄せる。"""
        if is_keyword and name_tok is not None:
            return self._apply_keyword_call_arg_entry(
                name_tok=name_tok,
            )
        return self._apply_positional_call_arg_entry(
            save_pos=save_pos,
        )

    def _apply_keyword_call_arg_entry(
        self,
        *,
        name_tok: dict[str, Any],
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """call argument 1件分の keyword apply を helper へ寄せる。"""
        kw_name, kw_val = self._resolve_keyword_call_arg_entry_state(name_tok=name_tok)
        return self._apply_keyword_call_arg_build(
            kw_name=kw_name,
            kw_val=kw_val,
        )

    def _apply_keyword_call_arg_build(
        self,
        *,
        kw_name: str,
        kw_val: dict[str, Any],
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """call argument keyword の node build を helper へ寄せる。"""
        return None, _sh_make_keyword_arg(kw_name, kw_val)

    def _resolve_keyword_call_arg_entry_state(
        self,
        *,
        name_tok: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        """call argument keyword の name/value state resolve を helper へ寄せる。"""
        self._consume_keyword_call_arg_equals_token()
        kw_val = self._parse_ifexp()
        kw_name = self._resolve_call_arg_entry_name_value(name_tok=name_tok)
        return self._apply_keyword_call_arg_entry_state(
            kw_name=kw_name,
            kw_val=kw_val,
        )

    def _apply_keyword_call_arg_entry_state(
        self,
        *,
        kw_name: str,
        kw_val: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        """call argument keyword の state apply を helper へ寄せる。"""
        return kw_name, kw_val

    def _consume_keyword_call_arg_equals_token(self) -> dict[str, Any]:
        """call argument keyword の `=` consume を helper へ寄せる。"""
        return self._eat("=")

    def _apply_positional_call_arg_entry(
        self,
        *,
        save_pos: int | None,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """call argument 1件分の positional apply を helper へ寄せる。"""
        self._apply_call_arg_entry_save_pos(save_pos=save_pos)
        arg_expr = self._resolve_positional_call_arg_entry_state()
        return self._apply_positional_call_arg_build_state(arg_expr=arg_expr)

    def _resolve_positional_call_arg_entry_state(self) -> dict[str, Any]:
        """call argument positional の value state resolve を helper へ寄せる。"""
        return self._parse_call_arg_expr()

    def _apply_positional_call_arg_build_state(
        self,
        *,
        arg_expr: dict[str, Any],
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """call argument positional の build state apply を helper へ寄せる。"""
        return self._apply_positional_call_arg_build(arg_expr=arg_expr)

    def _apply_positional_call_arg_build(
        self,
        *,
        arg_expr: dict[str, Any],
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """call argument positional の node build を helper へ寄せる。"""
        return arg_expr, None

    def _apply_call_arg_entry_save_pos(self, *, save_pos: int | None) -> None:
        """call argument positional apply の save_pos 復帰を helper へ寄せる。"""
        if save_pos is not None:
            self.pos = save_pos

    def _apply_call_arg_entry(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
        arg_entry: dict[str, Any] | None,
        keyword_entry: dict[str, Any] | None,
    ) -> None:
        """call argument loop の positional/keyword append を helper へ寄せる。"""
        is_keyword_entry = self._resolve_call_arg_loop_entry_kind(keyword_entry=keyword_entry)
        return self._apply_call_arg_loop_entry_kind(
            args=args,
            keywords=keywords,
            arg_entry=arg_entry,
            keyword_entry=keyword_entry,
            is_keyword_entry=is_keyword_entry,
        )

    def _resolve_call_arg_loop_entry_kind(
        self,
        *,
        keyword_entry: dict[str, Any] | None,
    ) -> bool:
        """call argument loop entry の dispatch kind を helper へ寄せる。"""
        return keyword_entry is not None

    def _apply_call_arg_loop_entry_kind(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
        arg_entry: dict[str, Any] | None,
        keyword_entry: dict[str, Any] | None,
        is_keyword_entry: bool,
    ) -> None:
        """call argument loop entry の dispatch apply を helper へ寄せる。"""
        has_keyword_entry = self._resolve_call_arg_loop_entry_apply_state(
            is_keyword_entry=is_keyword_entry,
            keyword_entry=keyword_entry,
        )
        return self._apply_call_arg_loop_entry_apply_state(
            args=args,
            keywords=keywords,
            arg_entry=arg_entry,
            keyword_entry=keyword_entry,
            has_keyword_entry=has_keyword_entry,
        )

    def _resolve_call_arg_loop_entry_apply_state(
        self,
        *,
        is_keyword_entry: bool,
        keyword_entry: dict[str, Any] | None,
    ) -> bool:
        """call argument loop entry の keyword apply state を helper へ寄せる。"""
        return is_keyword_entry and keyword_entry is not None

    def _apply_call_arg_loop_entry_apply_state(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
        arg_entry: dict[str, Any] | None,
        keyword_entry: dict[str, Any] | None,
        has_keyword_entry: bool,
    ) -> None:
        """call argument loop entry の keyword/positional apply を helper へ寄せる。"""
        if has_keyword_entry and keyword_entry is not None:
            return self._apply_keyword_call_arg_loop_entry(
                keywords=keywords,
                keyword_entry=keyword_entry,
            )
        return self._apply_positional_call_arg_loop_entry(
            args=args,
            arg_entry=arg_entry,
        )

    def _apply_keyword_call_arg_loop_entry(
        self,
        *,
        keywords: list[dict[str, Any]],
        keyword_entry: dict[str, Any],
    ) -> None:
        """call argument loop の keyword append を helper へ寄せる。"""
        return self._apply_keyword_call_arg_loop_entry_build(
            keywords=keywords,
            keyword_entry=keyword_entry,
        )

    def _apply_keyword_call_arg_loop_entry_build(
        self,
        *,
        keywords: list[dict[str, Any]],
        keyword_entry: dict[str, Any],
    ) -> None:
        """call argument loop の keyword node append を helper へ寄せる。"""
        keywords.append(keyword_entry)

    def _apply_positional_call_arg_loop_entry(
        self,
        *,
        args: list[dict[str, Any]],
        arg_entry: dict[str, Any] | None,
    ) -> None:
        """call argument loop の positional append を helper へ寄せる。"""
        has_arg_entry = self._resolve_positional_call_arg_loop_entry_state(arg_entry=arg_entry)
        return self._apply_positional_call_arg_loop_entry_state(
            args=args,
            arg_entry=arg_entry,
            has_arg_entry=has_arg_entry,
        )

    def _resolve_positional_call_arg_loop_entry_state(
        self,
        *,
        arg_entry: dict[str, Any] | None,
    ) -> bool:
        """call argument loop の positional append state を helper へ寄せる。"""
        return arg_entry is not None

    def _apply_positional_call_arg_loop_entry_state(
        self,
        *,
        args: list[dict[str, Any]],
        arg_entry: dict[str, Any] | None,
        has_arg_entry: bool,
    ) -> None:
        """call argument loop の positional append apply を helper へ寄せる。"""
        if has_arg_entry and arg_entry is not None:
            return self._apply_positional_call_arg_loop_entry_build(
                args=args,
                arg_entry=arg_entry,
            )

    def _apply_positional_call_arg_loop_entry_build(
        self,
        *,
        args: list[dict[str, Any]],
        arg_entry: dict[str, Any],
    ) -> None:
        """call argument loop の positional node append を helper へ寄せる。"""
        args.append(arg_entry)

    def _advance_call_arg_loop(self) -> bool:
        """call argument loop の comma/terminator 制御を helper へ寄せる。"""
        has_comma = self._resolve_call_arg_loop_state()
        return self._apply_call_arg_loop_state(has_comma=has_comma)

    def _resolve_call_arg_loop_state(self) -> bool:
        """call argument loop の comma state resolve を helper へ寄せる。"""
        return self._cur()["k"] == ","

    def _apply_call_arg_loop_state(self, *, has_comma: bool) -> bool:
        """call argument loop の comma/terminator apply を helper へ寄せる。"""
        if not has_comma:
            return False
        self._consume_call_arg_loop_comma_token()
        return self._apply_call_arg_loop_continue_state()

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

    def _apply_named_call_dispatch(
        self,
        payload: dict[str, Any],
        *,
        fn_name: str,
        args: list[dict[str, Any]],
        call_dispatch: dict[str, str],
        dispatch_kind: str,
    ) -> dict[str, Any]:
        """named-call dispatch の annotation 適用を helper へ寄せる。"""
        if dispatch_kind == "builtin":
            return self._apply_builtin_named_call_annotation(
                payload,
                fn_name=fn_name,
                args=args,
                call_dispatch=call_dispatch,
            )
        if dispatch_kind == "runtime":
            return self._apply_runtime_named_call_annotation(
                payload,
                fn_name=fn_name,
                call_dispatch=call_dispatch,
            )
        return payload

    def _coalesce_optional_annotation_payload(
        self,
        *,
        payload: dict[str, Any],
        annotated_payload: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """optional annotation payload の fallback を helper へ寄せる。"""
        return payload if annotated_payload is None else annotated_payload

    def _apply_builtin_named_call_annotation(
        self,
        payload: dict[str, Any],
        *,
        fn_name: str,
        args: list[dict[str, Any]],
        call_dispatch: dict[str, str],
    ) -> dict[str, Any]:
        """builtin named-call apply を helper へ寄せる。"""
        builtin_payload = self._annotate_builtin_named_call_expr(
            payload,
            fn_name=fn_name,
            args=args,
            call_dispatch=call_dispatch,
        )
        return self._coalesce_optional_annotation_payload(
            payload=payload,
            annotated_payload=builtin_payload,
        )

    def _apply_runtime_named_call_annotation(
        self,
        payload: dict[str, Any],
        *,
        fn_name: str,
        call_dispatch: dict[str, str],
    ) -> dict[str, Any]:
        """runtime named-call apply を helper へ寄せる。"""
        runtime_payload = self._annotate_runtime_named_call_expr(
            payload,
            fn_name=fn_name,
            call_dispatch=call_dispatch,
        )
        return self._coalesce_optional_annotation_payload(
            payload=payload,
            annotated_payload=runtime_payload,
        )

    def _resolve_named_call_dispatch(
        self,
        *,
        fn_name: str,
    ) -> dict[str, str]:
        """named-call dispatch lookup を helper へ寄せる。"""
        return _sh_lookup_named_call_dispatch(
            fn_name,
            import_symbols=_SH_IMPORT_SYMBOLS,
        )

    def _should_use_truthy_runtime_for_bool_ctor(
        self,
        *,
        args: list[dict[str, Any]],
    ) -> bool:
        """bool(...) が truthy runtime helper を使うべきか判定する。"""
        if len(args) != 1:
            return False
        arg0 = args[0]
        if not isinstance(arg0, dict):
            return False
        arg0_t = str(arg0.get("resolved_type", "unknown"))
        return self._is_forbidden_object_receiver_type(arg0_t)

    def _resolve_builtin_named_call_semantic_tag(
        self,
        *,
        call_dispatch: dict[str, str],
    ) -> str:
        """builtin named-call dispatch の semantic tag unpack を helper へ寄せる。"""
        return str(call_dispatch.get("builtin_semantic_tag", ""))

    def _resolve_builtin_named_call_kind(self, *, fn_name: str) -> str:
        """builtin named-call の分類決定を helper へ寄せる。"""
        if fn_name in {"print", "len", "range", "zip", "str"}:
            return "fixed_runtime"
        if fn_name in {"int", "float", "bool"}:
            return "scalar_ctor"
        if fn_name in {"min", "max"}:
            return "minmax"
        if fn_name in {"Exception", "RuntimeError"}:
            return "exception_ctor"
        if fn_name == "open":
            return "open"
        if fn_name in {"iter", "next", "reversed"}:
            return "iterator"
        if fn_name == "enumerate":
            return "enumerate"
        if fn_name in {"any", "all"}:
            return "anyall"
        if fn_name in {"ord", "chr"}:
            return "ordchr"
        if fn_name in {"bytes", "bytearray", "list", "set", "dict"}:
            return "collection_ctor"
        if fn_name in {"isinstance", "issubclass"}:
            return "type_predicate"
        return ""

    def _resolve_builtin_named_call_dispatch(
        self,
        *,
        fn_name: str,
        call_dispatch: dict[str, str],
    ) -> tuple[str, str]:
        """builtin named-call の semantic tag / kind 解決を helper へ寄せる。"""
        semantic_tag = self._resolve_builtin_named_call_semantic_tag(
            call_dispatch=call_dispatch,
        )
        dispatch_kind = self._resolve_builtin_named_call_kind(
            fn_name=fn_name,
        )
        return semantic_tag, dispatch_kind

    def _resolve_builtin_named_call_annotation_state(
        self,
        *,
        fn_name: str,
        args: list[dict[str, Any]],
        call_dispatch: dict[str, str],
    ) -> tuple[str, str, bool, str]:
        """builtin named-call の annotation 前段 state を helper へ寄せる。"""
        semantic_tag, dispatch_kind = self._resolve_builtin_named_call_dispatch(
            fn_name=fn_name,
            call_dispatch=call_dispatch,
        )
        use_truthy_runtime = self._resolve_builtin_named_call_truthy_state(
            fn_name=fn_name,
            dispatch_kind=dispatch_kind,
            args=args,
        )
        iter_element_type = self._resolve_builtin_named_call_iter_element_type(
            dispatch_kind=dispatch_kind,
            args=args,
        )
        return semantic_tag, dispatch_kind, use_truthy_runtime, iter_element_type

    def _resolve_builtin_named_call_truthy_state(
        self,
        *,
        fn_name: str,
        dispatch_kind: str,
        args: list[dict[str, Any]],
    ) -> bool:
        """builtin named-call の truthy-runtime 特例を helper へ寄せる。"""
        return (
            dispatch_kind == "scalar_ctor"
            and fn_name == "bool"
            and self._should_use_truthy_runtime_for_bool_ctor(args=args)
        )

    def _resolve_builtin_named_call_iter_element_type(
        self,
        *,
        dispatch_kind: str,
        args: list[dict[str, Any]],
    ) -> str:
        """builtin named-call の enumerate item 型推論を helper へ寄せる。"""
        if dispatch_kind == "enumerate":
            return _sh_infer_enumerate_item_type(
                args,
                infer_item_type=_sh_infer_item_type,
            )
        return "unknown"

    def _apply_fixed_runtime_builtin_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """fixed-runtime builtin apply を helper へ寄せる。"""
        return _sh_annotate_fixed_runtime_builtin_call_expr(
            payload,
            fn_name=fn_name,
            semantic_tag=semantic_tag,
        )

    def _apply_scalar_ctor_builtin_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        args: list[dict[str, Any]],
        use_truthy_runtime: bool,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """scalar ctor builtin apply を helper へ寄せる。"""
        return _sh_annotate_scalar_ctor_call_expr(
            payload,
            fn_name=fn_name,
            arg_count=len(args),
            use_truthy_runtime=use_truthy_runtime,
            semantic_tag=semantic_tag,
        )

    def _apply_minmax_builtin_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """min/max builtin apply を helper へ寄せる。"""
        return _sh_annotate_minmax_call_expr(
            payload,
            fn_name=fn_name,
            semantic_tag=semantic_tag,
        )

    def _apply_exception_ctor_builtin_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """exception ctor builtin apply を helper へ寄せる。"""
        return _sh_annotate_exception_ctor_call_expr(
            payload,
            fn_name=fn_name,
            semantic_tag=semantic_tag,
        )

    def _apply_open_builtin_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        semantic_tag: str,
    ) -> dict[str, Any]:
        """open builtin apply を helper へ寄せる。"""
        return _sh_annotate_open_call_expr(
            payload,
            semantic_tag=semantic_tag,
        )

    def _apply_iterator_builtin_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """iterator builtin apply を helper へ寄せる。"""
        return _sh_annotate_iterator_builtin_call_expr(
            payload,
            fn_name=fn_name,
            semantic_tag=semantic_tag,
        )

    def _apply_enumerate_builtin_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        iter_element_type: str,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """enumerate builtin apply を helper へ寄せる。"""
        return _sh_annotate_enumerate_call_expr(
            payload,
            iter_element_type=iter_element_type,
            semantic_tag=semantic_tag,
        )

    def _apply_anyall_builtin_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """any/all builtin apply を helper へ寄せる。"""
        return _sh_annotate_anyall_call_expr(
            payload,
            fn_name=fn_name,
            semantic_tag=semantic_tag,
        )

    def _apply_ordchr_builtin_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """ord/chr builtin apply を helper へ寄せる。"""
        return _sh_annotate_ordchr_call_expr(
            payload,
            fn_name=fn_name,
            semantic_tag=semantic_tag,
        )

    def _apply_collection_ctor_builtin_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """collection ctor builtin apply を helper へ寄せる。"""
        return _sh_annotate_collection_ctor_call_expr(
            payload,
            fn_name=fn_name,
            semantic_tag=semantic_tag,
        )

    def _apply_type_predicate_builtin_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """type predicate builtin apply を helper へ寄せる。"""
        return _sh_annotate_type_predicate_call_expr(
            payload,
            fn_name=fn_name,
            semantic_tag=semantic_tag,
        )

    def _apply_builtin_named_call_dispatch(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        args: list[dict[str, Any]],
        dispatch_kind: str,
        semantic_tag: str,
        use_truthy_runtime: bool,
        iter_element_type: str,
    ) -> dict[str, Any] | None:
        """builtin named-call dispatch の annotation 適用を helper へ寄せる。"""
        if dispatch_kind == "fixed_runtime":
            return self._apply_fixed_runtime_builtin_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "scalar_ctor":
            return self._apply_scalar_ctor_builtin_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                args=args,
                use_truthy_runtime=use_truthy_runtime,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "minmax":
            return self._apply_minmax_builtin_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "exception_ctor":
            return self._apply_exception_ctor_builtin_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "open":
            return self._apply_open_builtin_named_call_annotation(
                payload=payload,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "iterator":
            return self._apply_iterator_builtin_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "enumerate":
            return self._apply_enumerate_builtin_named_call_annotation(
                payload=payload,
                iter_element_type=iter_element_type,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "anyall":
            return self._apply_anyall_builtin_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "ordchr":
            return self._apply_ordchr_builtin_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "collection_ctor":
            return self._apply_collection_ctor_builtin_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "type_predicate":
            return self._apply_type_predicate_builtin_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                semantic_tag=semantic_tag,
            )
        return None

    def _apply_stdlib_function_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        runtime_call: str,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """stdlib function named-call annotation 適用を helper へ寄せる。"""
        return _sh_annotate_stdlib_function_call_expr(
            payload,
            fn_name=fn_name,
            runtime_call=runtime_call,
            semantic_tag=semantic_tag,
        )

    def _apply_stdlib_symbol_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        runtime_call: str,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """stdlib symbol named-call annotation 適用を helper へ寄せる。"""
        return _sh_annotate_stdlib_symbol_call_expr(
            payload,
            fn_name=fn_name,
            runtime_call=runtime_call,
            import_symbols=_SH_IMPORT_SYMBOLS,
            semantic_tag=semantic_tag,
        )

    def _apply_noncpp_symbol_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        runtime_call: str,
    ) -> dict[str, Any]:
        """non-C++ symbol named-call annotation 適用を helper へ寄せる。"""
        return _sh_annotate_noncpp_symbol_call_expr(
            payload,
            fn_name=fn_name,
            runtime_call=runtime_call,
            import_symbols=_SH_IMPORT_SYMBOLS,
        )

    def _apply_runtime_named_call_dispatch(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        dispatch_kind: str,
        runtime_call: str,
        semantic_tag: str,
    ) -> dict[str, Any] | None:
        """runtime named-call dispatch の annotation 適用を helper へ寄せる。"""
        if dispatch_kind == "stdlib_function":
            return self._apply_stdlib_function_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                runtime_call=runtime_call,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "stdlib_symbol":
            return self._apply_stdlib_symbol_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                runtime_call=runtime_call,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "noncpp_symbol":
            return self._apply_noncpp_symbol_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                runtime_call=runtime_call,
            )
        return None

    def _resolve_attr_expr_owner_state(
        self,
        *,
        owner_expr: dict[str, Any],
        attr_name: str,
        source_span: dict[str, int],
    ) -> str:
        """Attribute access の owner 型判定と preflight guard を helper へ寄せる。"""
        owner_t = self._owner_expr_resolved_type(owner_expr)
        if attr_name in {"keys", "items", "values"}:
            self._guard_dynamic_helper_receiver(
                helper_name=attr_name,
                owner_t=owner_t,
                source_span=source_span,
            )
        if self._is_forbidden_object_receiver_type(owner_t):
            raise _make_east_build_error(
                kind="unsupported_syntax",
                message="object receiver attribute/method access is forbidden by language constraints",
                source_span=source_span,
                hint="Cast or assign to a concrete type before attribute/method access.",
            )
        return owner_t

    def _apply_noncpp_attr_call_expr_annotation(
        self,
        *,
        payload: dict[str, Any],
        owner_expr: dict[str, Any] | None,
        attr: str,
    ) -> None:
        """non-C++ attr-call annotation 適用を helper へ寄せる。"""
        _sh_annotate_noncpp_attr_call_expr(
            payload,
            owner_expr=owner_expr,
            attr_name=attr,
            import_modules=_SH_IMPORT_MODULES,
            import_symbols=_SH_IMPORT_SYMBOLS,
        )

    def _apply_runtime_method_call_expr_annotation(
        self,
        *,
        payload: dict[str, Any],
        owner_expr: dict[str, Any] | None,
        owner_t: str,
        attr: str,
    ) -> None:
        """runtime method-call annotation 適用を helper へ寄せる。"""
        _sh_annotate_runtime_method_call_expr(
            payload,
            owner_type=owner_t,
            attr=attr,
            runtime_owner=owner_expr,
        )

    def _apply_attr_call_expr_annotation(
        self,
        *,
        payload: dict[str, Any],
        owner_expr: dict[str, Any] | None,
        owner_t: str,
        attr: str,
    ) -> dict[str, Any]:
        """Attribute callee annotation の適用を helper へ寄せる。"""
        self._apply_noncpp_attr_call_expr_annotation(
            payload=payload,
            owner_expr=owner_expr,
            attr=attr,
        )
        self._apply_runtime_method_call_expr_annotation(
            payload=payload,
            owner_expr=owner_expr,
            owner_t=owner_t,
            attr=attr,
        )
        return payload

    def _build_attr_expr_payload(
        self,
        *,
        source_span: dict[str, int],
        owner_expr: dict[str, Any],
        attr_name: str,
        resolved_type: str,
        repr_text: str,
    ) -> dict[str, Any]:
        """Attribute access node 組み立てを helper へ寄せる。"""
        node = _sh_make_attribute_expr(
            source_span,
            owner_expr,
            attr_name,
            resolved_type=resolved_type,
            repr_text=repr_text,
        )
        return node

    def _apply_runtime_attr_expr_annotation(
        self,
        *,
        node: dict[str, Any],
        owner_expr: dict[str, Any],
        attr_runtime_call: str,
        attr_semantic_tag: str,
        attr_module_id: str,
        attr_runtime_symbol: str,
    ) -> None:
        """runtime attr annotation 適用を helper へ寄せる。"""
        if self._apply_runtime_call_attr_expr_annotation(
            node=node,
            owner_expr=owner_expr,
            attr_runtime_call=attr_runtime_call,
            attr_semantic_tag=attr_semantic_tag,
            attr_module_id=attr_module_id,
            attr_runtime_symbol=attr_runtime_symbol,
        ):
            return
        self._apply_runtime_semantic_attr_expr_annotation(
            node=node,
            attr_semantic_tag=attr_semantic_tag,
        )

    def _apply_runtime_call_attr_expr_annotation(
        self,
        *,
        node: dict[str, Any],
        owner_expr: dict[str, Any],
        attr_runtime_call: str,
        attr_semantic_tag: str,
        attr_module_id: str,
        attr_runtime_symbol: str,
    ) -> bool:
        """runtime-call attr annotation 適用を helper へ寄せる。"""
        if attr_runtime_call == "":
            return False
        _sh_annotate_runtime_attr_expr(
            node,
            runtime_call=attr_runtime_call,
            module_id=attr_module_id,
            runtime_symbol=attr_runtime_symbol,
            semantic_tag=attr_semantic_tag,
            runtime_owner=owner_expr,
        )
        return True

    def _apply_runtime_semantic_attr_expr_annotation(
        self,
        *,
        node: dict[str, Any],
        attr_semantic_tag: str,
    ) -> None:
        """semantic-tag fallback attr annotation 適用を helper へ寄せる。"""
        if attr_semantic_tag != "":
            node["semantic_tag"] = attr_semantic_tag

    def _apply_noncpp_attr_expr_annotation(
        self,
        *,
        node: dict[str, Any],
        attr_name: str,
        noncpp_module_attr_runtime_call: str,
        noncpp_module_id: str,
    ) -> None:
        """non-C++ attr annotation 適用を helper へ寄せる。"""
        if noncpp_module_attr_runtime_call != "":
            _sh_annotate_resolved_runtime_expr(
                node,
                runtime_call=noncpp_module_attr_runtime_call,
                runtime_source="module_attr",
                module_id=noncpp_module_id,
                runtime_symbol=attr_name,
            )

    def _build_slice_subscript_expr(
        self,
        *,
        owner_expr: dict[str, Any],
        owner_t: str,
        lower: dict[str, Any] | None,
        upper: dict[str, Any] | None,
        source_span: dict[str, int],
        repr_text: str,
    ) -> dict[str, Any]:
        """slice subscript node 組み立てを helper へ寄せる。"""
        return _sh_make_subscript_expr(
            source_span,
            owner_expr,
            _sh_make_slice_node(lower, upper),
            resolved_type=owner_t,
            repr_text=repr_text,
            lowered_kind="SliceExpr",
            lower=lower,
            upper=upper,
        )

    def _build_index_subscript_expr(
        self,
        *,
        owner_expr: dict[str, Any],
        owner_t: str,
        index_expr: dict[str, Any],
        source_span: dict[str, int],
        repr_text: str,
    ) -> dict[str, Any]:
        """index subscript node 組み立てを helper へ寄せる。"""
        return _sh_make_subscript_expr(
            source_span,
            owner_expr,
            index_expr,
            resolved_type=self._subscript_result_type(owner_t),
            repr_text=repr_text,
        )

    def _parse_postfix(self) -> dict[str, Any]:
        """属性参照・呼び出し・添字・スライスなど後置構文を解析する。"""
        node = self._parse_primary()
        while True:
            next_node = self._parse_postfix_suffix(owner_expr=node)
            if next_node is None:
                return node
            node = next_node

    def _parse_comp_target(self) -> dict[str, Any]:
        """内包表現のターゲット（name / tuple）を解析する。"""
        name_target = self._parse_name_comp_target()
        if name_target is not None:
            return name_target
        tuple_target = self._parse_tuple_comp_target()
        if tuple_target is not None:
            return tuple_target
        tok = self._cur()
        raise _make_east_build_error(
            kind="unsupported_syntax",
            message="invalid comprehension target in call argument",
            source_span=self._node_span(tok["s"], tok["e"]),
            hint="Use name or tuple target in generator expression.",
        )

    def _parse_call_arg_expr(self) -> dict[str, Any]:
        """呼び出し引数式を解析し、必要なら generator 引数へ lower する。"""
        first = self._parse_ifexp()
        if not (self._cur()["k"] == "NAME" and self._cur()["v"] == "for"):
            return first

        snapshots: dict[str, str] = {}
        generators: list[dict[str, Any]] = []
        first_norm = first
        end_node: Any = first

        def _reparse_expr(expr_node: dict[str, Any]) -> dict[str, Any]:
            expr_repr = expr_node.get("repr")
            if not isinstance(expr_repr, str) or expr_repr == "":
                return expr_node
            return _sh_parse_expr(
                expr_repr,
                line_no=self.line_no,
                col_base=int(expr_node.get("source_span", {}).get("col", self.col_base)),
                name_types=self.name_types,
                fn_return_types=self.fn_return_types,
                class_method_return_types=self.class_method_return_types,
                class_base=self.class_base,
            )

        while self._cur()["k"] == "NAME" and self._cur()["v"] == "for":
            self._eat("NAME")
            target = self._parse_comp_target()
            in_tok = self._eat("NAME")
            if in_tok["v"] != "in":
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message="expected 'in' in generator expression",
                    source_span=self._node_span(in_tok["s"], in_tok["e"]),
                    hint="Use `for x in iterable` form.",
                )
            iter_expr = self._parse_or()
            if not isinstance(iter_expr, dict):
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message="unsupported iterator expression in generator argument",
                    source_span=self._node_span(
                        int(iter_expr["source_span"]["col"]) if isinstance(iter_expr, dict) else self.col_base,
                        int(iter_expr["source_span"]["end_col"]) if isinstance(iter_expr, dict) else self.col_base + 1,
                    ),
                    hint="Use a resolvable iterable expression.",
                )

            conds: list[dict[str, Any]] = []
            while self._cur()["k"] == "NAME" and self._cur()["v"] == "if":
                self._eat("NAME")
                conds.append(self._parse_or())
            conds_norm: list[dict[str, Any]] = list(conds)

            tgt_ty = self._iter_item_type(iter_expr)
            if tgt_ty != "unknown":
                self._collect_and_bind_comp_target_types(target, tgt_ty, snapshots)
                if len(generators) == 0:
                    first_norm = _reparse_expr(first)
                conds_norm = [_reparse_expr(cond) if isinstance(cond, dict) else cond for cond in conds]

            if len(conds_norm) > 0:
                end_node = conds_norm[-1]
            else:
                end_node = iter_expr

            generators.append(_sh_make_comp_generator(target, iter_expr, conds_norm))

        self._restore_comp_target_types(snapshots)
        s = int(first["source_span"]["col"]) - self.col_base
        if not isinstance(end_node, dict):
            return first
        e = int(end_node["source_span"]["end_col"]) - self.col_base
        return _sh_make_list_comp_expr(
            self._node_span(s, e),
            first_norm,
            generators,
            repr_text=self._src_slice(s, e),
            lowered_kind="GeneratorArg",
        )

    def _make_bin(self, left: dict[str, Any], op_sym: str, right: dict[str, Any]) -> dict[str, Any]:
        """二項演算ノードを構築し、数値昇格 cast も付与する。"""
        op_map = {
            "+": "Add",
            "-": "Sub",
            "*": "Mult",
            "**": "Pow",
            "/": "Div",
            "//": "FloorDiv",
            "%": "Mod",
            "&": "BitAnd",
            "|": "BitOr",
            "^": "BitXor",
            "<<": "LShift",
            ">>": "RShift",
        }
        lt = str(left.get("resolved_type", "unknown"))
        rt = str(right.get("resolved_type", "unknown"))
        casts: list[dict[str, Any]] = []
        if op_sym == "/":
            if is_stdlib_path_type(lt) and (rt == "str" or is_stdlib_path_type(rt)):
                out_t = "Path"
            elif (lt in INT_TYPES or lt in FLOAT_TYPES) and (rt in INT_TYPES or rt in FLOAT_TYPES):
                out_t = "float64"
                if lt in INT_TYPES:
                    casts.append(_sh_make_cast_entry("left", "int64", "float64", "numeric_promotion"))
                if rt in INT_TYPES:
                    casts.append(_sh_make_cast_entry("right", "int64", "float64", "numeric_promotion"))
            else:
                # object/unknown を数値に固定化しない。
                out_t = "unknown"
        elif op_sym == "//":
            out_t = "int64" if lt in {"int64", "unknown"} and rt in {"int64", "unknown"} else "float64"
        elif op_sym == "+" and (
            (lt in {"bytes", "bytearray"} and rt in {"bytes", "bytearray"})
            or (lt == "str" and rt == "str")
        ):
            out_t = "bytes" if (lt in {"bytes", "bytearray"} and rt in {"bytes", "bytearray"}) else "str"
        elif op_sym == "**" and lt in {"int64", "float64"} and rt in {"int64", "float64"}:
            out_t = "float64"
            if lt == "int64":
                casts.append(_sh_make_cast_entry("left", "int64", "float64", "numeric_promotion"))
            if rt == "int64":
                casts.append(_sh_make_cast_entry("right", "int64", "float64", "numeric_promotion"))
        elif lt == rt and lt in {"int64", "float64"}:
            out_t = lt
        elif lt in {"int64", "float64"} and rt in {"int64", "float64"}:
            out_t = "float64"
            if lt == "int64":
                casts.append(_sh_make_cast_entry("left", "int64", "float64", "numeric_promotion"))
            if rt == "int64":
                casts.append(_sh_make_cast_entry("right", "int64", "float64", "numeric_promotion"))
        elif op_sym in {"&", "|", "^", "<<", ">>"} and lt == "int64" and rt == "int64":
            out_t = "int64"
        else:
            out_t = "unknown"

        ls = int(left["source_span"]["col"]) - self.col_base
        rs = int(right["source_span"]["end_col"]) - self.col_base
        return _sh_make_binop_expr(
            self._node_span(ls, rs),
            left,
            op_map[op_sym],
            right,
            resolved_type=out_t,
            casts=casts,
            repr_text=self._src_slice(ls, rs),
        )

    def _parse_primary(self) -> dict[str, Any]:
        """リテラル・名前・括弧式などの primary 式を解析する。"""
        tok = self._cur()
        if tok["k"] == "INT":
            self._eat("INT")
            tok_v: str = str(tok["v"])
            if tok_v.startswith("0x") or tok_v.startswith("0X"):
                tok_value = int(tok_v[2:], 16)
            elif tok_v.startswith("0b") or tok_v.startswith("0B"):
                tok_value = int(tok_v[2:], 2)
            elif tok_v.startswith("0o") or tok_v.startswith("0O"):
                tok_value = int(tok_v[2:], 8)
            else:
                tok_value = int(tok_v)
            return _sh_make_constant_expr(
                self._node_span(tok["s"], tok["e"]),
                tok_value,
                resolved_type="int64",
                repr_text=str(tok["v"]),
            )
        if tok["k"] == "FLOAT":
            self._eat("FLOAT")
            return _sh_make_constant_expr(
                self._node_span(tok["s"], tok["e"]),
                float(tok["v"]),
                resolved_type="float64",
                repr_text=str(tok["v"]),
            )
        if tok["k"] == "STR":
            str_parts: list[dict[str, Any]] = [self._eat("STR")]
            while self._cur()["k"] == "STR":
                str_parts.append(self._eat("STR"))
            if len(str_parts) > 1:
                str_nodes = [
                    _sh_parse_expr(
                        part["v"],
                        line_no=self.line_no,
                        col_base=self.col_base + int(part["s"]),
                        name_types=self.name_types,
                        fn_return_types=self.fn_return_types,
                        class_method_return_types=self.class_method_return_types,
                        class_base=self.class_base,
                    )
                    for part in str_parts
                ]
                node = str_nodes[0]
                for str_rhs in str_nodes[1:]:
                    node = _sh_make_binop_expr(
                        self._node_span(str_parts[0]["s"], str_parts[-1]["e"]),
                        node,
                        "Add",
                        str_rhs,
                        resolved_type="str",
                        repr_text=self._src_slice(str_parts[0]["s"], str_parts[-1]["e"]),
                    )
                return node

            tok = str_parts[0]
            raw: str = tok["v"]
            # Support prefixed literals (f/r/b/u/rf/fr...) in expression parser.
            p = 0
            while p < len(raw) and raw[p] in "rRbBuUfF":
                p += 1
            prefix = raw[:p].lower()
            if p >= len(raw):
                p = 0

            is_triple = p + 2 < len(raw) and raw[p : p + 3] in {"'''", '"""'}
            if is_triple:
                body = raw[p + 3 : -3]
            else:
                body = raw[p + 1 : -1]

            if "f" in prefix:
                values: list[dict[str, Any]] = []
                is_raw = "r" in prefix

                i = 0
                while i < len(body):
                    j = body.find("{", i)
                    if j < 0:
                        _sh_append_fstring_literal(values, body[i:], self._node_span(tok["s"], tok["e"]), raw_mode=is_raw)
                        break
                    if j + 1 < len(body) and body[j + 1] == "{":
                        _sh_append_fstring_literal(values, body[i : j + 1], self._node_span(tok["s"], tok["e"]), raw_mode=is_raw)
                        i = j + 2
                        continue
                    if j > i:
                        _sh_append_fstring_literal(values, body[i:j], self._node_span(tok["s"], tok["e"]), raw_mode=is_raw)
                    k = body.find("}", j + 1)
                    if k < 0:
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message="unterminated f-string placeholder in self_hosted parser",
                            source_span=self._node_span(tok["s"], tok["e"]),
                            hint="Close f-string placeholder with `}`.",
                        )
                    inner_expr = body[j + 1 : k].strip()
                    expr_txt = inner_expr
                    conv_txt = ""
                    fmt_txt = ""
                    conv_pos = _sh_find_top_char(inner_expr, "!")
                    fmt_pos = _sh_find_top_char(inner_expr, ":")
                    if conv_pos >= 0 and (fmt_pos < 0 or conv_pos < fmt_pos):
                        expr_txt = inner_expr[:conv_pos].strip()
                        conv_tail_end = fmt_pos if fmt_pos >= 0 else len(inner_expr)
                        conv_txt = inner_expr[conv_pos + 1 : conv_tail_end].strip()
                        if fmt_pos >= 0:
                            fmt_txt = inner_expr[fmt_pos + 1 :].strip()
                    elif fmt_pos >= 0:
                        expr_txt = inner_expr[:fmt_pos].strip()
                        fmt_txt = inner_expr[fmt_pos + 1 :].strip()
                    if expr_txt == "":
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message="empty f-string placeholder expression in self_hosted parser",
                            source_span=self._node_span(tok["s"], tok["e"]),
                            hint="Use `{expr}` form inside f-string placeholders.",
                        )
                    values.append(
                        _sh_make_formatted_value_node(
                            _sh_parse_expr(
                                expr_txt,
                                line_no=self.line_no,
                                col_base=self.col_base + tok["s"] + j + 1,
                                name_types=self.name_types,
                                fn_return_types=self.fn_return_types,
                                class_method_return_types=self.class_method_return_types,
                                class_base=self.class_base,
                            ),
                            conversion=conv_txt,
                            format_spec=fmt_txt,
                        )
                    )
                    i = k + 1
                return _sh_make_joined_str_expr(
                    self._node_span(tok["s"], tok["e"]),
                    values,
                    repr_text=raw,
                )
            resolved_type = "str"
            if "b" in prefix and "f" not in prefix:
                resolved_type = "bytes"
            body = _sh_decode_py_string_body(body, "r" in prefix)
            return _sh_make_constant_expr(
                self._node_span(tok["s"], tok["e"]),
                body,
                resolved_type=resolved_type,
                repr_text=raw,
            )
        if tok["k"] == "NAME":
            name_tok = self._eat("NAME")
            nm = str(name_tok["v"])
            if nm in {"True", "False"}:
                return _sh_make_constant_expr(
                    self._node_span(name_tok["s"], name_tok["e"]),
                    nm == "True",
                    resolved_type="bool",
                    repr_text=nm,
                )
            if nm == "None":
                return _sh_make_constant_expr(
                    self._node_span(name_tok["s"], name_tok["e"]),
                    None,
                    resolved_type="None",
                    repr_text=nm,
                )
            t = self.name_types.get(nm, "unknown")
            return _sh_make_name_expr(
                self._node_span(name_tok["s"], name_tok["e"]),
                nm,
                resolved_type=t,
                borrow_kind="readonly_ref" if t != "unknown" else "value",
            )
        if tok["k"] == "(":
            l = self._eat("(")
            if self._cur()["k"] == ")":
                r = self._eat(")")
                return _sh_make_tuple_expr(
                    self._node_span(l["s"], r["e"]),
                    [],
                    resolved_type="tuple[]",
                    repr_text=self._src_slice(l["s"], r["e"]),
                )
            first = self._parse_ifexp()
            if self._cur()["k"] == "NAME" and self._cur()["v"] == "for":
                self._eat("NAME")
                target = self._parse_comp_target()
                in_tok = self._eat("NAME")
                if in_tok["v"] != "in":
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="expected 'in' in generator expression",
                        source_span=self._node_span(in_tok["s"], in_tok["e"]),
                        hint="Use `(expr for x in iterable)` syntax.",
                    )
                iter_expr = self._parse_or()
                ifs: list[dict[str, Any]] = []
                while self._cur()["k"] == "NAME" and self._cur()["v"] == "if":
                    self._eat("NAME")
                    ifs.append(self._parse_or())
                r = self._eat(")")
                end_node = ifs[-1] if len(ifs) > 0 else iter_expr
                s = l["s"]
                e = int(end_node["source_span"]["end_col"]) - self.col_base
                return _sh_make_list_comp_expr(
                    self._node_span(s, r["e"]),
                    first,
                    [_sh_make_comp_generator(target, iter_expr, ifs)],
                    repr_text=self._src_slice(s, r["e"]),
                    lowered_kind="GeneratorArg",
                )
            if self._cur()["k"] == ",":
                elements = [first]
                while self._cur()["k"] == ",":
                    self._eat(",")
                    if self._cur()["k"] == ")":
                        break
                    elements.append(self._parse_ifexp())
                r = self._eat(")")
                return _sh_make_tuple_expr(
                    self._node_span(l["s"], r["e"]),
                    elements,
                    repr_text=self._src_slice(l["s"], r["e"]),
                )
            r = self._eat(")")
            first["source_span"] = self._node_span(l["s"], r["e"])
            first["repr"] = self._src_slice(l["s"], r["e"])
            return first
        if tok["k"] == "[":
            l = self._eat("[")
            elements: list[dict[str, Any]] = []
            if self._cur()["k"] != "]":
                first = self._parse_ifexp()
                # list comprehension: [elt for x in iter if cond]
                if self._cur()["k"] == "NAME" and self._cur()["v"] == "for":
                    self._eat("NAME")
                    target = self._parse_comp_target()
                    in_tok = self._eat("NAME")
                    if in_tok["v"] != "in":
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message="expected 'in' in list comprehension",
                            source_span=self._node_span(in_tok["s"], in_tok["e"]),
                            hint="Use `[x for x in iterable]` syntax.",
                        )
                    iter_expr = self._parse_or()
                    if (
                        isinstance(iter_expr, dict)
                        and iter_expr.get("kind") == "Call"
                        and isinstance(iter_expr.get("func"), dict)
                        and iter_expr.get("func", {}).get("kind") == "Name"
                        and iter_expr.get("func", {}).get("id") == "range"
                    ):
                        rargs = list(iter_expr.get("args", []))
                        range_target_span = self._node_span(self.col_base, self.col_base)
                        if isinstance(target, dict):
                            target_span_obj = target.get("source_span")
                            if isinstance(target_span_obj, dict):
                                ts = target_span_obj.get("col")
                                te = target_span_obj.get("end_col")
                            else:
                                ts = None
                                te = None
                            if isinstance(ts, int) and isinstance(te, int):
                                range_target_span = self._node_span(ts, te)
                        if len(rargs) == 1:
                            start_node = _sh_make_constant_expr(
                                range_target_span,
                                0,
                                resolved_type="int64",
                                repr_text="0",
                            )
                            stop_node = rargs[0]
                            step_node = _sh_make_constant_expr(
                                range_target_span,
                                1,
                                resolved_type="int64",
                                repr_text="1",
                            )
                        elif len(rargs) == 2:
                            start_node = rargs[0]
                            stop_node = rargs[1]
                            step_node = _sh_make_constant_expr(
                                range_target_span,
                                1,
                                resolved_type="int64",
                                repr_text="1",
                            )
                        else:
                            start_node = rargs[0]
                            stop_node = rargs[1]
                            step_node = rargs[2]
                        iter_expr = _sh_make_range_expr(
                            iter_expr.get("source_span"),
                            start_node,
                            stop_node,
                            step_node,
                            repr_text=str(iter_expr.get("repr", "range(...)")),
                        )
                    ifs: list[dict[str, Any]] = []
                    while self._cur()["k"] == "NAME" and self._cur()["v"] == "if":
                        self._eat("NAME")
                        ifs.append(self._parse_or())
                    r = self._eat("]")
                    tgt_ty = self._iter_item_type(iter_expr)
                    first_norm = first
                    ifs_norm = ifs
                    if tgt_ty != "unknown":
                        snaps: dict[str, str] = {}
                        self._collect_and_bind_comp_target_types(target, tgt_ty, snaps)
                        first_repr = first.get("repr")
                        first_col = int(first.get("source_span", {}).get("col", self.col_base))
                        if isinstance(first_repr, str) and first_repr != "":
                            first_norm = _sh_parse_expr(
                                first_repr,
                                line_no=self.line_no,
                                col_base=first_col,
                                name_types=self.name_types,
                                fn_return_types=self.fn_return_types,
                                class_method_return_types=self.class_method_return_types,
                                class_base=self.class_base,
                            )
                        ifs_norm = []
                        for cond in ifs:
                            cond_repr = cond.get("repr")
                            cond_col = int(cond.get("source_span", {}).get("col", self.col_base))
                            if isinstance(cond_repr, str) and cond_repr != "":
                                ifs_norm.append(
                                    _sh_parse_expr(
                                        cond_repr,
                                        line_no=self.line_no,
                                        col_base=cond_col,
                                        name_types=self.name_types,
                                        fn_return_types=self.fn_return_types,
                                        class_method_return_types=self.class_method_return_types,
                                        class_base=self.class_base,
                                    )
                                )
                            else:
                                ifs_norm.append(cond)
                        self._restore_comp_target_types(snaps)
                    return _sh_make_list_comp_expr(
                        self._node_span(l["s"], r["e"]),
                        first_norm,
                        [_sh_make_comp_generator(target, iter_expr, ifs_norm)],
                        repr_text=self._src_slice(l["s"], r["e"]),
                    )

                elements.append(first)
                while True:
                    if self._cur()["k"] == ",":
                        self._eat(",")
                        if self._cur()["k"] == "]":
                            break
                        elements.append(self._parse_ifexp())
                        continue
                    break
            r = self._eat("]")
            return _sh_make_list_expr(
                self._node_span(l["s"], r["e"]),
                elements,
                repr_text=self._src_slice(l["s"], r["e"]),
            )
        if tok["k"] == "{":
            l = self._eat("{")
            if self._cur()["k"] == "}":
                r = self._eat("}")
                return _sh_make_dict_expr(
                    self._node_span(l["s"], r["e"]),
                    keys=[],
                    values=[],
                    repr_text=self._src_slice(l["s"], r["e"]),
                )
            first = self._parse_ifexp()
            if self._cur()["k"] == ":":
                keys = [first]
                vals: list[dict[str, Any]] = []
                self._eat(":")
                vals.append(self._parse_ifexp())
                first_key = keys[0]
                first_val = vals[0]
                if self._cur()["k"] == "NAME" and self._cur()["v"] == "for":
                    self._eat("NAME")
                    target = self._parse_comp_target()
                    in_tok = self._eat("NAME")
                    if in_tok["v"] != "in":
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message="expected 'in' in dict comprehension",
                            source_span=self._node_span(in_tok["s"], in_tok["e"]),
                            hint="Use `for x in iterable` form.",
                        )
                    iter_expr = self._parse_or()
                    ifs: list[dict[str, Any]] = []
                    while self._cur()["k"] == "NAME" and self._cur()["v"] == "if":
                        self._eat("NAME")
                        ifs.append(self._parse_or())

                    key_node = first_key
                    val_node = first_val
                    ifs_norm: list[dict[str, Any]] = list(ifs)
                    iter_ty = self._iter_item_type(iter_expr)
                    if iter_ty != "unknown":
                        snapshots: dict[str, str] = {}
                        self._collect_and_bind_comp_target_types(target, iter_ty, snapshots)
                        try:
                            key_repr = first_key.get("repr")
                            val_repr = first_val.get("repr")
                            if isinstance(key_repr, str) and key_repr != "":
                                key_node = _sh_parse_expr(
                                    key_repr,
                                    line_no=self.line_no,
                                    col_base=int(first_key.get("source_span", {}).get("col", self.col_base)),
                                    name_types=self.name_types,
                                    fn_return_types=self.fn_return_types,
                                    class_method_return_types=self.class_method_return_types,
                                    class_base=self.class_base,
                                )
                            if isinstance(val_repr, str) and val_repr != "":
                                val_node = _sh_parse_expr(
                                    val_repr,
                                    line_no=self.line_no,
                                    col_base=int(first_val.get("source_span", {}).get("col", self.col_base)),
                                    name_types=self.name_types,
                                    fn_return_types=self.fn_return_types,
                                    class_method_return_types=self.class_method_return_types,
                                    class_base=self.class_base,
                                )
                            ifs_norm = []
                            for cond in ifs:
                                cond_repr = cond.get("repr")
                                cond_col = int(cond.get("source_span", {}).get("col", self.col_base))
                                if isinstance(cond_repr, str) and cond_repr != "":
                                    ifs_norm.append(
                                        _sh_parse_expr(
                                            cond_repr,
                                            line_no=self.line_no,
                                            col_base=cond_col,
                                            name_types=self.name_types,
                                            fn_return_types=self.fn_return_types,
                                            class_method_return_types=self.class_method_return_types,
                                            class_base=self.class_base,
                                        )
                                    )
                                else:
                                    ifs_norm.append(cond)
                        finally:
                            self._restore_comp_target_types(snapshots)
                    end_node = ifs_norm[-1] if len(ifs_norm) > 0 else iter_expr
                    end_col = int(end_node.get("source_span", {}).get("end_col", self.col_base))
                    r = self._eat("}")
                    return _sh_make_dict_comp_expr(
                        self._node_span(l["s"], end_col - self.col_base),
                        key_node,
                        val_node,
                        [_sh_make_comp_generator(target, iter_expr, ifs_norm)],
                        repr_text=self._src_slice(l["s"], end_col - self.col_base),
                    )
                while self._cur()["k"] == ",":
                    self._eat(",")
                    if self._cur()["k"] == "}":
                        break
                    keys.append(self._parse_ifexp())
                    self._eat(":")
                    vals.append(self._parse_ifexp())
                r = self._eat("}")
                return _sh_make_dict_expr(
                    self._node_span(l["s"], r["e"]),
                    keys=keys,
                    values=vals,
                    repr_text=self._src_slice(l["s"], r["e"]),
                )
            elements = [first]
            while self._cur()["k"] == ",":
                self._eat(",")
                if self._cur()["k"] == "}":
                    break
                elements.append(self._parse_ifexp())
            r = self._eat("}")
            return _sh_make_set_expr(
                self._node_span(l["s"], r["e"]),
                elements,
                repr_text=self._src_slice(l["s"], r["e"]),
            )
        raise _make_east_build_error(
            kind="unsupported_syntax",
            message=f"self_hosted parser cannot parse expression token: {tok['k']}",
            source_span=self._node_span(tok["s"], tok["e"]),
            hint="Extend self_hosted expression parser for this syntax.",
        )


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
    """式文字列を EAST 式ノードへ変換する（簡易 lower を含む）。"""
    raw = expr_txt
    txt = raw.strip()

    # lambda は if-expression より結合が弱いので、
    # ここでの簡易 ifexp 分解を回避して self_hosted 式パーサへ委譲する。
    if txt.startswith("lambda "):
        return _sh_parse_expr(
            txt,
            line_no=ln_no,
            col_base=col,
            name_types=name_types,
            fn_return_types=_SH_FN_RETURNS,
            class_method_return_types=_SH_CLASS_METHOD_RETURNS,
            class_base=_SH_CLASS_BASE,
        )

    # if-expression: a if cond else b
    p_if = _sh_split_top_keyword(txt, "if")
    p_else = _sh_split_top_keyword(txt, "else")
    if p_if >= 0 and p_else > p_if:
        body_txt = txt[:p_if].strip()
        test_txt = txt[p_if + 2 : p_else].strip()
        else_txt = txt[p_else + 4 :].strip()
        body_node = _sh_parse_expr_lowered(body_txt, ln_no=ln_no, col=col + txt.find(body_txt), name_types=dict(name_types))
        test_node = _sh_parse_expr_lowered(test_txt, ln_no=ln_no, col=col + txt.find(test_txt), name_types=dict(name_types))
        else_node = _sh_parse_expr_lowered(else_txt, ln_no=ln_no, col=col + txt.rfind(else_txt), name_types=dict(name_types))
        return _sh_make_ifexp_expr(
            _sh_span(ln_no, col, col + len(raw)),
            test_node,
            body_node,
            else_node,
            repr_text=txt,
        )

    # Normalize generator-arg any/all into list-comp form for self_hosted parser.
    m_any_all: re.Match | None = re.match(r"^(any|all)\((.+)\)$", txt, flags=re.S)
    if m_any_all is not None:
        fn_name = re.group(m_any_all, 1)
        inner_arg = re.strip_group(m_any_all, 2)
        if _sh_split_top_keyword(inner_arg, "for") > 0 and _sh_split_top_keyword(inner_arg, "in") > 0:
            lc = _sh_parse_expr_lowered(f"[{inner_arg}]", ln_no=ln_no, col=col + txt.find(inner_arg), name_types=dict(name_types))
            runtime_call = "py_any" if fn_name == "any" else ("py_all" if fn_name == "all" else "")
            semantic_tag = lookup_builtin_semantic_tag(fn_name)
            return _sh_make_builtin_listcomp_call_expr(
                _sh_span(ln_no, col, col + len(raw)),
                line_no=ln_no,
                base_col=col,
                func_name=fn_name,
                arg=lc,
                repr_text=txt,
                runtime_call=runtime_call,
                semantic_tag=semantic_tag,
            )

    # Normalize single generator-argument calls into list-comp argument form.
    # Example: ", ".join(f(x) for x in items) -> ", ".join([f(x) for x in items])
    if txt.endswith(")"):
        depth = 0
        in_str: str | None = None
        esc = False
        open_idx = -1
        close_idx = -1
        for idx, ch in enumerate(txt):
            if in_str is not None:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == in_str:
                    in_str = None
                continue
            if ch in {"'", '"'}:
                in_str = ch
                continue
            if ch == "(":
                if depth == 0 and open_idx < 0:
                    open_idx = idx
                depth += 1
                continue
            if ch == ")":
                depth -= 1
                if depth == 0:
                    close_idx = idx
                continue
            if open_idx > 0 and close_idx == len(txt) - 1:
                inner = txt[open_idx + 1 : close_idx].strip()
                inner_parts: list[str] = _sh_split_top_commas(inner)
                if len(inner_parts) == 1 and inner_parts[0] == inner and _sh_split_top_keyword(inner, "for") > 0 and _sh_split_top_keyword(inner, "in") > 0:
                    rewritten = txt[: open_idx + 1] + "[" + inner + "]" + txt[close_idx:]
                    return _sh_parse_expr_lowered(rewritten, ln_no=ln_no, col=col, name_types=dict(name_types))

    # Handle concatenation chains that include f-strings before generic parsing.
    top_comma_parts = _sh_split_top_commas(txt)
    is_single_top_expr = len(top_comma_parts) == 1

    adjacent_strings = _sh_extract_adjacent_string_parts(txt, ln_no, col, name_types)
    if adjacent_strings is not None and len(adjacent_strings) >= 2:
        nodes = [
            _sh_parse_expr(
                part,
                line_no=ln_no,
                col_base=part_col,
                name_types=name_types,
                fn_return_types=_SH_FN_RETURNS,
                class_method_return_types=_SH_CLASS_METHOD_RETURNS,
                class_base=_SH_CLASS_BASE,
            )
            for part, part_col in adjacent_strings
        ]
        node = nodes[0]
        for rhs in nodes[1:]:
            node = _sh_make_binop_expr(
                _sh_span(ln_no, col, col + len(raw)),
                node,
                "Add",
                rhs,
                resolved_type="str",
                repr_text=txt,
            )
        return node

    plus_parts = _sh_split_top_plus(txt)
    if len(plus_parts) >= 2 and any(p.startswith("f\"") or p.startswith("f'") for p in plus_parts):
        nodes = [_sh_parse_expr_lowered(p, ln_no=ln_no, col=col + txt.find(p), name_types=dict(name_types)) for p in plus_parts]
        node = nodes[0]
        for rhs in nodes[1:]:
            node = _sh_make_binop_expr(
                _sh_span(ln_no, col, col + len(raw)),
                node,
                "Add",
                rhs,
                resolved_type="str",
                repr_text=txt,
            )
        return node
    if len(plus_parts) >= 2 and is_single_top_expr:
        return _sh_parse_expr(
            txt,
            line_no=ln_no,
            col_base=col,
            name_types=name_types,
            fn_return_types=_SH_FN_RETURNS,
            class_method_return_types=_SH_CLASS_METHOD_RETURNS,
            class_base=_SH_CLASS_BASE,
        )

    # dict-comp support: {k: v for x in it} / {k: v for a, b in it}
    if txt.startswith("{") and txt.endswith("}") and ":" in txt and is_single_top_expr:
        inner = txt[1:-1].strip()
        p_for = _sh_split_top_keyword(inner, "for")
        if p_for > 0:
            head = inner[:p_for].strip()
            tail = inner[p_for + 3 :].strip()
            p_in = _sh_split_top_keyword(tail, "in")
            if p_in <= 0:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"invalid dict comprehension in self_hosted parser: {txt}",
                    source_span=_sh_span(ln_no, col, col + len(raw)),
                    hint="Use `{key: value for item in iterable}` form.",
                )
            tgt_txt = tail[:p_in].strip()
            iter_and_if_txt = tail[p_in + 2 :].strip()
            p_if = _sh_split_top_keyword(iter_and_if_txt, "if")
            if p_if >= 0:
                iter_txt = iter_and_if_txt[:p_if].strip()
                if_txt = iter_and_if_txt[p_if + 2 :].strip()
            else:
                iter_txt = iter_and_if_txt
                if_txt = ""
            if ":" not in head:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"invalid dict comprehension pair in self_hosted parser: {txt}",
                    source_span=_sh_span(ln_no, col, col + len(raw)),
                    hint="Use `key: value` pair before `for`.",
                )
            ktxt, vtxt = head.split(":", 1)
            ktxt = ktxt.strip()
            vtxt = vtxt.strip()
            target_node = _sh_parse_expr_lowered(tgt_txt, ln_no=ln_no, col=col + txt.find(tgt_txt), name_types=dict(name_types))
            iter_node = _sh_parse_expr_lowered(iter_txt, ln_no=ln_no, col=col + txt.find(iter_txt), name_types=dict(name_types))
            comp_types = _sh_bind_comp_target_types(dict(name_types), target_node, iter_node)
            key_node = _sh_parse_expr_lowered(ktxt, ln_no=ln_no, col=col + txt.find(ktxt), name_types=dict(comp_types))
            val_node = _sh_parse_expr_lowered(vtxt, ln_no=ln_no, col=col + txt.find(vtxt), name_types=dict(comp_types))
            if_nodes: list[dict[str, Any]] = []
            if if_txt != "":
                if_nodes.append(_sh_parse_expr_lowered(if_txt, ln_no=ln_no, col=col + txt.find(if_txt), name_types=dict(comp_types)))
            kt = str(key_node.get("resolved_type", "unknown"))
            vt = str(val_node.get("resolved_type", "unknown"))
            return _sh_make_dict_comp_expr(
                _sh_span(ln_no, col, col + len(raw)),
                key_node,
                val_node,
                [_sh_make_comp_generator(target_node, iter_node, if_nodes)],
                resolved_type=f"dict[{kt},{vt}]",
                repr_text=txt,
            )

    # set-comp support: {x for x in it} / {x for a, b in it if cond}
    if txt.startswith("{") and txt.endswith("}") and ":" not in txt and is_single_top_expr:
        inner = txt[1:-1].strip()
        p_for = _sh_split_top_keyword(inner, "for")
        if p_for > 0:
            elt_txt = inner[:p_for].strip()
            tail = inner[p_for + 3 :].strip()
            p_in = _sh_split_top_keyword(tail, "in")
            if p_in <= 0:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"invalid set comprehension in self_hosted parser: {txt}",
                    source_span=_sh_span(ln_no, col, col + len(raw)),
                    hint="Use `{elem for item in iterable}` form.",
                )
            tgt_txt = tail[:p_in].strip()
            iter_and_if_txt = tail[p_in + 2 :].strip()
            p_if = _sh_split_top_keyword(iter_and_if_txt, "if")
            if p_if >= 0:
                iter_txt = iter_and_if_txt[:p_if].strip()
                if_txt = iter_and_if_txt[p_if + 2 :].strip()
            else:
                iter_txt = iter_and_if_txt
                if_txt = ""
            iter_node = _sh_parse_expr_lowered(iter_txt, ln_no=ln_no, col=col + txt.find(iter_txt), name_types=dict(name_types))
            target_node = _sh_parse_expr_lowered(tgt_txt, ln_no=ln_no, col=col + txt.find(tgt_txt), name_types=dict(name_types))
            comp_types = _sh_bind_comp_target_types(dict(name_types), target_node, iter_node)
            elt_node = _sh_parse_expr_lowered(elt_txt, ln_no=ln_no, col=col + txt.find(elt_txt), name_types=dict(comp_types))
            if_nodes: list[dict[str, Any]] = []
            if if_txt != "":
                if_nodes.append(_sh_parse_expr_lowered(if_txt, ln_no=ln_no, col=col + txt.find(if_txt), name_types=dict(comp_types)))
            return _sh_make_set_comp_expr(
                _sh_span(ln_no, col, col + len(raw)),
                elt_node,
                [_sh_make_comp_generator(target_node, iter_node, if_nodes)],
                repr_text=txt,
            )

    # dict literal: {"a": 1, "b": 2}
    if txt.startswith("{") and txt.endswith("}") and ":" in txt:
        inner = txt[1:-1].strip()
        entries: list[dict[str, Any]] = []
        if inner != "":
            for part in _sh_split_top_commas(inner):
                if ":" not in part:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"invalid dict entry in self_hosted parser: {part}",
                        source_span=_sh_span(ln_no, col, col + len(raw)),
                        hint="Use `key: value` form in dict literals.",
                    )
                ktxt, vtxt = part.split(":", 1)
                ktxt = ktxt.strip()
                vtxt = vtxt.strip()
                entries.append(
                    _sh_make_dict_entry(
                        _sh_parse_expr_lowered(
                            ktxt,
                            ln_no=ln_no,
                            col=col + txt.find(ktxt),
                            name_types=dict(name_types),
                        ),
                        _sh_parse_expr_lowered(
                            vtxt,
                            ln_no=ln_no,
                            col=col + txt.find(vtxt),
                            name_types=dict(name_types),
                        ),
                    )
                )
        return _sh_make_dict_expr(
            _sh_span(ln_no, col, col + len(raw)),
            entries=entries,
            repr_text=txt,
        )

    # list-comp support: [expr for target in iter if cond] + chained for-clauses
    if txt.startswith("[") and txt.endswith("]") and is_single_top_expr:
        first_closing = -1
        depth = 0
        in_str3: str | None = None
        esc3 = False
        for i, ch in enumerate(txt):
            if in_str3 is not None:
                if esc3:
                    esc3 = False
                    continue
                if ch == "\\":
                    esc3 = True
                elif ch == in_str3:
                    in_str3 = None
                continue
            if ch in {"'", '"'}:
                in_str3 = ch
                continue
            if ch == "[":
                depth += 1
            elif ch == "]":
                if depth == 0:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"invalid bracket nesting in self_hosted parser: {txt}",
                        source_span=_sh_span(ln_no, col, col + len(raw)),
                        hint="Check list/tuple bracket balance.",
                    )
                depth -= 1
                if depth == 0:
                    first_closing = i
                    break
        if first_closing != len(txt) - 1:
            # Delegate to full parser when this is not a standalone list expression
            # (e.g. list-comprehension result with trailing slice/index).
            return _sh_parse_expr(
                txt,
                line_no=ln_no,
                col_base=col,
                name_types=name_types,
                fn_return_types=_SH_FN_RETURNS,
                class_method_return_types=_SH_CLASS_METHOD_RETURNS,
                class_base=_SH_CLASS_BASE,
            )

        inner = txt[1:-1].strip()
        p_for = _sh_split_top_keyword(inner, "for")
        if p_for > 0:
            elt_txt = inner[:p_for].strip()
            rest = inner[p_for + 3 :].strip()
            generators: list[dict[str, Any]] = []
            comp_types: dict[str, str] = dict(name_types)
            while True:
                    p_in = _sh_split_top_keyword(rest, "in")
                    if p_in <= 0:
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message=f"invalid list comprehension in self_hosted parser: {txt}",
                            source_span=_sh_span(ln_no, col, col + len(raw)),
                            hint="Use `[elem for item in iterable]` form.",
                        )
                    tgt_txt = rest[:p_in].strip()
                    iter_and_suffix_txt = rest[p_in + 2 :].strip()
                    if tgt_txt == "" or iter_and_suffix_txt == "":
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message=f"invalid list comprehension in self_hosted parser: {txt}",
                            source_span=_sh_span(ln_no, col, col + len(raw)),
                            hint="Use `[elem for item in iterable]` form.",
                        )
                    p_next_for = _sh_split_top_keyword(iter_and_suffix_txt, "for")
                    p_next_if = _sh_split_top_keyword(iter_and_suffix_txt, "if")
                    next_pos = -1
                    if p_next_for >= 0 and (p_next_if < 0 or p_next_for < p_next_if):
                        next_pos = p_next_for
                    elif p_next_if >= 0:
                        next_pos = p_next_if
                    iter_txt = iter_and_suffix_txt
                    suffix_txt = ""
                    if next_pos >= 0:
                        iter_txt = iter_and_suffix_txt[:next_pos].strip()
                        suffix_txt = iter_and_suffix_txt[next_pos:].strip()
                    if iter_txt == "":
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message=f"invalid list comprehension in self_hosted parser: {txt}",
                            source_span=_sh_span(ln_no, col, col + len(raw)),
                            hint="Use `[elem for item in iterable]` form.",
                        )

                    target_node = _sh_parse_expr_lowered(
                        tgt_txt,
                        ln_no=ln_no,
                        col=col + txt.find(tgt_txt),
                        name_types=dict(comp_types),
                    )
                    iter_node = _sh_parse_expr_lowered(
                        iter_txt,
                        ln_no=ln_no,
                        col=col + txt.find(iter_txt),
                        name_types=dict(comp_types),
                    )
                    if (
                        isinstance(iter_node, dict)
                        and iter_node.get("kind") == "Call"
                        and isinstance(iter_node.get("func"), dict)
                        and iter_node.get("func", {}).get("kind") == "Name"
                        and iter_node.get("func", {}).get("id") == "range"
                    ):
                        rargs = list(iter_node.get("args", []))
                        if len(rargs) == 1:
                            start_node = _sh_make_constant_expr(
                                _sh_span(ln_no, col, col),
                                0,
                                resolved_type="int64",
                                repr_text="0",
                            )
                            stop_node = rargs[0]
                            step_node = _sh_make_constant_expr(
                                _sh_span(ln_no, col, col),
                                1,
                                resolved_type="int64",
                                repr_text="1",
                            )
                        elif len(rargs) == 2:
                            start_node = rargs[0]
                            stop_node = rargs[1]
                            step_node = _sh_make_constant_expr(
                                _sh_span(ln_no, col, col),
                                1,
                                resolved_type="int64",
                                repr_text="1",
                            )
                        else:
                            start_node = rargs[0]
                            stop_node = rargs[1]
                            step_node = rargs[2]
                        iter_node = _sh_make_range_expr(
                            iter_node.get("source_span"),
                            start_node,
                            stop_node,
                            step_node,
                            repr_text=str(iter_node.get("repr", "range(...)")),
                        )

                    comp_types = _sh_bind_comp_target_types(dict(comp_types), target_node, iter_node)
                    if_nodes: list[dict[str, Any]] = []
                    while suffix_txt.startswith("if "):
                        cond_tail = suffix_txt[3:].strip()
                        p_cond_for = _sh_split_top_keyword(cond_tail, "for")
                        p_cond_if = _sh_split_top_keyword(cond_tail, "if")
                        split_pos = -1
                        if p_cond_for >= 0 and (p_cond_if < 0 or p_cond_for < p_cond_if):
                            split_pos = p_cond_for
                        elif p_cond_if >= 0:
                            split_pos = p_cond_if
                        cond_txt = cond_tail
                        suffix_txt = ""
                        if split_pos >= 0:
                            cond_txt = cond_tail[:split_pos].strip()
                            suffix_txt = cond_tail[split_pos:].strip()
                        if cond_txt == "":
                            raise _make_east_build_error(
                                kind="unsupported_syntax",
                                message=f"invalid list comprehension condition in self_hosted parser: {txt}",
                                source_span=_sh_span(ln_no, col, col + len(raw)),
                                hint="Use `[elem for item in iterable if cond]` form.",
                            )
                        if_nodes.append(
                            _sh_parse_expr_lowered(
                                cond_txt,
                                ln_no=ln_no,
                                col=col + txt.find(cond_txt),
                                name_types=dict(comp_types),
                            )
                        )

                    generators.append(_sh_make_comp_generator(target_node, iter_node, if_nodes))
                    if suffix_txt == "":
                        break
                    if not suffix_txt.startswith("for "):
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message=f"invalid list comprehension in self_hosted parser: {txt}",
                            source_span=_sh_span(ln_no, col, col + len(raw)),
                            hint="Use `[elem for item in iterable for item2 in iterable2]` form.",
                        )
                    rest = suffix_txt[4:].strip()
                    if rest == "":
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message=f"invalid list comprehension in self_hosted parser: {txt}",
                            source_span=_sh_span(ln_no, col, col + len(raw)),
                            hint="Use `[elem for item in iterable for item2 in iterable2]` form.",
                        )

            elt_node = _sh_parse_expr_lowered(elt_txt, ln_no=ln_no, col=col + txt.find(elt_txt), name_types=dict(comp_types))
            elem_t = str(elt_node.get("resolved_type", "unknown"))
            return _sh_make_list_comp_expr(
                _sh_span(ln_no, col, col + len(raw)),
                elt_node,
                generators,
                resolved_type=f"list[{elem_t}]",
                repr_text=txt,
            )

    # Very simple list-comp support: [x for x in <iter>]
    m_lc: re.Match | None = re.match(r"^\[\s*([A-Za-z_][A-Za-z0-9_]*)\s+for\s+([A-Za-z_][A-Za-z0-9_]*)\s+in\s+(.+)\]$", txt)
    if m_lc is not None:
        elt_name = re.group(m_lc, 1)
        tgt_name = re.group(m_lc, 2)
        iter_txt = re.strip_group(m_lc, 3)
        iter_node = _sh_parse_expr_lowered(iter_txt, ln_no=ln_no, col=col + txt.find(iter_txt), name_types=dict(name_types))
        it_t = str(iter_node.get("resolved_type", "unknown"))
        elem_t = "unknown"
        if it_t.startswith("list[") and it_t.endswith("]"):
            elem_t = it_t[5:-1]
        return _sh_make_simple_name_list_comp_expr(
            _sh_span(ln_no, col, col + len(raw)),
            line_no=ln_no,
            base_col=col,
            elt_name=elt_name,
            target_name=tgt_name,
            iter_expr=iter_node,
            elem_type=elem_t,
            repr_text=txt,
        )

    if len(txt) >= 3 and txt[0] == "f" and txt[1] in {"'", '"'} and txt[-1] == txt[1]:
        return _sh_parse_expr(
            txt,
            line_no=ln_no,
            col_base=col,
            name_types=name_types,
            fn_return_types=_SH_FN_RETURNS,
            class_method_return_types=_SH_CLASS_METHOD_RETURNS,
            class_base=_SH_CLASS_BASE,
        )

    tuple_parts = _sh_split_top_commas(txt)
    if len(tuple_parts) >= 2 or (len(tuple_parts) == 1 and txt.endswith(",")):
        elems = [_sh_parse_expr_lowered(p, ln_no=ln_no, col=col + txt.find(p), name_types=dict(name_types)) for p in tuple_parts]
        elem_ts = [str(e.get("resolved_type", "unknown")) for e in elems]
        return _sh_make_tuple_expr(
            _sh_span(ln_no, col, col + len(raw)),
            elems,
            resolved_type="tuple[" + ", ".join(elem_ts) + "]",
            repr_text=txt,
        )

    return _sh_parse_expr(
        txt,
        line_no=ln_no,
        col_base=col,
        name_types=name_types,
        fn_return_types=_SH_FN_RETURNS,
        class_method_return_types=_SH_CLASS_METHOD_RETURNS,
        class_base=_SH_CLASS_BASE,
    )

def _sh_parse_stmt_block_mutable(body_lines: list[tuple[int, str]], *, name_types: dict[str, str], scope_label: str) -> list[dict[str, Any]]:
    """インデントブロックを文単位で解析し、EAST 文リストを返す。"""
    def _maybe_bind_self_field(
        target_expr: dict[str, Any] | None,
        value_type: str | None,
        *,
        explicit: str | None = None,
    ) -> None:
        """`self.xxx` への代入時、self フィールドの型推論を更新する。"""
        if not isinstance(target_expr, dict):
            return
        if target_expr.get("kind") != "Attribute":
            return
        owner = target_expr.get("value")
        if not isinstance(owner, dict):
            return
        if owner.get("kind") != "Name" or owner.get("id") != "self":
            return
        field_name = str(target_expr.get("attr", "")).strip()
        if field_name == "":
            return
        candidate = value_type or ""
        if candidate != "":
            name_types[field_name] = candidate
            return
        if isinstance(explicit, str) and explicit.strip() != "":
            name_types[field_name] = explicit.strip()

    body_lines, merged_line_end = _sh_merge_logical_lines(body_lines)

    stmts: list[dict[str, Any]] = []
    pending_leading_trivia: list[dict[str, Any]] = []
    pending_blank_count = 0

    skip = 0
    for i, (_, ln_txt) in enumerate(body_lines):
        if skip > 0:
            skip -= 1
            continue
        ln_no, ln_txt = body_lines[i]
        indent = len(ln_txt) - len(ln_txt.lstrip(" "))
        raw_s = ln_txt.strip()
        s = _sh_strip_inline_comment(raw_s)
        _sh_raise_if_trailing_stmt_terminator(
            s,
            line_no=ln_no,
            line_text=ln_txt,
            make_east_build_error=_make_east_build_error,
            make_span=_sh_span,
        )

        if raw_s == "":
            pending_blank_count += 1
            continue
        if raw_s.startswith("#"):
            if pending_blank_count > 0:
                pending_leading_trivia.append(_sh_make_trivia_blank(pending_blank_count))
                pending_blank_count = 0
            text = raw_s[1:]
            if text.startswith(" "):
                text = text[1:]
            pending_leading_trivia.append(_sh_make_trivia_comment(text))
            continue
        if s == "":
            continue

        sig_line, inline_fn_stmt = _sh_split_def_header_and_inline_stmt(s)
        sig = _sh_parse_def_sig(
            ln_no,
            sig_line,
            type_aliases=_SH_TYPE_ALIASES,
            make_east_build_error=_make_east_build_error,
            make_span=_sh_span,
            make_def_sig_info=_sh_make_def_sig_info,
        )
        if sig is not None:
            fn_name = str(sig["name"])
            fn_ret = str(sig["ret"])
            arg_types: dict[str, str] = dict(sig["arg_types"])
            arg_type_exprs_obj: Any = sig.get("arg_type_exprs")
            arg_type_exprs: dict[str, Any] = arg_type_exprs_obj if isinstance(arg_type_exprs_obj, dict) else {}
            arg_order: list[str] = list(sig["arg_order"])
            arg_defaults_raw_obj: Any = sig.get("arg_defaults")
            arg_defaults_raw: dict[str, Any] = arg_defaults_raw_obj if isinstance(arg_defaults_raw_obj, dict) else {}
            fn_block: list[tuple[int, str]] = []
            j = i + 1
            if inline_fn_stmt != "":
                fn_block = [(ln_no, " " * (indent + 4) + inline_fn_stmt)]
            else:
                fn_block, j = _sh_collect_indented_block(body_lines, i + 1, indent)
                if len(fn_block) == 0:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"self_hosted parser requires non-empty nested function body '{fn_name}'",
                        source_span=_sh_span(ln_no, 0, len(ln_txt)),
                        hint="Add nested function statements.",
                    )
            fn_scope_types: dict[str, str] = dict(name_types)
            for arg_name, arg_ty in arg_types.items():
                fn_scope_types[arg_name] = arg_ty
            fn_stmts = _sh_parse_stmt_block(fn_block, name_types=fn_scope_types, scope_label=f"{scope_label}.{fn_name}")
            docstring, fn_stmts = _sh_extract_leading_docstring(fn_stmts)
            fn_ret = _sh_infer_return_type_for_untyped_def(fn_ret, fn_stmts)
            yield_types = _sh_collect_yield_value_types(fn_stmts)
            is_generator = len(yield_types) > 0
            fn_ret_effective = fn_ret
            yield_value_type = "unknown"
            if is_generator:
                fn_ret_effective, yield_value_type = _sh_make_generator_return_type(fn_ret, yield_types)
            fn_ret_type_expr = _sh_ann_to_type_expr(fn_ret_effective, type_aliases=_SH_TYPE_ALIASES)
            arg_defaults: dict[str, Any] = {}
            arg_index_map: dict[str, int] = {}
            for arg_pos, arg_name in enumerate(arg_order):
                arg_index_map[arg_name] = int(arg_pos)
                if arg_name in arg_defaults_raw:
                    default_obj: Any = arg_defaults_raw[arg_name]
                    default_txt: str = str(default_obj).strip()
                    if default_txt != "":
                        default_col = ln_txt.find(default_txt)
                        if default_col < 0:
                            default_col = 0
                        arg_defaults[arg_name] = _sh_parse_expr_lowered(
                            default_txt,
                            ln_no=ln_no,
                            col=default_col,
                            name_types=dict(name_types),
                        )
            arg_usage_map = _sh_build_arg_usage_map(arg_order, arg_types, fn_stmts)
            callable_parts: list[str] = []
            for arg_name in arg_order:
                callable_parts.append(arg_types.get(arg_name, "unknown"))
            name_types[fn_name] = "callable[" + ", ".join(callable_parts) + "->" + fn_ret_effective + "]"
            _SH_FN_RETURNS[fn_name] = fn_ret_effective
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                _sh_make_function_def_stmt(
                    fn_name,
                    _sh_block_end_span(body_lines, ln_no, 0, len(ln_txt), j),
                    arg_types,
                    arg_order,
                    fn_ret_effective,
                    fn_stmts,
                    arg_type_exprs=arg_type_exprs,
                    arg_defaults=arg_defaults,
                    arg_index=arg_index_map,
                    return_type_expr=fn_ret_type_expr,
                    arg_usage=arg_usage_map,
                    docstring=docstring,
                    is_generator=is_generator,
                    yield_value_type=yield_value_type,
                ),
            )
            skip = j - i - 1
            continue

        if s.startswith("if ") and s.endswith(":"):
            cond_txt = s[len("if ") : -1].strip()
            cond_col = ln_txt.find(cond_txt)
            cond_expr = _sh_parse_expr_lowered(cond_txt, ln_no=ln_no, col=cond_col, name_types=dict(name_types))
            then_block, j = _sh_collect_indented_block(body_lines, i + 1, indent)
            if len(then_block) == 0:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"if body is missing in '{scope_label}'",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Add indented if-body.",
                )
            else_stmt_list, j = _sh_parse_if_tail(
                start_idx=j,
                parent_indent=indent,
                body_lines=body_lines,
                name_types=dict(name_types),
                scope_label=scope_label,
            )
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                _sh_make_if_stmt(
                    _sh_block_end_span(body_lines, ln_no, ln_txt.find("if "), len(ln_txt), j),
                    cond_expr,
                    _sh_parse_stmt_block(then_block, name_types=dict(name_types), scope_label=scope_label),
                    orelse=else_stmt_list,
                ),
            )
            skip = j - i - 1
            continue

        if s.startswith("for "):
            for_full = s[len("for ") :].strip()
            for_head = ""
            inline_stmt_text = ""
            if for_full.endswith(":"):
                for_head = for_full[:-1].strip()
            else:
                split_colon = _sh_split_top_level_colon(for_full)
                if split_colon is not None:
                    for_head = split_colon[0]
                    inline_stmt_text = split_colon[1]
            if for_head == "":
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse for statement: {s}",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Use `for target in iterable:` form.",
                )
            split_for = _sh_split_top_level_in(for_head)
            if split_for is None:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse for statement: {s}",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Use `for target in iterable:` form.",
                )
            tgt_txt, iter_txt = split_for
            tgt_col = ln_txt.find(tgt_txt)
            iter_col = ln_txt.find(iter_txt)
            target_expr = _sh_parse_expr_lowered(tgt_txt, ln_no=ln_no, col=tgt_col, name_types=dict(name_types))
            iter_expr = _sh_parse_expr_lowered(iter_txt, ln_no=ln_no, col=iter_col, name_types=dict(name_types))
            body_block: list[tuple[int, str]] = []
            j = i + 1
            if inline_stmt_text != "":
                body_block.append((ln_no, " " * (indent + 4) + inline_stmt_text))
            else:
                body_block, j = _sh_collect_indented_block(body_lines, i + 1, indent)
                if len(body_block) == 0:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"for body is missing in '{scope_label}'",
                        source_span=_sh_span(ln_no, 0, len(ln_txt)),
                        hint="Add indented for-body.",
                    )
            t_ty = "unknown"
            i_ty = str(iter_expr.get("resolved_type", "unknown"))
            i_ty_norm = i_ty.strip()
            iter_mode = "static_fastpath"
            iterable_trait = "unknown"
            iter_protocol = "static_range"
            tuple_target_elem_types: list[str] = []
            if i_ty.startswith("list[") and i_ty.endswith("]"):
                inner_t = i_ty[5:-1].strip()
                t_ty = inner_t
                iter_mode = "static_fastpath"
                iterable_trait = "yes"
                iter_protocol = "static_range"
                if inner_t.startswith("tuple[") and inner_t.endswith("]"):
                    tuple_inner = inner_t[6:-1].strip()
                    if tuple_inner != "":
                        tuple_target_elem_types = _sh_split_top_commas(tuple_inner)
            elif i_ty.startswith("dict[") and i_ty.endswith("]"):
                dict_inner = i_ty[5:-1].strip()
                dict_parts = _sh_split_top_commas(dict_inner)
                if len(dict_parts) >= 1:
                    key_t = dict_parts[0].strip()
                    t_ty = key_t if key_t != "" else "unknown"
                iter_mode = "static_fastpath"
                iterable_trait = "yes"
                iter_protocol = "static_range"
            elif i_ty.startswith("tuple[") and i_ty.endswith("]"):
                t_ty = "unknown"
                iter_mode = "static_fastpath"
                iterable_trait = "yes"
                iter_protocol = "static_range"
            elif i_ty.startswith("set[") and i_ty.endswith("]"):
                t_ty = i_ty[4:-1]
                iter_mode = "static_fastpath"
                iterable_trait = "yes"
                iter_protocol = "static_range"
            elif i_ty == "str":
                t_ty = "str"
                iter_mode = "static_fastpath"
                iterable_trait = "yes"
                iter_protocol = "static_range"
            elif i_ty in {"bytes", "bytearray"}:
                t_ty = "uint8"
                iter_mode = "static_fastpath"
                iterable_trait = "yes"
                iter_protocol = "static_range"
            elif i_ty_norm == "Any" or i_ty_norm == "object":
                iter_mode = "runtime_protocol"
                iterable_trait = "unknown"
                iter_protocol = "runtime_protocol"
            elif i_ty_norm in {"int", "int64", "float", "float64", "bool"}:
                iterable_trait = "no"
                iter_mode = "runtime_protocol"
                iter_protocol = "runtime_protocol"
            elif "|" in i_ty_norm:
                union_parts = _sh_split_top_commas(i_ty_norm.replace("|", ","))
                for up in union_parts:
                    u = up.strip()
                    if u == "Any" or u == "object":
                        iter_mode = "runtime_protocol"
                        iter_protocol = "runtime_protocol"
                        break
            if isinstance(iter_expr, dict):
                iter_expr["iterable_trait"] = iterable_trait
                iter_expr["iter_protocol"] = iter_protocol
                iter_expr["iter_element_type"] = t_ty
            target_names: list[str] = []
            if isinstance(target_expr, dict) and target_expr.get("kind") == "Name":
                nm = str(target_expr.get("id", ""))
                if nm != "":
                    target_names.append(nm)
            elif isinstance(target_expr, dict) and target_expr.get("kind") == "Tuple":
                elem_nodes_obj: Any = target_expr.get("elements", [])
                elem_nodes: list[dict[str, Any]] = elem_nodes_obj if isinstance(elem_nodes_obj, list) else []
                for e in elem_nodes:
                    if isinstance(e, dict) and e.get("kind") == "Name":
                        nm = str(e.get("id", ""))
                        if nm != "":
                            target_names.append(nm)
            if len(tuple_target_elem_types) > 0 and isinstance(target_expr, dict) and target_expr.get("kind") == "Tuple":
                target_expr["resolved_type"] = f"tuple[{','.join([t.strip() if t.strip() != '' else 'unknown' for t in tuple_target_elem_types])}]"
                for idx, nm in enumerate(target_names):
                    if idx < len(tuple_target_elem_types):
                        et = tuple_target_elem_types[idx].strip()
                        if et == "":
                            et = "unknown"
                        name_types[nm] = et
                        try:
                            elem_nodes[idx]["resolved_type"] = et
                        except Exception:
                            pass
                    else:
                        name_types[nm] = "unknown"
                        try:
                            elem_nodes[idx]["resolved_type"] = "unknown"
                        except Exception:
                            pass
            elif t_ty != "unknown":
                for nm in target_names:
                    name_types[nm] = t_ty
                if isinstance(target_expr, dict) and target_expr.get("kind") == "Name":
                    target_expr["resolved_type"] = t_ty
            if (
                isinstance(target_expr, dict)
                and target_expr.get("kind") == "Name"
                and
                isinstance(iter_expr, dict)
                and iter_expr.get("kind") == "Call"
                and isinstance(iter_expr.get("func"), dict)
                and iter_expr.get("func", {}).get("kind") == "Name"
                and iter_expr.get("func", {}).get("id") == "range"
            ):
                rargs = list(iter_expr.get("args", []))
                start_node: dict[str, Any]
                stop_node: dict[str, Any]
                step_node: dict[str, Any]
                if len(rargs) == 1:
                    start_node = _sh_make_constant_expr(
                        _sh_span(ln_no, ln_txt.find("range"), ln_txt.find("range") + 5),
                        0,
                        resolved_type="int64",
                        repr_text="0",
                    )
                    stop_node = rargs[0]
                    step_node = _sh_make_constant_expr(
                        _sh_span(ln_no, ln_txt.find("range"), ln_txt.find("range") + 5),
                        1,
                        resolved_type="int64",
                        repr_text="1",
                    )
                elif len(rargs) == 2:
                    start_node = rargs[0]
                    stop_node = rargs[1]
                    step_node = _sh_make_constant_expr(
                        _sh_span(ln_no, ln_txt.find("range"), ln_txt.find("range") + 5),
                        1,
                        resolved_type="int64",
                        repr_text="1",
                    )
                else:
                    start_node = rargs[0]
                    stop_node = rargs[1]
                    step_node = rargs[2]
                tgt = str(target_expr.get("id", ""))
                if tgt != "":
                    name_types[tgt] = "int64"
                pending_blank_count = _sh_push_stmt_with_trivia(
                    stmts,
                    pending_leading_trivia,
                    pending_blank_count,
                    _sh_make_for_range_stmt(
                        _sh_block_end_span(body_lines, ln_no, 0, len(ln_txt), j),
                        target_expr,
                        start_node,
                        stop_node,
                        step_node,
                        _sh_parse_stmt_block(body_block, name_types=dict(name_types), scope_label=scope_label),
                    ),
                )
                skip = j - i - 1
                continue
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                _sh_make_for_stmt(
                    _sh_block_end_span(body_lines, ln_no, 0, len(ln_txt), j),
                    target_expr,
                    iter_expr,
                    _sh_parse_stmt_block(body_block, name_types=dict(name_types), scope_label=scope_label),
                    target_type=t_ty,
                    iter_mode=iter_mode,
                    iter_source_type=i_ty_norm if i_ty_norm != "" else "unknown",
                    iter_element_type=t_ty,
                ),
            )
            skip = j - i - 1
            continue

        m_import: re.Match | None = re.match(r"^import\s+(.+)$", s, flags=re.S)
        if m_import is not None:
            names_txt = re.strip_group(m_import, 1)
            raw_parts: list[str] = []
            for p in names_txt.split(","):
                p2: str = p.strip()
                if p2 != "":
                    raw_parts.append(p2)
            if len(raw_parts) == 0:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message="import statement has no module names",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Use `import module` or `import module as alias`.",
                )
            aliases: list[dict[str, str | None]] = []
            for part in raw_parts:
                parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=True)
                if parsed_alias is None:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"unsupported import clause: {part}",
                        source_span=_sh_span(ln_no, 0, len(ln_txt)),
                        hint="Use `import module` or `import module as alias` form.",
                    )
                mod_name, as_name_txt = parsed_alias
                if mod_name == "typing":
                    # `typing` は注釈専用モジュールとして扱い、EAST 依存には積まない。
                    continue
                if mod_name == "dataclasses":
                    # `dataclasses` は decorator 解決専用モジュールとして扱い、EAST 依存には積まない。
                    bind_name_dc = as_name_txt if as_name_txt != "" else mod_name.split(".")[0]
                    _sh_register_import_module(_SH_IMPORT_MODULES, bind_name_dc, mod_name)
                    continue
                bind_name = as_name_txt if as_name_txt != "" else mod_name.split(".")[0]
                _sh_register_import_module(_SH_IMPORT_MODULES, bind_name, mod_name)
                if _sh_is_host_only_alias(bind_name):
                    continue
                aliases.append(_sh_make_import_alias(mod_name, as_name_txt if as_name_txt != "" else None))
            if len(aliases) > 0:
                pending_blank_count = _sh_push_stmt_with_trivia(
                    stmts,
                    pending_leading_trivia,
                    pending_blank_count,
                    _sh_make_import_stmt(
                        _sh_make_stmt_node,
                        _sh_stmt_span(merged_line_end, ln_no, 0, len(ln_txt)),
                        aliases,
                    ),
                )
            continue

        if s.startswith("from "):
            marker = " import "
            pos = s.find(marker)
            if pos >= 0:
                mod_txt = s[5:pos].strip()
                if mod_txt.startswith("."):
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="relative import is not supported",
                        source_span=_sh_span(ln_no, 0, len(ln_txt)),
                        hint="Use absolute import form: `from module import name`.",
                    )
        m_import_from: re.Match | None = re.match(r"^from\s+([A-Za-z_][A-Za-z0-9_\.]*)\s+import\s+(.+)$", s, flags=re.S)
        if m_import_from is not None:
            mod_name = re.strip_group(m_import_from, 1)
            names_txt = re.strip_group(m_import_from, 2)
            if mod_name == "typing":
                # `from typing import ...` は注釈解決専用で、EAST には出力しない。
                continue
            if mod_name == "dataclasses":
                # `from dataclasses import ...` は decorator 解決専用で、EAST には出力しない。
                if names_txt != "*":
                    raw_parts_dc: list[str] = []
                    for p in names_txt.split(","):
                        p2: str = p.strip()
                        if p2 != "":
                            raw_parts_dc.append(p2)
                    for part in raw_parts_dc:
                        parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=False)
                        if parsed_alias is None:
                            continue
                        sym_name, as_name_txt = parsed_alias
                        bind_name_dc = as_name_txt if as_name_txt != "" else sym_name
                        _sh_register_import_symbol(
                            _SH_IMPORT_SYMBOLS,
                            bind_name_dc,
                            mod_name,
                            sym_name,
                            make_import_symbol_binding=_sh_make_import_symbol_binding,
                        )
                continue
            if mod_name == "__future__":
                if names_txt == "*":
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="from __future__ import * is not supported",
                        source_span=_sh_span(ln_no, 0, len(ln_txt)),
                        hint="Use `from __future__ import annotations` only.",
                    )
                raw_parts: list[str] = []
                for p in names_txt.split(","):
                    p2: str = p.strip()
                    if p2 != "":
                        raw_parts.append(p2)
                if len(raw_parts) == 0:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="from-import statement has no symbol names",
                        source_span=_sh_span(ln_no, 0, len(ln_txt)),
                        hint="Use `from module import name` form.",
                    )
                for part in raw_parts:
                    parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=False)
                    if parsed_alias is None:
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message=f"unsupported from-import clause: {part}",
                            source_span=_sh_span(ln_no, 0, len(ln_txt)),
                            hint="Use `from module import name` or `... as alias`.",
                        )
                    sym_name, as_name_txt = parsed_alias
                    if sym_name != "annotations" or as_name_txt != "":
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message=f"unsupported __future__ feature: {part}",
                            source_span=_sh_span(ln_no, 0, len(ln_txt)),
                            hint="Only `from __future__ import annotations` is supported.",
                        )
                # `from __future__ import annotations` is frontend-only and does not appear in EAST.
                continue
            if names_txt == "*":
                pending_blank_count = _sh_push_stmt_with_trivia(
                    stmts,
                    pending_leading_trivia,
                    pending_blank_count,
                    _sh_make_import_from_stmt(
                        _sh_make_stmt_node,
                        _sh_stmt_span(merged_line_end, ln_no, 0, len(ln_txt)),
                        mod_name,
                        [_sh_make_import_alias("*")],
                    ),
                )
                continue
            raw_parts: list[str] = []
            for p in names_txt.split(","):
                p2: str = p.strip()
                if p2 != "":
                    raw_parts.append(p2)
            if len(raw_parts) == 0:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message="from-import statement has no symbol names",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Use `from module import name` form.",
                )
            aliases: list[dict[str, str | None]] = []
            for part in raw_parts:
                parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=False)
                if parsed_alias is None:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"unsupported from-import clause: {part}",
                        source_span=_sh_span(ln_no, 0, len(ln_txt)),
                        hint="Use `from module import name` or `... as alias`.",
                    )
                sym_name, as_name_txt = parsed_alias
                bind_name = as_name_txt if as_name_txt != "" else sym_name
                _sh_register_import_symbol(
                    _SH_IMPORT_SYMBOLS,
                    bind_name,
                    mod_name,
                    sym_name,
                    make_import_symbol_binding=_sh_make_import_symbol_binding,
                )
                if _sh_is_host_only_alias(bind_name):
                    continue
                aliases.append(_sh_make_import_alias(sym_name, as_name_txt if as_name_txt != "" else None))
            if len(aliases) > 0:
                pending_blank_count = _sh_push_stmt_with_trivia(
                    stmts,
                    pending_leading_trivia,
                    pending_blank_count,
                    _sh_make_import_from_stmt(
                        _sh_make_stmt_node,
                        _sh_stmt_span(merged_line_end, ln_no, 0, len(ln_txt)),
                        mod_name,
                        aliases,
                    ),
                )
            continue

        if s.startswith("with ") and s.endswith(":"):
            m_with: re.Match | None = re.match(r"^with\s+(.+)\s+as\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*$", s, flags=re.S)
            if m_with is None:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse with statement: {s}",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Use `with expr as name:` form.",
                )
            ctx_txt = re.strip_group(m_with, 1)
            as_name = re.strip_group(m_with, 2)
            ctx_col = ln_txt.find(ctx_txt)
            as_col = ln_txt.find(as_name, ctx_col + len(ctx_txt))
            ctx_expr = _sh_parse_expr_lowered(ctx_txt, ln_no=ln_no, col=ctx_col, name_types=dict(name_types))
            name_types[as_name] = str(ctx_expr.get("resolved_type", "unknown"))
            body_block, j = _sh_collect_indented_block(body_lines, i + 1, indent)
            if len(body_block) == 0:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"with body is missing in '{scope_label}'",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Add indented with-body.",
                )
            assign_stmt = _sh_make_assign_stmt(
                _sh_stmt_span(merged_line_end, ln_no, as_col, len(ln_txt)),
                _sh_make_name_expr(
                    _sh_span(ln_no, as_col, as_col + len(as_name)),
                    as_name,
                    resolved_type=str(ctx_expr.get("resolved_type", "unknown")),
                ),
                ctx_expr,
                declare=True,
                declare_init=True,
                decl_type=str(ctx_expr.get("resolved_type", "unknown")),
            )
            close_expr = _sh_parse_expr_lowered(f"{as_name}.close()", ln_no=ln_no, col=as_col, name_types=dict(name_types))
            try_stmt = _sh_make_try_stmt(
                _sh_block_end_span(body_lines, ln_no, ln_txt.find("with "), len(ln_txt), j),
                _sh_parse_stmt_block(body_block, name_types=dict(name_types), scope_label=scope_label),
                finalbody=[_sh_make_expr_stmt(close_expr, _sh_stmt_span(merged_line_end, ln_no, as_col, len(ln_txt)))],
            )
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, assign_stmt)
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, try_stmt)
            skip = j - i - 1
            continue

        if s.startswith("while ") and s.endswith(":"):
            cond_txt = s[len("while ") : -1].strip()
            cond_col = ln_txt.find(cond_txt)
            cond_expr = _sh_parse_expr_lowered(cond_txt, ln_no=ln_no, col=cond_col, name_types=dict(name_types))
            body_block, j = _sh_collect_indented_block(body_lines, i + 1, indent)
            if len(body_block) == 0:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"while body is missing in '{scope_label}'",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Add indented while-body.",
                )
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                _sh_make_while_stmt(
                    _sh_block_end_span(body_lines, ln_no, 0, len(ln_txt), j),
                    cond_expr,
                    _sh_parse_stmt_block(body_block, name_types=dict(name_types), scope_label=scope_label),
                ),
            )
            skip = j - i - 1
            continue

        if s == "try:":
            try_body, j = _sh_collect_indented_block(body_lines, i + 1, indent)
            if len(try_body) == 0:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"try body is missing in '{scope_label}'",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Add indented try-body.",
                )
            handlers: list[dict[str, Any]] = []
            finalbody: list[dict[str, Any]] = []
            while j < len(body_lines):
                h_no, h_ln = body_lines[j]
                h_s = h_ln.strip()
                h_indent = len(h_ln) - len(h_ln.lstrip(" "))
                if h_indent != indent:
                    break
                exc_clause = _sh_parse_except_clause(h_s)
                if exc_clause is not None:
                    ex_type_txt, ex_name = exc_clause
                    ex_type_col = h_ln.find(ex_type_txt)
                    if ex_type_col < 0:
                        ex_type_col = h_ln.find("except")
                        if ex_type_col < 0:
                            ex_type_col = 0
                    h_body, k = _sh_collect_indented_block(body_lines, j + 1, indent)
                    handlers.append(
                        _sh_make_except_handler(
                            _sh_parse_expr_lowered(
                                ex_type_txt,
                                ln_no=h_no,
                                col=ex_type_col,
                                name_types=dict(name_types),
                            ),
                            _sh_parse_stmt_block(h_body, name_types=dict(name_types), scope_label=scope_label),
                            name=ex_name,
                        )
                    )
                    j = k
                    continue
                if h_s == "finally:":
                    f_body, k = _sh_collect_indented_block(body_lines, j + 1, indent)
                    finalbody = _sh_parse_stmt_block(f_body, name_types=dict(name_types), scope_label=scope_label)
                    j = k
                    continue
                break
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                _sh_make_try_stmt(
                    _sh_block_end_span(body_lines, ln_no, 0, len(ln_txt), j),
                    _sh_parse_stmt_block(try_body, name_types=dict(name_types), scope_label=scope_label),
                    handlers=handlers,
                    finalbody=finalbody,
                ),
            )
            skip = j - i - 1
            continue

        if s.startswith("raise "):
            expr_txt = s[len("raise ") :].strip()
            expr_col = ln_txt.find(expr_txt)
            cause_expr = None
            cause_split = _sh_split_top_level_from(expr_txt)
            if cause_split is not None:
                exc_txt, cause_txt = cause_split
                expr_txt = exc_txt
                expr_col = ln_txt.find(expr_txt)
                cause_col = ln_txt.find(cause_txt)
                cause_expr = _sh_parse_expr_lowered(cause_txt, ln_no=ln_no, col=cause_col, name_types=dict(name_types))
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, 
                _sh_make_raise_stmt(
                    _sh_stmt_span(merged_line_end, ln_no, ln_txt.find("raise "), len(ln_txt)),
                    _sh_parse_expr_lowered(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types)),
                    cause=cause_expr,
                )
            )
            continue

        if s == "pass":
            pass_stmt = _sh_make_pass_stmt(_sh_stmt_span(merged_line_end, ln_no, indent, indent + 4))
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, pass_stmt)
            continue

        if s == "return":
            rcol = ln_txt.find("return")
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, 
                _sh_make_return_stmt(_sh_stmt_span(merged_line_end, ln_no, rcol, len(ln_txt)))
            )
            continue

        if s.startswith("return "):
            rcol = ln_txt.find("return ")
            expr_txt = s[len("return ") :].strip()
            expr_col = ln_txt.find(expr_txt)
            if expr_col < 0:
                expr_col = rcol + len("return ")
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, 
                _sh_make_return_stmt(
                    _sh_stmt_span(merged_line_end, ln_no, rcol, len(ln_txt)),
                    _sh_parse_expr_lowered(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types)),
                )
            )
            continue

        if s == "yield":
            ycol = ln_txt.find("yield")
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                _sh_make_yield_stmt(_sh_stmt_span(merged_line_end, ln_no, ycol, len(ln_txt))),
            )
            continue

        if s.startswith("yield "):
            ycol = ln_txt.find("yield ")
            expr_txt = s[len("yield ") :].strip()
            expr_col = ln_txt.find(expr_txt)
            if expr_col < 0:
                expr_col = ycol + len("yield ")
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                _sh_make_yield_stmt(
                    _sh_stmt_span(merged_line_end, ln_no, ycol, len(ln_txt)),
                    _sh_parse_expr_lowered(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types)),
                ),
            )
            continue

        parsed_typed = _sh_parse_typed_binding(s, allow_dotted_name=True)
        if parsed_typed is not None:
            typed_target, typed_ann, typed_default = parsed_typed
        else:
            typed_target, typed_ann, typed_default = "", "", ""
        if parsed_typed is not None and typed_default == "":
            target_txt = typed_target
            ann_txt = typed_ann
            ann = _sh_ann_to_type(ann_txt, type_aliases=_SH_TYPE_ALIASES)
            ann_expr = _sh_ann_to_type_expr(ann, type_aliases=_SH_TYPE_ALIASES)
            target_col = ln_txt.find(target_txt)
            target_expr = _sh_parse_expr_lowered(target_txt, ln_no=ln_no, col=target_col, name_types=dict(name_types))
            _maybe_bind_self_field(target_expr, None, explicit=ann)
            if isinstance(target_expr, dict):
                target_expr["type_expr"] = ann_expr
            if isinstance(target_expr, dict) and target_expr.get("kind") == "Name":
                name_types[str(target_expr.get("id", ""))] = ann
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                _sh_make_ann_assign_stmt(
                    _sh_stmt_span(merged_line_end, ln_no, target_col, len(ln_txt)),
                    target_expr,
                    ann,
                    annotation_type_expr=ann_expr,
                    value=None,
                    declare=True,
                    decl_type=ann,
                    decl_type_expr=ann_expr,
                ),
            )
            continue

        if parsed_typed is not None and typed_default != "":
            target_txt = typed_target
            ann_txt = typed_ann
            expr_txt = typed_default
            ann = _sh_ann_to_type(ann_txt, type_aliases=_SH_TYPE_ALIASES)
            ann_expr = _sh_ann_to_type_expr(ann, type_aliases=_SH_TYPE_ALIASES)
            expr_col = ln_txt.find(expr_txt)
            val_expr = _sh_parse_expr_lowered(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types))
            target_col = ln_txt.find(target_txt)
            target_expr = _sh_parse_expr_lowered(target_txt, ln_no=ln_no, col=target_col, name_types=dict(name_types))
            _maybe_bind_self_field(target_expr, None, explicit=ann)
            if isinstance(target_expr, dict):
                target_expr["type_expr"] = ann_expr
            if isinstance(target_expr, dict) and target_expr.get("kind") == "Name":
                name_types[str(target_expr.get("id", ""))] = ann
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                _sh_make_ann_assign_stmt(
                    _sh_stmt_span(merged_line_end, ln_no, target_col, len(ln_txt)),
                    target_expr,
                    ann,
                    annotation_type_expr=ann_expr,
                    value=val_expr,
                    declare=True,
                    decl_type=ann,
                    decl_type_expr=ann_expr,
                ),
            )
            continue

        parsed_aug = _sh_parse_augassign(s)
        if parsed_aug is not None:
            target_txt, aug_op, expr_txt = parsed_aug
            op_map = {
                "+=": "Add",
                "-=": "Sub",
                "*=": "Mult",
                "/=": "Div",
                "//=": "FloorDiv",
                "%=": "Mod",
                "&=": "BitAnd",
                "|=": "BitOr",
                "^=": "BitXor",
                "<<=": "LShift",
                ">>=": "RShift",
            }
            expr_col = ln_txt.find(expr_txt)
            target_col = ln_txt.find(target_txt)
            target_expr = _sh_parse_expr_lowered(target_txt, ln_no=ln_no, col=target_col, name_types=dict(name_types))
            val_expr = _sh_parse_expr_lowered(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types))
            target_ty = "unknown"
            if isinstance(target_expr, dict) and target_expr.get("kind") == "Name":
                target_ty = name_types.get(str(target_expr.get("id", "")), "unknown")
            decl_type: str | None = None
            if target_ty != "unknown":
                decl_type = target_ty
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, 
                _sh_make_augassign_stmt(
                    _sh_stmt_span(merged_line_end, ln_no, target_col, len(ln_txt)),
                    target_expr,
                    op_map[aug_op],
                    val_expr,
                    declare=False,
                    decl_type=decl_type,
                )
            )
            continue

        m_tasg: re.Match | None = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$", s)
        if m_tasg is not None:
            n1 = re.group(m_tasg, 1)
            n2 = re.group(m_tasg, 2)
            expr_txt = re.strip_group(m_tasg, 3)
            expr_col = ln_txt.find(expr_txt)
            rhs = _sh_parse_expr_lowered(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types))
            c1 = ln_txt.find(n1)
            c2 = ln_txt.find(n2, c1 + len(n1))
            if (
                isinstance(rhs, dict)
                and rhs.get("kind") == "Tuple"
                and len(rhs.get("elements", [])) == 2
                and isinstance(rhs.get("elements")[0], dict)
                and isinstance(rhs.get("elements")[1], dict)
                and rhs.get("elements")[0].get("kind") == "Name"
                and rhs.get("elements")[1].get("kind") == "Name"
                and str(rhs.get("elements")[0].get("id", "")) == n2
                and str(rhs.get("elements")[1].get("id", "")) == n1
            ):
                pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, 
                    _sh_make_swap_stmt(
                        _sh_stmt_span(merged_line_end, ln_no, c1, len(ln_txt)),
                        _sh_make_name_expr(
                            _sh_span(ln_no, c1, c1 + len(n1)),
                            n1,
                            resolved_type=name_types.get(n1, "unknown"),
                        ),
                        _sh_make_name_expr(
                            _sh_span(ln_no, c2, c2 + len(n2)),
                            n2,
                            resolved_type=name_types.get(n2, "unknown"),
                        ),
                    )
                )
                continue
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                _sh_make_tuple_destructure_assign_stmt(
                    _sh_stmt_span(merged_line_end, ln_no, c1, len(ln_txt)),
                    line_no=ln_no,
                    first_name=n1,
                    first_col=c1,
                    first_type=name_types.get(n1, "unknown"),
                    second_name=n2,
                    second_col=c2,
                    second_type=name_types.get(n2, "unknown"),
                    value=rhs,
                ),
            )
            continue

        asg_split = _sh_split_top_level_assign(s)
        if asg_split is not None:
            target_txt, expr_txt = asg_split
            expr_col = ln_txt.find(expr_txt)
            target_col = ln_txt.find(target_txt)
            target_expr = _sh_parse_expr_lowered(target_txt, ln_no=ln_no, col=target_col, name_types=dict(name_types))
            val_expr = _sh_parse_expr_lowered(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types))
            decl_type = val_expr.get("resolved_type", "unknown")
            _maybe_bind_self_field(target_expr, str(decl_type) if isinstance(decl_type, str) else "")
            if isinstance(target_expr, dict) and target_expr.get("kind") == "Name":
                nm = str(target_expr.get("id", ""))
                if nm != "":
                    name_types[nm] = str(decl_type)
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                _sh_make_assign_stmt(
                    _sh_stmt_span(merged_line_end, ln_no, target_col, len(ln_txt)),
                    target_expr,
                    val_expr,
                    declare=True,
                    declare_init=True,
                    decl_type=str(decl_type),
                ),
            )
            continue

        expr_col = len(ln_txt) - len(ln_txt.lstrip(" "))
        expr_stmt = _sh_parse_expr_lowered(s, ln_no=ln_no, col=expr_col, name_types=dict(name_types))
        pending_blank_count = _sh_push_stmt_with_trivia(
            stmts,
            pending_leading_trivia,
            pending_blank_count,
            _sh_make_expr_stmt(expr_stmt, _sh_stmt_span(merged_line_end, ln_no, expr_col, len(ln_txt))),
        )
    return stmts


def _sh_parse_stmt_block(body_lines: list[tuple[int, str]], *, name_types: dict[str, str], scope_label: str) -> list[dict[str, Any]]:
    """読み取り専用引数で受け取り、mutable 実体へコピーを渡す。"""
    body_lines_copy: list[tuple[int, str]] = list(body_lines)
    name_types_copy: dict[str, str] = dict(name_types)
    return _sh_parse_stmt_block_mutable(body_lines_copy, name_types=name_types_copy, scope_label=scope_label)


def convert_source_to_east_self_hosted(source: str, filename: str) -> dict[str, Any]:
    """Python ソースを self-hosted パーサで EAST Module に変換する。"""
    source = _sh_strip_utf8_bom(source)
    lines = source.splitlines()
    leading_file_comments: list[str] = []
    leading_file_trivia: list[dict[str, Any]] = []
    for ln in lines:
        s = ln.strip()
        if s == "":
            if len(leading_file_comments) > 0:
                leading_file_trivia.append(_sh_make_trivia_blank(1))
            continue
        if s.startswith("#"):
            text = s[1:].lstrip()
            leading_file_comments.append(text)
            leading_file_trivia.append(_sh_make_trivia_comment(text))
            continue
        break

    class_method_return_types: dict[str, dict[str, str]] = {}
    class_base: dict[str, str | None] = {}
    fn_returns: dict[str, str] = {}
    pre_import_symbol_bindings: dict[str, dict[str, str]] = {}
    pre_import_module_bindings: dict[str, str] = {}
    type_aliases: dict[str, str] = _sh_default_type_aliases()

    cur_cls: str | None = None
    cur_cls_indent = 0
    for ln_no, ln in enumerate(lines, start=1):
        s = _sh_strip_inline_comment(ln.strip())
        if s == "":
            continue
        indent = len(ln) - len(ln.lstrip(" "))
        if cur_cls is not None and indent <= cur_cls_indent and not s.startswith("#"):
            cur_cls = None
        if cur_cls is None and indent == 0:
            m_import = re.match(r"^import\s+(.+)$", s, flags=re.S)
            if m_import is not None:
                names_txt = re.strip_group(m_import, 1)
                raw_parts: list[str] = []
                for p in names_txt.split(","):
                    p2 = p.strip()
                    if p2 != "":
                        raw_parts.append(p2)
                for part in raw_parts:
                    parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=True)
                    if parsed_alias is None:
                        continue
                    mod_name, as_name_txt = parsed_alias
                    bind_name = as_name_txt if as_name_txt != "" else mod_name.split(".")[0]
                    if bind_name != "":
                        pre_import_module_bindings[bind_name] = mod_name
                continue
            m_import_from = re.match(r"^from\s+([A-Za-z_][A-Za-z0-9_\.]*)\s+import\s+(.+)$", s, flags=re.S)
            if m_import_from is not None:
                mod_txt = re.strip_group(m_import_from, 1)
                names_txt = re.strip_group(m_import_from, 2)
                if names_txt != "*":
                    raw_parts: list[str] = []
                    for p in names_txt.split(","):
                        p2 = p.strip()
                        if p2 != "":
                            raw_parts.append(p2)
                    for part in raw_parts:
                        parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=False)
                        if parsed_alias is None:
                            continue
                        sym_txt, as_name = parsed_alias
                        alias_name = as_name if as_name != "" else sym_txt
                        if alias_name != "":
                            pre_import_symbol_bindings[alias_name] = _sh_make_import_symbol_binding(
                                mod_txt,
                                sym_txt,
                            )
                if mod_txt == "typing":
                    raw_parts: list[str] = []
                    for p in names_txt.split(","):
                        p2: str = p.strip()
                        if p2 != "":
                            raw_parts.append(p2)
                    for part in raw_parts:
                        parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=False)
                        if parsed_alias is None:
                            continue
                        sym_txt, as_name = parsed_alias
                        alias_name = as_name if as_name != "" else sym_txt
                        target = _sh_typing_alias_to_type_name(sym_txt)
                        if target != "":
                            type_aliases[alias_name] = target
                continue
            asg_pre = _sh_split_top_level_assign(s)
            if asg_pre is not None:
                pre_left, pre_right = asg_pre
                _sh_register_type_alias(type_aliases, pre_left, pre_right)
                continue
        cls_hdr_info = _sh_parse_class_header_base_list(s, split_top_commas=_sh_split_top_commas)
        if cls_hdr_info is not None:
            cls_name_info, bases_info = cls_hdr_info
            if len(bases_info) > 1:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"multiple inheritance is not supported: class '{cls_name_info}'",
                    source_span=_sh_span(ln_no, 0, len(ln)),
                    hint="Use single inheritance (`class Child(Base):`) or composition.",
                )
        cls_hdr = _sh_parse_class_header(s, split_top_commas=_sh_split_top_commas)
        if cls_hdr is not None:
            cur_cls_name, cur_base = cls_hdr
            cur_cls = cur_cls_name
            cur_cls_indent = indent
            if cur_base != "":
                class_base[cur_cls_name] = cur_base
            else:
                class_base[cur_cls_name] = None
            if cur_cls_name not in class_method_return_types:
                empty_methods: dict[str, str] = {}
                class_method_return_types[cur_cls_name] = empty_methods
            continue
        if cur_cls is None:
            sig_line_scan, _inline_scan = _sh_split_def_header_and_inline_stmt(s)
            sig = _sh_parse_def_sig(
                ln_no,
                sig_line_scan,
                type_aliases=_SH_TYPE_ALIASES,
                make_east_build_error=_make_east_build_error,
                make_span=_sh_span,
                make_def_sig_info=_sh_make_def_sig_info,
            )
            if sig is not None:
                fn_returns[str(sig["name"])] = str(sig["ret"])
            continue
        cur_cls_name: str = cur_cls
        sig_line_scan, _inline_scan = _sh_split_def_header_and_inline_stmt(s)
        sig = _sh_parse_def_sig(
            ln_no,
            sig_line_scan,
            in_class=cur_cls_name,
            type_aliases=_SH_TYPE_ALIASES,
            make_east_build_error=_make_east_build_error,
            make_span=_sh_span,
            make_def_sig_info=_sh_make_def_sig_info,
        )
        if sig is not None:
            methods: dict[str, str] = class_method_return_types[cur_cls_name]
            methods[str(sig["name"])] = str(sig["ret"])
            class_method_return_types[cur_cls_name] = methods

    _sh_set_parse_context(fn_returns, class_method_return_types, class_base, type_aliases)
    _SH_IMPORT_SYMBOLS.clear()
    _SH_IMPORT_SYMBOLS.update(pre_import_symbol_bindings)
    _SH_IMPORT_MODULES.clear()
    _SH_IMPORT_MODULES.update(pre_import_module_bindings)

    body_items: list[dict[str, Any]] = []
    main_stmts: list[dict[str, Any]] = []
    import_module_bindings: dict[str, str] = {}
    import_symbol_bindings: dict[str, dict[str, str]] = {}
    import_bindings: list[dict[str, Any]] = []
    import_binding_names: set[str] = set()
    first_item_attached = False
    pending_dataclass = False
    pending_dataclass_options: dict[str, bool] = {}
    pending_top_level_decorators: list[str] = []
    sealed_families: set[str] = set()

    top_lines: list[tuple[int, str]] = []
    line_idx = 1
    while line_idx <= len(lines):
        top_lines.append((line_idx, lines[line_idx - 1]))
        line_idx += 1
    top_merged_lines, top_merged_end = _sh_merge_logical_lines(top_lines)
    top_merged_map: dict[int, str] = {}
    top_merged_index: dict[int, int] = {}
    for top_idx, top_pair in enumerate(top_merged_lines):
        top_ln_no, top_txt = top_pair
        top_merged_map[int(top_ln_no)] = str(top_txt)
        top_merged_index[int(top_ln_no)] = int(top_idx)
    i = 1
    while i <= len(lines):
        ln_obj = top_merged_map.get(i, lines[i - 1])
        ln: str = str(ln_obj)
        logical_end_pair = top_merged_end.get(i, (i, len(lines[i - 1])))
        logical_end = int(logical_end_pair[0])
        raw_s = ln.strip()
        s = _sh_strip_inline_comment(raw_s)
        _sh_raise_if_trailing_stmt_terminator(
            s,
            line_no=i,
            line_text=ln,
            make_east_build_error=_make_east_build_error,
            make_span=_sh_span,
        )
        if s == "" or s.startswith("#"):
            i += 1
            continue
        if ln.startswith(" "):
            i += 1
            continue
        if s.startswith("@"):
            dec_name = s[1:].strip()
            if _sh_is_dataclass_decorator(
                dec_name,
                import_module_bindings=import_module_bindings,
                import_symbol_bindings=import_symbol_bindings,
            ):
                pending_dataclass = True
                _dec_head, args_txt = _sh_parse_decorator_head_and_args(dec_name)
                if args_txt != "":
                    parsed_opts = _sh_parse_dataclass_decorator_options(
                        args_txt,
                        line_no=i,
                        line_text=ln,
                        split_top_commas=_sh_split_top_commas,
                        split_top_level_assign=_sh_split_top_level_assign,
                        is_identifier=_sh_is_identifier,
                        make_east_build_error=_make_east_build_error,
                        make_span=_sh_span,
                    )
                    for k_opt, v_opt in parsed_opts.items():
                        pending_dataclass_options[k_opt] = v_opt
            elif dec_name != "":
                pending_top_level_decorators.append(dec_name)
            i += 1
            continue

        ln_main = s
        is_main_guard = False
        if ln_main.startswith("if ") and ln_main.endswith(":"):
            cond = ln_main[3:-1].strip()
            if cond in {
                "__name__ == \"__main__\"",
                "__name__ == '__main__'",
                "\"__main__\" == __name__",
                "'__main__' == __name__",
            }:
                is_main_guard = True
        if is_main_guard:
            block: list[tuple[int, str]] = []
            if i < len(top_lines):
                block, block_end_idx = _sh_collect_indented_block(top_lines, i, 0)
                j = block_end_idx + 1
            main_name_types: dict[str, str] = {}
            main_stmts = _sh_parse_stmt_block(block, name_types=main_name_types, scope_label="__main__")
            i = j
            continue
        sig_line_full: str = s
        sig_line, inline_fn_stmt = _sh_split_def_header_and_inline_stmt(sig_line_full)
        sig_end_line = logical_end
        sig = _sh_parse_def_sig(
            i,
            sig_line,
            type_aliases=_SH_TYPE_ALIASES,
            make_east_build_error=_make_east_build_error,
            make_span=_sh_span,
            make_def_sig_info=_sh_make_def_sig_info,
        )
        if sig is not None:
            fn_name = str(sig["name"])
            fn_ret = str(sig["ret"])
            arg_types: dict[str, str] = dict(sig["arg_types"])
            arg_type_exprs_obj: Any = sig.get("arg_type_exprs")
            arg_type_exprs: dict[str, Any] = arg_type_exprs_obj if isinstance(arg_type_exprs_obj, dict) else {}
            arg_order: list[str] = list(sig["arg_order"])
            arg_defaults_raw_obj: Any = sig.get("arg_defaults")
            arg_defaults_raw: dict[str, Any] = arg_defaults_raw_obj if isinstance(arg_defaults_raw_obj, dict) else {}
            block: list[tuple[int, str]] = []
            j = sig_end_line + 1
            if inline_fn_stmt != "":
                block = [(i, "    " + inline_fn_stmt)]
                j = i + 1
            else:
                block, block_end_idx = _sh_collect_indented_block(top_lines, j - 1, 0)
                j = block_end_idx + 1
                if len(block) == 0:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"self_hosted parser requires non-empty function body '{fn_name}'",
                        source_span=_sh_span(i, 0, len(sig_line)),
                        hint="Add return or assignment statements in function body.",
                    )
            stmts = _sh_parse_stmt_block(block, name_types=dict(arg_types), scope_label=fn_name)
            docstring, stmts = _sh_extract_leading_docstring(stmts)
            fn_ret = _sh_infer_return_type_for_untyped_def(fn_ret, stmts)
            yield_types = _sh_collect_yield_value_types(stmts)
            is_generator = len(yield_types) > 0
            fn_ret_effective = fn_ret
            yield_value_type = "unknown"
            if is_generator:
                fn_ret_effective, yield_value_type = _sh_make_generator_return_type(fn_ret, yield_types)
            fn_ret_type_expr = _sh_ann_to_type_expr(fn_ret_effective, type_aliases=_SH_TYPE_ALIASES)
            arg_defaults: dict[str, Any] = {}
            arg_index_map: dict[str, int] = {}
            for arg_pos, arg_name in enumerate(arg_order):
                arg_index_map[arg_name] = int(arg_pos)
            arg_usage_map = _sh_build_arg_usage_map(arg_order, arg_types, stmts)
            for arg_name in arg_order:
                if arg_name in arg_defaults_raw:
                    default_obj: Any = arg_defaults_raw[arg_name]
                    default_txt: str = str(default_obj).strip()
                    if default_txt != "":
                        default_col = sig_line.find(default_txt)
                        if default_col < 0:
                            default_col = 0
                        arg_defaults[arg_name] = _sh_parse_expr_lowered(
                            default_txt,
                            ln_no=i,
                            col=default_col,
                            name_types=dict(arg_types),
                        )
            fn_decorators = list(pending_top_level_decorators)
            pending_top_level_decorators = []
            for decorator_text in fn_decorators:
                if _sh_is_sealed_decorator(decorator_text):
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="@sealed is supported on top-level classes only",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Move `@sealed` to a family class declaration.",
                    )
            runtime_abi_meta, template_meta = _sh_collect_function_runtime_decl_metadata(
                fn_decorators,
                arg_order=arg_order,
                import_module_bindings=import_module_bindings,
                import_symbol_bindings=import_symbol_bindings,
                line_no=i,
                line_text=ln,
                is_abi_decorator=_sh_is_abi_decorator,
                is_template_decorator=_sh_is_template_decorator,
                parse_decorator_head_and_args=_sh_parse_decorator_head_and_args,
                split_top_commas=_sh_split_top_commas,
                split_top_level_assign=_sh_split_top_level_assign,
                split_top_level_colon=_sh_split_top_level_colon,
                is_identifier=_sh_is_identifier,
                runtime_abi_arg_modes=_SH_RUNTIME_ABI_ARG_MODES,
                runtime_abi_ret_modes=_SH_RUNTIME_ABI_RET_MODES,
                runtime_abi_mode_aliases=_SH_RUNTIME_ABI_MODE_ALIASES,
                template_scope=_SH_TEMPLATE_SCOPE,
                template_instantiation_mode=_SH_TEMPLATE_INSTANTIATION_MODE,
                make_east_build_error=_make_east_build_error,
                make_span=_sh_span,
            )
            item = _sh_make_function_def_stmt(
                fn_name,
                _sh_block_end_span(block, i, 0, len(ln), len(block)),
                arg_types,
                arg_order,
                fn_ret_effective,
                stmts,
                arg_type_exprs=arg_type_exprs,
                arg_defaults=arg_defaults,
                arg_index=arg_index_map,
                return_type_expr=fn_ret_type_expr,
                arg_usage=arg_usage_map,
                decorators=list(fn_decorators) if len(fn_decorators) > 0 else None,
                leading_comments=[],
                leading_trivia=[],
                docstring=docstring,
                is_generator=is_generator,
                yield_value_type=yield_value_type,
            )
            if runtime_abi_meta is not None or template_meta is not None:
                item["meta"] = _sh_make_decl_meta(
                    runtime_abi_v1=runtime_abi_meta,
                    template_v1=template_meta,
                )
            fn_returns[fn_name] = fn_ret_effective
            _SH_FN_RETURNS[fn_name] = fn_ret_effective
            if not first_item_attached:
                item["leading_comments"] = list(leading_file_comments)
                item["leading_trivia"] = list(leading_file_trivia)
                first_item_attached = True
            body_items.append(item)
            i = j
            continue

        m_import: re.Match | None = re.match(r"^import\s+(.+)$", s, flags=re.S)
        if m_import is not None:
            names_txt = re.strip_group(m_import, 1)
            raw_parts: list[str] = []
            for p in names_txt.split(","):
                p2: str = p.strip()
                if p2 != "":
                    raw_parts.append(p2)
            if len(raw_parts) == 0:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message="import statement has no module names",
                    source_span=_sh_span(i, 0, len(ln)),
                    hint="Use `import module` or `import module as alias`.",
                )
            aliases: list[dict[str, str | None]] = []
            for part in raw_parts:
                parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=True)
                if parsed_alias is None:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"unsupported import clause: {part}",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Use `import module` or `import module as alias` form.",
                    )
                mod_name, as_name_txt = parsed_alias
                if mod_name == "typing":
                    # `typing` は注釈専用モジュールとして扱い、ImportBinding/EAST へは出さない。
                    continue
                if mod_name == "dataclasses":
                    # `dataclasses` は decorator 解決専用モジュールとして扱う（no-op import）。
                    bind_name_dc = as_name_txt if as_name_txt != "" else mod_name.split(".")[0]
                    import_module_bindings[bind_name_dc] = mod_name
                    _sh_register_import_module(_SH_IMPORT_MODULES, bind_name_dc, mod_name)
                    continue
                bind_name = as_name_txt if as_name_txt != "" else mod_name.split(".")[0]
                _sh_register_import_module(_SH_IMPORT_MODULES, bind_name, mod_name)
                if _sh_is_host_only_alias(bind_name):
                    continue
                _sh_append_import_binding(
                    import_bindings=import_bindings,
                    import_binding_names=import_binding_names,
                    module_id=mod_name,
                    export_name="",
                    local_name=bind_name,
                    binding_kind="module",
                    source_file=filename,
                    source_line=i,
                    make_east_build_error=_make_east_build_error,
                    make_span=_sh_span,
                    make_import_binding=_sh_make_import_binding,
                )
                aliases.append(_sh_make_import_alias(mod_name, as_name_txt if as_name_txt != "" else None))
            if len(aliases) > 0:
                body_items.append(_sh_make_import_stmt(_sh_make_stmt_node, _sh_span(i, 0, len(ln)), aliases))
            i = logical_end + 1
            continue
        if s.startswith("from "):
            marker = " import "
            pos = s.find(marker)
            if pos >= 0:
                mod_txt = s[5:pos].strip()
                if mod_txt.startswith("."):
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="relative import is not supported",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Use absolute import form: `from module import name`.",
                    )
        m_import_from: re.Match | None = re.match(r"^from\s+([A-Za-z_][A-Za-z0-9_\.]*)\s+import\s+(.+)$", s, flags=re.S)
        if m_import_from is not None:
            mod_name = re.strip_group(m_import_from, 1)
            names_txt = re.strip_group(m_import_from, 2)
            if mod_name == "typing":
                # `typing` の from-import は型別名解決にだけ使い、依存/AST には残さない。
                raw_parts_typing: list[str] = []
                if names_txt != "*":
                    for p in names_txt.split(","):
                        p2: str = p.strip()
                        if p2 != "":
                            raw_parts_typing.append(p2)
                for part in raw_parts_typing:
                    parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=False)
                    if parsed_alias is None:
                        continue
                    sym_name, as_name_txt = parsed_alias
                    alias_name = as_name_txt if as_name_txt != "" else sym_name
                    target = _sh_typing_alias_to_type_name(sym_name)
                    if target != "":
                        type_aliases[alias_name] = target
                i = logical_end + 1
                continue
            if mod_name == "dataclasses":
                # `from dataclasses import ...` は decorator 解決専用で、依存/AST には残さない。
                if names_txt == "*":
                    i = logical_end + 1
                    continue
                raw_parts_dc: list[str] = []
                for p in names_txt.split(","):
                    p2: str = p.strip()
                    if p2 != "":
                        raw_parts_dc.append(p2)
                if len(raw_parts_dc) == 0:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="from-import statement has no symbol names",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Use `from module import name` form.",
                    )
                for part in raw_parts_dc:
                    parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=False)
                    if parsed_alias is None:
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message=f"unsupported from-import clause: {part}",
                            source_span=_sh_span(i, 0, len(ln)),
                            hint="Use `from module import name` or `... as alias`.",
                        )
                    sym_name, as_name_txt = parsed_alias
                    bind_name_dc = as_name_txt if as_name_txt != "" else sym_name
                    import_symbol_bindings[bind_name_dc] = _sh_make_import_symbol_binding(
                        mod_name,
                        sym_name,
                    )
                    _sh_register_import_symbol(
                        _SH_IMPORT_SYMBOLS,
                        bind_name_dc,
                        mod_name,
                        sym_name,
                        make_import_symbol_binding=_sh_make_import_symbol_binding,
                    )
                i = logical_end + 1
                continue
            if mod_name == "__future__":
                if names_txt == "*":
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="from __future__ import * is not supported",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Use `from __future__ import annotations` only.",
                    )
                raw_parts: list[str] = []
                for p in names_txt.split(","):
                    p2: str = p.strip()
                    if p2 != "":
                        raw_parts.append(p2)
                if len(raw_parts) == 0:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="from-import statement has no symbol names",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Use `from module import name` form.",
                    )
                for part in raw_parts:
                    parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=False)
                    if parsed_alias is None:
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message=f"unsupported from-import clause: {part}",
                            source_span=_sh_span(i, 0, len(ln)),
                            hint="Use `from module import name` or `... as alias`.",
                        )
                    sym_name, as_name_txt = parsed_alias
                    if sym_name != "annotations" or as_name_txt != "":
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message=f"unsupported __future__ feature: {part}",
                            source_span=_sh_span(i, 0, len(ln)),
                            hint="Only `from __future__ import annotations` is supported.",
                        )
                # `from __future__ import annotations` is frontend-only and does not appear in EAST.
                i = logical_end + 1
                continue
            if names_txt == "*":
                wildcard_local = "__wildcard__" + mod_name.replace(".", "_")
                _sh_append_import_binding(
                    import_bindings=import_bindings,
                    import_binding_names=import_binding_names,
                    module_id=mod_name,
                    export_name="*",
                    local_name=wildcard_local,
                    binding_kind="wildcard",
                    source_file=filename,
                    source_line=i,
                    make_east_build_error=_make_east_build_error,
                    make_span=_sh_span,
                    make_import_binding=_sh_make_import_binding,
                )
                body_items.append(
                    _sh_make_import_from_stmt(
                        _sh_make_stmt_node,
                        _sh_span(i, 0, len(ln)),
                        mod_name,
                        [_sh_make_import_alias("*")],
                    )
                )
                i = logical_end + 1
                continue
            raw_parts: list[str] = []
            for p in names_txt.split(","):
                p2: str = p.strip()
                if p2 != "":
                    raw_parts.append(p2)
            if len(raw_parts) == 0:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message="from-import statement has no symbol names",
                    source_span=_sh_span(i, 0, len(ln)),
                    hint="Use `from module import name` form.",
                )
            aliases: list[dict[str, str | None]] = []
            for part in raw_parts:
                parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=False)
                if parsed_alias is None:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"unsupported from-import clause: {part}",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Use `from module import name` or `... as alias`.",
                )
                sym_name, as_name_txt = parsed_alias
                bind_name = as_name_txt if as_name_txt != "" else sym_name
                if _sh_is_host_only_alias(bind_name):
                    _sh_register_import_symbol(
                        _SH_IMPORT_SYMBOLS,
                        bind_name,
                        mod_name,
                        sym_name,
                        make_import_symbol_binding=_sh_make_import_symbol_binding,
                    )
                    continue
                # `Enum/IntEnum/IntFlag` は class 定義の lowering で吸収されるため、
                # 依存ヘッダ解決用の ImportBinding には積まない。
                if not (mod_name == "pytra.std.enum" and sym_name in {"Enum", "IntEnum", "IntFlag"}):
                    _sh_append_import_binding(
                        import_bindings=import_bindings,
                        import_binding_names=import_binding_names,
                        module_id=mod_name,
                        export_name=sym_name,
                        local_name=bind_name,
                        binding_kind="symbol",
                        source_file=filename,
                        source_line=i,
                        make_east_build_error=_make_east_build_error,
                        make_span=_sh_span,
                        make_import_binding=_sh_make_import_binding,
                    )
                    import_symbol_bindings[bind_name] = _sh_make_import_symbol_binding(
                        mod_name,
                        sym_name,
                    )
                    _sh_register_import_symbol(
                        _SH_IMPORT_SYMBOLS,
                        bind_name,
                        mod_name,
                        sym_name,
                        make_import_symbol_binding=_sh_make_import_symbol_binding,
                    )
                aliases.append(_sh_make_import_alias(sym_name, as_name_txt if as_name_txt != "" else None))
            if len(aliases) > 0:
                body_items.append(
                    _sh_make_import_from_stmt(
                        _sh_make_stmt_node,
                        _sh_span(i, 0, len(ln)),
                        mod_name,
                        aliases,
                    )
                )
            i = logical_end + 1
            continue
        cls_hdr_info = _sh_parse_class_header_base_list(s, split_top_commas=_sh_split_top_commas)
        if cls_hdr_info is not None:
            cls_name_info, bases_info = cls_hdr_info
            if len(bases_info) > 1:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"multiple inheritance is not supported: class '{cls_name_info}'",
                    source_span=_sh_span(i, 0, len(ln)),
                    hint="Use single inheritance (`class Child(Base):`) or composition.",
                )
        cls_hdr = _sh_parse_class_header(s, split_top_commas=_sh_split_top_commas)
        if cls_hdr is not None:
            class_decorators = list(pending_top_level_decorators)
            pending_top_level_decorators = []
            _sh_reject_runtime_decl_class_decorators(
                class_decorators,
                import_module_bindings=import_module_bindings,
                import_symbol_bindings=import_symbol_bindings,
                line_no=i,
                line_text=ln,
                is_abi_decorator=_sh_is_abi_decorator,
                is_template_decorator=_sh_is_template_decorator,
                make_east_build_error=_make_east_build_error,
                make_span=_sh_span,
            )
            cls_name, base = cls_hdr
            base_name = base
            is_enum_base = base_name in {"Enum", "IntEnum", "IntFlag"}
            cls_indent = len(ln) - len(ln.lstrip(" "))
            block: list[tuple[int, str]] = []
            j = i + 1
            while j <= len(lines):
                bl = lines[j - 1]
                if bl.strip() == "":
                    block.append((j, bl))
                    j += 1
                    continue
                bind = len(bl) - len(bl.lstrip(" "))
                if bind <= cls_indent:
                    break
                block.append((j, bl))
                j += 1
            if len(block) == 0:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser requires non-empty class body '{cls_name}'",
                    source_span=_sh_span(i, 0, len(ln)),
                    hint="Add field or method definitions.",
                )
            class_block, _class_line_end = _sh_merge_logical_lines(block)

            field_types: dict[str, str] = {}
            class_body: list[dict[str, Any]] = []
            pending_method_decorators: list[str] = []
            class_storage_hint_override = ""
            k = 0
            while k < len(class_block):
                ln_no_raw, ln_txt_raw = class_block[k]
                ln_no = int(ln_no_raw)
                ln_txt: str = str(ln_txt_raw)
                s2 = re.sub(r"\s+#.*$", "", ln_txt).strip()
                bind = len(ln_txt) - len(ln_txt.lstrip(" "))
                if s2 == "":
                    k += 1
                    continue
                if bind == cls_indent + 4 and s2.startswith("@"):
                    dec_name = s2[1:].strip()
                    if dec_name != "":
                        _sh_reject_runtime_decl_method_decorator(
                            dec_name,
                            import_module_bindings=import_module_bindings,
                            import_symbol_bindings=import_symbol_bindings,
                            line_no=ln_no,
                            line_text=ln_txt,
                            is_abi_decorator=_sh_is_abi_decorator,
                            is_template_decorator=_sh_is_template_decorator,
                            make_east_build_error=_make_east_build_error,
                            make_span=_sh_span,
                        )
                        if _sh_is_sealed_decorator(dec_name):
                            raise _make_east_build_error(
                                kind="unsupported_syntax",
                                message="@sealed is not supported on methods",
                                source_span=_sh_span(ln_no, 0, len(ln_txt)),
                                hint="Use @sealed on top-level family classes only.",
                            )
                        pending_method_decorators.append(dec_name)
                    k += 1
                    continue
                if bind == cls_indent + 4 and (s2.startswith('"""') or s2.startswith("'''")):
                    q = s2[:3]
                    if s2.count(q) >= 2 and len(s2) > 3:
                        k += 1
                        continue
                    k += 1
                    while k < len(class_block):
                        _doc_no, doc_txt = class_block[k]
                        if q in doc_txt:
                            k += 1
                            break
                        k += 1
                    continue
                if bind == cls_indent + 4:
                    if s2 == "pass":
                        class_body.append(
                            _sh_make_pass_stmt(_sh_span(ln_no, 0, len(ln_txt)))
                        )
                        k += 1
                        continue
                    if s2.startswith("__pytra_class_storage_hint__") or s2.startswith("__pytra_storage_hint__"):
                        parts = s2.split("=", 1)
                        if len(parts) == 2:
                            rhs = parts[1].strip()
                            if rhs in {'"value"', "'value'"}:
                                class_storage_hint_override = "value"
                                k += 1
                                continue
                            if rhs in {'"ref"', "'ref'"}:
                                class_storage_hint_override = "ref"
                                k += 1
                                continue
                    parsed_field = _sh_parse_typed_binding(s2, allow_dotted_name=False)
                    if parsed_field is not None:
                        fname, fty_txt, fdefault = parsed_field
                        fty = _sh_ann_to_type(fty_txt, type_aliases=_SH_TYPE_ALIASES)
                        fty_expr = _sh_ann_to_type_expr(fty, type_aliases=_SH_TYPE_ALIASES)
                        field_types[fname] = fty
                        val_node: dict[str, Any] | None = None
                        if fdefault != "":
                            fexpr_txt = fdefault.strip()
                            fexpr_col = ln_txt.find(fexpr_txt)
                            val_node = _sh_parse_expr_lowered(fexpr_txt, ln_no=ln_no, col=fexpr_col, name_types={})
                        class_body.append(
                            _sh_make_ann_assign_stmt(
                                _sh_span(ln_no, ln_txt.find(fname), len(ln_txt)),
                                _sh_make_name_expr(
                                    _sh_span(ln_no, ln_txt.find(fname), ln_txt.find(fname) + len(fname)),
                                    fname,
                                    resolved_type=fty,
                                    type_expr=fty_expr,
                                ),
                                fty,
                                annotation_type_expr=fty_expr,
                                value=val_node,
                                declare=True,
                                decl_type=fty,
                                decl_type_expr=fty_expr,
                            )
                        )
                        k += 1
                        continue
                    class_assign = _sh_split_top_level_assign(s2)
                    if class_assign is not None:
                        fname, fexpr_txt = class_assign
                        fname = fname.strip()
                        fexpr_txt = fexpr_txt.strip()
                        if _sh_is_identifier(fname) and fexpr_txt != "":
                            name_col = ln_txt.find(fname)
                            if name_col < 0:
                                name_col = 0
                            expr_col = ln_txt.find(fexpr_txt, name_col + len(fname))
                            if expr_col < 0:
                                expr_col = name_col + len(fname) + 1
                            val_node = _sh_parse_expr_lowered(fexpr_txt, ln_no=ln_no, col=expr_col, name_types={})
                            class_body.append(
                                _sh_make_assign_stmt(
                                    _sh_span(ln_no, name_col, len(ln_txt)),
                                    _sh_make_name_expr(
                                        _sh_span(ln_no, name_col, name_col + len(fname)),
                                        fname,
                                        resolved_type=str(val_node.get("resolved_type", "unknown")),
                                    ),
                                    val_node,
                                    declare=True,
                                    declare_init=True,
                                    decl_type=str(val_node.get("resolved_type", "unknown")),
                                )
                            )
                            k += 1
                            continue
                    if is_enum_base:
                        enum_assign = _sh_split_top_level_assign(s2)
                        if enum_assign is not None:
                            fname, fexpr_txt = enum_assign
                            fname = fname.strip()
                            fexpr_txt = fexpr_txt.strip()
                            if not _sh_is_identifier(fname) or fexpr_txt == "":
                                k += 1
                                continue
                            name_col = ln_txt.find(fname)
                            if name_col < 0:
                                name_col = 0
                            expr_col = ln_txt.find(fexpr_txt, name_col + len(fname))
                            if expr_col < 0:
                                expr_col = name_col + len(fname) + 1
                            val_node = _sh_parse_expr_lowered(fexpr_txt, ln_no=ln_no, col=expr_col, name_types={})
                            class_body.append(
                                _sh_make_assign_stmt(
                                    _sh_span(ln_no, name_col, len(ln_txt)),
                                    _sh_make_name_expr(
                                        _sh_span(ln_no, name_col, name_col + len(fname)),
                                        fname,
                                        resolved_type=str(val_node.get("resolved_type", "unknown")),
                                    ),
                                    val_node,
                                    declare=True,
                                    declare_init=True,
                                    decl_type=str(val_node.get("resolved_type", "unknown")),
                                )
                            )
                            k += 1
                            continue
                    sig_line, inline_method_stmt = _sh_split_def_header_and_inline_stmt(s2)
                    sig = _sh_parse_def_sig(
                        ln_no,
                        sig_line,
                        in_class=cls_name,
                        type_aliases=_SH_TYPE_ALIASES,
                        make_east_build_error=_make_east_build_error,
                        make_span=_sh_span,
                        make_def_sig_info=_sh_make_def_sig_info,
                    )
                    if sig is not None:
                        mname = str(sig["name"])
                        marg_types: dict[str, str] = dict(sig["arg_types"])
                        marg_order: list[str] = list(sig["arg_order"])
                        marg_defaults_raw_obj: Any = sig.get("arg_defaults")
                        marg_defaults_raw: dict[str, Any] = marg_defaults_raw_obj if isinstance(marg_defaults_raw_obj, dict) else {}
                        mret = str(sig["ret"])
                        method_block: list[tuple[int, str]] = []
                        m = k + 1
                        if inline_method_stmt != "":
                            method_block = [(ln_no, " " * (bind + 4) + inline_method_stmt)]
                        else:
                            while m < len(class_block):
                                n_pair: tuple[int, str] = class_block[m]
                                n_no: int = int(n_pair[0])
                                n_txt: str = str(n_pair[1])
                                if n_txt.strip() == "":
                                    t = m + 1
                                    while t < len(class_block) and class_block[t][1].strip() == "":
                                        t += 1
                                    if t >= len(class_block):
                                        break
                                    t_pair: tuple[int, str] = class_block[t]
                                    t_txt: str = str(t_pair[1])
                                    t_indent = len(t_txt) - len(t_txt.lstrip(" "))
                                    if t_indent <= bind:
                                        break
                                    method_block.append((n_no, n_txt))
                                    m += 1
                                    continue
                                n_indent = len(n_txt) - len(n_txt.lstrip(" "))
                                if n_indent <= bind:
                                    break
                                method_block.append((n_no, n_txt))
                                m += 1
                            if len(method_block) == 0:
                                raise _make_east_build_error(
                                    kind="unsupported_syntax",
                                    message=f"self_hosted parser requires non-empty method body '{cls_name}.{mname}'",
                                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                                    hint="Add method statements.",
                                )
                        local_types: dict[str, str] = dict(marg_types)
                        field_names: list[str] = list(field_types.keys())
                        for fnm in field_names:
                            fty: str = field_types[fnm]
                            local_types[fnm] = fty
                        stmts = _sh_parse_stmt_block(method_block, name_types=local_types, scope_label=f"{cls_name}.{mname}")
                        docstring, stmts = _sh_extract_leading_docstring(stmts)
                        mret = _sh_infer_return_type_for_untyped_def(mret, stmts)
                        yield_types = _sh_collect_yield_value_types(stmts)
                        is_generator = len(yield_types) > 0
                        mret_effective = mret
                        yield_value_type = "unknown"
                        if is_generator:
                            mret_effective, yield_value_type = _sh_make_generator_return_type(mret, yield_types)
                        marg_defaults: dict[str, Any] = {}
                        for arg_name in marg_order:
                            if arg_name in marg_defaults_raw:
                                default_obj: Any = marg_defaults_raw[arg_name]
                                default_txt: str = str(default_obj).strip()
                                if default_txt != "":
                                    default_col = ln_txt.find(default_txt)
                                    if default_col < 0:
                                        default_col = bind
                                    marg_defaults[arg_name] = _sh_parse_expr_lowered(
                                        default_txt,
                                        ln_no=ln_no,
                                        col=default_col,
                                        name_types=local_types,
                                    )
                        if mname == "__init__":
                            for st in stmts:
                                if st.get("kind") == "Assign":
                                    tgt = st.get("target")
                                    tgt_value: Any = None
                                    if isinstance(tgt, dict):
                                        tgt_value = tgt.get("value")
                                    tgt_value_dict: dict[str, Any] | None = None
                                    if isinstance(tgt_value, dict):
                                        tgt_value_dict = tgt_value
                                    if (
                                        isinstance(tgt, dict)
                                        and tgt.get("kind") == "Attribute"
                                        and tgt_value_dict is not None
                                        and tgt_value_dict.get("kind") == "Name"
                                        and tgt_value_dict.get("id") == "self"
                                    ):
                                        fname = str(tgt.get("attr", ""))
                                        if fname != "":
                                            st_value = st.get("value")
                                            st_value_rt: Any = None
                                            if isinstance(st_value, dict):
                                                st_value_rt = st_value.get("resolved_type")
                                            t_val: Any = st.get("decl_type")
                                            if not isinstance(t_val, str) or t_val == "":
                                                t_val = st_value_rt
                                            if isinstance(t_val, str) and t_val != "":
                                                field_types[fname] = t_val
                                if st.get("kind") == "AnnAssign":
                                    tgt = st.get("target")
                                    tgt_value: Any = None
                                    if isinstance(tgt, dict):
                                        tgt_value = tgt.get("value")
                                    tgt_value_dict: dict[str, Any] | None = None
                                    if isinstance(tgt_value, dict):
                                        tgt_value_dict = tgt_value
                                    if (
                                        isinstance(tgt, dict)
                                        and tgt.get("kind") == "Attribute"
                                        and tgt_value_dict is not None
                                        and tgt_value_dict.get("kind") == "Name"
                                        and tgt_value_dict.get("id") == "self"
                                    ):
                                        fname = str(tgt.get("attr", ""))
                                        ann = st.get("annotation")
                                        if fname != "" and isinstance(ann, str) and ann != "":
                                            field_types[fname] = ann
                        arg_index_map: dict[str, int] = {}
                        arg_pos = 0
                        while arg_pos < len(marg_order):
                            arg_name = marg_order[arg_pos]
                            arg_index_map[arg_name] = arg_pos
                            arg_pos += 1
                        arg_usage_map = _sh_build_arg_usage_map(marg_order, marg_types, stmts)
                        if cls_name in class_method_return_types:
                            methods_map = class_method_return_types[cls_name]
                            methods_map[mname] = mret_effective
                            class_method_return_types[cls_name] = methods_map
                        if cls_name in _SH_CLASS_METHOD_RETURNS:
                            methods_map2 = _SH_CLASS_METHOD_RETURNS[cls_name]
                            methods_map2[mname] = mret_effective
                            _SH_CLASS_METHOD_RETURNS[cls_name] = methods_map2
                        class_body.append(
                            _sh_make_function_def_stmt(
                                mname,
                                _sh_block_end_span(method_block, ln_no, bind, len(ln_txt), len(method_block)),
                                marg_types,
                                marg_order,
                                mret_effective,
                                stmts,
                                arg_defaults=marg_defaults,
                                arg_index=arg_index_map,
                                arg_usage=arg_usage_map,
                                decorators=list(pending_method_decorators),
                                docstring=docstring,
                                is_generator=is_generator,
                                yield_value_type=yield_value_type,
                            )
                        )
                        pending_method_decorators = []
                        k = m
                        continue
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse class statement: {s2}",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Use field annotation or method definitions in class body.",
                )

            storage_hint_override = class_storage_hint_override
            base_value: str | None = None
            if base != "":
                base_value = base
            class_meta = _sh_collect_nominal_adt_class_metadata(
                cls_name,
                base=base_value,
                decorators=class_decorators,
                is_dataclass=pending_dataclass,
                field_types=field_types,
                line_no=i,
                line_text=ln,
                sealed_families=sealed_families,
                is_sealed_decorator=_sh_is_sealed_decorator,
                parse_decorator_head_and_args=_sh_parse_decorator_head_and_args,
                make_east_build_error=_make_east_build_error,
                make_span=_sh_span,
            )

            cls_item = _sh_make_class_def_stmt(
                cls_name,
                _sh_block_end_span(block, i, 0, len(ln), len(block)),
                field_types,
                class_body,
                base=base_value,
                dataclass=pending_dataclass,
                dataclass_options=dict(pending_dataclass_options) if len(pending_dataclass_options) > 0 else None,
                decorators=list(class_decorators) if len(class_decorators) > 0 else None,
                meta=class_meta,
            )
            static_field_names: set[str] = set()
            if not pending_dataclass:
                for st in class_body:
                    if st.get("kind") == "AnnAssign":
                        tgt = st.get("target")
                        if isinstance(tgt, dict) and tgt.get("kind") == "Name":
                            fname = str(tgt.get("id", ""))
                            if fname != "":
                                static_field_names.add(fname)
            has_del = any(
                isinstance(st, dict) and st.get("kind") == "FunctionDef" and st.get("name") == "__del__"
                for st in class_body
            )
            instance_field_names: set[str] = set()
            for field_name in field_types.keys():
                if field_name not in static_field_names:
                    instance_field_names.add(field_name)
            # conservative hint:
            # - classes with instance state / __del__ / inheritance should keep reference semantics
            # - stateless, non-inherited classes can be value candidates
            if storage_hint_override != "":
                cls_item["class_storage_hint"] = storage_hint_override
            elif _sh_is_value_safe_dataclass_candidate(
                is_dataclass=pending_dataclass,
                base=base,
                has_del=has_del,
                class_body=class_body,
                field_types=field_types,
            ):
                cls_item["class_storage_hint"] = "value"
            elif base_name in {"Enum", "IntEnum", "IntFlag"}:
                cls_item["class_storage_hint"] = "value"
            elif len(instance_field_names) == 0 and not has_del and base == "":
                cls_item["class_storage_hint"] = "value"
            else:
                cls_item["class_storage_hint"] = "ref"
            if isinstance(class_meta, dict):
                nominal_adt_meta = class_meta.get("nominal_adt_v1")
                if isinstance(nominal_adt_meta, dict) and nominal_adt_meta.get("role") == "family":
                    sealed_families.add(cls_name)
            pending_dataclass = False
            pending_dataclass_options.clear()
            if not first_item_attached:
                cls_item["leading_comments"] = list(leading_file_comments)
                cls_item["leading_trivia"] = list(leading_file_trivia)
                first_item_attached = True
            body_items.append(cls_item)
            i = j
            continue

        if len(pending_top_level_decorators) > 0:
            for decorator_text in pending_top_level_decorators:
                if _sh_is_sealed_decorator(decorator_text):
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="@sealed is supported on top-level classes only",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Place `@sealed` immediately above a family class definition.",
                    )
            _sh_reject_runtime_decl_nonfunction_decorators(
                pending_top_level_decorators,
                import_module_bindings=import_module_bindings,
                import_symbol_bindings=import_symbol_bindings,
                line_no=i,
                line_text=ln,
                is_abi_decorator=_sh_is_abi_decorator,
                is_template_decorator=_sh_is_template_decorator,
                make_east_build_error=_make_east_build_error,
                make_span=_sh_span,
            )
            pending_top_level_decorators = []

        top_indent = len(ln) - len(ln.lstrip(" "))
        if s.startswith("if ") and s.endswith(":"):
            cur_idx_obj = top_merged_index.get(i)
            if isinstance(cur_idx_obj, int):
                cur_idx = int(cur_idx_obj)
                then_block, j_idx = _sh_collect_indented_block(top_merged_lines, cur_idx + 1, top_indent)
                if len(then_block) == 0:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="if body is missing in 'module'",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Add indented if-body.",
                    )
                _else_stmt_list, j_idx = _sh_parse_if_tail(
                    start_idx=j_idx,
                    parent_indent=top_indent,
                    body_lines=top_merged_lines,
                    name_types={},
                    scope_label="module",
                )
                stmt_chunk = top_merged_lines[cur_idx:j_idx]
                parsed_items = _sh_parse_stmt_block(stmt_chunk, name_types={}, scope_label="module")
                if not first_item_attached and len(parsed_items) > 0:
                    first_item = parsed_items[0]
                    if isinstance(first_item, dict):
                        first_item["leading_comments"] = list(leading_file_comments)
                        first_item["leading_trivia"] = list(leading_file_trivia)
                        first_item_attached = True
                for parsed_item in parsed_items:
                    body_items.append(parsed_item)
                if j_idx < len(top_merged_lines):
                    i = int(top_merged_lines[j_idx][0])
                else:
                    i = len(lines) + 1
                continue

        if s.startswith("for "):
            cur_idx_obj = top_merged_index.get(i)
            if isinstance(cur_idx_obj, int):
                cur_idx = int(cur_idx_obj)
                for_full = s[len("for ") :].strip()
                inline_for = False
                if not for_full.endswith(":"):
                    inline_for = _sh_split_top_level_colon(for_full) is not None
                j_idx = cur_idx + 1
                if for_full.endswith(":"):
                    body_block, j_idx = _sh_collect_indented_block(top_merged_lines, cur_idx + 1, top_indent)
                    if len(body_block) == 0:
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message="for body is missing in 'module'",
                            source_span=_sh_span(i, 0, len(ln)),
                            hint="Add indented for-body.",
                        )
                elif not inline_for:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"self_hosted parser cannot parse for statement: {s}",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Use `for target in iterable:` form.",
                    )
                stmt_chunk = top_merged_lines[cur_idx:j_idx]
                parsed_items = _sh_parse_stmt_block(stmt_chunk, name_types={}, scope_label="module")
                if not first_item_attached and len(parsed_items) > 0:
                    first_item = parsed_items[0]
                    if isinstance(first_item, dict):
                        first_item["leading_comments"] = list(leading_file_comments)
                        first_item["leading_trivia"] = list(leading_file_trivia)
                        first_item_attached = True
                for parsed_item in parsed_items:
                    body_items.append(parsed_item)
                if j_idx < len(top_merged_lines):
                    i = int(top_merged_lines[j_idx][0])
                else:
                    i = len(lines) + 1
                continue

        parsed_top_typed = _sh_parse_typed_binding(s, allow_dotted_name=False)
        if parsed_top_typed is not None:
            top_name, top_ann, top_default = parsed_top_typed
        else:
            top_name, top_ann, top_default = "", "", ""
        if parsed_top_typed is not None and top_default != "":
            name = top_name
            ann_txt = top_ann
            expr_txt = top_default
            ann = _sh_ann_to_type(ann_txt, type_aliases=_SH_TYPE_ALIASES)
            ann_expr = _sh_ann_to_type_expr(ann, type_aliases=_SH_TYPE_ALIASES)
            expr_col = ln.find(expr_txt)
            value_expr = _sh_parse_expr_lowered(expr_txt, ln_no=i, col=expr_col, name_types={})
            ann_item = _sh_make_ann_assign_stmt(
                _sh_span(i, ln.find(name), len(ln)),
                _sh_make_name_expr(
                    _sh_span(i, ln.find(name), ln.find(name) + len(name)),
                    name,
                    resolved_type=ann,
                    type_expr=ann_expr,
                ),
                ann,
                annotation_type_expr=ann_expr,
                value=value_expr,
                declare=True,
                decl_type=ann,
                decl_type_expr=ann_expr,
            )
            extern_var_meta = _sh_collect_extern_var_metadata(
                target_name=name,
                annotation=ann,
                value_expr=value_expr,
                import_module_bindings=import_module_bindings,
                import_symbol_bindings=import_symbol_bindings,
            )
            if extern_var_meta is not None:
                ann_item["meta"] = _sh_make_decl_meta(extern_var_v1=extern_var_meta)
            body_items.append(ann_item)
            i = logical_end + 1
            continue

        asg_top = _sh_split_top_level_assign(s)
        if asg_top is not None:
            asg_left, asg_right = asg_top
            target_txt = asg_left.strip()
            expr_txt = asg_right.strip()
            expr_col = ln.find(expr_txt)
            if expr_col < 0:
                expr_col = 0
            target_col = ln.find(target_txt)
            if target_col < 0:
                target_col = 0
            target_node = _sh_parse_expr_lowered(target_txt, ln_no=i, col=target_col, name_types={})
            val_node = _sh_parse_expr_lowered(expr_txt, ln_no=i, col=expr_col, name_types={})
            decl_type = str(val_node.get("resolved_type", "unknown"))
            declare_name = isinstance(target_node, dict) and target_node.get("kind") == "Name"
            body_items.append(
                _sh_make_assign_stmt(
                    _sh_span(i, target_col, len(ln)),
                    target_node,
                    val_node,
                    declare=declare_name,
                    declare_init=declare_name,
                    decl_type=decl_type if declare_name else None,
                )
            )
            i = logical_end + 1
            continue

        if (s.startswith('"""') and s.endswith('"""')) or (s.startswith("'''") and s.endswith("'''")):
            # Module-level docstring / standalone string expression.
            body_items.append(
                _sh_make_expr_stmt(
                    _sh_parse_expr_lowered(s, ln_no=i, col=0, name_types={}),
                    _sh_span(i, 0, len(ln)),
                )
            )
            i = logical_end + 1
            continue

        expr_col = len(ln) - len(ln.lstrip(" "))
        body_items.append(
            _sh_make_expr_stmt(
                _sh_parse_expr_lowered(s, ln_no=i, col=expr_col, name_types={}),
                _sh_span(i, expr_col, len(ln)),
            )
        )
        i = logical_end + 1
        continue

    renamed_symbols: dict[str, str] = {}
    for item in body_items:
        if item.get("kind") == "FunctionDef" and item.get("name") == "main":
            renamed_symbols["main"] = "__pytra_main"
            item["name"] = "__pytra_main"

    # 互換メタデータは ImportBinding 正本から導出する。
    import_module_bindings = {}
    import_symbol_bindings = {}
    qualified_symbol_refs: list[dict[str, str]] = []
    import_resolution_bindings: list[dict[str, Any]] = []
    for binding in import_bindings:
        import_resolution_bindings.append(
            _sh_make_import_resolution_binding(binding, make_import_binding=_sh_make_import_binding)
        )
        module_id, export_name, local_name, binding_kind, _source_file, _source_line = _sh_import_binding_fields(binding)
        if module_id == "" or local_name == "":
            continue
        if binding_kind == "module":
            import_module_bindings[local_name] = module_id
            continue
        if binding_kind == "symbol" and export_name != "":
            import_symbol_bindings[local_name] = _sh_make_import_symbol_binding(module_id, export_name)
            qualified_symbol_refs.append(_sh_make_qualified_symbol_ref(module_id, export_name, local_name))

    out = _sh_make_module_root(
        filename=filename,
        body_items=body_items,
        main_stmts=main_stmts,
        renamed_symbols=renamed_symbols,
        import_resolution_bindings=import_resolution_bindings,
        qualified_symbol_refs=qualified_symbol_refs,
        import_bindings=import_bindings,
        import_module_bindings=import_module_bindings,
        import_symbol_bindings=import_symbol_bindings,
        make_node=_sh_make_node,
    )
    sync_type_expr_mirrors(out)
    return validate_template_module(validate_runtime_abi_module(out))
