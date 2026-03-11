"""Source-contract regressions for EAST core string/f-string helper clusters."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import CORE_EXPR_PARSER_BASE_SOURCE_PATH
from _east_core_test_support import CORE_EXPR_PRIMARY_SOURCE_PATH
from _east_core_test_support import CORE_SOURCE_PATH
from _east_core_test_support import CORE_STRING_SEMANTICS_SOURCE_PATH


class EastCoreSourceContractStringSemanticsTest(unittest.TestCase):
    def test_core_source_moves_string_helpers_out_of_core(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        parser_base_text = CORE_EXPR_PARSER_BASE_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = CORE_STRING_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("from toolchain.ir.core_string_semantics import _sh_append_fstring_literal", core_text)
        self.assertIn("from toolchain.ir.core_string_semantics import _sh_decode_py_string_body", core_text)
        self.assertIn("from toolchain.ir.core_string_semantics import _sh_extract_adjacent_string_parts", core_text)
        self.assertIn("from toolchain.ir.core_string_semantics import _sh_scan_string_token", parser_base_text)

        self.assertIn("def _sh_extract_adjacent_string_parts(", helper_text)
        self.assertIn("def _sh_scan_string_token(", helper_text)
        self.assertIn("def _sh_decode_py_string_body(", helper_text)
        self.assertIn("def _sh_append_fstring_literal(", helper_text)

        self.assertNotIn("def _sh_extract_adjacent_string_parts(", core_text)
        self.assertNotIn("def _sh_scan_string_token(", core_text)
        self.assertNotIn("def _sh_decode_py_string_body(", core_text)
        self.assertNotIn("def _sh_append_fstring_literal(", core_text)

    def test_core_source_routes_string_and_fstring_parsing_through_helper_module(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        parser_base_text = CORE_EXPR_PARSER_BASE_SOURCE_PATH.read_text(encoding="utf-8")
        primary_text = CORE_EXPR_PRIMARY_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = CORE_STRING_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("_sh_scan_string_token(", parser_base_text)
        self.assertIn("make_east_build_error=lambda *, kind, message, source_span, hint:", parser_base_text)
        self.assertIn("self._raise_expr_build_error(", parser_base_text)
        self.assertIn("make_span=_sh_span", parser_base_text)
        self.assertIn("_sh_append_fstring_literal(", primary_text)
        self.assertIn('body = _sh_decode_py_string_body(body, "r" in prefix)', primary_text)

        self.assertIn("make_east_build_error: Any", helper_text)
        self.assertIn("make_span: Any", helper_text)
        self.assertIn("from toolchain.ir.core_expr_shell import _ShExprParser", helper_text)
        self.assertIn("parser = _ShExprParser(", helper_text)
        self.assertIn('lit = segment.replace("{{", "{").replace("}}", "}")', helper_text)
        self.assertIn("lit = _sh_decode_py_string_body(lit, raw_mode)", helper_text)


if __name__ == "__main__":
    unittest.main()
