"""Source-contract regressions for EAST core builder clusters."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import CORE_AST_BUILDERS_SOURCE_PATH
from _east_core_test_support import CORE_ATTR_SUBSCRIPT_ANNOTATION_SOURCE_PATH
from _east_core_test_support import CORE_BUILDER_BASE_SOURCE_PATH
from _east_core_test_support import CORE_CLASS_SEMANTICS_SOURCE_PATH
from _east_core_test_support import CORE_EXPR_LOWERED_SOURCE_PATH
from _east_core_test_support import CORE_EXPR_PRIMARY_SOURCE_PATH
from _east_core_test_support import CORE_EXPR_PRECEDENCE_SOURCE_PATH
from _east_core_test_support import CORE_MODULE_PARSER_SOURCE_PATH
from _east_core_test_support import CORE_SOURCE_PATH
from _east_core_test_support import CORE_STMT_PARSER_SOURCE_PATH


class EastCoreSourceContractBuildersTest(unittest.TestCase):
    def test_builder_defs_live_in_split_modules(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        base_text = CORE_BUILDER_BASE_SOURCE_PATH.read_text(encoding="utf-8")
        ast_text = CORE_AST_BUILDERS_SOURCE_PATH.read_text(encoding="utf-8")
        class_text = CORE_CLASS_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")

        for marker in (
            "def _sh_make_kind_carrier(",
            "def _sh_make_node(",
            "def _sh_make_stmt_node(",
            "def _sh_make_trivia_blank(",
            "def _sh_make_trivia_comment(",
            "def _sh_make_expr_token(",
            "def _sh_make_expr_stmt(",
            "def _sh_make_value_expr(",
            "def _sh_make_name_expr(",
            "def _sh_make_tuple_expr(",
        ):
            self.assertIn(marker, base_text)
            self.assertNotIn(marker, core_text)

        for marker in (
            "def _sh_make_constant_expr(",
            "def _sh_make_unaryop_expr(",
            "def _sh_make_boolop_expr(",
            "def _sh_make_compare_expr(",
            "def _sh_make_binop_expr(",
            "def _sh_make_cast_entry(",
            "def _sh_make_ifexp_expr(",
            "def _sh_make_attribute_expr(",
            "def _sh_make_call_expr(",
            "def _sh_make_keyword_arg(",
            "def _sh_make_slice_node(",
            "def _sh_make_subscript_expr(",
            "def _sh_make_comp_generator(",
            "def _sh_make_list_expr(",
            "def _sh_make_set_expr(",
            "def _sh_make_dict_entry(",
            "def _sh_make_dict_expr(",
            "def _sh_make_list_comp_expr(",
            "def _sh_make_simple_name_list_comp_expr(",
            "def _sh_make_simple_name_comp_generator(",
            "def _sh_make_builtin_listcomp_call_expr(",
            "def _sh_make_dict_comp_expr(",
            "def _sh_make_set_comp_expr(",
            "def _sh_make_range_expr(",
            "def _sh_make_arg_node(",
            "def _sh_make_lambda_arg_entry(",
            "def _sh_make_lambda_expr(",
            "def _sh_make_formatted_value_node(",
            "def _sh_make_joined_str_expr(",
            "def _sh_make_def_sig_info(",
            "def _sh_block_end_span(",
            "def _sh_stmt_span(",
            "def _sh_push_stmt_with_trivia(",
        ):
            self.assertIn(marker, ast_text)
            self.assertNotIn(marker, core_text)

        self.assertIn("def _sh_make_decl_meta(", class_text)
        self.assertIn("def _sh_make_nominal_adt_v1_meta(", class_text)
        self.assertNotIn("def _sh_make_decl_meta(", core_text)
        self.assertNotIn("def _sh_make_nominal_adt_v1_meta(", core_text)
        self.assertIn("vararg_name: str = \"\"", ast_text)
        self.assertIn("vararg_type_expr: dict[str, Any] | None = None", ast_text)

    def test_split_builder_modules_route_through_shared_envelopes(self) -> None:
        base_text = CORE_BUILDER_BASE_SOURCE_PATH.read_text(encoding="utf-8")
        ast_text = CORE_AST_BUILDERS_SOURCE_PATH.read_text(encoding="utf-8")

        node_helper_text = base_text.split("def _sh_make_node", 1)[1].split("def _sh_make_stmt_node", 1)[0]
        value_helper_text = base_text.split("def _sh_make_value_expr", 1)[1].split("def _sh_make_name_expr", 1)[0]
        call_text = ast_text.split("def _sh_make_call_expr", 1)[1].split("def _sh_make_keyword_arg", 1)[0]
        slice_text = ast_text.split("def _sh_make_slice_node", 1)[1].split("def _sh_make_subscript_expr", 1)[0]
        span_text = ast_text.split("def _sh_block_end_span", 1)[1].split("def _sh_stmt_span", 1)[0]
        stmt_span_text = ast_text.split("def _sh_stmt_span", 1)[1].split("def _sh_push_stmt_with_trivia", 1)[0]

        self.assertIn('node = _sh_make_kind_carrier(kind)', node_helper_text)
        self.assertIn("node.update(fields)", node_helper_text)
        self.assertIn("casts=[] if casts is None else casts", value_helper_text)
        self.assertIn('node = _sh_make_value_expr(', call_text)
        self.assertIn('"Call"', call_text)
        self.assertIn('return _sh_make_node("Slice", lower=lower, upper=upper, step=step)', slice_text)
        self.assertIn("return _sh_span(start_ln, start_col, len(end_txt), end_lineno=end_ln)", span_text)
        self.assertIn("return _sh_span(start_ln, start_col, end_col, end_lineno=end_ln)", stmt_span_text)
        self.assertNotIn('payload = {"kind": "Call"', call_text)
        self.assertNotIn('node = _sh_make_kind_carrier("Slice")', slice_text)

    def test_core_source_uses_split_builder_helpers_at_call_sites(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        module_parser_text = CORE_MODULE_PARSER_SOURCE_PATH.read_text(encoding="utf-8")
        stmt_parser_text = CORE_STMT_PARSER_SOURCE_PATH.read_text(encoding="utf-8")
        lowered_text = CORE_EXPR_LOWERED_SOURCE_PATH.read_text(encoding="utf-8")
        attr_annotation_text = CORE_ATTR_SUBSCRIPT_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        ast_text = CORE_AST_BUILDERS_SOURCE_PATH.read_text(encoding="utf-8")
        primary_text = CORE_EXPR_PRIMARY_SOURCE_PATH.read_text(encoding="utf-8")
        precedence_text = CORE_EXPR_PRECEDENCE_SOURCE_PATH.read_text(encoding="utf-8")
        surface_text = "\n".join(
            (
                module_parser_text,
                stmt_parser_text,
                attr_annotation_text,
                primary_text,
                precedence_text,
                lowered_text,
            )
        )

        self.assertIn("out = _sh_make_module_root(", module_parser_text)
        self.assertIn("item = _sh_make_function_def_stmt(", module_parser_text)
        self.assertIn("cls_item = _sh_make_class_def_stmt(", module_parser_text)
        self.assertIn("node = _sh_make_attribute_expr(", attr_annotation_text)
        self.assertIn("payload = _sh_make_call_expr(", ast_text)
        self.assertIn("_sh_make_subscript_expr(", attr_annotation_text)
        self.assertIn("return _sh_make_lambda_expr(", precedence_text)
        self.assertIn("_sh_make_formatted_value_node(", primary_text)
        self.assertIn("return _sh_make_joined_str_expr(", primary_text)
        self.assertIn("_sh_make_expr_stmt(expr_stmt, _sh_stmt_span(", stmt_parser_text)
        self.assertIn("_sh_make_simple_name_list_comp_expr(", lowered_text)
        self.assertIn("_sh_make_builtin_listcomp_call_expr(", lowered_text)
        self.assertNotIn('node = {"kind": "Attribute"', surface_text)
        self.assertNotIn('payload = {"kind": "Call"', surface_text)
        self.assertNotIn('return {"kind": "Lambda"', surface_text)
        self.assertNotIn('values.append({"kind": "FormattedValue"', surface_text)
        self.assertNotIn('return {"kind": "JoinedStr"', surface_text)
        self.assertNotIn('return {"kind": "Constant"', surface_text)
        self.assertNotIn('return {"kind": "ListComp"', surface_text)
        self.assertNotIn('return {"kind": "DictComp"', surface_text)
        self.assertNotIn(
            'pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, {"kind": "Expr"',
            surface_text,
        )

    def test_core_source_keeps_import_and_extern_clusters_on_split_helpers(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        class_text = CORE_CLASS_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")
        module_parser_text = CORE_MODULE_PARSER_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("from toolchain.compile.core_class_semantics import _sh_collect_nominal_adt_class_metadata", text)
        self.assertIn("class_meta = _sh_collect_nominal_adt_class_metadata(", module_parser_text)
        self.assertIn("def _sh_collect_nominal_adt_class_metadata(", class_text)
        self.assertNotIn("class_meta = _sh_collect_nominal_adt_class_metadata(", text)
        self.assertNotIn("def _sh_collect_nominal_adt_class_metadata(", text)
        self.assertNotIn('_SH_IMPORT_SYMBOLS[local] = {"module": module, "name": export}', text)
        self.assertNotIn('pre_import_symbol_bindings[alias_name] = {', text)
        self.assertNotIn('import_symbol_bindings[bind_name_dc] = {', text)
        self.assertNotIn('import_symbol_bindings[bind_name] = {', text)
        self.assertNotIn("for key, value in resolution.items():", text)
        self.assertNotIn('meta["runtime_abi_v1"] = runtime_abi_meta', text)
        self.assertNotIn('meta["template_v1"] = template_meta', text)
        self.assertNotIn('ann_item["meta"] = {"extern_var_v1": extern_var_meta}', text)


if __name__ == "__main__":
    unittest.main()
