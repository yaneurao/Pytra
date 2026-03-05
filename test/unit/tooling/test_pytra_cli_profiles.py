from __future__ import annotations

import unittest
from pathlib import Path
import sys

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from toolchain.compiler.pytra_cli_profiles import make_noncpp_build_plan, resolve_output_path


class PytraCliProfilesTest(unittest.TestCase):
    def test_resolve_output_path_defaults_to_target_extension(self) -> None:
        src = Path("sample/py/hello_world.py")
        out = resolve_output_path(src, "rs", "", "out")
        self.assertEqual(out, Path("out/hello_world.rs"))

    def test_resolve_output_path_uses_main_for_java(self) -> None:
        src = Path("sample/py/hello_world.py")
        out = resolve_output_path(src, "java", "", "out_java")
        self.assertEqual(out, Path("out_java/Main.java"))

    def test_make_noncpp_build_plan_rs(self) -> None:
        output = Path("out/hello.rs")
        plan = make_noncpp_build_plan(
            root=ROOT,
            target="rs",
            output_path=output,
            source_stem="hello",
            run_after_build=True,
        )
        self.assertIsNotNone(plan.build_cmd)
        self.assertEqual(plan.build_cmd[0], "rustc")
        self.assertIsNotNone(plan.run_cmd)
        self.assertTrue(plan.run_cmd[0].endswith("hello_rs.out"))

    def test_make_noncpp_build_plan_js_run(self) -> None:
        output = Path("out/hello.js")
        plan = make_noncpp_build_plan(
            root=ROOT,
            target="js",
            output_path=output,
            source_stem="hello",
            run_after_build=True,
        )
        self.assertIsNone(plan.build_cmd)
        self.assertEqual(plan.run_cmd, ["node", str(output)])

    def test_make_noncpp_build_plan_nim_embeds_run(self) -> None:
        output = Path("out/hello.nim")
        plan = make_noncpp_build_plan(
            root=ROOT,
            target="nim",
            output_path=output,
            source_stem="hello",
            run_after_build=True,
        )
        self.assertIsNotNone(plan.build_cmd)
        self.assertIn("-r", plan.build_cmd)
        self.assertIsNone(plan.run_cmd)


if __name__ == "__main__":
    unittest.main()
