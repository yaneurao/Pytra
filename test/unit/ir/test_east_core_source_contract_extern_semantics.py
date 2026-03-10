"""Source-contract regressions for EAST core extern helper clusters."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import CORE_EXTERN_SEMANTICS_SOURCE_PATH
from _east_core_test_support import CORE_SOURCE_PATH


class EastCoreSourceContractExternSemanticsTest(unittest.TestCase):
    def test_core_source_moves_extern_helpers_out_of_core(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = CORE_EXTERN_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("from toolchain.ir.core_extern_semantics import _sh_collect_extern_var_metadata", core_text)
        self.assertIn("def _sh_expr_attr_chain(", helper_text)
        self.assertIn("def _sh_is_extern_symbol_ref(", helper_text)
        self.assertIn("def _sh_collect_extern_var_metadata(", helper_text)
        self.assertNotIn("def _sh_expr_attr_chain(", core_text)
        self.assertNotIn("def _sh_is_extern_symbol_ref(", core_text)
        self.assertNotIn("def _sh_collect_extern_var_metadata(", core_text)

    def test_core_source_routes_extern_binding_annotation_through_helper_module(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("extern_var_meta = _sh_collect_extern_var_metadata(", core_text)


if __name__ == "__main__":
    unittest.main()
