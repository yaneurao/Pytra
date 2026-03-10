"""Source-contract regressions for EAST core decorator helper clusters."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import CORE_DECORATOR_SEMANTICS_SOURCE_PATH
from _east_core_test_support import CORE_SOURCE_PATH


class EastCoreSourceContractDecoratorsTest(unittest.TestCase):
    def test_core_source_moves_decorator_helpers_out_of_core(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = CORE_DECORATOR_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("from toolchain.ir.core_decorator_semantics import _sh_is_abi_decorator", core_text)
        self.assertIn("from toolchain.ir.core_decorator_semantics import _sh_is_dataclass_decorator", core_text)
        self.assertIn("from toolchain.ir.core_decorator_semantics import _sh_is_sealed_decorator", core_text)
        self.assertIn("from toolchain.ir.core_decorator_semantics import _sh_is_template_decorator", core_text)
        self.assertIn("from toolchain.ir.core_decorator_semantics import _sh_parse_decorator_head_and_args", core_text)
        self.assertIn("def _sh_parse_decorator_head_and_args(", helper_text)
        self.assertIn("def _sh_is_dataclass_decorator(", helper_text)
        self.assertIn("def _sh_is_sealed_decorator(", helper_text)
        self.assertIn("def _sh_is_abi_decorator(", helper_text)
        self.assertIn("def _sh_is_template_decorator(", helper_text)
        self.assertNotIn("def _sh_parse_decorator_head_and_args(", core_text)
        self.assertNotIn("def _sh_is_dataclass_decorator(", core_text)
        self.assertNotIn("def _sh_is_sealed_decorator(", core_text)
        self.assertNotIn("def _sh_is_abi_decorator(", core_text)
        self.assertNotIn("def _sh_is_template_decorator(", core_text)

    def test_core_source_routes_class_and_runtime_decorator_checks_through_helper_module(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("if _sh_is_dataclass_decorator(", core_text)
        self.assertIn("if _sh_is_sealed_decorator(decorator_text):", core_text)
        self.assertIn("_sh_reject_runtime_decl_class_decorators(", core_text)
        self.assertIn("_sh_reject_runtime_decl_method_decorator(", core_text)
        self.assertIn("_sh_reject_runtime_decl_nonfunction_decorators(", core_text)
        self.assertIn("parse_decorator_head_and_args=_sh_parse_decorator_head_and_args", core_text)


if __name__ == "__main__":
    unittest.main()
