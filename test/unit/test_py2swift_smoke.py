"""py2swift (EAST based) smoke tests."""

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

from src.py2swift import load_east, load_swift_profile, transpile_to_swift, transpile_to_swift_native
from src.pytra.compiler.east_parts.core import convert_path


def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


class Py2SwiftSmokeTest(unittest.TestCase):
    def test_load_swift_profile_contains_core_sections(self) -> None:
        profile = load_swift_profile()
        self.assertIn("types", profile)
        self.assertIn("operators", profile)
        self.assertIn("syntax", profile)
        self.assertIn("runtime_calls", profile)

    def test_transpile_add_fixture_uses_native_output(self) -> None:
        fixture = find_fixture_case("add")
        east = load_east(fixture, parser_backend="self_hosted")
        swift = transpile_to_swift(east)
        self.assertIn("@main", swift)
        self.assertIn("Auto-generated Pytra Swift native source from EAST3.", swift)
        self.assertIn("Runtime helpers are provided by py_runtime.swift in the same module.", swift)
        self.assertNotIn("func __pytra_truthy(_ v: Any?) -> Bool {", swift)
        self.assertNotIn("PYTRA_JS_ENTRY:", swift)

    def test_swift_native_emitter_skeleton_handles_module_function_class(self) -> None:
        fixture = find_fixture_case("inheritance")
        east = load_east(fixture, parser_backend="self_hosted")
        swift = transpile_to_swift_native(east)
        self.assertIn("@main", swift)
        self.assertIn("final class Animal", swift)
        self.assertIn("final class Dog: Animal", swift)
        self.assertIn("func _case_main()", swift)

    def test_module_leading_comments_are_emitted(self) -> None:
        sample = ROOT / "sample" / "py" / "01_mandelbrot.py"
        east = load_east(sample, parser_backend="self_hosted")
        swift = transpile_to_swift_native(east)
        self.assertIn("// 01: Sample that outputs the Mandelbrot set as a PNG image.", swift)
        self.assertIn("// Syntax is kept straightforward with future transpilation in mind.", swift)

    def test_load_east_from_json(self) -> None:
        fixture = find_fixture_case("add")
        east = convert_path(fixture)
        with tempfile.TemporaryDirectory() as td:
            east_json = Path(td) / "case.east.json"
            east_json.write_text(json.dumps(east), encoding="utf-8")
            loaded = load_east(east_json)
            swift = transpile_to_swift_native(loaded)
        self.assertIn("@main", swift)

    def test_load_east_defaults_to_stage3_entry_and_returns_east3_shape(self) -> None:
        fixture = find_fixture_case("for_range")
        loaded = load_east(fixture, parser_backend="self_hosted")
        self.assertIsInstance(loaded, dict)
        self.assertEqual(loaded.get("kind"), "Module")
        self.assertEqual(loaded.get("east_stage"), 3)

    def test_cli_smoke_defaults_to_native_without_sidecar(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            out_swift = Path(td) / "if_else.swift"
            out_js = Path(td) / "if_else.js"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/py2swift.py", str(fixture), "-o", str(out_swift)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertTrue(out_swift.exists())
            self.assertFalse(out_js.exists())
            txt = out_swift.read_text(encoding="utf-8")
            self.assertIn("@main", txt)
            self.assertIn("Auto-generated Pytra Swift native source from EAST3.", txt)
            self.assertNotIn("func __pytra_truthy(_ v: Any?) -> Bool {", txt)
            runtime_swift = Path(td) / "py_runtime.swift"
            self.assertTrue(runtime_swift.exists())
            runtime_txt = runtime_swift.read_text(encoding="utf-8")
            self.assertIn("func __pytra_truthy(_ v: Any?) -> Bool {", runtime_txt)
            self.assertFalse((Path(td) / "pytra" / "runtime.js").exists())

    def test_cli_rejects_stage2_compat_mode(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            out_swift = Path(td) / "if_else.swift"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/py2swift.py", str(fixture), "-o", str(out_swift), "--east-stage", "2"],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertIn("--east-stage 2 is no longer supported; use EAST3 (default).", proc.stderr)

    def test_py2swift_does_not_import_src_common(self) -> None:
        src = (ROOT / "src" / "py2swift.py").read_text(encoding="utf-8")
        self.assertNotIn("src.common", src)
        self.assertNotIn("from common.", src)

    def test_swift_runtime_source_path_is_migrated(self) -> None:
        runtime_path = ROOT / "src" / "runtime" / "swift" / "pytra" / "py_runtime.swift"
        legacy_path = ROOT / "src" / "swift_module" / "py_runtime.swift"
        self.assertTrue(runtime_path.exists())
        self.assertFalse(legacy_path.exists())


if __name__ == "__main__":
    unittest.main()
