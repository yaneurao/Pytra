from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import gen_runtime_from_manifest as gen_mod


class GenRuntimeFromManifestTest(unittest.TestCase):
    def test_load_manifest_items_contains_png_cpp_rs_and_cs_built_in_std(self) -> None:
        items = gen_mod.load_manifest_items(ROOT / "tools" / "runtime_generation_manifest.json")
        pairs = {(item.item_id, item.target, item.output_rel) for item in items}
        self.assertIn(("utils/png", "cpp", "src/runtime/cpp/generated/utils/png.cpp"), pairs)
        self.assertIn(("utils/png", "rs", "src/runtime/rs/generated/utils/png.rs"), pairs)
        self.assertIn(("built_in/type_id", "rs", "src/runtime/rs/generated/built_in/type_id.rs"), pairs)
        self.assertIn(("built_in/type_id", "cs", "src/runtime/cs/generated/built_in/type_id.cs"), pairs)
        self.assertIn(("std/pathlib", "cs", "src/runtime/cs/generated/std/pathlib.cs"), pairs)
        self.assertIn(("std/time", "java", "src/runtime/java/generated/std/time.java"), pairs)

    def test_built_in_manifest_covers_rs_and_cs_for_all_sot_modules(self) -> None:
        items = gen_mod.load_manifest_items(ROOT / "tools" / "runtime_generation_manifest.json")
        by_pair = {(item.item_id, item.target): item.output_rel for item in items}
        module_names = sorted(
            p.stem
            for p in (ROOT / "src" / "pytra" / "built_in").glob("*.py")
            if p.name != "__init__.py"
        )
        self.assertEqual(
            module_names,
            [
                "contains",
                "io_ops",
                "iter_ops",
                "numeric_ops",
                "predicates",
                "scalar_ops",
                "sequence",
                "string_ops",
                "type_id",
                "zip_ops",
            ],
        )
        for module_name in module_names:
            item_id = f"built_in/{module_name}"
            self.assertEqual(
                by_pair[(item_id, "rs")],
                f"src/runtime/rs/generated/built_in/{module_name}.rs",
            )
            self.assertEqual(
                by_pair[(item_id, "cs")],
                f"src/runtime/cs/generated/built_in/{module_name}.cs",
            )

    def test_resolve_targets_all_contains_cpp_and_swift(self) -> None:
        items = gen_mod.load_manifest_items(ROOT / "tools" / "runtime_generation_manifest.json")
        targets = gen_mod.resolve_targets("all", items)
        self.assertIn("cpp", targets)
        self.assertIn("swift", targets)

    def test_inject_generated_header_for_php_keeps_php_open_tag(self) -> None:
        src = "<?php\necho 'x';\n"
        out = gen_mod.inject_generated_header(src, "php", "src/pytra/utils/png.py")
        self.assertTrue(out.startswith("<?php\n"))
        self.assertIn("// source: src/pytra/utils/png.py", out)
        self.assertIn("// generated-by: tools/gen_runtime_from_manifest.py", out)

    def test_rewrite_cs_program_to_helper_renames_program_class(self) -> None:
        src = "\n".join(
            [
                "using System;",
                "public static class Program",
                "{",
                "    public static int f() { return 1; }",
                "}",
            ]
        )
        out = gen_mod.rewrite_cs_program_to_helper(src, "png_helper")
        self.assertIn("public static class png_helper", out)
        self.assertNotIn("public static class Program", out)

    def test_rewrite_cs_std_time_live_wrapper_targets_time_native(self) -> None:
        src = "\n".join(
            [
                "using Pytra.CsModule;",
                "public static class Program",
                "{",
                "    public static double perf_counter() { return __t.perf_counter(); }",
                "}",
            ]
        )
        out = gen_mod.rewrite_cs_std_time_live_wrapper(src)
        self.assertIn("namespace Pytra.CsModule", out)
        self.assertIn("public static class time", out)
        self.assertIn("return time_native.perf_counter();", out)
        self.assertNotIn("return __t.perf_counter();", out)

    def test_rewrite_java_std_time_live_wrapper_inlines_system_nanotime(self) -> None:
        src = "\n".join(
            [
                "public final class time {",
                "    public static double perf_counter() {",
                "        return __t.perf_counter();",
                "    }",
                "}",
            ]
        )
        out = gen_mod.rewrite_java_std_time_live_wrapper(src)
        self.assertIn("System.nanoTime()", out)
        self.assertNotIn("__t.perf_counter()", out)

    def test_rewrite_java_std_math_live_wrapper_inlines_java_math(self) -> None:
        src = "\n".join(
            [
                "public final class math {",
                "    public static double pi = extern(math.pi);",
                "    public static double fabs(double x) { return math.fabs(x); }",
                "    public static double pow(double x, double y) { return math.pow(x, y); }",
                "}",
            ]
        )
        out = gen_mod.rewrite_java_std_math_live_wrapper(src)
        self.assertIn("public static double pi = Math.PI;", out)
        self.assertIn("return Math.abs(x);", out)
        self.assertIn("return Math.pow(x, y);", out)
        self.assertNotIn("extern(math.pi)", out)
    def test_run_py2x_raises_when_backend_emits_no_text_and_no_file(self) -> None:
        with (
            patch.object(gen_mod, "get_backend_spec", return_value={}),
            patch.object(gen_mod, "load_east3_document", return_value={}),
            patch.object(gen_mod, "resolve_layer_options", return_value={}),
            patch.object(gen_mod, "lower_ir", return_value={}),
            patch.object(gen_mod, "optimize_ir", return_value={}),
            patch.object(gen_mod, "emit_source", return_value=""),
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "runtime generation backend emitted no inline text and wrote no file: "
                "nim -> src/runtime/nim/generated/utils/png_helper.nim",
            ):
                gen_mod.run_py2x(
                    "nim",
                    "src/pytra/utils/png.py",
                    "src/runtime/nim/generated/utils/png_helper.nim",
                )

    def test_run_py2x_nim_png_helper_lowers_try_finally(self) -> None:
        out = gen_mod.run_py2x(
            "nim",
            "src/pytra/utils/png.py",
            "src/runtime/nim/generated/utils/png_helper.nim",
        )
        self.assertIn("f.write(png)", out)
        self.assertIn("f.close()", out)
        self.assertNotIn("# unsupported stmt: Try", out)

    def test_run_py2x_lua_gif_helper_ignores_compile_time_std_imports(self) -> None:
        out = gen_mod.run_py2x(
            "lua",
            "src/pytra/utils/gif.py",
            "src/runtime/lua/generated/utils/gif_helper.lua",
        )
        self.assertIn("function grayscale_palette()", out)
        self.assertIn("function save_gif(", out)
        self.assertNotIn("pytra.std.abi", out)

    def test_wave_b_runtime_regeneration_check_passes(self) -> None:
        items = gen_mod.load_manifest_items(ROOT / "tools" / "runtime_generation_manifest.json")
        targets = gen_mod.resolve_targets("js,ts,lua,ruby,php", items)
        item_ids = gen_mod.resolve_item_ids("all", items)
        plan = gen_mod.build_generation_plan(items, targets, item_ids)
        checked, updated = gen_mod.generate(plan, check=True, dry_run=False)
        self.assertEqual(checked, 10)
        self.assertEqual(updated, 0)


if __name__ == "__main__":
    unittest.main()
