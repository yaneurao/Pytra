"""Source-contract regressions for dataclass field metadata helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import CORE_DATACLASS_FIELD_SEMANTICS_SOURCE_PATH
from _east_core_test_support import CORE_MODULE_PARSER_SOURCE_PATH


class EastCoreSourceContractDataclassFieldSemanticsTest(unittest.TestCase):
    def test_dataclass_field_helper_module_owns_supported_options_and_collectors(self) -> None:
        helper_text = CORE_DATACLASS_FIELD_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn('_SH_DATACLASS_FIELD_BOOL_OPTIONS = {"init", "repr", "compare"}', helper_text)
        self.assertIn('_SH_DATACLASS_FIELD_EXPR_OPTIONS = {"default", "default_factory"}', helper_text)
        self.assertIn("def _sh_make_dataclass_field_v1_meta(", helper_text)
        self.assertIn("def _sh_is_dataclass_field_call(", helper_text)
        self.assertIn("def _sh_collect_dataclass_field_metadata(", helper_text)
        self.assertIn("unsupported dataclass field option", helper_text)
        self.assertIn("duplicate dataclass field option", helper_text)
        self.assertIn("cannot use both default and default_factory", helper_text)

    def test_module_parser_routes_field_metadata_through_helper_module(self) -> None:
        module_text = CORE_MODULE_PARSER_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn(
            "from toolchain.compile.core_module_parser_support import (",
            module_text,
        )
        self.assertIn("_sh_collect_dataclass_field_metadata,", module_text)
        self.assertIn("field_meta = _sh_collect_dataclass_field_metadata(", module_text)
        self.assertIn("_sh_make_decl_meta(dataclass_field_v1=field_meta)", module_text)


if __name__ == "__main__":
    unittest.main()
