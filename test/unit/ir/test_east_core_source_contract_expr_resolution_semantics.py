"""Source-contract regressions for EAST core expression resolution helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import CORE_EXPR_RESOLUTION_SEMANTICS_SOURCE_PATH
from _east_core_test_support import CORE_CALL_ANNOTATION_SOURCE_PATH
from _east_core_test_support import CORE_EXPR_SHELL_SOURCE_PATH
from _east_core_test_support import CORE_SOURCE_PATH


class EastCoreSourceContractExprResolutionSemanticsTest(unittest.TestCase):
    def test_core_source_moves_resolution_helper_cluster_out_of_core(self) -> None:
        shell_text = CORE_EXPR_SHELL_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = CORE_EXPR_RESOLUTION_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn(
            "from toolchain.compile.core_expr_resolution_semantics import _ShExprResolutionSemanticsMixin",
            shell_text,
        )
        self.assertIn("class _ShExprResolutionSemanticsMixin:", helper_text)
        for marker in (
            "def _callable_return_type(",
            "def _lookup_method_return(",
            "def _lookup_builtin_method_return(",
            "def _resolve_named_call_declared_return_type(",
            "def _resolve_named_call_return_state(",
            "def _infer_named_call_return_type(",
            "def _lookup_attr_expr_metadata(",
            "def _split_generic_types(",
            "def _split_union_types(",
            "def _is_forbidden_object_receiver_type(",
            "def _is_forbidden_dynamic_helper_type(",
            "def _guard_dynamic_helper_receiver(",
            "def _guard_dynamic_helper_args(",
        ):
            self.assertIn(marker, helper_text)
            self.assertNotIn(marker, shell_text)

    def test_core_source_routes_resolution_helpers_through_split_mixin(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        shell_text = CORE_EXPR_SHELL_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = CORE_EXPR_RESOLUTION_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")
        call_annotation_text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("from toolchain.compile.core_expr_shell import _ShExprParser", core_text)
        self.assertIn("_ShExprResolutionSemanticsMixin,", shell_text)
        self.assertIn("class _ShExprParser(", shell_text)
        self.assertIn("self._resolve_named_call_return_state(", helper_text)
        self.assertIn("def _lookup_attr_expr_metadata(", helper_text)
        self.assertIn("self._split_union_types(", helper_text)
        self.assertIn("self._guard_dynamic_helper_args(", call_annotation_text)


if __name__ == "__main__":
    unittest.main()
