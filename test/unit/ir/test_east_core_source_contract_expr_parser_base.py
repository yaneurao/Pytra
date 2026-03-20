"""Source-contract regressions for EAST core expression parser base cluster."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import CORE_EXPR_PARSER_BASE_SOURCE_PATH
from _east_core_test_support import CORE_EXPR_SHELL_SOURCE_PATH
from _east_core_test_support import CORE_SOURCE_PATH


class EastCoreSourceContractExprParserBaseTest(unittest.TestCase):
    def test_core_source_routes_expr_parser_base_through_split_mixin(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        shell_text = CORE_EXPR_SHELL_SOURCE_PATH.read_text(encoding="utf-8")
        base_text = CORE_EXPR_PARSER_BASE_SOURCE_PATH.read_text(encoding="utf-8")
        class_text = shell_text.split("class _ShExprParser(", 1)[1].split("def _sh_parse_expr", 1)[0]

        self.assertIn("class _ShExprParserBaseMixin:", base_text)
        self.assertIn("from toolchain.compile.core_expr_shell import _ShExprParser", core_text)
        self.assertIn("from toolchain.compile.core_expr_parser_base import _ShExprParserBaseMixin", shell_text)
        self.assertIn("_ShExprParserBaseMixin,", shell_text)

        for marker in (
            "def _tokenize(",
            "def _cur(",
            "def _eat(",
            "def _node_span(",
            "def _src_slice(",
            "def parse(",
        ):
            self.assertIn(marker, base_text)
            self.assertNotIn(marker, class_text)

    def test_parser_base_mixin_keeps_tokenizer_and_parse_contracts(self) -> None:
        base_text = CORE_EXPR_PARSER_BASE_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("_sh_scan_string_token(", base_text)
        self.assertIn("_sh_make_expr_token(", base_text)
        self.assertIn('"~"', base_text)
        self.assertIn("raise self._raise_expr_build_error(", base_text)
        self.assertIn("return self.tokens[self.pos]", base_text)
        self.assertIn('self._eat("EOF")', base_text)


if __name__ == "__main__":
    unittest.main()
