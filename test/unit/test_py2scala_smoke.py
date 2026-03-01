"""py2scala (EAST based) smoke tests."""

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

from src.py2scala import load_east, load_scala_profile, transpile_to_scala, transpile_to_scala_native
from src.pytra.compiler.east_parts.core import convert_path


def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


class Py2ScalaSmokeTest(unittest.TestCase):
    def test_load_scala_profile_contains_core_sections(self) -> None:
        profile = load_scala_profile()
        self.assertIn("types", profile)
        self.assertIn("operators", profile)
        self.assertIn("syntax", profile)
        self.assertIn("runtime_calls", profile)

    def test_transpile_add_fixture_uses_native_output(self) -> None:
        fixture = find_fixture_case("add")
        east = load_east(fixture, parser_backend="self_hosted")
        scala = transpile_to_scala(east)
        self.assertIn("def main(args: Array[String]): Unit", scala)
        self.assertIn("Auto-generated Pytra Scala 3 native source from EAST3.", scala)

    def test_scala_native_emitter_skeleton_handles_module_function_class(self) -> None:
        fixture = find_fixture_case("inheritance")
        east = load_east(fixture, parser_backend="self_hosted")
        scala = transpile_to_scala_native(east)
        self.assertIn("def main(args: Array[String]): Unit", scala)
        self.assertIn("class Animal()", scala)
        self.assertIn("class Dog() extends Animal()", scala)
        self.assertIn("def _case_main(): Unit =", scala)

    def test_module_leading_comments_are_emitted(self) -> None:
        sample = ROOT / "sample" / "py" / "01_mandelbrot.py"
        east = load_east(sample, parser_backend="self_hosted")
        scala = transpile_to_scala_native(east)
        self.assertIn("// 01: Sample that outputs the Mandelbrot set as a PNG image.", scala)
        self.assertIn("// Syntax is kept straightforward with future transpilation in mind.", scala)

    def test_png_writer_uses_runtime_helper_instead_of_noop(self) -> None:
        sample = ROOT / "sample" / "py" / "01_mandelbrot.py"
        east = load_east(sample, parser_backend="self_hosted")
        scala = transpile_to_scala_native(east)
        self.assertIn("def __pytra_write_rgb_png(path: Any, width: Any, height: Any, pixels: Any): Unit = {", scala)
        self.assertIn("__pytra_write_rgb_png(out_path, width, height, pixels)", scala)
        self.assertNotIn("__pytra_noop(out_path, width, height, pixels)", scala)

    def test_gif_writer_uses_runtime_helper_instead_of_noop(self) -> None:
        sample = ROOT / "sample" / "py" / "06_julia_parameter_sweep.py"
        east = load_east(sample, parser_backend="self_hosted")
        scala = transpile_to_scala_native(east)
        self.assertIn(
            "def __pytra_save_gif(path: Any, width: Any, height: Any, frames: Any, palette: Any, delayCsArg: Any = 4L, loopArg: Any = 0L): Unit = {",
            scala,
        )
        self.assertIn("__pytra_save_gif(out_path, width, height, frames, julia_palette())", scala)
        self.assertNotIn("__pytra_noop(out_path, width, height, frames, julia_palette())", scala)

    def test_load_east_from_json(self) -> None:
        fixture = find_fixture_case("add")
        east = convert_path(fixture)
        with tempfile.TemporaryDirectory() as td:
            east_json = Path(td) / "case.east.json"
            east_json.write_text(json.dumps(east), encoding="utf-8")
            loaded = load_east(east_json)
            scala = transpile_to_scala_native(loaded)
        self.assertIn("def main(args: Array[String]): Unit", scala)

    def test_scala_native_emitter_fail_closed_on_unsupported_stmt_kind(self) -> None:
        east = {
            "kind": "Module",
            "east_stage": 3,
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "_case_main",
                    "arg_order": [],
                    "arg_types": {},
                    "return_type": "None",
                    "body": [{"kind": "UnsupportedStmt"}],
                }
            ],
            "main_guard_body": [],
        }
        with self.assertRaises(RuntimeError) as cm:
            transpile_to_scala_native(east)
        self.assertIn("unsupported stmt kind", str(cm.exception))

    def test_sample_18_scala_output_has_no_unsupported_todo_marker(self) -> None:
        sample = ROOT / "sample" / "py" / "18_mini_language_interpreter.py"
        east = load_east(sample, parser_backend="self_hosted")
        scala = transpile_to_scala_native(east)
        self.assertNotIn("TODO: unsupported", scala)

    def test_load_east_defaults_to_stage3_entry_and_returns_east3_shape(self) -> None:
        fixture = find_fixture_case("for_range")
        loaded = load_east(fixture, parser_backend="self_hosted")
        self.assertIsInstance(loaded, dict)
        self.assertEqual(loaded.get("kind"), "Module")
        self.assertEqual(loaded.get("east_stage"), 3)

    def test_cli_smoke_defaults_to_native_without_sidecar(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            out_scala = Path(td) / "if_else.scala"
            out_js = Path(td) / "if_else.js"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/py2scala.py", str(fixture), "-o", str(out_scala)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertTrue(out_scala.exists())
            self.assertFalse(out_js.exists())
            txt = out_scala.read_text(encoding="utf-8")
            self.assertIn("def main(args: Array[String]): Unit", txt)
            self.assertIn("Auto-generated Pytra Scala 3 native source from EAST3.", txt)
            self.assertFalse((Path(td) / "pytra" / "runtime.js").exists())

    def test_cli_rejects_stage2_compat_mode(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            out_scala = Path(td) / "if_else.scala"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/py2scala.py", str(fixture), "-o", str(out_scala), "--east-stage", "2"],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertIn("--east-stage 2 is no longer supported; use EAST3 (default).", proc.stderr)

    def test_py2scala_does_not_import_src_common(self) -> None:
        src = (ROOT / "src" / "py2scala.py").read_text(encoding="utf-8")
        self.assertNotIn("src.common", src)
        self.assertNotIn("from common.", src)


if __name__ == "__main__":
    unittest.main()
