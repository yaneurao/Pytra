"""Source-contract regressions for the thin EAST core facade."""

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


class EastCoreSourceContractCoreSurfaceTest(unittest.TestCase):
    def test_core_surface_stays_thin(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertLessEqual(len(core_text.splitlines()), 260)
        self.assertEqual(
            [line for line in core_text.splitlines() if line.startswith("def ")],
            [
                "def _sh_parse_stmt_block_mutable(body_lines: list[tuple[int, str]], *, name_types: dict[str, str], scope_label: str) -> list[dict[str, Any]]:",
                "def _sh_parse_stmt_block(body_lines: list[tuple[int, str]], *, name_types: dict[str, str], scope_label: str) -> list[dict[str, Any]]:",
                "def convert_source_to_east_self_hosted(source: str, filename: str) -> dict[str, Any]:",
            ],
        )
        self.assertNotIn("class _ShExprParser", core_text)
        self.assertNotIn("def _annotate_call_expr(", core_text)
        self.assertNotIn("def _parse_primary(", core_text)
        self.assertNotIn("def _sh_parse_expr_lowered_impl(", core_text)

    def test_core_surface_locks_public_and_bridge_exports(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn(
            'CORE_PUBLIC_FACADE_EXPORTS = (',
            core_text,
        )
        self.assertIn('"EastBuildError"', core_text)
        self.assertIn('"convert_path"', core_text)
        self.assertIn('"convert_source_to_east"', core_text)
        self.assertIn('"convert_source_to_east_with_backend"', core_text)
        self.assertIn(
            'CORE_BRIDGE_COMPAT_EXPORTS = (',
            core_text,
        )
        self.assertIn('"convert_source_to_east_self_hosted"', core_text)
        self.assertIn('"_sh_parse_stmt_block"', core_text)
        self.assertIn('"_sh_parse_stmt_block_mutable"', core_text)
        self.assertIn('"INT_TYPES"', core_text)
        self.assertIn('"FLOAT_TYPES"', core_text)
        self.assertIn("__all__ = [*CORE_PUBLIC_FACADE_EXPORTS, *CORE_BRIDGE_COMPAT_EXPORTS]", core_text)
        self.assertIn("from toolchain.compile.core_numeric_types import FLOAT_TYPES", core_text)
        self.assertIn("from toolchain.compile.core_numeric_types import INT_TYPES", core_text)
        self.assertNotIn('INT_TYPES = {', core_text)
        self.assertNotIn('FLOAT_TYPES = {"float32", "float64"}', core_text)

    def test_core_surface_delegates_stmt_and_module_entrypoints(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        stmt_parser_text = CORE_STMT_PARSER_SOURCE_PATH.read_text(encoding="utf-8")
        module_parser_text = CORE_MODULE_PARSER_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn(
            "from toolchain.compile.core_stmt_parser import _sh_parse_stmt_block as _sh_parse_stmt_block_impl",
            core_text,
        )
        self.assertIn(
            "from toolchain.compile.core_stmt_parser import _sh_parse_stmt_block_mutable as _sh_parse_stmt_block_mutable_impl",
            core_text,
        )
        self.assertIn(
            "return _sh_parse_stmt_block_mutable_impl(body_lines, name_types=name_types, scope_label=scope_label)",
            core_text,
        )
        self.assertIn(
            "return _sh_parse_stmt_block_impl(body_lines, name_types=name_types, scope_label=scope_label)",
            core_text,
        )
        self.assertIn(
            "return convert_source_to_east_self_hosted_impl(source, filename)",
            core_text,
        )
        self.assertIn(
            "from toolchain.compile.core_stmt_parser_support import (",
            stmt_parser_text,
        )
        self.assertIn(
            "from toolchain.compile.core_module_parser_support import (",
            module_parser_text,
        )
        self.assertNotIn("from toolchain.compile.core import (", stmt_parser_text)
        self.assertNotIn("from toolchain.compile.core import (", module_parser_text)
        self.assertIn("def _sh_parse_stmt_block_mutable(", stmt_parser_text)
        self.assertIn("def _sh_parse_stmt_block(", stmt_parser_text)
        self.assertIn("def convert_source_to_east_self_hosted_impl(", module_parser_text)


if __name__ == "__main__":
    unittest.main()
