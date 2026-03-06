from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.backends.cpp.cli import load_east, transpile_to_cpp
from src.backends.cpp.emitter.runtime_paths import module_name_to_cpp_include


class CppRuntimeSymbolIndexIntegrationTest(unittest.TestCase):
    def _transpile(self, src: str, name: str = "case.py") -> str:
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / name
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            return transpile_to_cpp(east)

    def test_pkg_symbol_import_module_include_is_index_driven(self) -> None:
        cpp = self._transpile(
            """from pytra.utils import png

def main() -> None:
    pixels: bytearray = bytearray(3)
    png.write_rgb_png("x.png", 1, 1, pixels)
""",
            "pkg_symbol_module.py",
        )
        self.assertIn('#include "runtime/cpp/utils/png.gen.h"', cpp)
        self.assertIn("pytra::utils::png::write_rgb_png(", cpp)

    def test_from_import_symbol_include_is_index_driven(self) -> None:
        cpp = self._transpile(
            """from pytra.std.time import perf_counter

def main() -> None:
    t0: float = perf_counter()
""",
            "perf_counter_case.py",
        )
        self.assertIn('#include "runtime/cpp/std/time.gen.h"', cpp)
        self.assertIn("pytra::std::time::perf_counter()", cpp)

    def test_runtime_paths_uses_index_for_std_and_core_modules(self) -> None:
        self.assertEqual(module_name_to_cpp_include("math"), "runtime/cpp/std/math.gen.h")
        self.assertEqual(module_name_to_cpp_include("pytra.core.dict"), "runtime/cpp/core/dict.ext.h")


if __name__ == "__main__":
    unittest.main()
