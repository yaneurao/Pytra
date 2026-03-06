from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from tools import gen_runtime_symbol_index as gen_mod
from toolchain.frontends.runtime_symbol_index import lookup_target_module_primary_header
from toolchain.frontends.runtime_symbol_index import lookup_target_module_compile_sources


class RuntimeSymbolIndexTest(unittest.TestCase):
    def test_build_runtime_symbol_index_contains_representative_modules(self) -> None:
        doc = gen_mod.build_runtime_symbol_index()
        modules = doc.get("modules")
        self.assertIsInstance(modules, dict)

        iter_ops = modules.get("pytra.built_in.iter_ops")
        self.assertIsInstance(iter_ops, dict)
        iter_symbols = iter_ops.get("symbols")
        self.assertIsInstance(iter_symbols, dict)
        self.assertEqual(iter_symbols.get("py_enumerate_object", {}).get("kind"), "function")

        predicates = modules.get("pytra.built_in.predicates")
        self.assertIsInstance(predicates, dict)
        pred_symbols = predicates.get("symbols")
        self.assertIsInstance(pred_symbols, dict)
        self.assertEqual(pred_symbols.get("py_any", {}).get("kind"), "function")

        string_ops = modules.get("pytra.built_in.string_ops")
        self.assertIsInstance(string_ops, dict)
        string_symbols = string_ops.get("symbols")
        self.assertIsInstance(string_symbols, dict)
        self.assertEqual(string_symbols.get("py_strip", {}).get("kind"), "function")

        time_mod = modules.get("pytra.std.time")
        self.assertIsInstance(time_mod, dict)
        time_symbols = time_mod.get("symbols")
        self.assertIsInstance(time_symbols, dict)
        self.assertEqual(time_symbols.get("perf_counter", {}).get("kind"), "function")

        png_mod = modules.get("pytra.utils.png")
        self.assertIsInstance(png_mod, dict)
        png_symbols = png_mod.get("symbols")
        self.assertIsInstance(png_symbols, dict)
        self.assertEqual(png_symbols.get("write_rgb_png", {}).get("kind"), "function")

        pathlib_mod = modules.get("pytra.std.pathlib")
        self.assertIsInstance(pathlib_mod, dict)
        pathlib_symbols = pathlib_mod.get("symbols")
        self.assertIsInstance(pathlib_symbols, dict)
        self.assertEqual(pathlib_symbols.get("Path", {}).get("kind"), "class")

    def test_cpp_target_artifacts_contain_gen_and_ext_companions(self) -> None:
        doc = gen_mod.build_runtime_symbol_index()
        targets = doc.get("targets")
        self.assertIsInstance(targets, dict)
        cpp_doc = targets.get("cpp")
        self.assertIsInstance(cpp_doc, dict)
        cpp_modules = cpp_doc.get("modules")
        self.assertIsInstance(cpp_modules, dict)

        iter_ops = cpp_modules.get("pytra.built_in.iter_ops")
        self.assertIsInstance(iter_ops, dict)
        self.assertEqual(iter_ops.get("companions"), ["gen", "ext"])
        self.assertIn("src/runtime/cpp/built_in/iter_ops.gen.h", iter_ops.get("public_headers", []))
        self.assertIn("src/runtime/cpp/built_in/iter_ops.ext.h", iter_ops.get("public_headers", []))
        self.assertIn("src/runtime/cpp/built_in/iter_ops.gen.cpp", iter_ops.get("compile_sources", []))

        time_mod = cpp_modules.get("pytra.std.time")
        self.assertIsInstance(time_mod, dict)
        self.assertEqual(time_mod.get("companions"), ["gen", "ext"])
        self.assertIn("src/runtime/cpp/std/time.gen.h", time_mod.get("public_headers", []))
        self.assertIn("src/runtime/cpp/std/time.ext.cpp", time_mod.get("compile_sources", []))

        png_mod = cpp_modules.get("pytra.utils.png")
        self.assertIsInstance(png_mod, dict)
        self.assertEqual(png_mod.get("companions"), ["gen"])
        self.assertIn("src/runtime/cpp/utils/png.gen.h", png_mod.get("public_headers", []))
        self.assertIn("src/runtime/cpp/utils/png.gen.cpp", png_mod.get("compile_sources", []))

    def test_check_mode_detects_stale_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "runtime_symbol_index.json"
            out.write_text("{}\n", encoding="utf-8")
            p = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools" / "gen_runtime_symbol_index.py"),
                    "--check",
                    "--output",
                    str(out),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(p.returncode, 0)
            self.assertIn("stale runtime symbol index", p.stderr)

    def test_generated_json_round_trips(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "runtime_symbol_index.json"
            p = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools" / "gen_runtime_symbol_index.py"),
                    "--output",
                    str(out),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertIn("generated:", p.stdout)
            doc = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(doc.get("generated_by"), "tools/gen_runtime_symbol_index.py")
            self.assertEqual(doc.get("schema_version"), 1)

    def test_runtime_symbol_index_loader_returns_primary_cpp_header(self) -> None:
        self.assertEqual(
            lookup_target_module_primary_header("cpp", "pytra.std.time"),
            "src/runtime/cpp/std/time.gen.h",
        )
        self.assertEqual(
            lookup_target_module_primary_header("cpp", "pytra.built_in.iter_ops"),
            "src/runtime/cpp/built_in/iter_ops.gen.h",
        )

    def test_runtime_symbol_index_loader_returns_cpp_compile_sources(self) -> None:
        self.assertIn(
            "src/runtime/cpp/std/time.ext.cpp",
            lookup_target_module_compile_sources("cpp", "pytra.std.time"),
        )
        self.assertIn(
            "src/runtime/cpp/utils/png.gen.cpp",
            lookup_target_module_compile_sources("cpp", "pytra.utils.png"),
        )


if __name__ == "__main__":
    unittest.main()
