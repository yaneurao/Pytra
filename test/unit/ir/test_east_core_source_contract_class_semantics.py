"""Source-contract regressions for EAST core class/declaration semantics clusters."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import CORE_CLASS_SEMANTICS_SOURCE_PATH
from _east_core_test_support import CORE_MODULE_PARSER_SOURCE_PATH
from _east_core_test_support import CORE_SOURCE_PATH


class EastCoreSourceContractClassSemanticsTest(unittest.TestCase):
    def test_core_source_moves_class_semantics_helpers_out_of_core(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = CORE_CLASS_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("from toolchain.compile.core_class_semantics import _sh_collect_nominal_adt_class_metadata", core_text)
        self.assertIn("from toolchain.compile.core_class_semantics import _sh_is_value_safe_dataclass_candidate", core_text)
        self.assertIn("from toolchain.compile.core_class_semantics import _sh_make_decl_meta", core_text)
        self.assertIn("from toolchain.compile.core_class_semantics import _sh_make_nominal_adt_v1_meta", core_text)
        self.assertIn("def _sh_make_decl_meta(", helper_text)
        self.assertIn("def _sh_make_nominal_adt_v1_meta(", helper_text)
        self.assertIn("def _sh_is_value_safe_dataclass_field_type(", helper_text)
        self.assertIn("def _sh_is_value_safe_dataclass_candidate(", helper_text)
        self.assertIn("def _sh_collect_nominal_adt_class_metadata(", helper_text)
        self.assertIn("_SH_VALUE_SAFE_CLASS_FIELD_TYPES", helper_text)
        self.assertNotIn("def _sh_make_decl_meta(", core_text)
        self.assertNotIn("def _sh_make_nominal_adt_v1_meta(", core_text)
        self.assertNotIn("def _sh_is_value_safe_dataclass_field_type(", core_text)
        self.assertNotIn("def _sh_is_value_safe_dataclass_candidate(", core_text)
        self.assertNotIn("def _sh_collect_nominal_adt_class_metadata(", core_text)

    def test_core_source_routes_nominal_adt_metadata_through_class_semantics_helper(self) -> None:
        module_text = CORE_MODULE_PARSER_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("class_meta = _sh_collect_nominal_adt_class_metadata(", module_text)
        self.assertIn("is_sealed_decorator=_sh_is_sealed_decorator", module_text)
        self.assertIn("parse_decorator_head_and_args=_sh_parse_decorator_head_and_args", module_text)
        self.assertIn("make_east_build_error=_make_east_build_error", module_text)
        self.assertIn("make_span=_sh_span", module_text)


if __name__ == "__main__":
    unittest.main()
