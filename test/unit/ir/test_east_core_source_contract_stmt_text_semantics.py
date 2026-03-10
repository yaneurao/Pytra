"""Source-contract regressions for EAST core statement/header text helper clusters."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import CORE_SOURCE_PATH
from _east_core_test_support import CORE_STMT_TEXT_SEMANTICS_SOURCE_PATH


class EastCoreSourceContractStmtTextSemanticsTest(unittest.TestCase):
    def test_core_source_moves_stmt_text_helpers_out_of_core(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = CORE_STMT_TEXT_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("from toolchain.ir.core_stmt_text_semantics import _sh_parse_class_header", core_text)
        self.assertIn("from toolchain.ir.core_stmt_text_semantics import _sh_parse_class_header_base_list", core_text)
        self.assertIn("from toolchain.ir.core_stmt_text_semantics import _sh_parse_except_clause", core_text)
        self.assertIn(
            "from toolchain.ir.core_stmt_text_semantics import _sh_raise_if_trailing_stmt_terminator",
            core_text,
        )
        self.assertIn("from toolchain.ir.core_stmt_text_semantics import _sh_split_def_header_and_inline_stmt", core_text)
        self.assertIn("from toolchain.ir.core_stmt_text_semantics import _sh_scan_logical_line_state", core_text)
        self.assertIn("from toolchain.ir.core_stmt_text_semantics import _sh_has_explicit_line_continuation", core_text)
        self.assertIn("from toolchain.ir.core_stmt_text_semantics import _sh_merge_logical_lines", core_text)
        self.assertIn("from toolchain.ir.core_stmt_text_semantics import _sh_split_top_commas", core_text)
        self.assertIn("from toolchain.ir.core_stmt_text_semantics import _sh_split_top_plus", core_text)
        self.assertIn("from toolchain.ir.core_stmt_text_semantics import _sh_find_top_char", core_text)
        self.assertIn("from toolchain.ir.core_stmt_text_semantics import _sh_infer_item_type", core_text)
        self.assertIn("from toolchain.ir.core_stmt_text_semantics import _sh_bind_comp_target_types", core_text)
        self.assertIn("from toolchain.ir.core_stmt_text_semantics import _sh_collect_indented_block", core_text)
        self.assertIn("from toolchain.ir.core_stmt_text_semantics import _sh_split_top_level_assign", core_text)
        self.assertIn("from toolchain.ir.core_stmt_text_semantics import _sh_split_top_level_colon", core_text)
        self.assertIn("from toolchain.ir.core_stmt_text_semantics import _sh_split_top_level_from", core_text)
        self.assertIn("from toolchain.ir.core_stmt_text_semantics import _sh_split_top_level_in", core_text)
        self.assertIn("from toolchain.ir.core_stmt_text_semantics import _sh_strip_inline_comment", core_text)

        self.assertIn("def _sh_split_def_header_and_inline_stmt(", helper_text)
        self.assertIn("def _sh_scan_logical_line_state(", helper_text)
        self.assertIn("def _sh_has_explicit_line_continuation(", helper_text)
        self.assertIn("def _sh_merge_logical_lines(", helper_text)
        self.assertIn("def _sh_split_top_commas(", helper_text)
        self.assertIn("def _sh_split_top_plus(", helper_text)
        self.assertIn("def _sh_find_top_char(", helper_text)
        self.assertIn("def _sh_infer_item_type(", helper_text)
        self.assertIn("def _sh_bind_comp_target_types(", helper_text)
        self.assertIn("def _sh_collect_indented_block(", helper_text)
        self.assertIn("def _sh_split_top_level_assign(", helper_text)
        self.assertIn("def _sh_strip_inline_comment(", helper_text)
        self.assertIn("def _sh_raise_if_trailing_stmt_terminator(", helper_text)
        self.assertIn("def _sh_split_top_level_from(", helper_text)
        self.assertIn("def _sh_split_top_level_in(", helper_text)
        self.assertIn("def _sh_split_top_level_colon(", helper_text)
        self.assertIn("def _sh_parse_except_clause(", helper_text)
        self.assertIn("def _sh_parse_class_header_base_list(", helper_text)
        self.assertIn("def _sh_parse_class_header(", helper_text)

        self.assertNotIn("def _sh_split_def_header_and_inline_stmt(", core_text)
        self.assertNotIn("def _sh_scan_logical_line_state(", core_text)
        self.assertNotIn("def _sh_has_explicit_line_continuation(", core_text)
        self.assertNotIn("def _sh_merge_logical_lines(", core_text)
        self.assertNotIn("def _sh_split_top_commas(", core_text)
        self.assertNotIn("def _sh_split_top_plus(", core_text)
        self.assertNotIn("def _sh_find_top_char(", core_text)
        self.assertNotIn("def _sh_infer_item_type(", core_text)
        self.assertNotIn("def _sh_bind_comp_target_types(", core_text)
        self.assertNotIn("def _sh_collect_indented_block(", core_text)
        self.assertNotIn("def _sh_split_top_level_assign(", core_text)
        self.assertNotIn("def _sh_strip_inline_comment(", core_text)
        self.assertNotIn("def _sh_raise_if_trailing_stmt_terminator(", core_text)
        self.assertNotIn("def _sh_split_top_level_from(", core_text)
        self.assertNotIn("def _sh_split_top_level_in(", core_text)
        self.assertNotIn("def _sh_split_top_level_colon(", core_text)
        self.assertNotIn("def _sh_parse_except_clause(", core_text)
        self.assertNotIn("def _sh_parse_class_header_base_list(", core_text)
        self.assertNotIn("def _sh_parse_class_header(", core_text)

    def test_core_source_routes_stmt_text_parsing_through_helper_module(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("make_east_build_error=_make_east_build_error", core_text)
        self.assertIn("make_span=_sh_span", core_text)
        self.assertIn("_sh_merge_logical_lines(", core_text)
        self.assertIn("_sh_collect_indented_block(", core_text)
        self.assertIn("_sh_bind_comp_target_types(dict(name_types), target_node, iter_node)", core_text)
        self.assertIn("_sh_split_def_header_and_inline_stmt(", core_text)
        self.assertIn("split_top_commas=_sh_split_top_commas", core_text)
        self.assertIn("_sh_parse_except_clause(h_s)", core_text)
        self.assertIn("_sh_split_top_level_from(expr_txt)", core_text)
        self.assertIn("_sh_split_top_level_in(for_head)", core_text)
        self.assertIn("_sh_split_top_level_colon(for_full)", core_text)
        self.assertIn("_sh_split_top_level_assign(s)", core_text)


if __name__ == "__main__":
    unittest.main()
