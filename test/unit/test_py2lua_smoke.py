"""py2lua (EAST based) smoke tests."""

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

from src.py2lua import load_east, load_lua_profile, transpile_to_lua, transpile_to_lua_native
from src.pytra.compiler.east_parts.core import convert_path


def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


class Py2LuaSmokeTest(unittest.TestCase):
    def test_load_lua_profile_contains_core_sections(self) -> None:
        profile = load_lua_profile()
        self.assertIn("types", profile)
        self.assertIn("operators", profile)
        self.assertIn("syntax", profile)
        self.assertIn("runtime_calls", profile)

    def test_transpile_add_fixture_uses_native_output(self) -> None:
        fixture = find_fixture_case("add")
        east = load_east(fixture, parser_backend="self_hosted")
        lua = transpile_to_lua(east)
        self.assertIn("Auto-generated Pytra Lua native source from EAST3.", lua)
        self.assertIn("function add(a, b)", lua)
        self.assertIn("print(add(3, 4))", lua)
        self.assertNotIn("node ", lua)

    def test_transpile_if_else_fixture_contains_lua_if(self) -> None:
        fixture = find_fixture_case("if_else")
        east = load_east(fixture, parser_backend="self_hosted")
        lua = transpile_to_lua_native(east)
        self.assertIn("function abs_like(n)", lua)
        self.assertIn("if (n < 0) then", lua)
        self.assertIn("return (-n)", lua)
        self.assertIn("else", lua)

    def test_transpile_for_range_fixture_contains_static_for(self) -> None:
        fixture = find_fixture_case("for_range")
        east = load_east(fixture, parser_backend="self_hosted")
        lua = transpile_to_lua_native(east)
        self.assertIn("function sum_range_29(n)", lua)
        self.assertIn("local total = 0", lua)
        self.assertIn("for i = 0, (n) - 1, 1 do", lua)
        self.assertIn("total = total + i", lua)

    def test_load_east_from_json(self) -> None:
        fixture = find_fixture_case("add")
        east = convert_path(fixture)
        with tempfile.TemporaryDirectory() as td:
            east_json = Path(td) / "case.east.json"
            east_json.write_text(json.dumps(east), encoding="utf-8")
            loaded = load_east(east_json)
            lua = transpile_to_lua_native(loaded)
        self.assertIn("function add(a, b)", lua)

    def test_load_east_defaults_to_stage3_entry_and_returns_east3_shape(self) -> None:
        fixture = find_fixture_case("for_range")
        loaded = load_east(fixture, parser_backend="self_hosted")
        self.assertIsInstance(loaded, dict)
        self.assertEqual(loaded.get("kind"), "Module")
        self.assertEqual(loaded.get("east_stage"), 3)

    def test_cli_smoke_defaults_to_native_without_sidecar(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            out_lua = Path(td) / "if_else.lua"
            out_js = Path(td) / "if_else.js"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/py2lua.py", str(fixture), "-o", str(out_lua)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertTrue(out_lua.exists())
            self.assertFalse(out_js.exists())
            txt = out_lua.read_text(encoding="utf-8")
            self.assertIn("Auto-generated Pytra Lua native source from EAST3.", txt)

    def test_cli_rejects_stage2_compat_mode(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            out_lua = Path(td) / "if_else.lua"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/py2lua.py", str(fixture), "-o", str(out_lua), "--east-stage", "2"],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertIn("--east-stage 2 is no longer supported; use EAST3 (default).", proc.stderr)

    def test_py2lua_does_not_import_src_common(self) -> None:
        src = (ROOT / "src" / "py2lua.py").read_text(encoding="utf-8")
        self.assertNotIn("src.common", src)
        self.assertNotIn("from common.", src)


if __name__ == "__main__":
    unittest.main()

