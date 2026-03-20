"""Source-contract regressions for EAST core expression precedence parser cluster."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import CORE_EXPR_PRECEDENCE_SOURCE_PATH
from _east_core_test_support import CORE_EXPR_SHELL_SOURCE_PATH
from _east_core_test_support import CORE_SOURCE_PATH


class EastCoreSourceContractExprPrecedenceTest(unittest.TestCase):
    def test_core_source_routes_precedence_parser_through_split_mixin(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        shell_text = CORE_EXPR_SHELL_SOURCE_PATH.read_text(encoding="utf-8")
        precedence_text = CORE_EXPR_PRECEDENCE_SOURCE_PATH.read_text(encoding="utf-8")
        class_text = shell_text.split("class _ShExprParser(", 1)[1].split("def _sh_parse_expr", 1)[0]

        self.assertIn("class _ShExprPrecedenceParserMixin:", precedence_text)
        self.assertIn("def _parse_lambda(", precedence_text)
        self.assertIn("def _parse_ifexp(", precedence_text)
        self.assertIn("def _parse_compare(", precedence_text)
        self.assertIn("def _parse_unary(", precedence_text)
        self.assertIn('"Invert"', precedence_text)
        self.assertIn('{"+", "-", "~"}', precedence_text)
        self.assertIn("from toolchain.compile.core_expr_shell import _ShExprParser", core_text)
        self.assertIn("_ShExprPrecedenceParserMixin,", shell_text)

        self.assertNotIn("def _parse_lambda(", class_text)
        self.assertNotIn("def _parse_ifexp(", class_text)
        self.assertNotIn("def _parse_compare(", class_text)
        self.assertNotIn("def _parse_unary(", class_text)

    def test_precedence_mixin_uses_shared_build_error_and_builder_helpers(self) -> None:
        precedence_text = CORE_EXPR_PRECEDENCE_SOURCE_PATH.read_text(encoding="utf-8")
        shell_text = CORE_EXPR_SHELL_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("raise self._raise_expr_build_error(", precedence_text)
        self.assertIn("def _raise_expr_build_error(", shell_text)
        self.assertIn("_sh_make_lambda_expr(", precedence_text)
        self.assertIn("_sh_make_ifexp_expr(", precedence_text)
        self.assertIn("_sh_make_boolop_expr(", precedence_text)
        self.assertIn("_sh_make_compare_expr(", precedence_text)
        self.assertIn("_sh_make_unaryop_expr(", precedence_text)


if __name__ == "__main__":
    unittest.main()
