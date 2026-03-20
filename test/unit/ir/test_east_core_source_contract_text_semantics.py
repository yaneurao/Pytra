"""Source-contract regressions for EAST core text/import helper clusters."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import CORE_SOURCE_PATH
from _east_core_test_support import CORE_MODULE_PARSER_SOURCE_PATH
from _east_core_test_support import CORE_STMT_PARSER_SOURCE_PATH
from _east_core_test_support import CORE_TEXT_SEMANTICS_SOURCE_PATH


class EastCoreSourceContractTextSemanticsTest(unittest.TestCase):
    def test_core_source_moves_text_import_helpers_out_of_core(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = CORE_TEXT_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("from toolchain.compile.core_text_semantics import _sh_is_identifier", core_text)
        self.assertIn("from toolchain.compile.core_text_semantics import _sh_strip_utf8_bom", core_text)
        self.assertIn("from toolchain.compile.core_text_semantics import _sh_is_dotted_identifier", core_text)
        self.assertIn("from toolchain.compile.core_text_semantics import _sh_split_top_keyword", core_text)
        self.assertIn("from toolchain.compile.core_text_semantics import _sh_split_top_level_as", core_text)
        self.assertIn("from toolchain.compile.core_text_semantics import _sh_parse_import_alias", core_text)
        self.assertIn("from toolchain.compile.core_text_semantics import _sh_parse_dataclass_decorator_options", core_text)

        self.assertIn("def _sh_is_identifier(", helper_text)
        self.assertIn("def _sh_strip_utf8_bom(", helper_text)
        self.assertIn("def _sh_is_dotted_identifier(", helper_text)
        self.assertIn("def _sh_split_top_keyword(", helper_text)
        self.assertIn("def _sh_split_top_level_as(", helper_text)
        self.assertIn("def _sh_parse_import_alias(", helper_text)
        self.assertIn("def _sh_normalize_import_from_names_text(", helper_text)
        self.assertIn("def _sh_parse_import_from_clause(", helper_text)
        self.assertIn("def _sh_parse_dataclass_decorator_options(", helper_text)

        self.assertNotIn("def _sh_is_identifier(", core_text)
        self.assertNotIn("def _sh_strip_utf8_bom(", core_text)
        self.assertNotIn("def _sh_is_dotted_identifier(", core_text)
        self.assertNotIn("def _sh_split_top_keyword(", core_text)
        self.assertNotIn("def _sh_split_top_level_as(", core_text)
        self.assertNotIn("def _sh_parse_import_alias(", core_text)
        self.assertNotIn("def _sh_normalize_import_from_names_text(", core_text)
        self.assertNotIn("def _sh_parse_import_from_clause(", core_text)
        self.assertNotIn("def _sh_parse_dataclass_decorator_options(", core_text)

    def test_core_source_routes_import_and_dataclass_text_parsing_through_helper_module(self) -> None:
        module_parser_text = CORE_MODULE_PARSER_SOURCE_PATH.read_text(encoding="utf-8")
        stmt_parser_text = CORE_STMT_PARSER_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("source = _sh_strip_utf8_bom(source)", module_parser_text)
        self.assertIn("_sh_parse_import_alias(part, allow_dotted_name=True)", module_parser_text)
        self.assertIn("_sh_parse_import_alias(part, allow_dotted_name=False)", module_parser_text)
        self.assertIn("import_from_clause = _sh_parse_import_from_clause(s)", module_parser_text)
        self.assertIn("_sh_parse_dataclass_decorator_options(", module_parser_text)
        self.assertIn("split_top_commas=_sh_split_top_commas", module_parser_text)
        self.assertIn("split_top_level_assign=_sh_split_top_level_assign", module_parser_text)
        self.assertIn("is_identifier=_sh_is_identifier", module_parser_text)
        self.assertIn("make_east_build_error=_make_east_build_error", module_parser_text)
        self.assertIn("make_span=_sh_span", module_parser_text)
        self.assertIn("_sh_parse_import_alias(part, allow_dotted_name=True)", stmt_parser_text)
        self.assertIn("_sh_parse_import_alias(part, allow_dotted_name=False)", stmt_parser_text)
        self.assertIn("import_from_clause = _sh_parse_import_from_clause(s)", stmt_parser_text)


if __name__ == "__main__":
    unittest.main()
