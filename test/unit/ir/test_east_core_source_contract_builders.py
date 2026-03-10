"""Source-contract regressions for EAST core builder clusters."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import CORE_SOURCE_PATH


class EastCoreSourceContractBuildersTest(unittest.TestCase):
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
        self.assertIn("def _sh_make_nominal_adt_v1_meta(", text)
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
        self.assertIn("def _sh_collect_nominal_adt_class_metadata(", text)
        self.assertIn("class_meta = _sh_collect_nominal_adt_class_metadata(", text)
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
        self.assertIn("_sh_make_subscript_expr(", text)
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
        arg_text = text.split("def _sh_make_arg_node", 1)[1].split("def _sh_make_lambda_arg_entry", 1)[0]
        formatted_text = text.split("def _sh_make_formatted_value_node", 1)[1].split("def _sh_make_joined_str_expr", 1)[0]
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
        self.assertIn('node = _sh_make_node(', arg_text)
        self.assertIn('"arg"', arg_text)
        self.assertIn('node = _sh_make_node("FormattedValue", value=value)', formatted_text)
        self.assertIn('return _sh_make_node("Slice", lower=lower, upper=upper, step=step)', slice_text)
        self.assertNotIn('"kind": "Name"', name_text)
        self.assertNotIn('"kind": "Tuple"', tuple_text)
        self.assertNotIn('"kind": "Call"', call_text)
        self.assertNotIn('"kind": "Dict"', dict_text)
        self.assertNotIn('"kind": "arg"', arg_text)
        self.assertNotIn('"kind": "FormattedValue"', formatted_text)
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
        module_text = text.split("def _sh_make_module_root", 1)[1].split("def _sh_ann_to_type", 1)[0]

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
        self.assertIn('return _sh_make_node(', module_text)
        self.assertIn('"Module"', module_text)
        self.assertNotIn('{"kind": "Expr"', expr_text)
        self.assertNotIn('{"kind": "Assign"', assign_text)
        self.assertNotIn('"kind": "ExceptHandler"', except_text)
        self.assertNotIn('{"kind": "Try"', try_text)
        self.assertNotIn('{"kind": "FunctionDef"', fn_text)
        self.assertNotIn('"kind": "Module"', module_text)

    def test_core_source_uses_builder_helpers_for_residual_stmt_name_tuple_clusters(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn("_sh_make_ann_assign_stmt(", text)
        self.assertIn("def _sh_make_tuple_destructure_assign_stmt(", text)
        self.assertIn("_sh_make_tuple_destructure_assign_stmt(", text)
        self.assertIn("def _sh_make_simple_name_list_comp_expr(", text)
        self.assertIn("_sh_make_simple_name_list_comp_expr(", text)
        self.assertIn("def _sh_make_simple_name_comp_generator(", text)
        self.assertIn("_sh_make_simple_name_comp_generator(", text)
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
        self.assertNotIn('dict<str, object>{{"kind", make_object("Name")}', text)

    def test_core_source_uses_builder_helpers_for_literal_and_target_clusters(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        name_target_text = text.split("def _parse_name_comp_target", 1)[1].split(
            "def _parse_tuple_comp_target", 1
        )[0]
        tuple_target_text = text.split("def _parse_tuple_comp_target", 1)[1].split(
            "def _parse_comp_target", 1
        )[0]
        comp_target_text = text.split("def _parse_comp_target", 1)[1].split(
            "def _collect_and_bind_comp_target_types", 1
        )[0]
        primary_text = text.split("def _parse_primary", 1)[1].split("def _sh_parse_expr", 1)[0]

        self.assertIn('if self._cur()["k"] != "NAME":', name_target_text)
        self.assertIn("first_node = _sh_make_name_expr(", name_target_text)
        self.assertIn("return _sh_make_tuple_expr(", name_target_text)
        self.assertIn('if self._cur()["k"] != "(":', tuple_target_text)
        self.assertIn("elems.append(self._parse_comp_target())", tuple_target_text)
        self.assertIn("return _sh_make_tuple_expr(", tuple_target_text)
        self.assertIn("name_target = self._parse_name_comp_target()", comp_target_text)
        self.assertIn("if name_target is not None:", comp_target_text)
        self.assertIn("tuple_target = self._parse_tuple_comp_target()", comp_target_text)
        self.assertIn("if tuple_target is not None:", comp_target_text)
        self.assertIn("return _sh_make_constant_expr(", primary_text)
        self.assertIn("return _sh_make_name_expr(", primary_text)
        self.assertIn("return _sh_make_tuple_expr(", primary_text)
        self.assertIn("return _sh_make_list_expr(", primary_text)
        self.assertIn("return _sh_make_dict_expr(", primary_text)
        self.assertIn("return _sh_make_set_expr(", primary_text)
        self.assertNotIn('first_node = {"kind": "Name"', name_target_text)
        self.assertNotIn("first_node = _sh_make_name_expr(", comp_target_text)
        self.assertNotIn("return _sh_make_tuple_expr(", comp_target_text)
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
