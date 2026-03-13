from __future__ import annotations

import unittest
from pathlib import Path
import sys

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from toolchain.compiler.pytra_cli_profiles import (
    get_target_profile,
    list_parity_targets,
    list_supported_targets,
    make_noncpp_build_plan,
    resolve_output_path,
    validate_profile_option_compatibility,
)


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

    def test_make_noncpp_build_plan_cs_uses_generated_time_math_and_json_lanes(self) -> None:
        output = Path("out/hello.cs")
        plan = make_noncpp_build_plan(
            root=ROOT,
            target="cs",
            output_path=output,
            source_stem="hello",
            run_after_build=False,
        )
        self.assertIsNotNone(plan.build_cmd)
        self.assertIn(str(ROOT / "src/runtime/cs/generated/std/time.cs"), plan.build_cmd)
        self.assertIn(str(ROOT / "src/runtime/cs/native/std/time_native.cs"), plan.build_cmd)
        self.assertIn(str(ROOT / "src/runtime/cs/generated/std/math.cs"), plan.build_cmd)
        self.assertIn(str(ROOT / "src/runtime/cs/generated/std/json.cs"), plan.build_cmd)
        self.assertNotIn(str(ROOT / "src/runtime/cs/native/built_in/math.cs"), plan.build_cmd)
        self.assertNotIn(str(ROOT / "src/runtime/cs/native/std/json.cs"), plan.build_cmd)

    def test_validate_profile_option_compatibility_rejects_codegen_opt_for_noncpp(self) -> None:
        profile = get_target_profile("rs")
        err = validate_profile_option_compatibility(
            profile,
            codegen_opt=2,
            build=False,
            compiler="g++",
            std="c++20",
            opt="-O2",
            exe="app.out",
        )
        self.assertIn("--codegen-opt", err)

    def test_validate_profile_option_compatibility_rejects_cpp_build_opts_for_noncpp(self) -> None:
        profile = get_target_profile("go")
        err = validate_profile_option_compatibility(
            profile,
            codegen_opt=None,
            build=True,
            compiler="clang++",
            std="c++20",
            opt="-O2",
            exe="app.out",
        )
        self.assertIn("--compiler/--std/--opt/--exe", err)

    def test_target_lists_are_stable(self) -> None:
        supported = list_supported_targets()
        self.assertIn("cpp", supported)
        self.assertIn("nim", supported)
        parity = list_parity_targets()
        self.assertEqual(parity[0], "cpp")
        self.assertEqual(parity[-1], "nim")

    def test_runner_needs_are_defined(self) -> None:
        profile = get_target_profile("kotlin")
        self.assertEqual(profile.runner_needs, ("python", "kotlinc", "java"))


if __name__ == "__main__":
    unittest.main()
