"""Source-contract regressions for EAST core statement analysis helper clusters."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import CORE_SOURCE_PATH
from _east_core_test_support import CORE_MODULE_PARSER_SOURCE_PATH
from _east_core_test_support import CORE_STMT_ANALYSIS_SOURCE_PATH
from _east_core_test_support import CORE_STMT_PARSER_SOURCE_PATH


class EastCoreSourceContractStmtAnalysisTest(unittest.TestCase):
    def test_core_source_moves_stmt_analysis_helpers_out_of_core(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = CORE_STMT_ANALYSIS_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("from toolchain.compile.core_stmt_analysis import _sh_extract_leading_docstring", core_text)
        self.assertIn("from toolchain.compile.core_stmt_analysis import _sh_collect_yield_value_types", core_text)
        self.assertIn("from toolchain.compile.core_stmt_analysis import _sh_collect_return_value_types", core_text)
        self.assertIn(
            "from toolchain.compile.core_stmt_analysis import _sh_infer_return_type_for_untyped_def",
            core_text,
        )
        self.assertIn("from toolchain.compile.core_stmt_analysis import _sh_collect_store_name_ids", core_text)
        self.assertIn("from toolchain.compile.core_stmt_analysis import _sh_collect_reassigned_names", core_text)
        self.assertIn("from toolchain.compile.core_stmt_analysis import _sh_build_arg_usage_map", core_text)
        self.assertIn("from toolchain.compile.core_stmt_analysis import _sh_make_generator_return_type", core_text)

        self.assertIn("def _sh_extract_leading_docstring(", helper_text)
        self.assertIn("def _sh_collect_yield_value_types(", helper_text)
        self.assertIn("def _sh_collect_return_value_types(", helper_text)
        self.assertIn("def _sh_infer_return_type_for_untyped_def(", helper_text)
        self.assertIn("def _sh_collect_store_name_ids(", helper_text)
        self.assertIn("def _sh_collect_reassigned_names(", helper_text)
        self.assertIn("def _sh_build_arg_usage_map(", helper_text)
        self.assertIn("def _sh_make_generator_return_type(", helper_text)

        self.assertNotIn("def _sh_extract_leading_docstring(", core_text)
        self.assertNotIn("def _sh_collect_yield_value_types(", core_text)
        self.assertNotIn("def _sh_collect_return_value_types(", core_text)
        self.assertNotIn("def _sh_infer_return_type_for_untyped_def(", core_text)
        self.assertNotIn("def _sh_collect_store_name_ids(", core_text)
        self.assertNotIn("def _sh_collect_reassigned_names(", core_text)
        self.assertNotIn("def _sh_build_arg_usage_map(", core_text)
        self.assertNotIn("def _sh_make_generator_return_type(", core_text)

    def test_core_source_routes_stmt_analysis_through_helper_module(self) -> None:
        module_text = CORE_MODULE_PARSER_SOURCE_PATH.read_text(encoding="utf-8")
        stmt_text = CORE_STMT_PARSER_SOURCE_PATH.read_text(encoding="utf-8")
        surface_text = module_text + "\n" + stmt_text
        helper_text = CORE_STMT_ANALYSIS_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("yield_types = _sh_collect_yield_value_types(fn_stmts)", surface_text)
        self.assertIn("fn_ret = _sh_infer_return_type_for_untyped_def(fn_ret, fn_stmts)", surface_text)
        self.assertIn("docstring, fn_stmts = _sh_extract_leading_docstring(fn_stmts)", surface_text)
        self.assertIn("arg_usage_map = _sh_build_arg_usage_map(arg_order, arg_types, fn_stmts)", surface_text)
        self.assertIn("_sh_collect_store_name_ids(st.get(\"target\"), out)", helper_text)
        self.assertIn("out.update(_sh_collect_reassigned_names(body))", helper_text)


if __name__ == "__main__":
    unittest.main()
