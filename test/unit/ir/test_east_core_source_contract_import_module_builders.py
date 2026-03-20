"""Source-contract regressions for EAST core import/module builder clusters."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import CORE_IMPORT_MODULE_BUILDERS_SOURCE_PATH
from _east_core_test_support import CORE_MODULE_PARSER_SOURCE_PATH
from _east_core_test_support import CORE_SOURCE_PATH
from _east_core_test_support import CORE_STMT_PARSER_SOURCE_PATH


class EastCoreSourceContractImportModuleBuildersTest(unittest.TestCase):
    def test_core_source_moves_import_and_module_builder_helpers_out_of_core(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = CORE_IMPORT_MODULE_BUILDERS_SOURCE_PATH.read_text(encoding="utf-8")

        for helper_name in (
            "_sh_make_import_alias",
            "_sh_make_import_binding",
            "_sh_make_import_symbol_binding",
            "_sh_make_qualified_symbol_ref",
            "_sh_make_import_stmt",
            "_sh_make_import_from_stmt",
            "_sh_make_module_source_span",
            "_sh_make_import_resolution_meta",
            "_sh_make_module_meta",
            "_sh_make_module_root",
        ):
            self.assertIn(f"from toolchain.compile.core_import_module_builders import {helper_name}", core_text)
            self.assertIn(f"def {helper_name}(", helper_text)
            self.assertNotIn(f"def {helper_name}(", core_text)

    def test_core_source_routes_import_and_module_builders_through_split_module(self) -> None:
        module_text = CORE_MODULE_PARSER_SOURCE_PATH.read_text(encoding="utf-8")
        stmt_text = CORE_STMT_PARSER_SOURCE_PATH.read_text(encoding="utf-8")
        surface_text = module_text + "\n" + stmt_text

        self.assertIn("_sh_make_import_stmt(_sh_make_stmt_node, _sh_span(i, 0, len(ln)), aliases)", surface_text)
        self.assertIn("_sh_make_import_from_stmt(\n                        _sh_make_stmt_node,", surface_text)
        self.assertIn(
            "import_symbol_bindings[local_name] = _sh_make_import_symbol_binding(module_id, export_name)",
            module_text,
        )
        self.assertIn("qualified_symbol_refs.append(_sh_make_qualified_symbol_ref(module_id, export_name, local_name))", module_text)
        self.assertIn("out = _sh_make_module_root(", module_text)
        self.assertIn("make_node=_sh_make_node", module_text)


if __name__ == "__main__":
    unittest.main()
