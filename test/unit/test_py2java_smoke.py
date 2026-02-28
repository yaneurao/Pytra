"""py2java (EAST based) smoke tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.py2java import load_east, load_java_profile, transpile_to_java
from hooks.java.emitter.java_native_emitter import transpile_to_java_native
from src.pytra.compiler.east_parts.core import convert_path
from comment_fidelity import assert_no_generated_comments, assert_sample01_module_comments


def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


class Py2JavaSmokeTest(unittest.TestCase):
    def test_load_java_profile_contains_core_sections(self) -> None:
        profile = load_java_profile()
        self.assertIn("types", profile)
        self.assertIn("operators", profile)
        self.assertIn("syntax", profile)
        self.assertIn("runtime_calls", profile)

    def test_transpile_add_fixture_uses_native_output(self) -> None:
        fixture = find_fixture_case("add")
        east = load_east(fixture, parser_backend="self_hosted")
        java = transpile_to_java(east)
        self.assertIn("public final class Main", java)
        assert_no_generated_comments(self, java)
        self.assertNotIn("private static boolean __pytra_truthy(Object value)", java)
        self.assertNotIn("private static long __pytra_int(Object value)", java)
        self.assertNotIn("ProcessBuilder", java)

    def test_load_east_from_json(self) -> None:
        fixture = find_fixture_case("add")
        east = convert_path(fixture)
        with tempfile.TemporaryDirectory() as td:
            east_json = Path(td) / "case.east.json"
            east_json.write_text(json.dumps(east), encoding="utf-8")
            loaded = load_east(east_json)
            java = transpile_to_java(loaded)
        self.assertIn("public final class Main", java)

    def test_load_east_defaults_to_stage3_entry_and_returns_east3_shape(self) -> None:
        fixture = find_fixture_case("for_range")
        loaded = load_east(fixture, parser_backend="self_hosted")
        self.assertIsInstance(loaded, dict)
        self.assertEqual(loaded.get("kind"), "Module")
        self.assertEqual(loaded.get("east_stage"), 3)

    def test_cli_smoke_defaults_to_native_without_sidecar(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            out_java = Path(td) / "if_else.java"
            out_js = Path(td) / "if_else.js"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/py2java.py", str(fixture), "-o", str(out_java)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertTrue(out_java.exists())
            self.assertFalse(out_js.exists())
            txt = out_java.read_text(encoding="utf-8")
            self.assertIn("public final class", txt)
            self.assertNotIn("Auto-generated Java native source", txt)
            self.assertNotIn("private static boolean __pytra_truthy(Object value)", txt)
            runtime_java = Path(td) / "PyRuntime.java"
            self.assertTrue(runtime_java.exists())
            runtime_txt = runtime_java.read_text(encoding="utf-8")
            self.assertIn("static boolean __pytra_truthy(Object value)", runtime_txt)
            self.assertNotIn("ProcessBuilder", txt)
            self.assertFalse((Path(td) / "pytra" / "runtime.js").exists())

    def test_cli_rejects_stage2_compat_mode(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            out_java = Path(td) / "if_else.java"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/py2java.py", str(fixture), "-o", str(out_java), "--east-stage", "2"],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertIn("--east-stage 2 is no longer supported; use EAST3 (default).", proc.stderr)

    def test_java_native_emitter_skeleton_handles_module_function_class(self) -> None:
        fixture = find_fixture_case("inheritance")
        east = load_east(fixture, parser_backend="self_hosted")
        java = transpile_to_java_native(east, class_name="Main")
        self.assertIn("public final class Main", java)
        self.assertIn("public static class Animal", java)
        self.assertIn("public static class Dog extends Animal", java)
        self.assertIn('return (this.sound() + "-bark");', java)
        self.assertIn("public static void _case_main()", java)
        self.assertIn("Dog d = new Dog();", java)
        self.assertIn('System.out.println("True");', java)

    def test_java_native_emitter_skeleton_maps_simple_int_signature(self) -> None:
        fixture = find_fixture_case("add")
        east = load_east(fixture, parser_backend="self_hosted")
        java = transpile_to_java_native(east, class_name="Main")
        self.assertIn("public static long add(long a, long b)", java)
        self.assertIn("return (a + b);", java)
        self.assertIn('System.out.println("True");', java)

    def test_module_leading_comments_are_emitted(self) -> None:
        sample = ROOT / "sample" / "py" / "01_mandelbrot.py"
        east = load_east(sample, parser_backend="self_hosted")
        java = transpile_to_java_native(east, class_name="Main")
        assert_no_generated_comments(self, java)
        assert_sample01_module_comments(self, java, prefix="//")

    def test_java_native_emitter_lowers_if_and_forcore(self) -> None:
        if_fixture = find_fixture_case("if_else")
        if_east = load_east(if_fixture, parser_backend="self_hosted")
        if_java = transpile_to_java_native(if_east, class_name="Main")
        self.assertIn(
            "public static long abs_like(long n) {\n"
            "        if ((n < 0L)) {\n"
            "            return (-n);\n"
            "        } else {\n"
            "            return n;\n"
            "        }\n"
            "    }",
            if_java,
        )

        for_fixture = find_fixture_case("for_range")
        for_east = load_east(for_fixture, parser_backend="self_hosted")
        for_java = transpile_to_java_native(for_east, class_name="Main")
        self.assertIn("for (long i = 0L;", for_java)
        self.assertIn("total += i;", for_java)

    def test_java_native_emitter_uses_main_guard_body_for_sample_entry(self) -> None:
        sample = ROOT / "sample" / "py" / "17_monte_carlo_pi.py"
        east = load_east(sample, parser_backend="self_hosted")
        java = transpile_to_java_native(east, class_name="Main")
        self.assertIn("run_integer_benchmark();", java)

    def test_java_native_emitter_handles_bytearray_cast_and_runtime_noop(self) -> None:
        sample = ROOT / "sample" / "py" / "03_julia_set.py"
        east = load_east(sample, parser_backend="self_hosted")
        java = transpile_to_java_native(east, class_name="Main")
        self.assertIn("java.util.ArrayList<Long> pixels = new java.util.ArrayList<Long>();", java)
        self.assertIn("pixels.add(r);", java)
        self.assertIn("r = PyRuntime.__pytra_int(", java)
        self.assertIn("PyRuntime.__pytra_noop(out_path, width, height, pixels);", java)

    def test_java_native_emitter_allocates_sized_bytearray_for_subscript_set(self) -> None:
        sample = ROOT / "sample" / "py" / "05_mandelbrot_zoom.py"
        east = load_east(sample, parser_backend="self_hosted")
        java = transpile_to_java_native(east, class_name="Main")
        self.assertIn("PyRuntime.__pytra_bytearray((width * height))", java)
        self.assertIn("frame.set((int)(", java)

    def test_java_native_emitter_maps_math_calls_to_java_math(self) -> None:
        sample = ROOT / "sample" / "py" / "06_julia_parameter_sweep.py"
        east = load_east(sample, parser_backend="self_hosted")
        java = transpile_to_java_native(east, class_name="Main")
        self.assertIn("double angle = ((2.0 * Math.PI) * t);", java)
        self.assertIn("Math.cos(angle)", java)
        self.assertIn("Math.sin(angle)", java)

    def test_java_native_emitter_lowers_listcomp_and_repeat_list_init(self) -> None:
        sample = ROOT / "sample" / "py" / "07_game_of_life_loop.py"
        east = load_east(sample, parser_backend="self_hosted")
        java = transpile_to_java_native(east, class_name="Main")
        self.assertIn("grid = new java.util.ArrayList<Object>();", java)
        self.assertIn("grid.add(PyRuntime.__pytra_list_repeat(0L, w));", java)

    def test_java_native_emitter_maps_min_max_and_list_truthy(self) -> None:
        sample = ROOT / "sample" / "py" / "14_raymarching_light_cycle.py"
        east = load_east(sample, parser_backend="self_hosted")
        java = transpile_to_java_native(east, class_name="Main")
        self.assertIn("Math.max(", java)
        self.assertIn("Math.min(", java)

        sample2 = ROOT / "sample" / "py" / "13_maze_generation_steps.py"
        east2 = load_east(sample2, parser_backend="self_hosted")
        java2 = transpile_to_java_native(east2, class_name="Main")
        self.assertIn("while (((stack) != null && !(stack).isEmpty()))", java2)

    def test_java_native_emitter_lowers_tuple_subscript_swap_assignment(self) -> None:
        sample = ROOT / "sample" / "py" / "12_sort_visualizer.py"
        east = load_east(sample, parser_backend="self_hosted")
        java = transpile_to_java_native(east, class_name="Main")
        self.assertGreaterEqual(java.count("values.set((int)("), 2)
        self.assertIn("__tuple_", java)

    def test_java_native_emitter_lowers_len_and_subscript_set(self) -> None:
        sample = ROOT / "sample" / "py" / "07_game_of_life_loop.py"
        east = load_east(sample, parser_backend="self_hosted")
        java = transpile_to_java_native(east, class_name="Main")
        self.assertIn(".size()", java)
        self.assertIn(".set((int)(", java)

    def test_java_native_emitter_rejects_non_module_root(self) -> None:
        with self.assertRaises(RuntimeError):
            transpile_to_java_native({"kind": "FunctionDef"}, class_name="Main")

    def test_py2java_does_not_import_src_common(self) -> None:
        src = (ROOT / "src" / "py2java.py").read_text(encoding="utf-8")
        self.assertNotIn("src.common", src)
        self.assertNotIn("from common.", src)

    def test_java_runtime_source_path_is_migrated(self) -> None:
        runtime_path = ROOT / "src" / "runtime" / "java" / "pytra" / "built_in" / "PyRuntime.java"
        legacy_path = ROOT / "src" / "java_module" / "PyRuntime.java"
        self.assertTrue(runtime_path.exists())
        self.assertFalse(legacy_path.exists())


if __name__ == "__main__":
    unittest.main()
