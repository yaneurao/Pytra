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

    def test_transpile_add_fixture_contains_preview_and_main(self) -> None:
        fixture = find_fixture_case("add")
        east = load_east(fixture, parser_backend="self_hosted")
        java = transpile_to_java(east)
        self.assertIn("public final class Main", java)
        self.assertIn("Java プレビュー出力", java)
        self.assertIn("add(", java)

    def test_load_east_from_json(self) -> None:
        fixture = find_fixture_case("add")
        east = convert_path(fixture)
        with tempfile.TemporaryDirectory() as td:
            east_json = Path(td) / "case.east.json"
            east_json.write_text(json.dumps(east), encoding="utf-8")
            loaded = load_east(east_json)
            java = transpile_to_java(loaded)
        self.assertIn("public final class Main", java)

    def test_load_east_defaults_to_stage3_entry_and_returns_legacy_shape(self) -> None:
        fixture = find_fixture_case("for_range")
        loaded = load_east(fixture, parser_backend="self_hosted")
        self.assertIsInstance(loaded, dict)
        self.assertEqual(loaded.get("kind"), "Module")
        self.assertEqual(loaded.get("east_stage"), 2)

    def test_cli_smoke_generates_java_file(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            out_java = Path(td) / "if_else.java"
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
            txt = out_java.read_text(encoding="utf-8")
            self.assertIn("public final class Main", txt)

    def test_cli_warns_when_stage2_compat_mode_is_selected(self) -> None:
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
            self.assertEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertIn("warning: --east-stage 2 is compatibility mode; default is 3.", proc.stderr)

    def test_py2java_does_not_import_src_common(self) -> None:
        src = (ROOT / "src" / "py2java.py").read_text(encoding="utf-8")
        self.assertNotIn("src.common", src)
        self.assertNotIn("from common.", src)


if __name__ == "__main__":
    unittest.main()
