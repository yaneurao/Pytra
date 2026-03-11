"""Source-contract regressions for EAST core primary-expression helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import CORE_EXPR_PRIMARY_SOURCE_PATH
from _east_core_test_support import CORE_EXPR_SHELL_SOURCE_PATH
from _east_core_test_support import CORE_SOURCE_PATH


class EastCoreSourceContractExprPrimaryTest(unittest.TestCase):
    def test_primary_cluster_defs_live_in_split_module(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        shell_text = CORE_EXPR_SHELL_SOURCE_PATH.read_text(encoding="utf-8")
        primary_text = CORE_EXPR_PRIMARY_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("def _make_bin_impl(", primary_text)
        self.assertIn("def _parse_primary_impl(", primary_text)
        self.assertIn("class _ShExprPrimaryParserMixin:", primary_text)
        self.assertNotIn("def _make_bin_impl(", shell_text)
        self.assertNotIn("def _parse_primary_impl(", shell_text)
        self.assertIn("from toolchain.ir.core_expr_shell import _ShExprParser", core_text)
        self.assertIn("from toolchain.ir.core_expr_primary import _make_bin_impl", shell_text)
        self.assertIn("from toolchain.ir.core_expr_primary import _ShExprPrimaryParserMixin", shell_text)

    def test_core_wrappers_delegate_primary_cluster_to_split_module(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        shell_text = CORE_EXPR_SHELL_SOURCE_PATH.read_text(encoding="utf-8")

        make_bin_text = shell_text.split("def _make_bin", 1)[1].split("def _sh_parse_expr", 1)[0]

        self.assertIn("from toolchain.ir.core_expr_shell import _sh_parse_expr", core_text)
        self.assertIn("return _make_bin_impl(self, left, op_sym, right)", make_bin_text)
        self.assertNotIn("op_map = {", make_bin_text)
        self.assertNotIn("def _parse_primary(", core_text)

    def test_split_primary_module_keeps_primary_parse_logic(self) -> None:
        primary_text = CORE_EXPR_PRIMARY_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("def _reparse_expr_with_context(", primary_text)
        self.assertIn("def _parse_primary(self) -> dict[str, Any]:", primary_text)
        self.assertIn("return _parse_primary_impl(self)", primary_text)
        self.assertIn('if tok["k"] == "INT":', primary_text)
        self.assertIn("_sh_append_fstring_literal(", primary_text)
        self.assertIn("_sh_make_list_comp_expr(", primary_text)
        self.assertIn("_sh_make_dict_comp_expr(", primary_text)
        self.assertIn('message=f"self_hosted parser cannot parse expression token:', primary_text)
        self.assertIn("from toolchain.ir.core_expr_shell import _sh_parse_expr", primary_text)


if __name__ == "__main__":
    unittest.main()
