"""Source-contract regressions for EAST core import helper clusters."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import CORE_IMPORT_SEMANTICS_SOURCE_PATH
from _east_core_test_support import CORE_MODULE_PARSER_SOURCE_PATH
from _east_core_test_support import CORE_SOURCE_PATH
from _east_core_test_support import CORE_STMT_PARSER_SOURCE_PATH


class EastCoreSourceContractImportSemanticsTest(unittest.TestCase):
    def test_core_source_moves_import_helper_cluster_out_of_core(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = CORE_IMPORT_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("from toolchain.compile.core_import_semantics import _sh_append_import_binding", core_text)
        self.assertIn("from toolchain.compile.core_import_semantics import _sh_import_binding_fields", core_text)
        self.assertIn("from toolchain.compile.core_import_semantics import _sh_is_host_only_alias", core_text)
        self.assertIn("from toolchain.compile.core_import_semantics import _sh_make_import_resolution_binding", core_text)
        self.assertIn("from toolchain.compile.core_import_semantics import _sh_register_import_module", core_text)
        self.assertIn("from toolchain.compile.core_import_semantics import _sh_register_import_symbol", core_text)

        self.assertIn("def _sh_append_import_binding(", helper_text)
        self.assertIn("def _sh_import_binding_fields(", helper_text)
        self.assertIn("def _sh_make_import_resolution_binding(", helper_text)
        self.assertIn("def _sh_is_host_only_alias(", helper_text)
        self.assertIn("def _sh_register_import_symbol(", helper_text)
        self.assertIn("def _sh_register_import_module(", helper_text)

        self.assertNotIn("def _sh_append_import_binding(", core_text)
        self.assertNotIn("def _sh_import_binding_fields(", core_text)
        self.assertNotIn("def _sh_make_import_resolution_binding(", core_text)
        self.assertNotIn("def _sh_is_host_only_alias(", core_text)
        self.assertNotIn("def _sh_register_import_symbol(", core_text)
        self.assertNotIn("def _sh_register_import_module(", core_text)

    def test_core_source_routes_import_binding_and_registration_through_helper_module(self) -> None:
        module_text = CORE_MODULE_PARSER_SOURCE_PATH.read_text(encoding="utf-8")
        stmt_text = CORE_STMT_PARSER_SOURCE_PATH.read_text(encoding="utf-8")
        surface_text = module_text + "\n" + stmt_text

        self.assertIn(
            "_sh_register_import_module(_SH_IMPORT_MODULES, bind_name_dc, mod_name)",
            surface_text,
        )
        self.assertIn(
            "_sh_register_import_symbol(",
            surface_text,
        )
        self.assertIn(
            "make_import_symbol_binding=_sh_make_import_symbol_binding",
            surface_text,
        )
        self.assertIn("make_east_build_error=_make_east_build_error", surface_text)
        self.assertIn("make_span=_sh_span", surface_text)
        self.assertIn("make_import_binding=_sh_make_import_binding", surface_text)
        self.assertIn(
            "_sh_make_import_resolution_binding(binding, make_import_binding=_sh_make_import_binding)",
            surface_text,
        )


if __name__ == "__main__":
    unittest.main()
