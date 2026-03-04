from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.toolchain.compiler.stdlib.signature_registry import lookup_stdlib_function_return_type
from src.toolchain.compiler.stdlib.signature_registry import lookup_stdlib_attribute_type
from src.toolchain.compiler.stdlib.signature_registry import lookup_noncpp_imported_symbol_runtime_call
from src.toolchain.compiler.stdlib.signature_registry import lookup_noncpp_module_attr_runtime_call
from src.toolchain.compiler.stdlib.signature_registry import lookup_stdlib_method_runtime_call
from src.toolchain.compiler.stdlib.signature_registry import lookup_stdlib_method_return_type
from src.toolchain.compiler.stdlib.signature_registry import lookup_stdlib_function_runtime_call
from src.toolchain.compiler.stdlib.frontend_semantics import lookup_builtin_semantic_tag
from src.toolchain.compiler.stdlib.frontend_semantics import lookup_stdlib_function_semantic_tag
from src.toolchain.compiler.stdlib.frontend_semantics import lookup_stdlib_method_semantic_tag
from src.toolchain.compiler.stdlib.frontend_semantics import lookup_stdlib_symbol_semantic_tag


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

    def test_lookup_noncpp_imported_symbol_runtime_call(self) -> None:
        import_symbols = {
            "write_rgb_png": {"module": "pytra.utils.png", "name": "write_rgb_png"},
            "save_gif": {"module": "pytra.utils.gif", "name": "save_gif"},
            "grayscale_palette": {"module": "pytra.utils.gif", "name": "grayscale_palette"},
            "py_assert_stdout": {"module": "pytra.utils.assertions", "name": "py_assert_stdout"},
        }
        self.assertEqual(
            lookup_noncpp_imported_symbol_runtime_call("write_rgb_png", import_symbols),
            "write_rgb_png",
        )
        self.assertEqual(
            lookup_noncpp_imported_symbol_runtime_call("save_gif", import_symbols),
            "save_gif",
        )
        self.assertEqual(
            lookup_noncpp_imported_symbol_runtime_call("grayscale_palette", import_symbols),
            "grayscale_palette",
        )
        self.assertEqual(
            lookup_noncpp_imported_symbol_runtime_call("py_assert_stdout", import_symbols),
            "py_assert_stdout",
        )
        self.assertEqual(
            lookup_noncpp_imported_symbol_runtime_call("missing", import_symbols),
            "",
        )

    def test_lookup_noncpp_module_attr_runtime_call(self) -> None:
        self.assertEqual(
            lookup_noncpp_module_attr_runtime_call("pytra.std.json", "loads"),
            "json.loads",
        )
        self.assertEqual(
            lookup_noncpp_module_attr_runtime_call("pytra.std.json", "dumps"),
            "json.dumps",
        )
        self.assertEqual(
            lookup_noncpp_module_attr_runtime_call("pytra.utils.png", "write_rgb_png"),
            "write_rgb_png",
        )
        self.assertEqual(
            lookup_noncpp_module_attr_runtime_call("pytra.utils.gif", "save_gif"),
            "save_gif",
        )
        self.assertEqual(
            lookup_noncpp_module_attr_runtime_call("pytra.utils.gif", "grayscale_palette"),
            "grayscale_palette",
        )
        self.assertEqual(
            lookup_noncpp_module_attr_runtime_call("math", "sin"),
            "math.sin",
        )
        self.assertEqual(
            lookup_noncpp_module_attr_runtime_call("math", "pi"),
            "math.pi",
        )
        self.assertEqual(
            lookup_noncpp_module_attr_runtime_call("pytra.utils.gif", "unknown"),
            "",
        )

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
