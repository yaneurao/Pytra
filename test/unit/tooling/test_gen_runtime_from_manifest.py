from __future__ import annotations

import sys
import unittest
from pathlib import Path


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
        self.assertIn(("std/time", "java", "src/runtime/java/pytra-gen/std/time.java"), pairs)

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


if __name__ == "__main__":
    unittest.main()
