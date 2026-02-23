"""py2cs (EAST based) smoke tests."""

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

from src.py2cs import load_east, load_cs_profile, transpile_to_csharp
from src.pytra.compiler.east_parts.core import convert_path


def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


class Py2CsSmokeTest(unittest.TestCase):
    def test_load_cs_profile_contains_core_sections(self) -> None:
        profile = load_cs_profile()
        self.assertIn("types", profile)
        self.assertIn("operators", profile)
        self.assertIn("syntax", profile)
        self.assertIn("runtime_calls", profile)

    def test_transpile_add_fixture_contains_function_signature(self) -> None:
        fixture = find_fixture_case("add")
        east = load_east(fixture, parser_backend="self_hosted")
        cs = transpile_to_csharp(east)
        self.assertIn("public static long add(long a, long b)", cs)
        self.assertIn("public static class Program", cs)
        self.assertIn("public static void Main(string[] args)", cs)

    def test_load_east_from_json(self) -> None:
        fixture = find_fixture_case("add")
        east = convert_path(fixture)
        with tempfile.TemporaryDirectory() as td:
            east_json = Path(td) / "case.east.json"
            east_json.write_text(json.dumps(east), encoding="utf-8")
            loaded = load_east(east_json)
            cs = transpile_to_csharp(loaded)
        self.assertIn("public static long add(long a, long b)", cs)

    def test_cli_smoke_generates_cs_file(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            out_cs = Path(td) / "if_else.cs"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/py2cs.py", str(fixture), "-o", str(out_cs)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertTrue(out_cs.exists())
            txt = out_cs.read_text(encoding="utf-8")
            self.assertIn("public static long abs_like", txt)

    def test_isinstance_builtin_lowers_to_csharp_is_checks(self) -> None:
        src = """def f(x: object) -> bool:
    return isinstance(x, int) or isinstance(x, str)
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "isinstance_builtin.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            cs = transpile_to_csharp(east)

        self.assertIn("(x is long)", cs)
        self.assertIn("(x is string)", cs)
        self.assertNotIn("isinstance(", cs)

    def test_isinstance_user_class_lowers_to_is_operator(self) -> None:
        src = """class Base:
    pass

class Child(Base):
    pass

def f(x: object) -> bool:
    return isinstance(x, Base)
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "isinstance_class.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            cs = transpile_to_csharp(east)

        self.assertIn("(x is Base)", cs)
        self.assertNotIn("isinstance(", cs)

    def test_py2cs_does_not_import_src_common(self) -> None:
        src = (ROOT / "src" / "py2cs.py").read_text(encoding="utf-8")
        self.assertNotIn("src.common", src)
        self.assertNotIn("from common.", src)


if __name__ == "__main__":
    unittest.main()
