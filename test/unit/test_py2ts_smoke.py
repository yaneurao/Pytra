"""py2ts (EAST based) smoke tests."""

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

from src.py2ts import load_east, load_ts_profile, transpile_to_typescript
from src.pytra.compiler.east_parts.core import convert_path


def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


class Py2TsSmokeTest(unittest.TestCase):
    def test_load_ts_profile_contains_core_sections(self) -> None:
        profile = load_ts_profile()
        self.assertIn("types", profile)
        self.assertIn("operators", profile)
        self.assertIn("syntax", profile)
        self.assertIn("runtime_calls", profile)

    def test_transpile_add_fixture_contains_function_signature(self) -> None:
        fixture = find_fixture_case("add")
        east = load_east(fixture, parser_backend="self_hosted")
        ts = transpile_to_typescript(east)
        self.assertIn("TypeScript プレビュー出力", ts)
        self.assertIn("function add(a, b) {", ts)

    def test_load_east_from_json(self) -> None:
        fixture = find_fixture_case("add")
        east = convert_path(fixture)
        with tempfile.TemporaryDirectory() as td:
            east_json = Path(td) / "case.east.json"
            east_json.write_text(json.dumps(east), encoding="utf-8")
            loaded = load_east(east_json)
            ts = transpile_to_typescript(loaded)
        self.assertIn("function add(a, b)", ts)

    def test_cli_smoke_generates_ts_file(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            out_ts = Path(td) / "if_else.ts"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/py2ts.py", str(fixture), "-o", str(out_ts)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertTrue(out_ts.exists())
            txt = out_ts.read_text(encoding="utf-8")
            self.assertIn("function abs_like", txt)

    def test_py2ts_does_not_import_src_common(self) -> None:
        src = (ROOT / "src" / "py2ts.py").read_text(encoding="utf-8")
        self.assertNotIn("src.common", src)
        self.assertNotIn("from common.", src)

    def test_ts_preview_keeps_isinstance_type_id_lowering(self) -> None:
        src = """class Base:
    def __init__(self):
        pass

def f(x: object) -> bool:
    return isinstance(x, int) or isinstance(x, Base)
"""
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "ts_isinstance_type_id.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, parser_backend="self_hosted")
            ts = transpile_to_typescript(east)

        self.assertIn("pyIsInstance(x, PY_TYPE_NUMBER)", ts)
        self.assertIn("pyIsInstance(x, Base.PYTRA_TYPE_ID)", ts)
        self.assertIn("static PYTRA_TYPE_ID = pyRegisterClassType([PY_TYPE_OBJECT]);", ts)


if __name__ == "__main__":
    unittest.main()
