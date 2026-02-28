from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.pytra.compiler.stdlib.signature_registry import lookup_stdlib_function_return_type
from src.pytra.compiler.stdlib.signature_registry import lookup_stdlib_method_return_type


class StdlibSignatureRegistryTest(unittest.TestCase):
    def test_lookup_function_return_type_from_pytra_std(self) -> None:
        self.assertEqual(lookup_stdlib_function_return_type("perf_counter"), "float64")
        self.assertEqual(lookup_stdlib_function_return_type("unknown_symbol"), "")

    def test_lookup_method_return_type_from_pytra_std(self) -> None:
        self.assertEqual(lookup_stdlib_method_return_type("Path", "exists"), "bool")
        self.assertEqual(lookup_stdlib_method_return_type("Path", "parent"), "Path")
        self.assertEqual(lookup_stdlib_method_return_type("Path", "missing_method"), "")


if __name__ == "__main__":
    unittest.main()
