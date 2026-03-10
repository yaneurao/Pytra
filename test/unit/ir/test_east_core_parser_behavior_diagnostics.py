"""Parser behavior regressions for self-hosted diagnostics."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from src.toolchain.compiler.east import EastBuildError
from src.toolchain.compiler.east import convert_source_to_east_with_backend


class EastCoreParserBehaviorDiagnosticsTest(unittest.TestCase):
    def test_self_hosted_parser_rejects_local_object_receiver_method_call(self) -> None:
        src = """
def main() -> None:
    x: object = 1
    x.bit_length()
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("object receiver attribute/method access is forbidden", str(cm.exception))

    def test_self_hosted_parser_rejects_object_receiver_method_return_access(self) -> None:
        src = """
def bad_attr(x: object) -> int:
    return x.bit_length()
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("object receiver attribute/method access is forbidden", str(cm.exception))

    def test_object_receiver_access_is_rejected(self) -> None:
        src = """
def f(x: object) -> int:
    return x.bit_length()

def main() -> None:
    print(f(1))

if __name__ == "__main__":
    main()
"""
        with self.assertRaises((EastBuildError, RuntimeError)):
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
