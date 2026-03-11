"""Source-contract regressions for EAST core signature helper clusters."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import CORE_SIGNATURE_SEMANTICS_SOURCE_PATH
from _east_core_test_support import CORE_SOURCE_PATH


class EastCoreSourceContractSignatureSemanticsTest(unittest.TestCase):
    def test_core_source_moves_signature_helpers_out_of_core(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = CORE_SIGNATURE_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("from toolchain.ir.core_signature_semantics import _sh_parse_augassign", core_text)
        self.assertIn("from toolchain.ir.core_signature_semantics import _sh_parse_def_sig", core_text)
        self.assertIn("from toolchain.ir.core_signature_semantics import _sh_parse_typed_binding", core_text)

        self.assertIn("def _sh_parse_typed_binding(", helper_text)
        self.assertIn("def _sh_parse_augassign(", helper_text)
        self.assertIn("def _sh_parse_def_sig(", helper_text)

        self.assertNotIn("def _sh_parse_typed_binding(", core_text)
        self.assertNotIn("def _sh_parse_augassign(", core_text)
        self.assertNotIn("def _sh_parse_def_sig(", core_text)

    def test_core_source_routes_signature_helpers_through_callback_injection(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("_sh_parse_typed_binding(s, allow_dotted_name=True)", core_text)
        self.assertIn("_sh_parse_typed_binding(s, allow_dotted_name=False)", core_text)
        self.assertIn("_sh_parse_augassign(s)", core_text)
        self.assertIn("type_aliases=_SH_TYPE_ALIASES", core_text)
        self.assertIn("make_east_build_error=_make_east_build_error", core_text)
        self.assertIn("make_span=_sh_span", core_text)
        self.assertIn("make_def_sig_info=_sh_make_def_sig_info", core_text)


if __name__ == "__main__":
    unittest.main()
