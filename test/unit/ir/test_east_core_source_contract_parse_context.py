"""Source-contract regressions for EAST core parse-context clusters."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import CORE_PARSE_CONTEXT_SOURCE_PATH
from _east_core_test_support import CORE_NAMED_CALL_ANNOTATION_SOURCE_PATH
from _east_core_test_support import CORE_EXPR_RESOLUTION_SEMANTICS_SOURCE_PATH
from _east_core_test_support import CORE_CALL_ANNOTATION_SOURCE_PATH
from _east_core_test_support import CORE_MODULE_PARSER_SOURCE_PATH
from _east_core_test_support import CORE_SOURCE_PATH


class EastCoreSourceContractParseContextTest(unittest.TestCase):
    def test_core_source_moves_parse_context_cluster_out_of_core(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = CORE_PARSE_CONTEXT_SOURCE_PATH.read_text(encoding="utf-8")

        for marker in (
            "from toolchain.compile.core_parse_context import _SH_CLASS_BASE",
            "from toolchain.compile.core_parse_context import _SH_CLASS_METHOD_RETURNS",
            "from toolchain.compile.core_parse_context import _SH_EMPTY_SPAN",
            "from toolchain.compile.core_parse_context import _SH_FN_RETURNS",
            "from toolchain.compile.core_parse_context import _SH_IMPORT_MODULES",
            "from toolchain.compile.core_parse_context import _SH_IMPORT_SYMBOLS",
            "from toolchain.compile.core_parse_context import _SH_RUNTIME_ABI_ARG_MODES",
            "from toolchain.compile.core_parse_context import _SH_RUNTIME_ABI_MODE_ALIASES",
            "from toolchain.compile.core_parse_context import _SH_RUNTIME_ABI_RET_MODES",
            "from toolchain.compile.core_parse_context import _SH_TEMPLATE_INSTANTIATION_MODE",
            "from toolchain.compile.core_parse_context import _SH_TEMPLATE_SCOPE",
            "from toolchain.compile.core_parse_context import _SH_TYPE_ALIASES",
            "from toolchain.compile.core_parse_context import _sh_set_parse_context",
        ):
            self.assertIn(marker, core_text)

        for marker in (
            "_SH_FN_RETURNS: dict[str, str] = {}",
            "_SH_CLASS_METHOD_RETURNS: dict[str, dict[str, str]] = {}",
            "_SH_CLASS_BASE: dict[str, str | None] = {}",
            "_SH_IMPORT_SYMBOLS: dict[str, dict[str, str]] = {}",
            "_SH_IMPORT_MODULES: dict[str, str] = {}",
            "_SH_EMPTY_SPAN: dict[str, Any] = {}",
            '_SH_TEMPLATE_SCOPE = "runtime_helper"',
            'def _sh_set_parse_context(',
        ):
            self.assertIn(marker, helper_text)
            self.assertNotIn(marker, core_text)

    def test_core_source_keeps_parse_context_usage_after_split(self) -> None:
        module_text = CORE_MODULE_PARSER_SOURCE_PATH.read_text(encoding="utf-8")
        resolution_text = CORE_EXPR_RESOLUTION_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")
        call_annotation_text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        named_call_annotation_text = CORE_NAMED_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("import_modules=_SH_IMPORT_MODULES", resolution_text)
        self.assertIn("import_symbols=_SH_IMPORT_SYMBOLS", resolution_text)
        self.assertIn(
            "from toolchain.compile.core_expr_named_call_annotation import _ShExprNamedCallAnnotationMixin",
            call_annotation_text,
        )
        self.assertIn("import_symbols=_SH_IMPORT_SYMBOLS", named_call_annotation_text)
        self.assertIn("runtime_abi_arg_modes=_SH_RUNTIME_ABI_ARG_MODES", module_text)
        self.assertIn("runtime_abi_mode_aliases=_SH_RUNTIME_ABI_MODE_ALIASES", module_text)
        self.assertIn("runtime_abi_ret_modes=_SH_RUNTIME_ABI_RET_MODES", module_text)
        self.assertIn("template_scope=_SH_TEMPLATE_SCOPE", module_text)
        self.assertIn("template_instantiation_mode=_SH_TEMPLATE_INSTANTIATION_MODE", module_text)
        self.assertIn("_sh_set_parse_context(fn_returns, class_method_return_types, class_base, type_aliases)", module_text)


if __name__ == "__main__":
    unittest.main()
