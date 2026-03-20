"""Source-contract regressions for EAST core runtime declaration helper clusters."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import CORE_RUNTIME_DECL_SEMANTICS_SOURCE_PATH
from _east_core_test_support import CORE_MODULE_PARSER_SOURCE_PATH
from _east_core_test_support import CORE_SOURCE_PATH


class EastCoreSourceContractRuntimeDeclSemanticsTest(unittest.TestCase):
    def test_core_source_moves_runtime_decl_helpers_out_of_core(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = CORE_RUNTIME_DECL_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn(
            "from toolchain.compile.core_runtime_decl_semantics import _sh_collect_function_runtime_decl_metadata",
            core_text,
        )
        self.assertIn(
            "from toolchain.compile.core_runtime_decl_semantics import _sh_reject_runtime_decl_class_decorators",
            core_text,
        )
        self.assertIn(
            "from toolchain.compile.core_runtime_decl_semantics import _sh_reject_runtime_decl_method_decorator",
            core_text,
        )
        self.assertIn(
            "from toolchain.compile.core_runtime_decl_semantics import _sh_reject_runtime_decl_nonfunction_decorators",
            core_text,
        )
        self.assertIn("def _sh_parse_runtime_abi_decorator(", helper_text)
        self.assertIn("def _sh_collect_runtime_abi_metadata(", helper_text)
        self.assertIn("def _sh_parse_template_decorator(", helper_text)
        self.assertIn("def _sh_collect_template_metadata(", helper_text)
        self.assertIn("def _sh_collect_function_runtime_decl_metadata(", helper_text)
        self.assertIn("def _sh_reject_runtime_decl_class_decorators(", helper_text)
        self.assertIn("def _sh_reject_runtime_decl_method_decorator(", helper_text)
        self.assertIn("def _sh_reject_runtime_decl_nonfunction_decorators(", helper_text)
        self.assertIn("def _sh_parse_runtime_abi_string_literal(", helper_text)
        self.assertIn("def _sh_parse_runtime_abi_mode(", helper_text)
        self.assertIn("def _sh_parse_runtime_abi_args_map(", helper_text)
        self.assertNotIn("def _sh_parse_runtime_abi_decorator(", core_text)
        self.assertNotIn("def _sh_collect_runtime_abi_metadata(", core_text)
        self.assertNotIn("def _sh_parse_template_decorator(", core_text)
        self.assertNotIn("def _sh_collect_template_metadata(", core_text)
        self.assertNotIn("def _sh_collect_function_runtime_decl_metadata(", core_text)
        self.assertNotIn("def _sh_reject_runtime_decl_class_decorators(", core_text)
        self.assertNotIn("def _sh_reject_runtime_decl_method_decorator(", core_text)
        self.assertNotIn("def _sh_reject_runtime_decl_nonfunction_decorators(", core_text)
        self.assertNotIn("def _sh_parse_runtime_abi_string_literal(", core_text)
        self.assertNotIn("def _sh_parse_runtime_abi_mode(", core_text)
        self.assertNotIn("def _sh_parse_runtime_abi_args_map(", core_text)

    def test_core_source_routes_runtime_decl_helpers_through_callback_injection(self) -> None:
        module_text = CORE_MODULE_PARSER_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("runtime_abi_arg_modes=_SH_RUNTIME_ABI_ARG_MODES", module_text)
        self.assertIn("runtime_abi_mode_aliases=_SH_RUNTIME_ABI_MODE_ALIASES", module_text)
        self.assertIn("runtime_abi_ret_modes=_SH_RUNTIME_ABI_RET_MODES", module_text)
        self.assertIn("template_scope=_SH_TEMPLATE_SCOPE", module_text)
        self.assertIn("template_instantiation_mode=_SH_TEMPLATE_INSTANTIATION_MODE", module_text)
        self.assertIn("make_east_build_error=_make_east_build_error", module_text)
        self.assertIn("make_span=_sh_span", module_text)
        self.assertIn("is_abi_decorator=_sh_is_abi_decorator", module_text)
        self.assertIn("is_template_decorator=_sh_is_template_decorator", module_text)
        self.assertIn("parse_decorator_head_and_args=_sh_parse_decorator_head_and_args", module_text)
        self.assertIn("split_top_level_colon=_sh_split_top_level_colon", module_text)
        self.assertIn("split_top_level_assign=_sh_split_top_level_assign", module_text)

    def test_core_source_routes_runtime_decl_collectors_through_callback_injection(self) -> None:
        module_text = CORE_MODULE_PARSER_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("_sh_collect_function_runtime_decl_metadata(", module_text)
        self.assertIn("_sh_reject_runtime_decl_class_decorators(", module_text)
        self.assertIn("_sh_reject_runtime_decl_method_decorator(", module_text)
        self.assertIn("_sh_reject_runtime_decl_nonfunction_decorators(", module_text)
        self.assertIn("runtime_abi_ret_modes=_SH_RUNTIME_ABI_RET_MODES", module_text)
        self.assertIn("template_scope=_SH_TEMPLATE_SCOPE", module_text)
        self.assertIn("template_instantiation_mode=_SH_TEMPLATE_INSTANTIATION_MODE", module_text)


if __name__ == "__main__":
    unittest.main()
