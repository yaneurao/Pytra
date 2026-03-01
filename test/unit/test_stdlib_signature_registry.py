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
from src.pytra.compiler.stdlib.signature_registry import lookup_stdlib_attribute_type
from src.pytra.compiler.stdlib.signature_registry import lookup_stdlib_method_runtime_call
from src.pytra.compiler.stdlib.signature_registry import lookup_stdlib_method_return_type
from src.pytra.compiler.stdlib.signature_registry import lookup_stdlib_function_runtime_call
from src.pytra.compiler.stdlib.frontend_semantics import lookup_builtin_semantic_tag
from src.pytra.compiler.stdlib.frontend_semantics import lookup_stdlib_function_semantic_tag
from src.pytra.compiler.stdlib.frontend_semantics import lookup_stdlib_method_semantic_tag
from src.pytra.compiler.stdlib.frontend_semantics import lookup_stdlib_symbol_semantic_tag


class StdlibSignatureRegistryTest(unittest.TestCase):
    def test_lookup_function_return_type_from_pytra_std(self) -> None:
        self.assertEqual(lookup_stdlib_function_return_type("perf_counter"), "float64")
        self.assertEqual(lookup_stdlib_function_return_type("unknown_symbol"), "")

    def test_lookup_method_return_type_from_pytra_std(self) -> None:
        self.assertEqual(lookup_stdlib_method_return_type("Path", "exists"), "bool")
        self.assertEqual(lookup_stdlib_method_return_type("Path", "parent"), "Path")
        self.assertEqual(lookup_stdlib_method_return_type("Path", "missing_method"), "")

    def test_lookup_runtime_call_by_owner_type(self) -> None:
        self.assertEqual(lookup_stdlib_method_runtime_call("str", "strip"), "py_strip")
        self.assertEqual(lookup_stdlib_method_runtime_call("Path", "exists"), "std::filesystem::exists")
        self.assertEqual(lookup_stdlib_method_runtime_call("list[int64]", "append"), "list.append")
        self.assertEqual(lookup_stdlib_method_runtime_call("int64", "to_bytes"), "py_int_to_bytes")
        self.assertEqual(lookup_stdlib_method_runtime_call("unknown", "isdigit"), "py_isdigit")

    def test_lookup_function_runtime_call(self) -> None:
        self.assertEqual(lookup_stdlib_function_runtime_call("perf_counter"), "perf_counter")
        self.assertEqual(lookup_stdlib_function_runtime_call("unknown_symbol"), "")

    def test_lookup_attribute_type_by_owner_type(self) -> None:
        self.assertEqual(lookup_stdlib_attribute_type("Path", "parent"), "Path")
        self.assertEqual(lookup_stdlib_attribute_type("Path", "name"), "str")
        self.assertEqual(lookup_stdlib_attribute_type("str", "name"), "")

    def test_lookup_frontend_semantic_tags(self) -> None:
        self.assertEqual(lookup_builtin_semantic_tag("len"), "core.len")
        self.assertEqual(lookup_builtin_semantic_tag("isinstance"), "type.isinstance")
        self.assertEqual(lookup_builtin_semantic_tag("unknown"), "")
        self.assertEqual(lookup_stdlib_function_semantic_tag("perf_counter"), "stdlib.fn.perf_counter")
        self.assertEqual(lookup_stdlib_symbol_semantic_tag("Path"), "stdlib.symbol.Path")
        self.assertEqual(lookup_stdlib_method_semantic_tag("exists"), "stdlib.method.exists")


if __name__ == "__main__":
    unittest.main()
