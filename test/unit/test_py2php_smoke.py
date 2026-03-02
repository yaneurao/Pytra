"""py2php (EAST based) smoke tests."""

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

from src.py2php import load_east, load_php_profile, transpile_to_php, transpile_to_php_native


def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


class Py2PhpSmokeTest(unittest.TestCase):
    def test_load_php_profile_contains_core_sections(self) -> None:
        profile = load_php_profile()
        self.assertIn("types", profile)
        self.assertIn("operators", profile)
        self.assertIn("syntax", profile)
        self.assertIn("runtime_calls", profile)

    def test_transpile_add_fixture_uses_native_output(self) -> None:
        fixture = find_fixture_case("add")
        east = load_east(fixture, parser_backend="self_hosted")
        php = transpile_to_php(east)
        self.assertIn("require_once __DIR__ . '/pytra/py_runtime.php';", php)
        self.assertIn("function add($a, $b)", php)
        self.assertIn("__pytra_print(add(3, 4));", php)

    def test_transpile_for_range_fixture_contains_static_for(self) -> None:
        fixture = find_fixture_case("for_range")
        east = load_east(fixture, parser_backend="self_hosted")
        php = transpile_to_php_native(east)
        self.assertIn("function sum_range_29($n)", php)
        self.assertIn("for ($i = 0; $i < $n; $i += 1)", php)
        self.assertIn("$total += $i;", php)

    def test_transpile_downcount_range_fixture_uses_descending_condition(self) -> None:
        fixture = find_fixture_case("range_downcount_len_minus1")
        east = load_east(fixture, parser_backend="self_hosted")
        php = transpile_to_php_native(east)
        self.assertIn("for ($i = (__pytra_len($xs) - 1); $i > (-1); $i -= 1)", php)

    def test_transpile_inheritance_fixture_contains_extends(self) -> None:
        fixture = find_fixture_case("inheritance")
        east = load_east(fixture, parser_backend="self_hosted")
        php = transpile_to_php_native(east)
        self.assertIn("class Animal", php)
        self.assertIn("class Dog extends Animal", php)
        self.assertIn("$this->sound()", php)

    def test_transpile_virtual_dispatch_fixture_lowers_parent_method_call(self) -> None:
        fixture = find_fixture_case("inheritance_virtual_dispatch_multilang")
        east = load_east(fixture, parser_backend="self_hosted")
        php = transpile_to_php_native(east)
        self.assertIn("class LoudDog extends Dog", php)
        self.assertIn("parent::speak()", php)

    def test_transpile_is_instance_fixture_uses_instanceof(self) -> None:
        fixture = find_fixture_case("is_instance")
        east = load_east(fixture, parser_backend="self_hosted")
        php = transpile_to_php_native(east)
        self.assertIn("($cat instanceof Dog)", php)
        self.assertIn("($dog instanceof Animal)", php)

    def test_load_east_from_json(self) -> None:
        fixture = find_fixture_case("add")
        east = load_east(fixture, parser_backend="self_hosted")
        with tempfile.TemporaryDirectory() as td:
            east_json = Path(td) / "case.east.json"
            east_json.write_text(json.dumps(east), encoding="utf-8")
            loaded = load_east(east_json)
            php = transpile_to_php_native(loaded)
        self.assertIn("function add($a, $b)", php)

    def test_load_east_defaults_to_stage3_entry_and_returns_east3_shape(self) -> None:
        fixture = find_fixture_case("for_range")
        loaded = load_east(fixture, parser_backend="self_hosted")
        self.assertIsInstance(loaded, dict)
        self.assertEqual(loaded.get("kind"), "Module")
        self.assertEqual(loaded.get("east_stage"), 3)

    def test_cli_smoke_defaults_to_native_and_copies_runtime_tree(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            out_php = Path(td) / "if_else.php"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/py2php.py", str(fixture), "-o", str(out_php)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertTrue(out_php.exists())
            txt = out_php.read_text(encoding="utf-8")
            self.assertIn("require_once __DIR__ . '/pytra/py_runtime.php';", txt)
            self.assertTrue((Path(td) / "pytra" / "py_runtime.php").exists())
            self.assertTrue((Path(td) / "pytra" / "runtime" / "png.php").exists())
            self.assertTrue((Path(td) / "pytra" / "runtime" / "gif.php").exists())
            self.assertTrue((Path(td) / "pytra" / "std" / "time.php").exists())

    def test_cli_rejects_stage2_compat_mode(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            out_php = Path(td) / "if_else.php"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/py2php.py", str(fixture), "-o", str(out_php), "--east-stage", "2"],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertIn("--east-stage 2 is no longer supported; use EAST3 (default).", proc.stderr)


if __name__ == "__main__":
    unittest.main()
