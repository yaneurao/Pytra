"""Source-contract regressions for EAST core type annotation helper clusters."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import CORE_MODULE_PARSER_SOURCE_PATH
from _east_core_test_support import CORE_SOURCE_PATH
from _east_core_test_support import CORE_STMT_PARSER_SOURCE_PATH
from _east_core_test_support import CORE_TYPE_SEMANTICS_SOURCE_PATH


class EastCoreSourceContractTypeSemanticsTest(unittest.TestCase):
    def test_core_source_moves_type_helper_cluster_out_of_core(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = CORE_TYPE_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("from toolchain.compile.core_type_semantics import _sh_default_type_aliases", core_text)
        self.assertIn("from toolchain.compile.core_type_semantics import _sh_is_type_expr_text", core_text)
        self.assertIn("from toolchain.compile.core_type_semantics import _sh_typing_alias_to_type_name", core_text)
        self.assertIn("from toolchain.compile.core_type_semantics import _sh_register_type_alias", core_text)
        self.assertIn("from toolchain.compile.core_type_semantics import _sh_ann_to_type", core_text)
        self.assertIn("from toolchain.compile.core_type_semantics import _sh_ann_to_type_expr", core_text)
        self.assertIn("def _sh_default_type_aliases(", helper_text)
        self.assertIn("def _sh_is_type_expr_text(", helper_text)
        self.assertIn("def _sh_typing_alias_to_type_name(", helper_text)
        self.assertIn("def _sh_register_type_alias(", helper_text)
        self.assertIn("def _sh_ann_to_type(", helper_text)
        self.assertIn("def _sh_ann_to_type_expr(", helper_text)
        self.assertIn("def _sh_type_expr_to_type_name(", helper_text)
        self.assertIn("def _sh_split_args_with_offsets(", helper_text)

        self.assertNotIn("def _sh_default_type_aliases(", core_text)
        self.assertNotIn("def _sh_is_type_expr_text(", core_text)
        self.assertNotIn("def _sh_typing_alias_to_type_name(", core_text)
        self.assertNotIn("def _sh_register_type_alias(", core_text)
        self.assertNotIn("def _sh_ann_to_type(", core_text)
        self.assertNotIn("def _sh_ann_to_type_expr(", core_text)
        self.assertNotIn("def _sh_type_expr_to_type_name(", core_text)
        self.assertNotIn("def _sh_split_args_with_offsets(", core_text)

    def test_core_source_routes_type_alias_and_annotation_parsing_through_helper_module(self) -> None:
        module_parser_text = CORE_MODULE_PARSER_SOURCE_PATH.read_text(encoding="utf-8")
        stmt_parser_text = CORE_STMT_PARSER_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("target = _sh_typing_alias_to_type_name(sym_txt)", module_parser_text)
        self.assertIn("_sh_register_type_alias(type_aliases, pre_left, pre_right)", module_parser_text)
        self.assertIn("ann = _sh_ann_to_type(ann_txt, type_aliases=_SH_TYPE_ALIASES)", stmt_parser_text)
        self.assertIn(
            "fn_ret_type_expr = _sh_ann_to_type_expr(fn_ret_effective, type_aliases=_SH_TYPE_ALIASES)",
            stmt_parser_text,
        )


if __name__ == "__main__":
    unittest.main()
