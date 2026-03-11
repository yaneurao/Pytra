"""Source-contract regressions for EAST core entrypoint and error helper clusters."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import CORE_ENTRYPOINTS_SOURCE_PATH
from _east_core_test_support import CORE_SOURCE_PATH


class EastCoreSourceContractEntrypointsTest(unittest.TestCase):
    def test_core_source_moves_entrypoint_and_error_helpers_out_of_core(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = CORE_ENTRYPOINTS_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("from toolchain.ir.core_entrypoints import EastBuildError", core_text)
        self.assertIn("from toolchain.ir.core_entrypoints import _make_east_build_error", core_text)
        self.assertIn("from toolchain.ir.core_entrypoints import convert_path", core_text)
        self.assertIn("from toolchain.ir.core_entrypoints import convert_source_to_east", core_text)
        self.assertIn("from toolchain.ir.core_entrypoints import convert_source_to_east_with_backend", core_text)

        self.assertIn("class EastBuildError(Exception):", helper_text)
        self.assertIn("def _make_east_build_error(", helper_text)
        self.assertIn("def convert_source_to_east(", helper_text)
        self.assertIn("def convert_source_to_east_with_backend(", helper_text)
        self.assertIn("def convert_path(", helper_text)

        self.assertNotIn("class EastBuildError(Exception):", core_text)
        self.assertNotIn("def _make_east_build_error(", core_text)
        self.assertNotIn("def convert_source_to_east(", core_text)
        self.assertNotIn("def convert_source_to_east_with_backend(", core_text)
        self.assertNotIn("def convert_path(", core_text)

    def test_core_source_keeps_self_hosted_conversion_implementation_local(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = CORE_ENTRYPOINTS_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("def convert_source_to_east_self_hosted(", core_text)
        self.assertIn(
            "from toolchain.ir.core import convert_source_to_east_self_hosted as _convert_source_to_east_self_hosted",
            helper_text,
        )
        self.assertIn("return _convert_source_to_east_self_hosted(source, filename)", helper_text)


if __name__ == "__main__":
    unittest.main()
