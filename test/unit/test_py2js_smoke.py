"""py2js (EAST based) smoke tests."""

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

from src.py2js import load_east, load_js_profile, transpile_to_js
from src.pytra.compiler.east_parts.core import convert_path


def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


class Py2JsSmokeTest(unittest.TestCase):
    def test_load_js_profile_contains_core_sections(self) -> None:
        profile = load_js_profile()
        self.assertIn("types", profile)
        self.assertIn("operators", profile)
        self.assertIn("syntax", profile)
        self.assertIn("runtime_calls", profile)

    def test_transpile_add_fixture_contains_function_signature(self) -> None:
        fixture = find_fixture_case("add")
        east = load_east(fixture, parser_backend="self_hosted")
        js = transpile_to_js(east)
        self.assertIn("function add(a, b) {", js)
        self.assertIn("console.log(", js)

    def test_load_east_from_json(self) -> None:
        fixture = find_fixture_case("add")
        east = convert_path(fixture)
        with tempfile.TemporaryDirectory() as td:
            east_json = Path(td) / "case.east.json"
            east_json.write_text(json.dumps(east), encoding="utf-8")
            loaded = load_east(east_json)
            js = transpile_to_js(loaded)
        self.assertIn("function add(a, b)", js)

    def test_browser_import_symbols_are_treated_as_external(self) -> None:
        fixture = find_fixture_case("browser_external_symbols")
        east = load_east(fixture, parser_backend="self_hosted")
        js = transpile_to_js(east)
        self.assertIn("document.title", js)
        self.assertNotIn("import { document", js)
        self.assertNotIn("browser/widgets/dialog", js)

    def test_cli_smoke_generates_js_file(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            out_js = Path(td) / "if_else.js"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/py2js.py", str(fixture), "-o", str(out_js)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertTrue(out_js.exists())
            txt = out_js.read_text(encoding="utf-8")
            self.assertIn("function abs_like", txt)

    def test_py2js_does_not_import_src_common(self) -> None:
        src = (ROOT / "src" / "py2js.py").read_text(encoding="utf-8")
        self.assertNotIn("src.common", src)
        self.assertNotIn("from common.", src)


if __name__ == "__main__":
    unittest.main()

