"""Source-contract regressions for EAST core if/elif/else tail helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import CORE_SOURCE_PATH
from _east_core_test_support import CORE_STMT_PARSER_SOURCE_PATH
from _east_core_test_support import CORE_STMT_IF_SEMANTICS_SOURCE_PATH


class EastCoreSourceContractIfSemanticsTest(unittest.TestCase):
    def test_core_source_moves_if_tail_helper_out_of_core(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = CORE_STMT_IF_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("from toolchain.compile.core_stmt_if_semantics import _sh_parse_if_tail", core_text)
        self.assertIn("def _sh_parse_if_tail(", helper_text)

        self.assertNotIn("def _sh_parse_if_tail(", core_text)

    def test_core_source_routes_if_tail_callback_dependencies_through_split_helper(self) -> None:
        stmt_text = CORE_STMT_PARSER_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("strip_inline_comment=_sh_strip_inline_comment", stmt_text)
        self.assertIn("raise_if_trailing_stmt_terminator=_sh_raise_if_trailing_stmt_terminator", stmt_text)
        self.assertIn("make_east_build_error=_make_east_build_error", stmt_text)
        self.assertIn("make_span=_sh_span", stmt_text)
        self.assertIn("collect_indented_block=_sh_collect_indented_block", stmt_text)
        self.assertIn("parse_expr_lowered=_sh_parse_expr_lowered", stmt_text)
        self.assertIn("parse_stmt_block=_sh_parse_stmt_block", stmt_text)
        self.assertIn("make_if_stmt=_sh_make_if_stmt", stmt_text)
        self.assertIn("block_end_span=_sh_block_end_span", stmt_text)


if __name__ == "__main__":
    unittest.main()
