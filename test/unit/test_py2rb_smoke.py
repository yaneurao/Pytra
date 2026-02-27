"""py2rb (EAST based) smoke tests."""

from __future__ import annotations

import json
import os
import shutil
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

from src.py2rb import load_east, load_ruby_profile, transpile_to_ruby, transpile_to_ruby_native
from src.pytra.compiler.east_parts.core import convert_path


def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


class Py2RbSmokeTest(unittest.TestCase):
    def test_load_ruby_profile_contains_core_sections(self) -> None:
        profile = load_ruby_profile()
        self.assertIn("types", profile)
        self.assertIn("operators", profile)
        self.assertIn("syntax", profile)
        self.assertIn("runtime_calls", profile)

    def test_transpile_add_fixture_uses_native_output(self) -> None:
        fixture = find_fixture_case("add")
        east = load_east(fixture, parser_backend="self_hosted")
        ruby = transpile_to_ruby(east)
        self.assertIn("Auto-generated Pytra Ruby native source from EAST3.", ruby)
        self.assertIn("def add(a, b)", ruby)
        self.assertNotIn('exec.Command("node"', ruby)

    def test_ruby_native_emitter_skeleton_handles_module_function_class(self) -> None:
        fixture = find_fixture_case("inheritance")
        east = load_east(fixture, parser_backend="self_hosted")
        ruby = transpile_to_ruby_native(east)
        self.assertIn("class Animal", ruby)
        self.assertIn("class Dog < Animal", ruby)
        self.assertIn("def _case_main()", ruby)

    def test_load_east_from_json(self) -> None:
        fixture = find_fixture_case("add")
        east = convert_path(fixture)
        with tempfile.TemporaryDirectory() as td:
            east_json = Path(td) / "case.east.json"
            east_json.write_text(json.dumps(east), encoding="utf-8")
            loaded = load_east(east_json)
            ruby = transpile_to_ruby_native(loaded)
        self.assertIn("def add(a, b)", ruby)

    def test_load_east_defaults_to_stage3_entry_and_returns_east3_shape(self) -> None:
        fixture = find_fixture_case("for_range")
        loaded = load_east(fixture, parser_backend="self_hosted")
        self.assertIsInstance(loaded, dict)
        self.assertEqual(loaded.get("kind"), "Module")
        self.assertEqual(loaded.get("east_stage"), 3)

    def test_cli_smoke_defaults_to_native_without_sidecar(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            out_rb = Path(td) / "if_else.rb"
            out_js = Path(td) / "if_else.js"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/py2rb.py", str(fixture), "-o", str(out_rb)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertTrue(out_rb.exists())
            self.assertFalse(out_js.exists())
            txt = out_rb.read_text(encoding="utf-8")
            self.assertIn("Auto-generated Pytra Ruby native source from EAST3.", txt)

    def test_cli_rejects_stage2_compat_mode(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            out_rb = Path(td) / "if_else.rb"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/py2rb.py", str(fixture), "-o", str(out_rb), "--east-stage", "2"],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertIn("--east-stage 2 is no longer supported; use EAST3 (default).", proc.stderr)

    def test_py2rb_does_not_import_src_common(self) -> None:
        src = (ROOT / "src" / "py2rb.py").read_text(encoding="utf-8")
        self.assertNotIn("src.common", src)
        self.assertNotIn("from common.", src)

    def test_generated_add_fixture_executes_when_ruby_available(self) -> None:
        if shutil.which("ruby") is None:
            self.skipTest("ruby toolchain is not installed in this environment")
        fixture = find_fixture_case("add")
        with tempfile.TemporaryDirectory() as td:
            out_rb = Path(td) / "add.rb"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/py2rb.py", str(fixture), "-o", str(out_rb)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            run = subprocess.run(["ruby", str(out_rb)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, msg=f"{run.stdout}\n{run.stderr}")


if __name__ == "__main__":
    unittest.main()
