from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from tools import gen_runtime_symbol_index as gen_mod
from toolchain.frontends.runtime_symbol_index import canonical_runtime_module_id
from toolchain.frontends.runtime_symbol_index import lookup_cpp_namespace_for_runtime_module
from toolchain.frontends.runtime_symbol_index import resolve_import_binding_runtime_module
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

    def test_cpp_target_artifacts_follow_generated_native_and_public_shim_contract(self) -> None:
        doc = gen_mod.build_runtime_symbol_index()
        targets = doc.get("targets")
        self.assertIsInstance(targets, dict)
        cpp_doc = targets.get("cpp")
        self.assertIsInstance(cpp_doc, dict)
        cpp_modules = cpp_doc.get("modules")
        self.assertIsInstance(cpp_modules, dict)

        iter_ops = cpp_modules.get("pytra.built_in.iter_ops")
        self.assertIsInstance(iter_ops, dict)
        self.assertEqual(iter_ops.get("companions"), ["generated", "native"])
        self.assertIn("src/runtime/cpp/pytra/built_in/iter_ops.h", iter_ops.get("public_headers", []))
        self.assertNotIn("src/runtime/cpp/built_in/iter_ops.gen.h", iter_ops.get("public_headers", []))
        self.assertIn("src/runtime/cpp/generated/built_in/iter_ops.cpp", iter_ops.get("compile_sources", []))

        time_mod = cpp_modules.get("pytra.std.time")
        self.assertIsInstance(time_mod, dict)
        self.assertEqual(time_mod.get("companions"), ["generated", "native"])
        self.assertIn("src/runtime/cpp/pytra/std/time.h", time_mod.get("public_headers", []))
        self.assertNotIn("src/runtime/cpp/std/time.gen.h", time_mod.get("public_headers", []))
        self.assertIn("src/runtime/cpp/native/std/time.cpp", time_mod.get("compile_sources", []))
        self.assertNotIn("src/runtime/cpp/std/time.ext.cpp", time_mod.get("compile_sources", []))

        png_mod = cpp_modules.get("pytra.utils.png")
        self.assertIsInstance(png_mod, dict)
        self.assertEqual(png_mod.get("companions"), ["generated"])
        self.assertIn("src/runtime/cpp/pytra/utils/png.h", png_mod.get("public_headers", []))
        self.assertNotIn("src/runtime/cpp/utils/png.gen.h", png_mod.get("public_headers", []))
        self.assertIn("src/runtime/cpp/generated/utils/png.cpp", png_mod.get("compile_sources", []))

        core_dict = cpp_modules.get("pytra.core.dict")
        self.assertIsInstance(core_dict, dict)
        self.assertEqual(core_dict.get("companions"), ["native"])
        self.assertIn("src/runtime/cpp/core/dict.h", core_dict.get("public_headers", []))
        self.assertNotIn("src/runtime/cpp/native/core/dict.ext.h", core_dict.get("public_headers", []))

        core_gc = cpp_modules.get("pytra.core.gc")
        self.assertIsInstance(core_gc, dict)
        self.assertEqual(core_gc.get("companions"), ["native"])
        self.assertIn("src/runtime/cpp/core/gc.h", core_gc.get("public_headers", []))
        self.assertIn("src/runtime/cpp/native/core/gc.ext.cpp", core_gc.get("compile_sources", []))
        self.assertNotIn("src/runtime/cpp/core/gc.ext.cpp", core_gc.get("compile_sources", []))

        core_io = cpp_modules.get("pytra.core.io")
        self.assertIsInstance(core_io, dict)
        self.assertEqual(core_io.get("companions"), ["native"])
        self.assertIn("src/runtime/cpp/core/io.h", core_io.get("public_headers", []))
        self.assertIn("src/runtime/cpp/native/core/io.ext.cpp", core_io.get("compile_sources", []))
        self.assertNotIn("src/runtime/cpp/core/io.ext.cpp", core_io.get("compile_sources", []))

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
            "src/runtime/cpp/pytra/std/time.h",
        )
        self.assertEqual(
            lookup_target_module_primary_header("cpp", "pytra.built_in.iter_ops"),
            "src/runtime/cpp/pytra/built_in/iter_ops.h",
        )
        self.assertEqual(
            lookup_target_module_primary_header("cpp", "pytra.utils.png"),
            "src/runtime/cpp/pytra/utils/png.h",
        )
        self.assertEqual(
            lookup_target_module_primary_header("cpp", "pytra.core.dict"),
            "src/runtime/cpp/core/dict.h",
        )

    def test_runtime_symbol_index_loader_returns_cpp_compile_sources(self) -> None:
        self.assertIn(
            "src/runtime/cpp/native/std/time.cpp",
            lookup_target_module_compile_sources("cpp", "pytra.std.time"),
        )
        self.assertIn(
            "src/runtime/cpp/generated/built_in/iter_ops.cpp",
            lookup_target_module_compile_sources("cpp", "pytra.built_in.iter_ops"),
        )
        self.assertIn(
            "src/runtime/cpp/generated/utils/png.cpp",
            lookup_target_module_compile_sources("cpp", "pytra.utils.png"),
        )
        self.assertIn(
            "src/runtime/cpp/native/core/gc.ext.cpp",
            lookup_target_module_compile_sources("cpp", "pytra.core.gc"),
        )
        self.assertEqual(
            lookup_target_module_compile_sources("cpp", "pytra.core.dict"),
            [],
        )

    def test_real_repo_cpp_core_layout_exposes_surface_and_ownership_lanes(self) -> None:
        self.assertTrue((ROOT / "src/runtime/cpp/core/dict.h").exists())
        self.assertTrue((ROOT / "src/runtime/cpp/native/core/dict.ext.h").exists())
        self.assertTrue((ROOT / "src/runtime/cpp/generated/core/README.md").exists())
        self.assertEqual(
            lookup_target_module_primary_header("cpp", "pytra.core.dict"),
            "src/runtime/cpp/core/dict.h",
        )
        self.assertIn(
            "src/runtime/cpp/native/core/gc.ext.cpp",
            lookup_target_module_compile_sources("cpp", "pytra.core.gc"),
        )

    def test_iter_target_core_module_ids_supports_future_plain_core_headers(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            runtime_root = root / "src/runtime/cpp"
            (runtime_root / "core").mkdir(parents=True, exist_ok=True)
            (runtime_root / "core/dict.h").write_text("#pragma once\n", encoding="utf-8")
            (runtime_root / "core/py_runtime.h").write_text("#pragma once\n", encoding="utf-8")

            with patch.object(gen_mod, "ROOT", root):
                module_ids = gen_mod._iter_target_core_module_ids("cpp")

        self.assertEqual(module_ids, ["pytra.core.dict", "pytra.core.py_runtime"])

    def test_cpp_core_artifacts_support_future_generated_native_split(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            runtime_root = root / "src/runtime/cpp"
            (runtime_root / "core").mkdir(parents=True, exist_ok=True)
            (runtime_root / "generated/core").mkdir(parents=True, exist_ok=True)
            (runtime_root / "native/core").mkdir(parents=True, exist_ok=True)
            (runtime_root / "core/dict.h").write_text("#pragma once\n", encoding="utf-8")
            (runtime_root / "generated/core/dict.cpp").write_text("// gen\n", encoding="utf-8")
            (runtime_root / "native/core/dict.cpp").write_text("// native\n", encoding="utf-8")

            with patch.object(gen_mod, "ROOT", root):
                art = gen_mod._target_cpp_core_artifacts("dict")

        self.assertEqual(
            art,
            {
                "public_headers": ["src/runtime/cpp/core/dict.h"],
                "compile_sources": [
                    "src/runtime/cpp/generated/core/dict.cpp",
                    "src/runtime/cpp/native/core/dict.cpp",
                ],
                "companions": ["generated", "native"],
            },
        )

    def test_representative_std_modules_follow_generated_native_shim_contract(self) -> None:
        cases = [
            ("math", "float64 sqrt(float64 x);"),
            ("os_path", "str join(const str& a, const str& b);"),
            ("time", "float64 perf_counter();"),
        ]
        for module_tail, marker in cases:
            module_id = "pytra.std." + module_tail
            self.assertEqual(
                lookup_target_module_primary_header("cpp", module_id),
                f"src/runtime/cpp/pytra/std/{module_tail}.h",
            )
            self.assertIn(
                f"src/runtime/cpp/native/std/{module_tail}.cpp",
                lookup_target_module_compile_sources("cpp", module_id),
            )

            shim = (ROOT / "src/runtime/cpp/pytra/std" / f"{module_tail}.h").read_text(encoding="utf-8")
            generated_header = (ROOT / "src/runtime/cpp/generated/std" / f"{module_tail}.h").read_text(encoding="utf-8")
            native_cpp = (ROOT / "src/runtime/cpp/native/std" / f"{module_tail}.cpp").read_text(encoding="utf-8")

            self.assertIn(f'#include "runtime/cpp/generated/std/{module_tail}.h"', shim)
            self.assertNotIn(f'runtime/cpp/native/std/{module_tail}.h', shim)
            self.assertIn(marker, generated_header)
            self.assertIn(f'#include "runtime/cpp/generated/std/{module_tail}.h"', native_cpp)
            self.assertFalse((ROOT / "src/runtime/cpp/native/std" / f"{module_tail}.h").exists())

    def test_import_binding_runtime_module_resolution_uses_index(self) -> None:
        self.assertEqual(
            resolve_import_binding_runtime_module("pytra.utils", "png", "symbol"),
            "pytra.utils.png",
        )
        self.assertEqual(
            resolve_import_binding_runtime_module("pytra.std.time", "perf_counter", "symbol"),
            "pytra.std.time",
        )
        self.assertEqual(
            resolve_import_binding_runtime_module("math", "", "module"),
            "pytra.std.math",
        )

    def test_cpp_namespace_resolution_uses_runtime_group(self) -> None:
        self.assertEqual(lookup_cpp_namespace_for_runtime_module("math"), "pytra::std::math")
        self.assertEqual(
            lookup_cpp_namespace_for_runtime_module("pytra.utils.png"),
            "pytra::utils::png",
        )
        self.assertEqual(
            lookup_cpp_namespace_for_runtime_module("pytra.built_in.iter_ops"),
            "",
        )
        self.assertEqual(
            lookup_cpp_namespace_for_runtime_module("pytra.core.dict"),
            "",
        )
        self.assertEqual(canonical_runtime_module_id("math"), "pytra.std.math")


if __name__ == "__main__":
    unittest.main()
