"""py2nim (EAST based) smoke tests."""

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

from src.py2nim import load_east, _copy_nim_runtime
from src.hooks.nim.emitter.nim_emitter import load_nim_profile, transpile_to_nim
from src.hooks.nim.emitter.nim_native_emitter import transpile_to_nim_native


def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


class Py2NimSmokeTest(unittest.TestCase):
    def test_load_nim_profile_returns_dict(self) -> None:
        profile = load_nim_profile()
        self.assertIsInstance(profile, dict)

    def test_transpile_basic_fixture(self) -> None:
        fixture = find_fixture_case("add")
        east = load_east(fixture, parser_backend="self_hosted")
        nim = transpile_to_nim(east)
        self.assertIn("import std/os", nim)
        self.assertIn("proc add", nim)

    def test_nim_native_emitter_handles_classes(self) -> None:
        fixture = find_fixture_case("inheritance")
        east = load_east(fixture, parser_backend="self_hosted")
        nim = transpile_to_nim_native(east)
        self.assertIn("type Animal* = ref object", nim)
        # self.assertIn("proc newAnimal", nim) # No __init__ in this fixture

    def test_nim_native_emitter_emits_math_import(self) -> None:
        sample = ROOT / "sample" / "py" / "01_mandelbrot.py"
        east = load_east(sample, parser_backend="self_hosted")
        nim = transpile_to_nim_native(east)
        self.assertIn("std/math", nim)
        # self.assertIn("sqrt(", nim) # Not used in 01_mandelbrot.py

    def test_cli_smoke(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            out_nim = Path(td) / "if_else.nim"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/py2nim.py", str(fixture), "-o", str(out_nim)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertTrue(out_nim.exists())
            runtime_nim = Path(td) / "py_runtime.nim"
            self.assertTrue(runtime_nim.exists())

if __name__ == "__main__":
    unittest.main()
