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
    def _load_east(self, src: str, name: str = "case.py") -> dict[str, object]:
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / name
            src_py.write_text(src, encoding="utf-8")
            return load_east(src_py)

    def _transpile(self, src: str, name: str = "case.py") -> str:
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / name
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            return transpile_to_cpp(east)

    def _collect_builtin_bindings(self, east: dict[str, object]) -> set[tuple[str, str]]:
        out: set[tuple[str, str]] = set()
        stack: list[object] = [east]
        while len(stack) > 0:
            cur = stack.pop()
            if isinstance(cur, dict):
                if cur.get("kind") == "Call" and cur.get("lowered_kind") == "BuiltinCall":
                    module_id = cur.get("runtime_module_id")
                    runtime_symbol = cur.get("runtime_symbol")
                    if isinstance(module_id, str) and isinstance(runtime_symbol, str):
                        out.add((module_id, runtime_symbol))
                for value in cur.values():
                    stack.append(value)
            elif isinstance(cur, list):
                for item in cur:
                    stack.append(item)
        return out

    def test_pkg_symbol_import_module_include_is_index_driven(self) -> None:
        cpp = self._transpile(
            """from pytra.utils import png

def main() -> None:
    pixels: bytearray = bytearray(3)
    png.write_rgb_png("x.png", 1, 1, pixels)
""",
            "pkg_symbol_module.py",
        )
        self.assertIn('#include "generated/utils/png.h"', cpp)
        self.assertIn("pytra::utils::png::write_rgb_png(", cpp)

    def test_from_import_symbol_include_is_index_driven(self) -> None:
        cpp = self._transpile(
            """from pytra.std.time import perf_counter

def main() -> None:
    t0: float = perf_counter()
""",
            "perf_counter_case.py",
        )
        self.assertIn('#include "generated/std/time.h"', cpp)
        self.assertIn("pytra::std::time::perf_counter()", cpp)

    def test_frontend_facade_symbol_import_uses_runtime_namespace(self) -> None:
        cpp = self._transpile(
            """from toolchain.frontends import load_east3_document_typed

def main(input_path: str) -> None:
    _ = load_east3_document_typed(input_path)
""",
            "frontend_facade_symbol_case.py",
        )
        self.assertIn('#include "runtime/cpp/generated/compiler/transpile_cli.h"', cpp)
        self.assertIn("pytra::compiler::transpile_cli::load_east3_document_typed(", cpp)

    def test_runtime_paths_uses_index_for_std_and_core_modules(self) -> None:
        self.assertEqual(module_name_to_cpp_include("math"), "generated/std/math.h")
        self.assertEqual(module_name_to_cpp_include("pytra.std.time"), "generated/std/time.h")
        self.assertEqual(module_name_to_cpp_include("pytra.core.dict"), "native/core/dict.h")

    def test_transpiled_cpp_uses_native_core_runtime_headers(self) -> None:
        cpp = self._transpile(
            """def main(xs: list[int], d: dict[str, int]) -> None:
    print(xs[0])
    print(d.get("a", 0))
""",
            "core_include_surface_case.py",
        )
        self.assertIn('#include "runtime/cpp/native/core/py_runtime.h"', cpp)
        self.assertNotIn('runtime/cpp/core/py_runtime.h', cpp)

    def test_transpiled_cpp_emits_direct_built_in_headers_after_py_runtime_slimming(self) -> None:
        cpp = self._transpile(
            """def main(xs: list[int], s: str) -> None:
    _ = any(xs)
    _ = range(0, 3)
    _ = reversed(xs)
    _ = enumerate(xs)
    _ = s.split(",")
    print("-" * 3)
""",
            "built_in_include_surface_case.py",
        )
        self.assertIn('#include "runtime/cpp/native/core/py_runtime.h"', cpp)
        self.assertIn('#include "generated/built_in/predicates.h"', cpp)
        self.assertIn('#include "generated/built_in/sequence.h"', cpp)
        self.assertIn('#include "generated/built_in/iter_ops.h"', cpp)
        self.assertNotIn('#include "generated/built_in/string_ops.h"', cpp)

    def test_builtin_call_bindings_and_imported_symbol_calls_are_ir_driven(self) -> None:
        src = """from pytra.std.time import perf_counter as now
from pytra.std.pathlib import Path as P

def main(xs: list[int], s: str, d: dict[str, int]) -> None:
    t0: float = now()
    p: P = P("x")
    base16: int = int("10", 16)
    ch: str = chr(65)
    code: int = ord("A")
    _ = enumerate(xs)
    _ = any(xs)
    _ = s.strip()
    _ = d.get("a", 0)
    print(t0, p.name, base16, ch, code)
"""
        east = self._load_east(src, "binding_case.py")
        bindings = self._collect_builtin_bindings(east)
        self.assertIn(("pytra.built_in.iter_ops", "enumerate"), bindings)
        self.assertIn(("pytra.built_in.predicates", "any"), bindings)
        self.assertIn(("pytra.built_in.string_ops", "str.strip"), bindings)
        self.assertIn(("pytra.built_in.io_ops", "py_print"), bindings)
        self.assertIn(("pytra.built_in.scalar_ops", "py_to_int64_base"), bindings)
        self.assertIn(("pytra.built_in.scalar_ops", "py_chr"), bindings)
        self.assertIn(("pytra.built_in.scalar_ops", "py_ord"), bindings)
        self.assertIn(("pytra.core.dict", "dict.get"), bindings)

        cpp = self._transpile(src, "binding_case.py")
        self.assertIn("pytra::std::time::perf_counter()", cpp)
        self.assertIn('pytra::std::pathlib::Path("x")', cpp)


if __name__ == "__main__":
    unittest.main()
