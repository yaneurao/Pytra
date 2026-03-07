from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import gen_runtime_from_manifest as gen_mod


class GenImageRuntimeFromCanonicalTest(unittest.TestCase):
    def test_resolve_targets_all_contains_swift_and_cpp(self) -> None:
        all_items = gen_mod.load_manifest_items(ROOT / "tools" / "runtime_generation_manifest.json")
        targets = gen_mod.resolve_targets("all", all_items)
        self.assertIn("cpp", targets)
        self.assertIn("swift", targets)

    def test_build_generation_plan_uses_generated_cpp_convention(self) -> None:
        all_items = gen_mod.load_manifest_items(ROOT / "tools" / "runtime_generation_manifest.json")
        plan = gen_mod.build_generation_plan(all_items, ["cpp", "php"], ["utils/png"])
        paths = [item.output_rel for item in plan]
        self.assertIn("src/runtime/cpp/generated/utils/png.cpp", paths)
        self.assertIn("src/runtime/php/pytra-gen/runtime/png.php", paths)

    def test_inject_generated_header_for_php_keeps_php_open_tag(self) -> None:
        src = "<?php\necho 'x';\n"
        out = gen_mod.inject_generated_header(src, "php", "src/pytra/utils/png.py")
        self.assertTrue(out.startswith("<?php\n"))
        self.assertIn("// source: src/pytra/utils/png.py", out)
        self.assertIn("// generated-by: tools/gen_runtime_from_manifest.py", out)

    def test_inject_generated_header_for_lua_uses_lua_comment_prefix(self) -> None:
        src = "print('x')\n"
        out = gen_mod.inject_generated_header(src, "lua", "src/pytra/utils/gif.py")
        self.assertTrue(out.startswith("-- AUTO-GENERATED FILE. DO NOT EDIT."))
        self.assertIn("-- source: src/pytra/utils/gif.py", out)


if __name__ == "__main__":
    unittest.main()
