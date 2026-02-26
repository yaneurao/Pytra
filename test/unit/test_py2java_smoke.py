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

    def test_transpile_add_fixture_contains_node_bridge_and_main(self) -> None:
        fixture = find_fixture_case("add")
        east = load_east(fixture, parser_backend="self_hosted")
        java = transpile_to_java(east)
        self.assertIn("public final class Main", java)
        self.assertIn("ProcessBuilder", java)
        self.assertIn('command.add("node");', java)

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
            self.assertIn("Auto-generated Java native source", txt)
            self.assertNotIn("ProcessBuilder", txt)
            self.assertFalse((Path(td) / "pytra" / "runtime.js").exists())

    def test_cli_sidecar_mode_generates_js_and_runtime_shim(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            out_java = Path(td) / "if_else.java"
            out_js = Path(td) / "if_else.js"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [
                    sys.executable,
                    "src/py2java.py",
                    str(fixture),
                    "-o",
                    str(out_java),
                    "--java-backend",
                    "sidecar",
                ],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertTrue(out_java.exists())
            self.assertTrue(out_js.exists())
            txt = out_java.read_text(encoding="utf-8")
            self.assertIn("if_else.js", txt)
            self.assertIn("ProcessBuilder", txt)
            self.assertTrue((Path(td) / "pytra" / "runtime.js").exists())

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
        self.assertIn("_case_main();", java)

    def test_java_native_emitter_skeleton_maps_simple_int_signature(self) -> None:
        fixture = find_fixture_case("add")
        east = load_east(fixture, parser_backend="self_hosted")
        java = transpile_to_java_native(east, class_name="Main")
        self.assertIn("public static long add(long a, long b)", java)
        self.assertIn("return (a + b);", java)

    def test_java_native_emitter_lowers_if_and_forcore(self) -> None:
        if_fixture = find_fixture_case("if_else")
        if_east = load_east(if_fixture, parser_backend="self_hosted")
        if_java = transpile_to_java_native(if_east, class_name="Main")
        self.assertIn("if ((n < 0L))", if_java)
        self.assertIn("return (-n);", if_java)
        self.assertNotIn("return 0L;", if_java)

        for_fixture = find_fixture_case("for_range")
        for_east = load_east(for_fixture, parser_backend="self_hosted")
        for_java = transpile_to_java_native(for_east, class_name="Main")
        self.assertIn("for (long i = 0L;", for_java)
        self.assertIn("total += i;", for_java)

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
