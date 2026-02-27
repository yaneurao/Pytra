"""py2kotlin (EAST based) smoke tests."""

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

from src.py2kotlin import load_east, load_kotlin_profile, transpile_to_kotlin, transpile_to_kotlin_native
from src.pytra.compiler.east_parts.core import convert_path


def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


class Py2KotlinSmokeTest(unittest.TestCase):
    def test_load_kotlin_profile_contains_core_sections(self) -> None:
        profile = load_kotlin_profile()
        self.assertIn("types", profile)
        self.assertIn("operators", profile)
        self.assertIn("syntax", profile)
        self.assertIn("runtime_calls", profile)

    def test_transpile_add_fixture_sidecar_contains_node_bridge_and_main(self) -> None:
        fixture = find_fixture_case("add")
        east = load_east(fixture, parser_backend="self_hosted")
        kotlin = transpile_to_kotlin(east)
        self.assertIn("fun main(args: Array<String>)", kotlin)
        self.assertIn("ProcessBuilder", kotlin)
        self.assertIn('command.add("node")', kotlin)

    def test_kotlin_native_emitter_skeleton_handles_module_function_class(self) -> None:
        fixture = find_fixture_case("inheritance")
        east = load_east(fixture, parser_backend="self_hosted")
        kotlin = transpile_to_kotlin_native(east)
        self.assertIn("fun main(args: Array<String>)", kotlin)
        self.assertIn("open class Animal", kotlin)
        self.assertIn("open class Dog : Animal()", kotlin)
        self.assertIn("fun _case_main()", kotlin)

    def test_load_east_from_json(self) -> None:
        fixture = find_fixture_case("add")
        east = convert_path(fixture)
        with tempfile.TemporaryDirectory() as td:
            east_json = Path(td) / "case.east.json"
            east_json.write_text(json.dumps(east), encoding="utf-8")
            loaded = load_east(east_json)
            kotlin = transpile_to_kotlin_native(loaded)
        self.assertIn("fun main(args: Array<String>)", kotlin)

    def test_load_east_defaults_to_stage3_entry_and_returns_east3_shape(self) -> None:
        fixture = find_fixture_case("for_range")
        loaded = load_east(fixture, parser_backend="self_hosted")
        self.assertIsInstance(loaded, dict)
        self.assertEqual(loaded.get("kind"), "Module")
        self.assertEqual(loaded.get("east_stage"), 3)

    def test_cli_smoke_defaults_to_native_without_sidecar(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            out_kotlin = Path(td) / "if_else.kt"
            out_js = Path(td) / "if_else.js"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/py2kotlin.py", str(fixture), "-o", str(out_kotlin)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertTrue(out_kotlin.exists())
            self.assertFalse(out_js.exists())
            txt = out_kotlin.read_text(encoding="utf-8")
            self.assertIn("fun main(args: Array<String>)", txt)
            self.assertIn("Auto-generated Pytra Kotlin native source from EAST3.", txt)
            self.assertFalse((Path(td) / "pytra" / "runtime.js").exists())

    def test_cli_sidecar_mode_generates_js_and_runtime_shim(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            out_kotlin = Path(td) / "if_else.kt"
            out_js = Path(td) / "if_else.js"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/py2kotlin.py", str(fixture), "-o", str(out_kotlin), "--kotlin-backend", "sidecar"],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertTrue(out_kotlin.exists())
            self.assertTrue(out_js.exists())
            txt = out_kotlin.read_text(encoding="utf-8")
            self.assertIn("if_else.js", txt)
            self.assertTrue((Path(td) / "pytra" / "runtime.js").exists())

    def test_cli_rejects_stage2_compat_mode(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            out_kotlin = Path(td) / "if_else.kt"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/py2kotlin.py", str(fixture), "-o", str(out_kotlin), "--east-stage", "2"],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertIn("--east-stage 2 is no longer supported; use EAST3 (default).", proc.stderr)

    def test_py2kotlin_does_not_import_src_common(self) -> None:
        src = (ROOT / "src" / "py2kotlin.py").read_text(encoding="utf-8")
        self.assertNotIn("src.common", src)
        self.assertNotIn("from common.", src)

    def test_kotlin_runtime_source_path_is_migrated(self) -> None:
        runtime_path = ROOT / "src" / "runtime" / "kotlin" / "pytra" / "py_runtime.kt"
        legacy_path = ROOT / "src" / "kotlin_module" / "py_runtime.kt"
        self.assertTrue(runtime_path.exists())
        self.assertFalse(legacy_path.exists())


if __name__ == "__main__":
    unittest.main()
