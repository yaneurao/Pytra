"""Unit regression tests for the self_hosted EAST converter."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path
from typing import Any

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

CORE_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core.py"

from src.toolchain.compiler.east import convert_source_to_east_with_backend
from src.toolchain.compiler.east import EastBuildError


def _walk(node: Any):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for it in node:
            yield from _walk(it)


class EastCoreTest(unittest.TestCase):
    def test_core_source_uses_builder_helpers_for_module_root_and_trivia(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn("def _sh_make_kind_carrier(", text)
        self.assertIn("def _sh_make_node(", text)
        self.assertIn("def _sh_make_stmt_node(", text)
        self.assertIn("def _sh_make_trivia_blank(", text)
        self.assertIn("def _sh_make_trivia_comment(", text)
        self.assertIn("def _sh_make_expr_token(", text)
        self.assertIn("def _sh_make_expr_stmt(", text)
        self.assertIn("def _sh_make_value_expr(", text)
        self.assertIn("def _sh_make_name_expr(", text)
        self.assertIn("def _sh_make_tuple_expr(", text)
        self.assertIn("def _sh_make_constant_expr(", text)
        self.assertIn("def _sh_make_unaryop_expr(", text)
        self.assertIn("def _sh_make_boolop_expr(", text)
        self.assertIn("def _sh_make_compare_expr(", text)
        self.assertIn("def _sh_make_binop_expr(", text)
        self.assertIn("def _sh_make_cast_entry(", text)
        self.assertIn("def _sh_make_ifexp_expr(", text)
        self.assertIn("def _sh_make_attribute_expr(", text)
        self.assertIn("def _sh_make_call_expr(", text)
        self.assertIn("def _sh_make_keyword_arg(", text)
        self.assertIn("def _sh_make_slice_node(", text)
        self.assertIn("def _sh_make_subscript_expr(", text)
        self.assertIn("def _sh_make_comp_generator(", text)
        self.assertIn("def _sh_make_list_expr(", text)
        self.assertIn("def _sh_make_set_expr(", text)
        self.assertIn("def _sh_make_dict_entry(", text)
        self.assertIn("def _sh_make_dict_expr(", text)
        self.assertIn("def _sh_make_list_comp_expr(", text)
        self.assertIn("def _sh_make_dict_comp_expr(", text)
        self.assertIn("def _sh_make_set_comp_expr(", text)
        self.assertIn("def _sh_make_range_expr(", text)
        self.assertIn("def _sh_make_arg_node(", text)
        self.assertIn("def _sh_make_lambda_arg_entry(", text)
        self.assertIn("def _sh_make_lambda_expr(", text)
        self.assertIn("def _sh_make_formatted_value_node(", text)
        self.assertIn("def _sh_make_joined_str_expr(", text)
        self.assertIn("def _sh_make_import_alias(", text)
        self.assertIn("def _sh_make_import_stmt(", text)
        self.assertIn("def _sh_make_import_from_stmt(", text)
        self.assertIn("def _sh_make_if_stmt(", text)
        self.assertIn("def _sh_make_while_stmt(", text)
        self.assertIn("def _sh_make_except_handler(", text)
        self.assertIn("def _sh_make_try_stmt(", text)
        self.assertIn("def _sh_make_for_stmt(", text)
        self.assertIn("def _sh_make_for_range_stmt(", text)
        self.assertIn("def _sh_make_function_def_stmt(", text)
        self.assertIn("def _sh_make_class_def_stmt(", text)
        self.assertIn("def _sh_make_def_sig_info(", text)
        self.assertIn("def _sh_make_module_source_span(", text)
        self.assertIn("def _sh_make_import_resolution_meta(", text)
        self.assertIn("def _sh_make_import_resolution_binding(", text)
        self.assertIn("def _sh_make_module_meta(", text)
        self.assertIn("def _sh_make_decl_meta(", text)
        self.assertIn("def _sh_import_binding_fields(", text)
        self.assertIn("def _sh_make_import_resolution_binding(", text)
        self.assertIn("def _sh_make_assign_stmt(", text)
        self.assertIn("def _sh_make_ann_assign_stmt(", text)
        self.assertIn("def _sh_make_raise_stmt(", text)
        self.assertIn("def _sh_make_pass_stmt(", text)
        self.assertIn("def _sh_make_return_stmt(", text)
        self.assertIn("def _sh_make_yield_stmt(", text)
        self.assertIn("def _sh_make_augassign_stmt(", text)
        self.assertIn("def _sh_make_swap_stmt(", text)
        self.assertIn("def _sh_make_import_alias(", text)
        self.assertIn("def _sh_make_import_binding(", text)
        self.assertIn("def _sh_make_import_symbol_binding(", text)
        self.assertIn("def _sh_make_qualified_symbol_ref(", text)
        self.assertIn("def _sh_make_import_stmt(", text)
        self.assertIn("def _sh_make_import_from_stmt(", text)
        self.assertIn("def _sh_make_if_stmt(", text)
        self.assertIn("def _sh_make_while_stmt(", text)
        self.assertIn("def _sh_make_except_handler(", text)
        self.assertIn("def _sh_make_try_stmt(", text)
        self.assertIn("def _sh_make_for_stmt(", text)
        self.assertIn("def _sh_make_for_range_stmt(", text)
        self.assertIn("def _sh_make_module_root(", text)
        self.assertIn("out = _sh_make_module_root(", text)
        self.assertNotIn('out["kind"] = "Module"', text)
        self.assertNotIn('_SH_IMPORT_SYMBOLS[local] = {"module": module, "name": export}', text)
        self.assertNotIn('pre_import_symbol_bindings[alias_name] = {', text)
        self.assertNotIn('import_symbol_bindings[bind_name_dc] = {', text)
        self.assertNotIn('import_symbol_bindings[bind_name] = {', text)
        self.assertNotIn("for key, value in resolution.items():", text)
        self.assertNotIn('arg_entries.append({"name": nm, "default": default_expr, "resolved_type": param_t})', text)
        self.assertNotIn('keywords.append({"arg": str(name_tok["v"]), "value": kw_val})', text)
        self.assertNotIn('casts.append({"on": "left", "from": "int64", "to": "float64", "reason": "numeric_promotion"})', text)
        self.assertNotIn('casts.append({"on": "right", "from": "int64", "to": "float64", "reason": "numeric_promotion"})', text)
        self.assertNotIn('meta["runtime_abi_v1"] = runtime_abi_meta', text)
        self.assertNotIn('meta["template_v1"] = template_meta', text)
        self.assertNotIn('ann_item["meta"] = {"extern_var_v1": extern_var_meta}', text)
        module_root_tail = text.split("for binding in import_bindings:", 1)[1]
        self.assertNotIn('module_id_obj = binding.get("module_id")', module_root_tail)
        self.assertNotIn('local_name_obj = binding.get("local_name")', module_root_tail)
        self.assertNotIn('export_name_obj = binding.get("export_name")', module_root_tail)
        self.assertNotIn('binding_kind_obj = binding.get("binding_kind")', module_root_tail)

    def test_core_source_uses_builder_helpers_for_statement_clusters(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn("assign_stmt = _sh_make_assign_stmt(", text)
        self.assertIn("try_stmt = _sh_make_try_stmt(", text)
        self.assertIn(
            "pending_blank_count = _sh_push_stmt_with_trivia(\n"
            "                stmts,\n"
            "                pending_leading_trivia,\n"
            "                pending_blank_count,\n"
            "                _sh_make_while_stmt(",
            text,
        )
        self.assertIn("_sh_make_except_handler(", text)
        self.assertIn(
            "pending_blank_count = _sh_push_stmt_with_trivia(\n"
            "                stmts,\n"
            "                pending_leading_trivia,\n"
            "                pending_blank_count,\n"
            "                _sh_make_try_stmt(",
            text,
        )
        self.assertIn("_sh_make_raise_stmt(", text)
        self.assertIn("pass_stmt = _sh_make_pass_stmt(", text)
        self.assertIn("_sh_make_return_stmt(", text)
        self.assertIn("_sh_make_augassign_stmt(", text)
        self.assertIn("_sh_make_swap_stmt(", text)
        self.assertNotIn('assign_stmt = {"kind": "Assign"', text)
        self.assertNotIn('try_stmt = {"kind": "Try"', text)
        self.assertNotIn(
            'pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, {"kind": "While"',
            text,
        )
        self.assertNotIn('handlers.append({"kind": "ExceptHandler"', text)
        self.assertNotIn(
            'pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, {"kind": "Try"',
            text,
        )
        self.assertNotIn(
            'pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, {"kind": "Raise"',
            text,
        )
        self.assertNotIn('pass_stmt = {"kind": "Pass"', text)
        self.assertNotIn(
            'pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, {"kind": "Return"',
            text,
        )
        self.assertNotIn(
            'pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, {"kind": "AugAssign"',
            text,
        )
        self.assertNotIn(
            'pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, {"kind": "Swap"',
            text,
        )

    def test_core_source_uses_builder_helpers_for_decl_and_import_clusters(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn("aliases.append(_sh_make_import_alias(", text)
        self.assertIn("body_items.append(_sh_make_import_stmt(_sh_span(i, 0, len(ln)), aliases))", text)
        self.assertIn(
            "body_items.append(\n"
            "                    _sh_make_import_from_stmt(",
            text,
        )
        self.assertIn("item = _sh_make_function_def_stmt(", text)
        self.assertIn("_sh_block_end_span(block, i, 0, len(ln), len(block))", text)
        self.assertIn(
            "class_body.append(\n"
            "                            _sh_make_function_def_stmt(",
            text,
        )
        self.assertIn(
            "_sh_block_end_span(method_block, ln_no, bind, len(ln_txt), len(method_block))",
            text,
        )
        self.assertIn("cls_item = _sh_make_class_def_stmt(", text)
        self.assertNotIn('body_items.append({"kind": "Import"', text)
        self.assertNotIn('body_items.append({"kind": "ImportFrom"', text)
        self.assertNotIn('item = {"kind": "FunctionDef"', text)
        self.assertNotIn('class_body.append({"kind": "FunctionDef"', text)
        self.assertNotIn('cls_item = {"kind": "ClassDef"', text)
        self.assertNotIn(
            '{"lineno": i, "col": 0, "end_lineno": block[-1][0], "end_col": len(block[-1][1])}',
            text,
        )
        self.assertNotIn(
            '{"lineno": ln_no, "col": bind, "end_lineno": method_block[-1][0], "end_col": len(method_block[-1][1])}',
            text,
        )

    def test_core_source_routes_stmt_span_helpers_through_sh_span(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        span_helper_text = text.split("def _sh_span", 1)[1].split("def _sh_make_trivia_blank", 1)[0]
        block_span_text = text.split("def _sh_block_end_span", 1)[1].split("def _sh_stmt_span", 1)[0]
        stmt_span_text = text.split("def _sh_stmt_span", 1)[1].split("def _sh_push_stmt_with_trivia", 1)[0]

        self.assertIn("(line: int, col: int, end_col: int, *, end_lineno: int | None = None) -> dict[str, int]:", span_helper_text)
        self.assertIn('return {"lineno": line, "col": col, "end_lineno": line if end_lineno is None else end_lineno, "end_col": end_col}', span_helper_text)
        self.assertIn("return _sh_span(start_ln, start_col, len(end_txt), end_lineno=end_ln)", block_span_text)
        self.assertIn("return _sh_span(start_ln, start_col, end_col, end_lineno=end_ln)", stmt_span_text)
        self.assertNotIn(
            '{"lineno": start_ln, "col": start_col, "end_lineno": end_ln, "end_col": len(end_txt)}',
            block_span_text,
        )
        self.assertNotIn(
            '{"lineno": start_ln, "col": start_col, "end_lineno": end_ln, "end_col": end_col}',
            stmt_span_text,
        )

    def test_core_source_uses_builder_helpers_for_expression_clusters(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn("node = _sh_make_attribute_expr(", text)
        self.assertIn("payload = _sh_make_call_expr(", text)
        self.assertIn("node = _sh_make_subscript_expr(", text)
        self.assertIn("return _sh_make_binop_expr(", text)
        self.assertIn("node = _sh_make_binop_expr(", text)
        self.assertIn("return _sh_make_lambda_expr(", text)
        self.assertIn("_sh_make_formatted_value_node(", text)
        self.assertIn("return _sh_make_joined_str_expr(", text)
        self.assertNotIn('node = {"kind": "Attribute"', text)
        self.assertNotIn('payload = {"kind": "Call"', text)
        self.assertNotIn('return {"kind": "BinOp"', text)
        self.assertNotIn('node = {"kind": "Subscript"', text)
        self.assertNotIn('return {"kind": "Lambda"', text)
        self.assertNotIn('values.append({"kind": "FormattedValue"', text)
        self.assertNotIn('return {"kind": "JoinedStr"', text)

    def test_core_source_routes_expr_envelopes_through_shared_helper(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        node_helper_text = text.split("def _sh_make_node", 1)[1].split("def _sh_make_stmt_node", 1)[0]
        helper_text = text.split("def _sh_make_value_expr", 1)[1].split("def _sh_make_name_expr", 1)[0]
        name_text = text.split("def _sh_make_name_expr", 1)[1].split("def _sh_make_tuple_expr", 1)[0]
        tuple_text = text.split("def _sh_make_tuple_expr", 1)[1].split("def _sh_make_constant_expr", 1)[0]
        call_text = text.split("def _sh_make_call_expr", 1)[1].split("def _sh_make_keyword_arg", 1)[0]
        dict_text = text.split("def _sh_make_dict_expr", 1)[1].split("def _sh_make_list_comp_expr", 1)[0]
        slice_text = text.split("def _sh_make_slice_node", 1)[1].split("def _sh_make_subscript_expr", 1)[0]

        self.assertIn('node = _sh_make_kind_carrier(kind)', node_helper_text)
        self.assertIn("node.update(fields)", node_helper_text)
        self.assertIn('return _sh_make_node(', helper_text)
        self.assertIn("source_span=source_span", helper_text)
        self.assertIn("resolved_type=resolved_type", helper_text)
        self.assertIn("casts=[] if casts is None else casts", helper_text)
        self.assertIn('node = _sh_make_value_expr(', name_text)
        self.assertIn('"Name"', name_text)
        self.assertIn('node = _sh_make_value_expr(', tuple_text)
        self.assertIn('"Tuple"', tuple_text)
        self.assertIn('node = _sh_make_value_expr(', call_text)
        self.assertIn('"Call"', call_text)
        self.assertIn('node = _sh_make_value_expr(', dict_text)
        self.assertIn('"Dict"', dict_text)
        self.assertIn('return _sh_make_node("Slice", lower=lower, upper=upper, step=step)', slice_text)
        self.assertNotIn('"kind": "Name"', name_text)
        self.assertNotIn('"kind": "Tuple"', tuple_text)
        self.assertNotIn('"kind": "Call"', call_text)
        self.assertNotIn('"kind": "Dict"', dict_text)
        self.assertNotIn('node = _sh_make_kind_carrier("Slice")', slice_text)

    def test_core_source_routes_statement_envelopes_through_shared_helper(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        node_helper_text = text.split("def _sh_make_node", 1)[1].split("def _sh_make_stmt_node", 1)[0]
        helper_text = text.split("def _sh_make_stmt_node", 1)[1].split("def _sh_make_trivia_blank", 1)[0]
        blank_text = text.split("def _sh_make_trivia_blank", 1)[1].split("def _sh_make_trivia_comment", 1)[0]
        comment_text = text.split("def _sh_make_trivia_comment", 1)[1].split("def _sh_make_expr_token", 1)[0]
        expr_text = text.split("def _sh_make_expr_stmt", 1)[1].split("def _sh_make_value_expr", 1)[0]
        assign_text = text.split("def _sh_make_assign_stmt", 1)[1].split("def _sh_make_ann_assign_stmt", 1)[0]
        except_text = text.split("def _sh_make_except_handler", 1)[1].split("def _sh_make_try_stmt", 1)[0]
        try_text = text.split("def _sh_make_try_stmt", 1)[1].split("def _sh_make_for_stmt", 1)[0]
        fn_text = text.split("def _sh_make_function_def_stmt", 1)[1].split("def _sh_make_class_def_stmt", 1)[0]

        self.assertIn('node = _sh_make_kind_carrier(kind)', node_helper_text)
        self.assertIn("node.update(fields)", node_helper_text)
        self.assertIn("return _sh_make_node(kind, source_span=source_span)", helper_text)
        self.assertIn('return _sh_make_node("blank", count=count)', blank_text)
        self.assertIn('return _sh_make_node("comment", text=text)', comment_text)
        self.assertIn('node = _sh_make_stmt_node("Expr", source_span)', expr_text)
        self.assertIn('node = _sh_make_stmt_node("Assign", source_span)', assign_text)
        self.assertIn('return _sh_make_node("ExceptHandler", type=type_expr, name=name, body=body)', except_text)
        self.assertIn('node = _sh_make_stmt_node("Try", source_span)', try_text)
        self.assertIn('node = _sh_make_stmt_node("FunctionDef", source_span)', fn_text)
        self.assertNotIn('{"kind": "Expr"', expr_text)
        self.assertNotIn('{"kind": "Assign"', assign_text)
        self.assertNotIn('"kind": "ExceptHandler"', except_text)
        self.assertNotIn('{"kind": "Try"', try_text)
        self.assertNotIn('{"kind": "FunctionDef"', fn_text)

    def test_core_source_uses_builder_helpers_for_residual_stmt_name_tuple_clusters(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn("_sh_make_ann_assign_stmt(", text)
        self.assertIn("target_expr = _sh_make_tuple_expr(", text)
        self.assertIn(
            "_sh_make_comp_generator(\n"
            "                    _sh_make_name_expr(",
            text,
        )
        self.assertIn(
            "_sh_make_expr_stmt(expr_stmt, _sh_stmt_span(merged_line_end, ln_no, expr_col, len(ln_txt)))",
            text,
        )
        self.assertNotIn(
            'pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, {"kind": "AnnAssign"',
            text,
        )
        self.assertNotIn(
            'pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, {"kind": "Assign"',
            text,
        )
        self.assertNotIn(
            'pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, {"kind": "Expr"',
            text,
        )
        self.assertNotIn('target_expr = {"kind": "Tuple"', text)
        self.assertNotIn(
            'dict<str, object>{{"kind", make_object("Name")}',
            text,
        )

    def test_core_source_uses_builder_helpers_for_literal_and_target_clusters(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        comp_target_text = text.split("def _parse_comp_target", 1)[1].split(
            "def _collect_and_bind_comp_target_types", 1
        )[0]
        primary_text = text.split("def _parse_primary", 1)[1].split("def _sh_parse_expr", 1)[0]

        self.assertIn("first_node = _sh_make_name_expr(", comp_target_text)
        self.assertIn("return _sh_make_tuple_expr(", comp_target_text)
        self.assertIn("return _sh_make_constant_expr(", primary_text)
        self.assertIn("return _sh_make_name_expr(", primary_text)
        self.assertIn("return _sh_make_tuple_expr(", primary_text)
        self.assertIn("return _sh_make_list_expr(", primary_text)
        self.assertIn("return _sh_make_dict_expr(", primary_text)
        self.assertIn("return _sh_make_set_expr(", primary_text)

        self.assertNotIn('first_node = {"kind": "Name"', comp_target_text)
        self.assertNotIn('return {"kind": "Tuple"', comp_target_text)
        self.assertNotIn('return {"kind": "Constant"', primary_text)
        self.assertNotIn('return {"kind": "Name"', primary_text)
        self.assertNotIn('return {"kind": "Tuple"', primary_text)
        self.assertNotIn('return {"kind": "List"', primary_text)
        self.assertNotIn('return {"kind": "Dict"', primary_text)
        self.assertNotIn('return {"kind": "Set"', primary_text)

    def test_core_source_uses_builder_helpers_for_collection_and_dict_entry_clusters(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        primary_text = text.split("def _parse_primary", 1)[1].split("def _sh_parse_expr", 1)[0]
        lowered_text = text.split("def _sh_parse_expr_lowered", 1)[1]

        self.assertIn("return _sh_make_list_comp_expr(", primary_text)
        self.assertIn("[_sh_make_comp_generator(target, iter_expr, ifs)]", primary_text)
        self.assertIn("[_sh_make_comp_generator(target, iter_expr, ifs_norm)]", primary_text)
        self.assertIn("iter_expr = _sh_make_range_expr(", primary_text)
        self.assertIn("return _sh_make_dict_comp_expr(", primary_text)
        self.assertIn("return _sh_make_set_comp_expr(", lowered_text)
        self.assertIn("entries.append(\n                    _sh_make_dict_entry(", lowered_text)
        self.assertIn("return _sh_make_dict_expr(", lowered_text)

        self.assertNotIn('return {"kind": "ListComp"', primary_text)
        self.assertNotIn('iter_expr = {"kind": "RangeExpr"', primary_text)
        self.assertNotIn('return {"kind": "DictComp"', primary_text)
        self.assertNotIn('return {"kind": "SetComp"', lowered_text)
        self.assertNotIn(
            'entries.append(\n                    {\n                        "key": _sh_parse_expr_lowered(',
            lowered_text,
        )

    def test_core_source_uses_builder_helpers_for_lowered_residual_call_dict_tuple_clusters(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        lowered_text = text.split("def _sh_parse_expr_lowered", 1)[1].split(
            "def _sh_parse_stmt_block_mutable",
            1,
        )[0]

        self.assertIn("payload = _sh_make_call_expr(", lowered_text)
        self.assertIn("_sh_make_name_expr(_sh_span(ln_no, col, col + len(fn_name)), fn_name, repr_text=fn_name)", lowered_text)
        self.assertIn("return _sh_make_dict_expr(", lowered_text)
        self.assertIn("return _sh_make_tuple_expr(", lowered_text)

        self.assertNotIn('return {"kind": "Call"', lowered_text)
        self.assertNotIn('return {"kind": "Dict"', lowered_text)
        self.assertNotIn('return {"kind": "Tuple"', lowered_text)

    def test_core_source_uses_builder_helpers_for_lowered_any_all_and_simple_listcomp_clusters(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        lowered_text = text.split("def _sh_parse_expr_lowered", 1)[1].split(
            "def _sh_parse_stmt_block_mutable",
            1,
        )[0]

        self.assertIn('lowered_kind = "BuiltinCall" if fn_name in {"any", "all"} else None', lowered_text)
        self.assertIn("payload = _sh_make_call_expr(", lowered_text)
        self.assertIn(
            '_sh_make_name_expr(_sh_span(ln_no, col, col + len(fn_name)), fn_name, repr_text=fn_name)',
            lowered_text,
        )
        self.assertIn("elt_node = _sh_make_name_expr(", lowered_text)
        self.assertIn("_sh_make_comp_generator(", lowered_text)
        self.assertIn('resolved_type=f"list[{elem_t}]"', lowered_text)
        self.assertNotIn('return dict<str, object>{{"kind", make_object("Call")}', lowered_text)
        self.assertNotIn('dict<str, object>{{"kind", make_object("Name")}', lowered_text)

    def test_core_source_uses_builder_helpers_for_tuple_destructuring_clusters(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        stmt_text = text.split("def _sh_parse_stmt_block_mutable", 1)[1].split(
            "def _sh_build_module_root",
            1,
        )[0]

        self.assertIn("target_expr = _sh_make_tuple_expr(", stmt_text)
        self.assertIn("_sh_make_assign_stmt(", stmt_text)
        self.assertIn('resolved_type=name_types.get(n1, "unknown")', stmt_text)
        self.assertIn('resolved_type=name_types.get(n2, "unknown")', stmt_text)
        self.assertNotIn('target_expr = {"kind": "Tuple"', stmt_text)
        self.assertNotIn('pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, dict<str, object>{{"kind", make_object("Assign")}', stmt_text)

    def test_core_source_known_inline_kind_residual_set_is_helper_only(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        raw_kinds = re.findall(r'\{"kind": "([^"]+)"', text)
        inline_kinds = {kind for kind in raw_kinds if kind != "" and kind[0].isupper()}
        trivia_kinds = {kind for kind in raw_kinds if kind != "" and kind[0].islower()}

        self.assertIn('node = _sh_make_stmt_node("Expr", source_span)', text)
        self.assertIn('return _sh_make_node("Slice", lower=lower, upper=upper, step=step)', text)
        self.assertIn('return _sh_make_node("blank", count=count)', text)
        self.assertIn('return _sh_make_node("comment", text=text)', text)
        self.assertNotIn('return {"kind": "Expr", "source_span": source_span, "value": value}', text)
        self.assertNotIn('return {"kind": "Slice", "lower": lower, "upper": upper, "step": step}', text)
        self.assertNotIn('return {"kind": "blank", "count": count}', text)
        self.assertNotIn('return {"kind": "comment", "text": text}', text)
        self.assertEqual(inline_kinds, set())
        self.assertEqual(trivia_kinds, set())
        self.assertTrue(
            {
                "If",
                "While",
                "ExceptHandler",
                "Try",
                "For",
                "ForRange",
                "Raise",
                "Pass",
                "Return",
                "AugAssign",
                "Swap",
                "RangeExpr",
                "ListComp",
                "DictComp",
                "SetComp",
                "FormattedValue",
                "JoinedStr",
                "Subscript",
                "BoolOp",
                "UnaryOp",
                "Compare",
                "BinOp",
                "Lambda",
                "Call",
                "Dict",
                "Tuple",
                "Name",
                "Assign",
                "AnnAssign",
            }.isdisjoint(inline_kinds)
        )

    def test_top_level_extern_decorator_is_preserved(self) -> None:
        src = """
from pytra.std import extern

@extern
def f(x: float) -> float:
    return x
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        funcs = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "f"
        ]
        self.assertEqual(len(funcs), 1)
        self.assertEqual(funcs[0].get("decorators"), ["extern"])

    def test_top_level_annassign_extern_same_name_sets_ambient_global_metadata(self) -> None:
        src = """
from pytra.std import extern

document: Any = extern()
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        ann_assigns = [
            n for n in east.get("body", []) if isinstance(n, dict) and n.get("kind") == "AnnAssign"
        ]
        self.assertEqual(len(ann_assigns), 1)
        self.assertEqual(
            ann_assigns[0].get("meta", {}).get("extern_var_v1"),
            {
                "schema_version": 1,
                "symbol": "document",
                "same_name": 1,
            },
        )

    def test_top_level_annassign_extern_alias_sets_ambient_global_metadata(self) -> None:
        src = """
from pytra.std import extern

doc: Any = extern("document")
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        ann_assigns = [
            n for n in east.get("body", []) if isinstance(n, dict) and n.get("kind") == "AnnAssign"
        ]
        self.assertEqual(len(ann_assigns), 1)
        self.assertEqual(
            ann_assigns[0].get("meta", {}).get("extern_var_v1"),
            {
                "schema_version": 1,
                "symbol": "document",
                "same_name": 0,
            },
        )

    def test_top_level_abi_decorator_sets_runtime_abi_metadata(self) -> None:
        src = """
from pytra.std import abi

@abi(args={"parts": "value"}, ret="value")
def py_join(sep: str, parts: list[str]) -> str:
    return sep
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        funcs = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "py_join"
        ]
        self.assertEqual(len(funcs), 1)
        fn = funcs[0]
        self.assertEqual(
            fn.get("decorators"),
            ['abi(args={"parts": "value"}, ret="value")'],
        )
        self.assertEqual(
            fn.get("meta", {}).get("runtime_abi_v1"),
            {
                "schema_version": 1,
                "args": {"parts": "value"},
                "ret": "value",
            },
        )

    def test_legacy_value_readonly_alias_is_normalized_to_value(self) -> None:
        src = """
from pytra.std import abi

@abi(args={"parts": "value_readonly"}, ret="value")
def py_join(sep: str, parts: list[str]) -> str:
    return sep
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        funcs = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "py_join"
        ]
        self.assertEqual(len(funcs), 1)
        fn = funcs[0]
        self.assertEqual(
            fn.get("decorators"),
            ['abi(args={"parts": "value_readonly"}, ret="value")'],
        )
        self.assertEqual(
            fn.get("meta", {}).get("runtime_abi_v1"),
            {
                "schema_version": 1,
                "args": {"parts": "value"},
                "ret": "value",
            },
        )

    def test_top_level_extern_and_abi_decorators_can_coexist(self) -> None:
        src = """
from pytra.std import extern, abi

@extern
@abi(args={"xs": "value"}, ret="value")
def clone(xs: list[int]) -> list[int]:
    return xs
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        funcs = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "clone"
        ]
        self.assertEqual(len(funcs), 1)
        fn = funcs[0]
        self.assertEqual(
            fn.get("decorators"),
            ["extern", 'abi(args={"xs": "value"}, ret="value")'],
        )
        self.assertEqual(
            fn.get("meta", {}).get("runtime_abi_v1"),
            {
                "schema_version": 1,
                "args": {"xs": "value"},
                "ret": "value",
            },
        )

    def test_top_level_abi_decorator_accepts_value_mut_arg(self) -> None:
        src = """
from pytra.std import abi

@abi(args={"xs": "value_mut"})
def sort_inplace(xs: list[int]) -> None:
    return None
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        funcs = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "sort_inplace"
        ]
        self.assertEqual(len(funcs), 1)
        self.assertEqual(
            funcs[0].get("meta", {}).get("runtime_abi_v1"),
            {
                "schema_version": 1,
                "args": {"xs": "value_mut"},
                "ret": "default",
            },
        )

    def test_top_level_template_decorator_sets_template_metadata(self) -> None:
        src = """
from pytra.std.template import template

@template("T", "U")
def py_zip(lhs: list[T], rhs: list[U]) -> list[tuple[T, U]]:
    return []
"""
        east = convert_source_to_east_with_backend(
            src,
            "src/pytra/built_in/template_ops.py",
            parser_backend="self_hosted",
        )
        funcs = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "py_zip"
        ]
        self.assertEqual(len(funcs), 1)
        fn = funcs[0]
        self.assertEqual(fn.get("decorators"), ['template("T", "U")'])
        self.assertEqual(
            fn.get("meta", {}).get("template_v1"),
            {
                "schema_version": 1,
                "params": ["T", "U"],
                "scope": "runtime_helper",
                "instantiation_mode": "linked_implicit",
            },
        )

    def test_top_level_template_and_abi_decorators_can_coexist(self) -> None:
        src = """
from pytra.std import abi
from pytra.std.template import template

@template("T")
@abi(args={"xs": "value"}, ret="value")
def clone(xs: list[T]) -> list[T]:
    return xs
"""
        east = convert_source_to_east_with_backend(
            src,
            "src/pytra/built_in/template_ops.py",
            parser_backend="self_hosted",
        )
        funcs = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "clone"
        ]
        self.assertEqual(len(funcs), 1)
        fn = funcs[0]
        self.assertEqual(
            fn.get("meta", {}),
            {
                "template_v1": {
                    "schema_version": 1,
                    "params": ["T"],
                    "scope": "runtime_helper",
                    "instantiation_mode": "linked_implicit",
                },
                "runtime_abi_v1": {
                    "schema_version": 1,
                    "args": {"xs": "value"},
                    "ret": "value",
                },
            },
        )

    def test_method_level_template_decorator_is_rejected(self) -> None:
        src = """
from pytra.std.template import template

class Box:
    @template("T")
    def f(self, xs: list[int]) -> list[int]:
        return xs
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("@template is not supported on methods", str(cm.exception))

    def test_template_decorator_rejects_duplicate_params(self) -> None:
        src = """
from pytra.std.template import template

@template("T", "T")
def f(xs: list[int]) -> list[int]:
    return xs
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("duplicate template parameter", str(cm.exception))

    def test_template_decorator_rejects_keyword_form(self) -> None:
        src = """
from pytra.std.template import template

@template(name="T")
def f(xs: list[int]) -> list[int]:
    return xs
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("template decorator accepts positional string literal parameters only", str(cm.exception))

    def test_template_decorator_is_rejected_outside_runtime_helper_modules(self) -> None:
        src = """
from pytra.std.template import template

@template("T")
def f(xs: list[T]) -> list[T]:
    return xs
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(
                src,
                "sample/py/template_demo.py",
                parser_backend="self_hosted",
            )
        self.assertIn("@template is supported on runtime helper modules only", str(cm.exception))

    def test_method_level_abi_decorator_is_rejected(self) -> None:
        src = """
from pytra.std import abi

class Box:
    @abi(args={"xs": "value"})
    def f(self, xs: list[int]) -> list[int]:
        return xs
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("@abi is not supported on methods", str(cm.exception))

    def test_positional_abi_decorator_is_rejected(self) -> None:
        src = """
from pytra.std import abi

@abi("value")
def f(xs: list[int]) -> list[int]:
    return xs
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("abi decorator accepts keyword arguments only", str(cm.exception))

    def test_value_mut_is_rejected_for_return_mode(self) -> None:
        src = """
from pytra.std import abi

@abi(ret="value_mut")
def f(xs: list[int]) -> list[int]:
    return xs
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("unsupported abi mode for abi ret", str(cm.exception))

    def test_value_abi_rejects_mutating_append(self) -> None:
        src = """
from pytra.std import abi

@abi(args={"parts": "value"})
def py_join(parts: list[str]) -> str:
    parts.append("x")
    return ""
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("value parameter mutated", str(cm.exception))
        self.assertIn("parts", str(cm.exception))

    def test_sum_on_json_object_is_rejected_by_decode_first_guard(self) -> None:
        src = """
from pytra.std import json

def f(text: str) -> int:
    value = json.loads(text)
    return sum(value)
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("sum() does not accept object/Any values", str(cm.exception))

    def test_zip_on_json_values_is_rejected_by_decode_first_guard(self) -> None:
        src = """
from pytra.std import json

def f(lhs_text: str, rhs_text: str) -> None:
    lhs = json.loads(lhs_text)
    rhs = json.loads(rhs_text)
    _ = zip(lhs, rhs)
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("zip() does not accept object/Any values", str(cm.exception))

    def test_dict_keys_on_json_object_is_rejected_by_decode_first_guard(self) -> None:
        src = """
from pytra.std import json

def f(text: str) -> None:
    value = json.loads(text)
    _ = value.keys()
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("keys() does not accept object/Any receivers", str(cm.exception))

    def test_quoted_type_annotation_is_normalized(self) -> None:
        src = """
def f(p: "Path", xs: "list[int]") -> "Path":
    return p
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        funcs = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "f"]
        self.assertEqual(len(funcs), 1)
        fn = funcs[0]
        arg_types = fn.get("arg_types", {})
        self.assertEqual(arg_types.get("p"), "Path")
        self.assertEqual(arg_types.get("xs"), "list[int64]")
        self.assertEqual(fn.get("return_type"), "Path")
        arg_type_exprs = fn.get("arg_type_exprs", {})
        self.assertEqual(arg_type_exprs.get("p"), {"kind": "NamedType", "name": "Path"})
        self.assertEqual(
            arg_type_exprs.get("xs"),
            {
                "kind": "GenericType",
                "base": "list",
                "args": [{"kind": "NamedType", "name": "int64"}],
            },
        )
        self.assertEqual(fn.get("return_type_expr"), {"kind": "NamedType", "name": "Path"})

    def test_type_expr_is_emitted_for_union_optional_and_nested_generic_annotations(self) -> None:
        src = """
from pytra.std.json import JsonValue

def f(x: int | bool, ys: list[int | bool], payload: JsonValue | None) -> dict[str, int | bool]:
    local: list[int | bool] = []
    return {"a": 1}
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        fn = next(
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "f"
        )
        self.assertEqual(fn.get("arg_types", {}).get("x"), "int64|bool")
        self.assertEqual(fn.get("arg_types", {}).get("ys"), "list[int64|bool]")
        self.assertEqual(fn.get("arg_types", {}).get("payload"), "JsonValue | None")
        self.assertEqual(fn.get("return_type"), "dict[str,int64|bool]")

        arg_type_exprs = fn.get("arg_type_exprs", {})
        self.assertEqual(
            arg_type_exprs.get("x"),
            {
                "kind": "UnionType",
                "union_mode": "general",
                "options": [
                    {"kind": "NamedType", "name": "int64"},
                    {"kind": "NamedType", "name": "bool"},
                ],
            },
        )
        self.assertEqual(
            arg_type_exprs.get("ys"),
            {
                "kind": "GenericType",
                "base": "list",
                "args": [
                    {
                        "kind": "UnionType",
                        "union_mode": "general",
                        "options": [
                            {"kind": "NamedType", "name": "int64"},
                            {"kind": "NamedType", "name": "bool"},
                        ],
                    }
                ],
            },
        )
        self.assertEqual(
            arg_type_exprs.get("payload"),
            {
                "kind": "OptionalType",
                "inner": {
                    "kind": "NominalAdtType",
                    "name": "JsonValue",
                    "adt_family": "json",
                    "variant_domain": "closed",
                },
            },
        )
        self.assertEqual(
            fn.get("return_type_expr"),
            {
                "kind": "GenericType",
                "base": "dict",
                "args": [
                    {"kind": "NamedType", "name": "str"},
                    {
                        "kind": "UnionType",
                        "union_mode": "general",
                        "options": [
                            {"kind": "NamedType", "name": "int64"},
                            {"kind": "NamedType", "name": "bool"},
                        ],
                    },
                ],
            },
        )

        ann_assign = next(
            st for st in fn.get("body", []) if isinstance(st, dict) and st.get("kind") == "AnnAssign"
        )
        self.assertEqual(ann_assign.get("annotation"), "list[int64|bool]")
        self.assertEqual(
            ann_assign.get("annotation_type_expr"),
            {
                "kind": "GenericType",
                "base": "list",
                "args": [
                    {
                        "kind": "UnionType",
                        "union_mode": "general",
                        "options": [
                            {"kind": "NamedType", "name": "int64"},
                            {"kind": "NamedType", "name": "bool"},
                        ],
                    }
                ],
            },
        )

    def test_type_expr_is_built_for_union_optional_and_nominal_annotations(self) -> None:
        src = """
from pytra.std.json import JsonObj, JsonValue

def f(x: int | bool, xs: list[int | bool], payload: JsonValue | None) -> JsonObj | None:
    local: dict[str, int | bool] = {}
    return None
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        fn = next(
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "f"
        )
        arg_type_exprs = fn.get("arg_type_exprs", {})
        self.assertEqual(
            arg_type_exprs.get("x"),
            {
                "kind": "UnionType",
                "union_mode": "general",
                "options": [
                    {"kind": "NamedType", "name": "int64"},
                    {"kind": "NamedType", "name": "bool"},
                ],
            },
        )
        self.assertEqual(
            arg_type_exprs.get("xs"),
            {
                "kind": "GenericType",
                "base": "list",
                "args": [
                    {
                        "kind": "UnionType",
                        "union_mode": "general",
                        "options": [
                            {"kind": "NamedType", "name": "int64"},
                            {"kind": "NamedType", "name": "bool"},
                        ],
                    }
                ],
            },
        )
        self.assertEqual(
            arg_type_exprs.get("payload"),
            {
                "kind": "OptionalType",
                "inner": {
                    "kind": "NominalAdtType",
                    "name": "JsonValue",
                    "adt_family": "json",
                    "variant_domain": "closed",
                },
            },
        )
        self.assertEqual(
            fn.get("return_type_expr"),
            {
                "kind": "OptionalType",
                "inner": {
                    "kind": "NominalAdtType",
                    "name": "JsonObj",
                    "adt_family": "json",
                    "variant_domain": "closed",
                },
            },
        )
        ann_assign = next(
            n
            for n in fn.get("body", [])
            if isinstance(n, dict) and n.get("kind") == "AnnAssign"
        )
        expected_decl = {
            "kind": "GenericType",
            "base": "dict",
            "args": [
                {"kind": "NamedType", "name": "str"},
                {
                    "kind": "UnionType",
                    "union_mode": "general",
                    "options": [
                        {"kind": "NamedType", "name": "int64"},
                        {"kind": "NamedType", "name": "bool"},
                    ],
                },
            ],
        }
        self.assertEqual(ann_assign.get("annotation_type_expr"), expected_decl)
        self.assertEqual(ann_assign.get("decl_type_expr"), expected_decl)
        self.assertEqual(ann_assign.get("target", {}).get("type_expr"), expected_decl)

    def test_dict_set_comprehension_infers_target_type(self) -> None:
        src = """
def main() -> None:
    xs: list[int] = [1, 2, 3, 4]
    ys: set[int] = {x * x for x in xs if x % 2 == 1}
    ds: dict[int, int] = {x: x * x for x in xs if x % 2 == 0}
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        dict_comps = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "DictComp"]
        set_comps = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "SetComp"]
        self.assertEqual(len(dict_comps), 1)
        self.assertEqual(len(set_comps), 1)
        dc = dict_comps[0]
        sc = set_comps[0]
        self.assertEqual(dc.get("resolved_type"), "dict[int64,int64]")
        self.assertEqual(sc.get("resolved_type"), "set[int64]")
        self.assertEqual(dc.get("key", {}).get("resolved_type"), "int64")
        self.assertEqual(dc.get("value", {}).get("resolved_type"), "int64")
        self.assertEqual(sc.get("elt", {}).get("resolved_type"), "int64")
        d_ifs = dc.get("generators", [{}])[0].get("ifs", [])
        s_ifs = sc.get("generators", [{}])[0].get("ifs", [])
        self.assertEqual(len(d_ifs), 1)
        self.assertEqual(len(s_ifs), 1)

    def test_list_comprehension_over_range_uses_range_expr(self) -> None:
        src = """
def main() -> list[int]:
    return [x for x in range(3)]
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        list_comps = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "ListComp"]
        self.assertEqual(len(list_comps), 1)
        generators = list_comps[0].get("generators", [])
        self.assertEqual(len(generators), 1)
        iter_node = generators[0].get("iter", {})
        self.assertEqual(iter_node.get("kind"), "RangeExpr")
        self.assertEqual(iter_node.get("range_mode"), "ascending")
        self.assertEqual(iter_node.get("start", {}).get("value"), 0)
        self.assertEqual(iter_node.get("stop", {}).get("value"), 3)
        self.assertEqual(iter_node.get("step", {}).get("value"), 1)

    def test_lambda_expression_builds_lambda_node(self) -> None:
        src = """
def main() -> None:
    fn = lambda x: x + 1
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        lambdas = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Lambda"]
        self.assertEqual(len(lambdas), 1)
        lam = lambdas[0]
        self.assertEqual([arg.get("arg") for arg in lam.get("args", [])], ["x"])
        self.assertEqual(lam.get("body", {}).get("kind"), "BinOp")

    def test_fstring_builds_joinedstr_and_formatted_value_nodes(self) -> None:
        src = """
def main(name: str) -> str:
    return f"hello {name}"
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        joined = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "JoinedStr"]
        self.assertEqual(len(joined), 1)
        values = joined[0].get("values", [])
        formatted = [v for v in values if isinstance(v, dict) and v.get("kind") == "FormattedValue"]
        self.assertEqual(len(formatted), 1)
        self.assertEqual(formatted[0].get("value", {}).get("kind"), "Name")
        self.assertEqual(formatted[0].get("value", {}).get("id"), "name")

    def test_except_without_as_is_supported(self) -> None:
        src = """
def f(x: str) -> bool:
    try:
        _ = int(x)
        return True
    except ValueError:
        return False

def main() -> None:
    print(f("12"))

if __name__ == "__main__":
    main()
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        try_nodes = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Try"]
        self.assertEqual(len(try_nodes), 1)
        handlers = try_nodes[0].get("handlers", [])
        self.assertEqual(len(handlers), 1)
        self.assertIsNone(handlers[0].get("name"))

    def test_builtin_call_lowering_for_common_methods(self) -> None:
        src = """
from pathlib import Path

def main() -> None:
    s: str = "  abc  "
    t: str = s.strip()
    u: str = s.lstrip()
    p0: int = s.find("a")
    p1: int = s.rfind("a")
    blob: bytes = bytes()
    ba: bytearray = bytearray(blob)
    xs: list[int] = []
    xs.append(1)
    zp = zip(xs, xs)
    n: int = int("10", 16)
    o: object = xs
    b: bool = bool(o)
    it = iter(xs)
    first = next(it)
    ri = reversed(xs)
    en = enumerate(xs, 1)
    has_any: bool = any(xs)
    has_all: bool = all(xs)
    ch: str = chr(65)
    ocode: int = ord("A")
    r = range(3)
    ys: list[int] = list(xs)
    zs: set[int] = set(xs)
    d: dict[str, int] = {"a": 1}
    d2: dict[str, int] = dict(d)
    v: int = d.get("a", 0)
    p: Path = Path("tmp")
    ok: bool = p.exists()
    print(len(xs), t, u, p0, p1, len(ba), n, b, first, ri, en, zp, has_any, has_all, ch, ocode, len(ys), len(zs), len(d2), v, ok)

if __name__ == "__main__":
    main()
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        calls = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Call"]
        runtime_calls = {str(n.get("runtime_call")) for n in calls if n.get("lowered_kind") == "BuiltinCall"}
        semantic_tags = {str(n.get("semantic_tag")) for n in calls if n.get("lowered_kind") == "BuiltinCall"}
        self.assertIn("py_strip", runtime_calls)
        self.assertIn("py_lstrip", runtime_calls)
        self.assertIn("py_find", runtime_calls)
        self.assertIn("py_rfind", runtime_calls)
        self.assertIn("bytes_ctor", runtime_calls)
        self.assertIn("bytearray_ctor", runtime_calls)
        self.assertIn("py_iter_or_raise", runtime_calls)
        self.assertIn("py_next_or_stop", runtime_calls)
        self.assertIn("py_reversed", runtime_calls)
        self.assertIn("py_enumerate", runtime_calls)
        self.assertIn("zip", runtime_calls)
        self.assertIn("py_any", runtime_calls)
        self.assertIn("py_all", runtime_calls)
        self.assertIn("py_ord", runtime_calls)
        self.assertIn("py_chr", runtime_calls)
        self.assertIn("py_range", runtime_calls)
        self.assertIn("list_ctor", runtime_calls)
        self.assertIn("set_ctor", runtime_calls)
        self.assertIn("dict_ctor", runtime_calls)
        self.assertIn("py_to_bool", runtime_calls)
        self.assertIn("py_to_int64_base", runtime_calls)
        self.assertIn("list.append", runtime_calls)
        self.assertIn("dict.get", runtime_calls)
        self.assertIn("std::filesystem::exists", runtime_calls)
        self.assertIn("py_len", runtime_calls)
        self.assertIn("py_print", runtime_calls)
        self.assertIn("core.len", semantic_tags)
        self.assertIn("core.print", semantic_tags)
        self.assertIn("cast.bool", semantic_tags)
        self.assertIn("cast.int", semantic_tags)
        self.assertIn("iter.init", semantic_tags)
        self.assertIn("iter.next", semantic_tags)
        self.assertIn("logic.any", semantic_tags)
        self.assertIn("logic.all", semantic_tags)
        runtime_bindings = {
            str(n.get("runtime_call")): (str(n.get("runtime_module_id", "")), str(n.get("runtime_symbol", "")))
            for n in calls
            if n.get("lowered_kind") == "BuiltinCall" and isinstance(n.get("runtime_call"), str)
        }
        self.assertEqual(runtime_bindings.get("py_enumerate"), ("pytra.built_in.iter_ops", "enumerate"))
        self.assertEqual(runtime_bindings.get("py_any"), ("pytra.built_in.predicates", "any"))
        self.assertEqual(runtime_bindings.get("py_print"), ("pytra.built_in.io_ops", "py_print"))
        self.assertEqual(runtime_bindings.get("py_to_int64_base"), ("pytra.built_in.scalar_ops", "py_to_int64_base"))
        self.assertEqual(runtime_bindings.get("py_ord"), ("pytra.built_in.scalar_ops", "py_ord"))
        self.assertEqual(runtime_bindings.get("py_chr"), ("pytra.built_in.scalar_ops", "py_chr"))
        self.assertEqual(runtime_bindings.get("dict.get"), ("pytra.core.dict", "dict.get"))
        self.assertEqual(runtime_bindings.get("std::filesystem::exists"), ("pytra.std.pathlib", "Path.exists"))

    def test_perf_counter_resolved_type_comes_from_stdlib_signature(self) -> None:
        src = """
from pytra.std.time import perf_counter

def main() -> float:
    t0: float = perf_counter()
    return t0
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        calls = [
            n
            for n in _walk(east)
            if isinstance(n, dict)
            and n.get("kind") == "Call"
            and n.get("lowered_kind") == "BuiltinCall"
            and n.get("runtime_call") == "perf_counter"
        ]
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].get("resolved_type"), "float64")
        self.assertEqual(calls[0].get("runtime_module_id"), "pytra.std.time")
        self.assertEqual(calls[0].get("runtime_symbol"), "perf_counter")

    def test_noncpp_runtime_call_annotations_for_import_symbol_and_module_attr(self) -> None:
        src = """
from pytra.std import json
from pytra.utils import png, gif
from pytra.utils.assertions import py_assert_stdout
import math

def main() -> None:
    obj = json.loads("{\\"ok\\": true}")
    txt = json.dumps(obj)
    pixels: bytes = bytes([0, 0, 0])
    wave = math.sin(math.pi)
    png.write_rgb_png("x.png", 1, 1, pixels)
    palette = gif.grayscale_palette()
    gif.save_gif("x.gif", 1, 1, [pixels], palette, delay_cs=1, loop=0)
    py_assert_stdout("ok", txt + str(wave))
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        calls = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Call"]
        resolved_runtime_calls = {
            str(n.get("resolved_runtime_call"))
            for n in calls
            if isinstance(n.get("resolved_runtime_call"), str)
            and str(n.get("resolved_runtime_call")) != ""
        }
        self.assertIn("json.loads", resolved_runtime_calls)
        self.assertIn("json.dumps", resolved_runtime_calls)
        self.assertIn("write_rgb_png", resolved_runtime_calls)
        self.assertIn("save_gif", resolved_runtime_calls)
        self.assertIn("grayscale_palette", resolved_runtime_calls)
        self.assertIn("py_assert_stdout", resolved_runtime_calls)
        self.assertIn("math.sin", resolved_runtime_calls)
        math_sin_calls = [
            n for n in calls if isinstance(n.get("resolved_runtime_call"), str) and n.get("resolved_runtime_call") == "math.sin"
        ]
        self.assertEqual(len(math_sin_calls), 1)
        self.assertEqual(math_sin_calls[0].get("resolved_type"), "float64")
        self.assertEqual(math_sin_calls[0].get("runtime_module_id"), "math")
        self.assertEqual(math_sin_calls[0].get("runtime_symbol"), "sin")
        json_loads_calls = [
            n for n in calls if isinstance(n.get("resolved_runtime_call"), str) and n.get("resolved_runtime_call") == "json.loads"
        ]
        self.assertEqual(len(json_loads_calls), 1)
        self.assertEqual(json_loads_calls[0].get("runtime_module_id"), "pytra.std.json")
        self.assertEqual(json_loads_calls[0].get("runtime_symbol"), "loads")
        png_calls = [
            n for n in calls if isinstance(n.get("resolved_runtime_call"), str) and n.get("resolved_runtime_call") == "write_rgb_png"
        ]
        self.assertEqual(len(png_calls), 1)
        self.assertEqual(png_calls[0].get("runtime_module_id"), "pytra.utils.png")
        self.assertEqual(png_calls[0].get("runtime_symbol"), "write_rgb_png")
        attrs = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Attribute"]
        resolved_runtime_attrs = {
            str(n.get("resolved_runtime_call"))
            for n in attrs
            if isinstance(n.get("resolved_runtime_call"), str)
            and str(n.get("resolved_runtime_call")) != ""
        }
        self.assertIn("math.pi", resolved_runtime_attrs)
        math_pi_attrs = [
            n for n in attrs if isinstance(n.get("resolved_runtime_call"), str) and n.get("resolved_runtime_call") == "math.pi"
        ]
        self.assertEqual(len(math_pi_attrs), 1)
        self.assertEqual(math_pi_attrs[0].get("runtime_module_id"), "math")
        self.assertEqual(math_pi_attrs[0].get("runtime_symbol"), "pi")

    def test_json_decode_helpers_receive_json_semantic_tags(self) -> None:
        src = """
from pytra.std import json
from pytra.std.json import JsonArr, JsonObj, JsonValue

def main(text: str, value: JsonValue, obj: JsonObj, arr: JsonArr) -> None:
    root = json.loads(text)
    obj0 = json.loads_obj(text)
    arr0 = json.loads_arr(text)
    a = value.as_obj()
    b = value.as_int()
    c = obj.get_arr("items")
    d = arr.get_bool(0)
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        calls = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "Call" and isinstance(n.get("repr"), str)
        ]
        by_repr = {str(n.get("repr")): n for n in calls}
        self.assertEqual(by_repr["json.loads(text)"].get("semantic_tag"), "json.loads")
        self.assertEqual(by_repr["json.loads_obj(text)"].get("semantic_tag"), "json.loads_obj")
        self.assertEqual(by_repr["json.loads_arr(text)"].get("semantic_tag"), "json.loads_arr")
        self.assertEqual(by_repr["value.as_obj()"].get("semantic_tag"), "json.value.as_obj")
        self.assertEqual(by_repr["value.as_int()"].get("semantic_tag"), "json.value.as_int")
        self.assertEqual(by_repr['obj.get_arr("items")'].get("semantic_tag"), "json.obj.get_arr")
        self.assertEqual(by_repr["arr.get_bool(0)"].get("semantic_tag"), "json.arr.get_bool")

    def test_core_does_not_reintroduce_perf_counter_direct_branch(self) -> None:
        src = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        self.assertNotIn('fn_name == "perf_counter"', src)
        self.assertNotIn("fn_name == 'perf_counter'", src)

    def test_core_does_not_reintroduce_path_direct_branches(self) -> None:
        src = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        self.assertNotIn('fn_name == "Path"', src)
        self.assertNotIn("fn_name == 'Path'", src)
        self.assertNotIn('owner_t == "Path"', src)
        self.assertNotIn("owner_t == 'Path'", src)

    def test_core_semantic_tag_mapping_is_adapter_driven(self) -> None:
        src = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn("lookup_builtin_semantic_tag", src)
        self.assertIn("lookup_stdlib_function_semantic_tag", src)
        self.assertIn("lookup_stdlib_symbol_semantic_tag", src)
        self.assertIn("lookup_stdlib_method_semantic_tag", src)
        self.assertNotIn('payload["semantic_tag"] = "', src)

    def test_path_constructor_is_resolved_via_import_binding(self) -> None:
        src = """
from pathlib import Path as P
from pytra.std.pathlib import Path as PP

def main() -> None:
    p = P("out")
    q = PP("tmp")
    r = p / "a.txt"
    print(q, r)
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        calls = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Call"]
        path_ctor_calls = [
            n
            for n in calls
            if n.get("lowered_kind") == "BuiltinCall" and n.get("runtime_call") == "Path"
        ]
        self.assertEqual(len(path_ctor_calls), 2)
        for call in path_ctor_calls:
            self.assertEqual(call.get("resolved_type"), "Path")
            self.assertEqual(call.get("runtime_module_id"), "pytra.std.pathlib")
            self.assertEqual(call.get("runtime_symbol"), "Path")

        path_div_binops = [
            n
            for n in _walk(east)
            if isinstance(n, dict)
            and n.get("kind") == "BinOp"
            and n.get("op") == "Div"
            and n.get("resolved_type") == "Path"
        ]
        self.assertEqual(len(path_div_binops), 1)

    def test_path_mkdir_keywords_are_kept(self) -> None:
        src = """
from pathlib import Path

def main() -> None:
    p: Path = Path("out")
    p.mkdir(parents=True, exist_ok=True)
    print(True)

if __name__ == "__main__":
    main()
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        mkdir_calls = [
            n
            for n in _walk(east)
            if isinstance(n, dict)
            and n.get("kind") == "Call"
            and n.get("runtime_call") == "std::filesystem::create_directories"
        ]
        self.assertEqual(len(mkdir_calls), 1)
        kws = mkdir_calls[0].get("keywords", [])
        names = [k.get("arg") for k in kws if isinstance(k, dict)]
        self.assertIn("parents", names)
        self.assertIn("exist_ok", names)

    def test_path_property_attributes_are_lowered_with_runtime_call(self) -> None:
        src = """
from pathlib import Path

def main() -> None:
    p: Path = Path("out/a.txt")
    parent = p.parent
    name = p.name
    stem = p.stem
    print(parent, name, stem)
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        attrs = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Attribute"]
        path_attrs = [n for n in attrs if str(n.get("attr")) in {"parent", "name", "stem"}]
        self.assertEqual(len(path_attrs), 3)
        runtime_calls = {str(n.get("runtime_call")) for n in path_attrs}
        self.assertEqual(runtime_calls, {"path_parent", "path_name", "path_stem"})
        lowered_kinds = {str(n.get("lowered_kind")) for n in path_attrs}
        self.assertEqual(lowered_kinds, {"BuiltinAttr"})
        semantic_tags = {str(n.get("semantic_tag")) for n in path_attrs}
        self.assertEqual(
            semantic_tags,
            {"stdlib.method.parent", "stdlib.method.name", "stdlib.method.stem"},
        )

    def test_range_keywords_are_kept_for_builtin_call(self) -> None:
        src = """
def main() -> None:
    r = range(start=1, stop=5, step=2)
    print(r)
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        range_calls = [
            n
            for n in _walk(east)
            if isinstance(n, dict)
            and n.get("kind") == "Call"
            and n.get("lowered_kind") == "BuiltinCall"
            and n.get("runtime_call") == "py_range"
        ]
        self.assertEqual(len(range_calls), 1)
        kws = range_calls[0].get("keywords", [])
        names = [k.get("arg") for k in kws if isinstance(k, dict)]
        self.assertEqual(names, ["start", "stop", "step"])

    def test_numeric_literal_prefixes_are_parsed(self) -> None:
        src = """
def main() -> int:
    a: int = 0xFF
    b: int = 0X10
    return a + b
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        constants = [n.get("value") for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Constant"]
        self.assertIn(255, constants)
        self.assertIn(16, constants)

    def test_identifier_prefixed_with_import_is_not_import_stmt(self) -> None:
        src = """
def f() -> None:
    import_modules: dict[str, str] = {}
    print(import_modules)

if __name__ == "__main__":
    f()
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        funcs = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "f"]
        self.assertEqual(len(funcs), 1)
        body = funcs[0].get("body", [])
        ann = [n for n in body if isinstance(n, dict) and n.get("kind") == "AnnAssign"]
        self.assertEqual(len(ann), 1)
        target = ann[0].get("target")
        self.assertIsInstance(target, dict)
        self.assertEqual(target.get("id"), "import_modules")

    def test_future_annotations_is_not_emitted_to_east_imports(self) -> None:
        src = """
from __future__ import annotations
from pytra.std import json

def main() -> int:
    x: "int" = 1
    _ = json.dumps({"x": x})
    return x
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        import_from_nodes = [
            n
            for n in _walk(east)
            if isinstance(n, dict)
            and n.get("kind") == "ImportFrom"
        ]
        future_nodes = [n for n in import_from_nodes if n.get("module") == "__future__"]
        self.assertEqual(future_nodes, [])
        meta = east.get("meta", {})
        import_bindings = meta.get("import_bindings", [])
        self.assertIsInstance(import_bindings, list)
        for ent in import_bindings:
            if isinstance(ent, dict):
                self.assertNotEqual(ent.get("module_id"), "__future__")

    def test_typing_imports_are_annotation_only_noop(self) -> None:
        src = """
import typing
from typing import Any as A, List as L
from pytra.std import json

def main(xs: L[int]) -> A:
    _ = json.dumps({"n": len(xs)})
    return xs
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        import_nodes = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") in {"Import", "ImportFrom"}
        ]
        self.assertEqual(len(import_nodes), 1)
        self.assertEqual(import_nodes[0].get("kind"), "ImportFrom")
        self.assertEqual(import_nodes[0].get("module"), "pytra.std")

        meta = east.get("meta", {})
        import_bindings = meta.get("import_bindings", [])
        self.assertIsInstance(import_bindings, list)
        module_ids = [
            str(ent.get("module_id"))
            for ent in import_bindings
            if isinstance(ent, dict) and isinstance(ent.get("module_id"), str)
        ]
        self.assertNotIn("typing", module_ids)
        self.assertIn("pytra.std", module_ids)

    def test_typing_alias_is_resolved_without_runtime_import(self) -> None:
        src = """
from typing import List as L

def main() -> None:
    ys: L[int] = []
    print(ys)
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        fn = next(
            n
            for n in east.get("body", [])
            if isinstance(n, dict)
            and n.get("kind") == "FunctionDef"
            and (n.get("original_name") == "main" or n.get("name") == "main")
        )
        ann_assigns = [
            st for st in fn.get("body", []) if isinstance(st, dict) and st.get("kind") == "AnnAssign"
        ]
        self.assertEqual(len(ann_assigns), 1)
        self.assertEqual(ann_assigns[0].get("annotation"), "list[int64]")
        self.assertEqual(ann_assigns[0].get("value", {}).get("resolved_type"), "list[unknown]")

        import_bindings = east.get("meta", {}).get("import_bindings", [])
        self.assertEqual(import_bindings, [])

    def test_future_non_annotations_is_rejected(self) -> None:
        src = """
from __future__ import generator_stop
"""
        with self.assertRaises((EastBuildError, RuntimeError)) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("__future__", str(cm.exception))

    def test_builtin_call_nodes_always_have_runtime_call(self) -> None:
        src = """
from pathlib import Path

def main(xs: list[int], s: str, p: Path) -> None:
    _ = print(len(xs), str(1), int("10", 16), bool(xs), range(3), zip(xs, xs))
    _ = s.strip()
    _ = s.find("x")
    _ = p.exists()
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        builtin_calls = [
            n
            for n in _walk(east)
            if isinstance(n, dict)
            and n.get("kind") == "Call"
            and n.get("lowered_kind") == "BuiltinCall"
        ]
        self.assertGreater(len(builtin_calls), 0)
        missing_runtime = [
            n
            for n in builtin_calls
            if not isinstance(n.get("runtime_call"), str) or str(n.get("runtime_call")) == ""
        ]
        self.assertEqual(missing_runtime, [])

    def test_builtin_method_calls_keep_runtime_owner(self) -> None:
        src = """
from pathlib import Path

def main(xs: list[int], d: dict[str, int], s: str, n: int, p: Path) -> None:
    xs.append(1)
    _ = d.get("a", 0)
    _ = s.strip()
    _ = n.to_bytes(2, "little")
    _ = p.exists()
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        calls = [
            n
            for n in _walk(east)
            if isinstance(n, dict)
            and n.get("kind") == "Call"
            and n.get("lowered_kind") == "BuiltinCall"
        ]
        target_runtime_calls = {"list.append", "dict.get", "py_strip", "py_int_to_bytes", "std::filesystem::exists"}
        targets = [c for c in calls if str(c.get("runtime_call")) in target_runtime_calls]
        self.assertEqual(len(targets), 5)
        for c in targets:
            owner = c.get("runtime_owner")
            self.assertIsInstance(owner, dict)
            self.assertNotEqual(owner.get("kind"), "")

    def test_raw_range_call_is_lowered_out(self) -> None:
        src = """
def main() -> None:
    s: int = 0
    for i in range(3):
        s += i
    print(s)

if __name__ == "__main__":
    main()
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        calls = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Call"]
        has_raw_range = any(
            isinstance(c.get("func"), dict)
            and c.get("func", {}).get("kind") == "Name"
            and c.get("func", {}).get("id") == "range"
            for c in calls
        )
        self.assertFalse(has_raw_range)
        has_for_range = any(
            isinstance(n, dict) and n.get("kind") == "ForRange"
            for n in _walk(east)
        )
        self.assertTrue(has_for_range)

    def test_for_iter_mode_and_iterable_traits_are_annotated(self) -> None:
        src = """
def f(xs: list[int], d: dict[str, int], x: object) -> None:
    for a in xs:
        pass
    for k in d:
        pass
    for v in x:
        pass
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        funcs = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "f"]
        self.assertEqual(len(funcs), 1)
        body = funcs[0].get("body", [])
        for_nodes = [n for n in body if isinstance(n, dict) and n.get("kind") == "For"]
        self.assertEqual(len(for_nodes), 3)

        list_for = for_nodes[0]
        self.assertEqual(list_for.get("iter_mode"), "static_fastpath")
        self.assertEqual(list_for.get("iter_element_type"), "int64")
        self.assertEqual(list_for.get("iter", {}).get("iterable_trait"), "yes")
        self.assertEqual(list_for.get("iter", {}).get("iter_protocol"), "static_range")

        dict_for = for_nodes[1]
        self.assertEqual(dict_for.get("iter_mode"), "static_fastpath")
        self.assertEqual(dict_for.get("iter_element_type"), "str")
        self.assertEqual(dict_for.get("iter", {}).get("iterable_trait"), "yes")
        self.assertEqual(dict_for.get("iter", {}).get("iter_protocol"), "static_range")

        obj_for = for_nodes[2]
        self.assertEqual(obj_for.get("iter_mode"), "runtime_protocol")
        self.assertEqual(obj_for.get("iter_source_type"), "object")
        self.assertEqual(obj_for.get("iter", {}).get("iterable_trait"), "unknown")
        self.assertEqual(obj_for.get("iter", {}).get("iter_protocol"), "runtime_protocol")

    def test_super_call_is_parsed(self) -> None:
        src = """
class Base:
    def __init__(self) -> None:
        self.x: int = 1

class Child(Base):
    def __init__(self) -> None:
        super().__init__()
        self.x += 1

def main() -> None:
    c: Child = Child()
    print(c.x)

if __name__ == "__main__":
    main()
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        calls = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Call"]
        has_super = any(
            isinstance(c.get("func"), dict)
            and c.get("func", {}).get("kind") == "Attribute"
            and isinstance(c.get("func", {}).get("value"), dict)
            and c.get("func", {}).get("value", {}).get("kind") == "Call"
            and isinstance(c.get("func", {}).get("value", {}).get("func"), dict)
            and c.get("func", {}).get("value", {}).get("func", {}).get("kind") == "Name"
            and c.get("func", {}).get("value", {}).get("func", {}).get("id") == "super"
            for c in calls
        )
        self.assertTrue(has_super)

    def test_object_receiver_access_is_rejected(self) -> None:
        src = """
def f(x: object) -> int:
    return x.bit_length()

def main() -> None:
    print(f(1))

if __name__ == "__main__":
    main()
"""
        with self.assertRaises((EastBuildError, RuntimeError)):
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")

    def test_bare_return_is_parsed_as_return_stmt(self) -> None:
        src = """
def f(flag: bool) -> None:
    if flag:
        return
    print(1)

def main() -> None:
    f(True)
    print(True)

if __name__ == "__main__":
    main()
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        returns = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Return"]
        self.assertGreaterEqual(len(returns), 1)
        bare = [r for r in returns if r.get("value") is None]
        self.assertGreaterEqual(len(bare), 1)

    def test_class_storage_hint_override_is_supported(self) -> None:
        src = """
class Box:
    __pytra_class_storage_hint__ = "value"

    def __init__(self, x: int) -> None:
        self.x = x
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        classes = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "ClassDef" and n.get("name") == "Box"]
        self.assertEqual(len(classes), 1)
        cls = classes[0]
        self.assertEqual(cls.get("class_storage_hint"), "value")
        names = []
        for st in cls.get("body", []):
            if isinstance(st, dict) and st.get("kind") == "Assign":
                tgt = st.get("target")
                if isinstance(tgt, dict) and tgt.get("kind") == "Name":
                    names.append(tgt.get("id"))
        self.assertNotIn("__pytra_class_storage_hint__", names)

    def test_dataclass_scalar_fields_are_value_candidates(self) -> None:
        src = """
from dataclasses import dataclass

@dataclass
class Token:
    kind: str
    text: str
    pos: int
    number_value: int
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        classes = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "ClassDef" and n.get("name") == "Token"]
        self.assertEqual(len(classes), 1)
        self.assertEqual(classes[0].get("class_storage_hint"), "value")

    def test_dataclass_container_field_falls_back_to_ref(self) -> None:
        src = """
from dataclasses import dataclass

@dataclass
class Box:
    items: list[int]
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        classes = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "ClassDef" and n.get("name") == "Box"]
        self.assertEqual(len(classes), 1)
        self.assertEqual(classes[0].get("class_storage_hint"), "ref")

    def test_std_dataclasses_imports_are_noop_and_decorator_resolves(self) -> None:
        src = """
import dataclasses as dc
from dataclasses import dataclass as d

@dc.dataclass(eq=False)
class A:
    x: int

@d(init=False, frozen=True)
class B:
    y: int
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")

        import_nodes = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") in {"Import", "ImportFrom"}
        ]
        self.assertEqual(import_nodes, [])

        import_bindings = east.get("meta", {}).get("import_bindings", [])
        self.assertIsInstance(import_bindings, list)
        for ent in import_bindings:
            if isinstance(ent, dict):
                self.assertNotEqual(ent.get("module_id"), "dataclasses")

        classes = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "ClassDef" and n.get("name") in {"A", "B"}
        ]
        self.assertEqual(len(classes), 2)
        by_name = {str(c.get("name")): c for c in classes}
        self.assertTrue(bool(by_name["A"].get("dataclass")))
        self.assertTrue(bool(by_name["B"].get("dataclass")))
        opts_a = by_name["A"].get("dataclass_options", {})
        opts_b = by_name["B"].get("dataclass_options", {})
        self.assertIsInstance(opts_a, dict)
        self.assertIsInstance(opts_b, dict)
        self.assertEqual(opts_a.get("eq"), False)
        self.assertEqual(opts_b.get("init"), False)
        self.assertEqual(opts_b.get("frozen"), True)

    def test_enum_members_are_parsed_in_class_body(self) -> None:
        src = """
from pytra.std.enum import Enum

class Color(Enum):
    RED = 1
    BLUE = 2
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        classes = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "ClassDef" and n.get("name") == "Color"]
        self.assertEqual(len(classes), 1)
        cls = classes[0]
        self.assertEqual(cls.get("base"), "Enum")
        self.assertEqual(cls.get("class_storage_hint"), "value")
        members: list[str] = []
        for st in cls.get("body", []):
            if isinstance(st, dict) and st.get("kind") == "Assign":
                tgt = st.get("target")
                if isinstance(tgt, dict) and tgt.get("kind") == "Name":
                    members.append(str(tgt.get("id", "")))
        self.assertIn("RED", members)
        self.assertIn("BLUE", members)

    def test_parser_accepts_bom_line_continuation_and_pow(self) -> None:
        src = """\ufefffrom pytra.std import math

def main() -> None:
    x: int = 1 + \\
        2
    y: float = math.sqrt(float(x ** 2))
    print(x, y)
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        binops = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "BinOp"]
        has_pow = any(b.get("op") == "Pow" for b in binops)
        self.assertTrue(has_pow)

    def test_parser_accepts_top_level_expr_class_pass_nested_def_and_tuple_trailing_comma(self) -> None:
        src = """
class E:
    X = 0,
    pass

def outer() -> int:
    def inner(x: int) -> int:
        return x + 1
    return inner(2)

print(outer())
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        classes = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "ClassDef" and n.get("name") == "E"]
        self.assertEqual(len(classes), 1)
        tuples = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Tuple"]
        self.assertGreaterEqual(len(tuples), 1)
        nested_fns = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "inner"
        ]
        self.assertEqual(len(nested_fns), 1)
        exprs = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Expr"]
        self.assertGreaterEqual(len(exprs), 1)

    def test_yield_is_parsed_as_generator_function(self) -> None:
        src = """
def gen(n: int) -> int:
    i: int = 0
    while i < n:
        yield i
        i += 1
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        funcs = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "gen"]
        self.assertEqual(len(funcs), 1)
        fn = funcs[0]
        self.assertEqual(fn.get("is_generator"), 1)
        self.assertEqual(fn.get("return_type"), "list[int64]")
        yields = [n for n in _walk(fn.get("body", [])) if isinstance(n, dict) and n.get("kind") == "Yield"]
        self.assertGreaterEqual(len(yields), 1)

    def test_single_line_for_with_yield_is_parsed(self) -> None:
        src = """
def gen() -> int:
    for _ in range(3): yield 1
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        funcs = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "gen"]
        self.assertEqual(len(funcs), 1)
        fn = funcs[0]
        self.assertEqual(fn.get("is_generator"), 1)
        for_ranges = [n for n in _walk(fn.get("body", [])) if isinstance(n, dict) and n.get("kind") == "ForRange"]
        self.assertEqual(len(for_ranges), 1)
        yields = [n for n in _walk(for_ranges[0].get("body", [])) if isinstance(n, dict) and n.get("kind") == "Yield"]
        self.assertEqual(len(yields), 1)

    def test_arg_usage_tracks_reassigned_parameters(self) -> None:
        src = """
def f(x: int, y: int, z: int, w: int) -> int:
    x = x + 1
    for y in range(2):
        z += y
    return x + z + w
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        funcs = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "f"]
        self.assertEqual(len(funcs), 1)
        fn = funcs[0]
        arg_usage = fn.get("arg_usage", {})
        self.assertEqual(arg_usage.get("x"), "reassigned")
        self.assertEqual(arg_usage.get("y"), "reassigned")
        self.assertEqual(arg_usage.get("z"), "reassigned")
        self.assertEqual(arg_usage.get("w"), "readonly")

    def test_arg_usage_ignores_nested_scope_reassignment(self) -> None:
        src = """
def outer(a: int) -> int:
    def inner(a: int) -> int:
        a = a + 1
        return a
    return inner(a)
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        outer_funcs = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "outer"]
        self.assertEqual(len(outer_funcs), 1)
        outer = outer_funcs[0]
        outer_usage = outer.get("arg_usage", {})
        self.assertEqual(outer_usage.get("a"), "readonly")

        inner_funcs = [n for n in _walk(outer.get("body", [])) if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "inner"]
        self.assertEqual(len(inner_funcs), 1)
        inner = inner_funcs[0]
        inner_usage = inner.get("arg_usage", {})
        self.assertEqual(inner_usage.get("a"), "reassigned")

    def test_trailing_semicolon_is_rejected(self) -> None:
        src = """
def main() -> None:
    x: int = 1;
    print(x)
"""
        with self.assertRaises((EastBuildError, RuntimeError)) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("statement terminator", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
