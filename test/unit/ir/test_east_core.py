"""Unit regression tests for the self_hosted EAST converter."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import CORE_SOURCE_PATH
from _east_core_test_support import CORE_CALL_ANNOTATION_SOURCE_PATH
from _east_core_test_support import _walk


class EastCoreTest(unittest.TestCase):
    def test_core_does_not_reintroduce_perf_counter_direct_branch(self) -> None:
        src = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        self.assertNotIn('fn_name == "perf_counter"', src)
        self.assertNotIn("fn_name == 'perf_counter'", src)

    def test_core_does_not_reintroduce_path_direct_branches(self) -> None:
        src = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        self.assertNotIn('fn_name == "Path"', src)
        self.assertNotIn("fn_name == 'Path'", src)
        self.assertNotIn('owner_t == "Path"', src)
        self.assertNotIn("owner_t == 'Path'", src)

    def test_core_semantic_tag_mapping_is_adapter_driven(self) -> None:
        src = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        call_src = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn("lookup_builtin_semantic_tag", src)
        self.assertIn("lookup_stdlib_function_semantic_tag", src)
        self.assertIn("lookup_stdlib_symbol_semantic_tag", src)
        self.assertIn("lookup_owner_method_semantic_tag", src)
        self.assertIn("lookup_runtime_binding_semantic_tag", src)
        self.assertNotIn('payload["semantic_tag"] = "', src)
        self.assertNotIn('payload["semantic_tag"] = "', call_src)


if __name__ == "__main__":
    unittest.main()
