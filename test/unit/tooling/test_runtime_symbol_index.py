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
from toolchain.frontends import runtime_symbol_index as runtime_index_mod
from toolchain.frontends.runtime_symbol_index import canonical_runtime_module_id
from toolchain.frontends.runtime_symbol_index import clear_runtime_symbol_index_cache
from toolchain.frontends.runtime_symbol_index import lookup_cpp_namespace_for_runtime_module
from toolchain.frontends.runtime_symbol_index import lookup_runtime_symbol_doc
from toolchain.frontends.runtime_symbol_index import resolve_import_binding_runtime_module
from toolchain.frontends.runtime_symbol_index import resolve_import_binding_doc
from toolchain.frontends.runtime_symbol_index import lookup_target_module_primary_compiler_header
from toolchain.frontends.runtime_symbol_index import lookup_target_module_primary_header
from toolchain.frontends.runtime_symbol_index import lookup_target_module_compile_sources
from toolchain.frontends.runtime_symbol_index import load_runtime_symbol_index


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
        self.assertEqual(string_symbols.get("py_join", {}).get("kind"), "function")
        self.assertEqual(string_symbols.get("py_split", {}).get("kind"), "function")
        self.assertEqual(string_symbols.get("py_splitlines", {}).get("kind"), "function")
        self.assertEqual(string_symbols.get("py_count", {}).get("kind"), "function")

        numeric_ops = modules.get("pytra.built_in.numeric_ops")
        self.assertIsInstance(numeric_ops, dict)
        numeric_symbols = numeric_ops.get("symbols")
        self.assertIsInstance(numeric_symbols, dict)
        self.assertEqual(numeric_symbols.get("sum", {}).get("kind"), "function")
        self.assertEqual(numeric_symbols.get("py_min", {}).get("kind"), "function")
        self.assertEqual(numeric_symbols.get("py_max", {}).get("kind"), "function")

        scalar_ops = modules.get("pytra.built_in.scalar_ops")
        self.assertIsInstance(scalar_ops, dict)
        scalar_symbols = scalar_ops.get("symbols")
        self.assertIsInstance(scalar_symbols, dict)
        self.assertEqual(scalar_symbols.get("py_to_int64_base", {}).get("kind"), "function")
        self.assertEqual(scalar_symbols.get("py_ord", {}).get("kind"), "function")
        self.assertEqual(scalar_symbols.get("py_chr", {}).get("kind"), "function")

        io_ops = modules.get("pytra.built_in.io_ops")
        self.assertIsInstance(io_ops, dict)
        io_symbols = io_ops.get("symbols")
        self.assertIsInstance(io_symbols, dict)
        self.assertEqual(io_symbols.get("py_print", {}).get("kind"), "function")

        zip_ops = modules.get("pytra.built_in.zip_ops")
        self.assertIsInstance(zip_ops, dict)
        zip_symbols = zip_ops.get("symbols")
        self.assertIsInstance(zip_symbols, dict)
        self.assertEqual(zip_symbols.get("zip", {}).get("kind"), "function")

        sequence_mod = modules.get("pytra.built_in.sequence")
        self.assertIsInstance(sequence_mod, dict)
        sequence_symbols = sequence_mod.get("symbols")
        self.assertIsInstance(sequence_symbols, dict)
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

        gif_mod = modules.get("pytra.utils.gif")
        self.assertIsInstance(gif_mod, dict)
        gif_symbols = gif_mod.get("symbols")
        self.assertIsInstance(gif_symbols, dict)
        self.assertEqual(
            gif_symbols.get("save_gif", {}).get("call_adapter_kind"),
            "image.save_gif.keyword_defaults",
        )

        math_mod = modules.get("pytra.std.math")
        self.assertIsInstance(math_mod, dict)
        math_symbols = math_mod.get("symbols")
        self.assertIsInstance(math_symbols, dict)
        self.assertEqual(math_symbols.get("pi", {}).get("kind"), "const")
        self.assertEqual(math_symbols.get("pi", {}).get("semantic_tag"), "stdlib.symbol.pi")
        self.assertEqual(math_symbols.get("e", {}).get("kind"), "const")
        self.assertEqual(math_symbols.get("sqrt", {}).get("semantic_tag"), "stdlib.fn.sqrt")

        pathlib_mod = modules.get("pytra.std.pathlib")
        self.assertIsInstance(pathlib_mod, dict)
        pathlib_symbols = pathlib_mod.get("symbols")
        self.assertIsInstance(pathlib_symbols, dict)
        self.assertEqual(pathlib_symbols.get("Path", {}).get("kind"), "class")

    def test_cpp_target_artifacts_follow_direct_generated_native_contract(self) -> None:
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
        self.assertEqual(iter_ops.get("public_headers"), ["src/runtime/cpp/generated/built_in/iter_ops.h"])
        self.assertEqual(iter_ops.get("compiler_headers"), ["src/runtime/cpp/generated/built_in/iter_ops.h"])
        self.assertIn("src/runtime/cpp/generated/built_in/iter_ops.cpp", iter_ops.get("compile_sources", []))

        sequence_mod = cpp_modules.get("pytra.built_in.sequence")
        self.assertIsInstance(sequence_mod, dict)
        self.assertEqual(sequence_mod.get("companions"), ["generated", "native"])
        self.assertEqual(
            sequence_mod.get("public_headers"),
            ["src/runtime/cpp/generated/built_in/sequence.h"],
        )
        self.assertEqual(
            sequence_mod.get("compiler_headers"),
            ["src/runtime/cpp/generated/built_in/sequence.h"],
        )
        self.assertIn(
            "src/runtime/cpp/generated/built_in/sequence.cpp",
            sequence_mod.get("compile_sources", []),
        )

        string_ops = cpp_modules.get("pytra.built_in.string_ops")
        self.assertIsInstance(string_ops, dict)
        self.assertEqual(string_ops.get("companions"), ["generated"])
        self.assertEqual(
            string_ops.get("public_headers"),
            ["src/runtime/cpp/generated/built_in/string_ops.h"],
        )
        self.assertEqual(
            string_ops.get("compiler_headers"),
            ["src/runtime/cpp/generated/built_in/string_ops.h"],
        )
        self.assertIn(
            "src/runtime/cpp/generated/built_in/string_ops.cpp",
            string_ops.get("compile_sources", []),
        )

        numeric_ops = cpp_modules.get("pytra.built_in.numeric_ops")
        self.assertIsInstance(numeric_ops, dict)
        self.assertEqual(numeric_ops.get("companions"), ["generated"])
        self.assertEqual(
            numeric_ops.get("public_headers"),
            ["src/runtime/cpp/generated/built_in/numeric_ops.h"],
        )
        self.assertEqual(
            numeric_ops.get("compiler_headers"),
            ["src/runtime/cpp/generated/built_in/numeric_ops.h"],
        )
        self.assertEqual(numeric_ops.get("compile_sources"), [])

        scalar_ops = cpp_modules.get("pytra.built_in.scalar_ops")
        self.assertIsInstance(scalar_ops, dict)
        self.assertEqual(scalar_ops.get("companions"), ["generated", "native"])
        self.assertEqual(
            scalar_ops.get("public_headers"),
            ["src/runtime/cpp/generated/built_in/scalar_ops.h"],
        )
        self.assertEqual(
            scalar_ops.get("compiler_headers"),
            ["src/runtime/cpp/generated/built_in/scalar_ops.h"],
        )
        self.assertEqual(scalar_ops.get("compile_sources"), [])

        io_ops = cpp_modules.get("pytra.built_in.io_ops")
        self.assertIsInstance(io_ops, dict)
        self.assertEqual(io_ops.get("companions"), ["generated", "native"])
        self.assertEqual(
            io_ops.get("public_headers"),
            ["src/runtime/cpp/generated/built_in/io_ops.h"],
        )
        self.assertEqual(
            io_ops.get("compiler_headers"),
            ["src/runtime/cpp/generated/built_in/io_ops.h"],
        )
        self.assertEqual(io_ops.get("compile_sources"), [])

        zip_ops = cpp_modules.get("pytra.built_in.zip_ops")
        self.assertIsInstance(zip_ops, dict)
        self.assertEqual(zip_ops.get("companions"), ["generated"])
        self.assertEqual(
            zip_ops.get("public_headers"),
            ["src/runtime/cpp/generated/built_in/zip_ops.h"],
        )
        self.assertEqual(
            zip_ops.get("compiler_headers"),
            ["src/runtime/cpp/generated/built_in/zip_ops.h"],
        )
        self.assertEqual(zip_ops.get("compile_sources"), [])

        time_mod = cpp_modules.get("pytra.std.time")
        self.assertIsInstance(time_mod, dict)
        self.assertEqual(time_mod.get("companions"), ["generated", "native"])
        self.assertEqual(time_mod.get("public_headers"), ["src/runtime/cpp/generated/std/time.h"])
        self.assertEqual(time_mod.get("compiler_headers"), ["src/runtime/cpp/generated/std/time.h"])
        self.assertIn("src/runtime/cpp/native/std/time.cpp", time_mod.get("compile_sources", []))
        self.assertNotIn("src/runtime/cpp/std/time.ext.cpp", time_mod.get("compile_sources", []))

        png_mod = cpp_modules.get("pytra.utils.png")
        self.assertIsInstance(png_mod, dict)
        self.assertEqual(png_mod.get("companions"), ["generated"])
        self.assertEqual(png_mod.get("public_headers"), ["src/runtime/cpp/generated/utils/png.h"])
        self.assertEqual(png_mod.get("compiler_headers"), ["src/runtime/cpp/generated/utils/png.h"])
        self.assertIn("src/runtime/cpp/generated/utils/png.cpp", png_mod.get("compile_sources", []))

        core_dict = cpp_modules.get("pytra.core.dict")
        self.assertIsInstance(core_dict, dict)
        self.assertEqual(core_dict.get("companions"), ["native"])
        self.assertEqual(core_dict.get("public_headers"), ["src/runtime/cpp/native/core/dict.h"])
        self.assertEqual(core_dict.get("compiler_headers"), ["src/runtime/cpp/native/core/dict.h"])

        core_gc = cpp_modules.get("pytra.core.gc")
        self.assertIsInstance(core_gc, dict)
        self.assertEqual(core_gc.get("companions"), ["native"])
        self.assertEqual(core_gc.get("public_headers"), ["src/runtime/cpp/native/core/gc.h"])
        self.assertEqual(core_gc.get("compiler_headers"), ["src/runtime/cpp/native/core/gc.h"])
        self.assertIn("src/runtime/cpp/native/core/gc.cpp", core_gc.get("compile_sources", []))

        core_io = cpp_modules.get("pytra.core.io")
        self.assertIsInstance(core_io, dict)
        self.assertEqual(core_io.get("companions"), ["native"])
        self.assertEqual(core_io.get("public_headers"), ["src/runtime/cpp/native/core/io.h"])
        self.assertEqual(core_io.get("compiler_headers"), ["src/runtime/cpp/native/core/io.h"])
        self.assertIn("src/runtime/cpp/native/core/io.cpp", core_io.get("compile_sources", []))

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
            "src/runtime/cpp/generated/std/time.h",
        )
        self.assertEqual(
            lookup_target_module_primary_header("cpp", "pytra.built_in.iter_ops"),
            "src/runtime/cpp/generated/built_in/iter_ops.h",
        )
        self.assertEqual(
            lookup_target_module_primary_header("cpp", "pytra.built_in.numeric_ops"),
            "src/runtime/cpp/generated/built_in/numeric_ops.h",
        )
        self.assertEqual(
            lookup_target_module_primary_header("cpp", "pytra.built_in.scalar_ops"),
            "src/runtime/cpp/generated/built_in/scalar_ops.h",
        )
        self.assertEqual(
            lookup_target_module_primary_header("cpp", "pytra.built_in.io_ops"),
            "src/runtime/cpp/generated/built_in/io_ops.h",
        )
        self.assertEqual(
            lookup_target_module_primary_header("cpp", "pytra.built_in.zip_ops"),
            "src/runtime/cpp/generated/built_in/zip_ops.h",
        )
        self.assertEqual(
            lookup_target_module_primary_header("cpp", "pytra.utils.png"),
            "src/runtime/cpp/generated/utils/png.h",
        )
        self.assertEqual(
            lookup_target_module_primary_header("cpp", "pytra.core.dict"),
            "src/runtime/cpp/native/core/dict.h",
        )

    def test_runtime_symbol_index_loader_returns_primary_cpp_compiler_header(self) -> None:
        self.assertEqual(
            lookup_target_module_primary_compiler_header("cpp", "pytra.std.time"),
            "src/runtime/cpp/generated/std/time.h",
        )
        self.assertEqual(
            lookup_target_module_primary_compiler_header("cpp", "pytra.built_in.iter_ops"),
            "src/runtime/cpp/generated/built_in/iter_ops.h",
        )
        self.assertEqual(
            lookup_target_module_primary_compiler_header("cpp", "pytra.built_in.numeric_ops"),
            "src/runtime/cpp/generated/built_in/numeric_ops.h",
        )
        self.assertEqual(
            lookup_target_module_primary_compiler_header("cpp", "pytra.utils.png"),
            "src/runtime/cpp/generated/utils/png.h",
        )
        self.assertEqual(
            lookup_target_module_primary_compiler_header("cpp", "pytra.core.dict"),
            "src/runtime/cpp/native/core/dict.h",
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
            "src/runtime/cpp/generated/built_in/sequence.cpp",
            lookup_target_module_compile_sources("cpp", "pytra.built_in.sequence"),
        )
        self.assertIn(
            "src/runtime/cpp/generated/built_in/string_ops.cpp",
            lookup_target_module_compile_sources("cpp", "pytra.built_in.string_ops"),
        )
        self.assertEqual(
            lookup_target_module_compile_sources("cpp", "pytra.built_in.numeric_ops"),
            [],
        )
        self.assertEqual(
            lookup_target_module_compile_sources("cpp", "pytra.built_in.scalar_ops"),
            [],
        )
        self.assertEqual(
            lookup_target_module_compile_sources("cpp", "pytra.built_in.io_ops"),
            [],
        )
        self.assertEqual(
            lookup_target_module_compile_sources("cpp", "pytra.built_in.zip_ops"),
            [],
        )

    def test_runtime_symbol_index_loader_rejects_non_object_root(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "runtime_symbol_index.json"
            out.write_text('["not-an-object"]', encoding="utf-8")
            with patch.object(runtime_index_mod, "INDEX_PATH", out):
                clear_runtime_symbol_index_cache()
                self.assertEqual(load_runtime_symbol_index(), {})
                clear_runtime_symbol_index_cache()
        self.assertIn(
            "src/runtime/cpp/generated/utils/png.cpp",
            lookup_target_module_compile_sources("cpp", "pytra.utils.png"),
        )
        self.assertIn(
            "src/runtime/cpp/native/core/gc.cpp",
            lookup_target_module_compile_sources("cpp", "pytra.core.gc"),
        )
        self.assertEqual(
            lookup_target_module_compile_sources("cpp", "pytra.core.dict"),
            [],
        )

    def test_lookup_runtime_symbol_doc_supports_functions_and_constants(self) -> None:
        self.assertEqual(
            lookup_runtime_symbol_doc("math", "sqrt"),
            {
                "dispatch": "function",
                "kind": "function",
                "semantic_tag": "stdlib.fn.sqrt",
            },
        )
        self.assertEqual(
            lookup_runtime_symbol_doc("math", "pi"),
            {
                "dispatch": "value",
                "kind": "const",
                "semantic_tag": "stdlib.symbol.pi",
            },
        )
        self.assertEqual(
            lookup_runtime_symbol_doc("pytra.utils.gif", "save_gif"),
            {
                "call_adapter_kind": "image.save_gif.keyword_defaults",
                "dispatch": "function",
                "kind": "function",
                "semantic_tag": "stdlib.fn.save_gif",
            },
        )
        self.assertEqual(lookup_runtime_symbol_doc("math", "missing"), {})

    def test_resolve_import_binding_doc_returns_canonical_runtime_metadata(self) -> None:
        self.assertEqual(
            resolve_import_binding_doc("math", "", "module"),
            {
                "source_module_id": "math",
                "source_export_name": "",
                "source_binding_kind": "module",
                "runtime_module_id": "pytra.std.math",
                "runtime_group": "std",
                "resolved_binding_kind": "module",
            },
        )
        self.assertEqual(
            resolve_import_binding_doc("math", "sqrt", "symbol"),
            {
                "source_module_id": "math",
                "source_export_name": "sqrt",
                "source_binding_kind": "symbol",
                "runtime_module_id": "pytra.std.math",
                "runtime_group": "std",
                "resolved_binding_kind": "symbol",
                "runtime_symbol": "sqrt",
                "runtime_symbol_kind": "function",
                "runtime_symbol_dispatch": "function",
                "runtime_semantic_tag": "stdlib.fn.sqrt",
            },
        )
        self.assertEqual(
            resolve_import_binding_doc("math", "pi", "symbol"),
            {
                "source_module_id": "math",
                "source_export_name": "pi",
                "source_binding_kind": "symbol",
                "runtime_module_id": "pytra.std.math",
                "runtime_group": "std",
                "resolved_binding_kind": "symbol",
                "runtime_symbol": "pi",
                "runtime_symbol_kind": "const",
                "runtime_symbol_dispatch": "value",
                "runtime_semantic_tag": "stdlib.symbol.pi",
            },
        )
        self.assertEqual(
            resolve_import_binding_doc("pytra.utils.gif", "save_gif", "symbol"),
            {
                "source_module_id": "pytra.utils.gif",
                "source_export_name": "save_gif",
                "source_binding_kind": "symbol",
                "runtime_module_id": "pytra.utils.gif",
                "runtime_group": "utils",
                "resolved_binding_kind": "symbol",
                "runtime_symbol": "save_gif",
                "runtime_symbol_kind": "function",
                "runtime_symbol_dispatch": "function",
                "runtime_semantic_tag": "stdlib.fn.save_gif",
                "runtime_call_adapter_kind": "image.save_gif.keyword_defaults",
            },
        )
        self.assertEqual(
            resolve_import_binding_doc("pytra.std", "json", "symbol"),
            {
                "source_module_id": "pytra.std",
                "source_export_name": "json",
                "source_binding_kind": "symbol",
                "runtime_module_id": "pytra.std.json",
                "runtime_group": "std",
                "resolved_binding_kind": "module",
            },
        )
        self.assertEqual(
            resolve_import_binding_doc("pytra.utils", "gif", "symbol"),
            {
                "source_module_id": "pytra.utils",
                "source_export_name": "gif",
                "source_binding_kind": "symbol",
                "runtime_module_id": "pytra.utils.gif",
                "runtime_group": "utils",
                "resolved_binding_kind": "module",
            },
        )

    def test_real_repo_cpp_core_layout_exposes_direct_ownership_lanes(self) -> None:
        self.assertFalse((ROOT / "src/runtime/cpp/core/dict.h").exists())
        self.assertTrue((ROOT / "src/runtime/cpp/native/core/dict.h").exists())
        self.assertTrue((ROOT / "src/runtime/cpp/generated/core/README.md").exists())
        self.assertEqual(
            lookup_target_module_primary_header("cpp", "pytra.core.dict"),
            "src/runtime/cpp/native/core/dict.h",
        )
        self.assertEqual(
            lookup_target_module_primary_compiler_header("cpp", "pytra.core.dict"),
            "src/runtime/cpp/native/core/dict.h",
        )
        self.assertIn(
            "src/runtime/cpp/native/core/gc.cpp",
            lookup_target_module_compile_sources("cpp", "pytra.core.gc"),
        )

    def test_iter_target_core_module_ids_supports_future_generated_native_headers(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            runtime_root = root / "src/runtime/cpp"
            (runtime_root / "native/core").mkdir(parents=True, exist_ok=True)
            (runtime_root / "native/core/dict.h").write_text("#pragma once\n", encoding="utf-8")
            (runtime_root / "native/core/py_runtime.h").write_text("#pragma once\n", encoding="utf-8")

            with patch.object(gen_mod, "ROOT", root):
                module_ids = gen_mod._iter_target_core_module_ids("cpp")

        self.assertEqual(module_ids, ["pytra.core.dict", "pytra.core.py_runtime"])

    def test_cpp_core_artifacts_support_future_generated_native_split(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            runtime_root = root / "src/runtime/cpp"
            (runtime_root / "generated/core").mkdir(parents=True, exist_ok=True)
            (runtime_root / "native/core").mkdir(parents=True, exist_ok=True)
            (runtime_root / "native/core/dict.h").write_text("#pragma once\n", encoding="utf-8")
            (runtime_root / "generated/core/dict.cpp").write_text("// gen\n", encoding="utf-8")
            (runtime_root / "native/core/dict.cpp").write_text("// native\n", encoding="utf-8")

            with patch.object(gen_mod, "ROOT", root):
                art = gen_mod._target_cpp_core_artifacts("dict")

        self.assertEqual(
            art,
            {
                "public_headers": ["src/runtime/cpp/native/core/dict.h"],
                "compiler_headers": ["src/runtime/cpp/native/core/dict.h"],
                "compile_sources": [
                    "src/runtime/cpp/generated/core/dict.cpp",
                    "src/runtime/cpp/native/core/dict.cpp",
                ],
                "companions": ["generated", "native"],
            },
        )

    def test_representative_std_modules_follow_direct_generated_native_contract(self) -> None:
        cases = [
            ("math", "float64 sqrt(float64 x);"),
            ("os_path", "str join(const str& a, const str& b);"),
            ("time", "float64 perf_counter();"),
        ]
        for module_tail, marker in cases:
            module_id = "pytra.std." + module_tail
            self.assertEqual(
                lookup_target_module_primary_header("cpp", module_id),
                f"src/runtime/cpp/generated/std/{module_tail}.h",
            )
            self.assertEqual(
                lookup_target_module_primary_compiler_header("cpp", module_id),
                f"src/runtime/cpp/generated/std/{module_tail}.h",
            )
            self.assertIn(
                f"src/runtime/cpp/native/std/{module_tail}.cpp",
                lookup_target_module_compile_sources("cpp", module_id),
            )

            generated_header = (ROOT / "src/runtime/cpp/generated/std" / f"{module_tail}.h").read_text(encoding="utf-8")
            native_cpp = (ROOT / "src/runtime/cpp/native/std" / f"{module_tail}.cpp").read_text(encoding="utf-8")

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
