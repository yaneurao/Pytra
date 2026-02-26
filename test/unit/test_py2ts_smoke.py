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
from hooks.ts.emitter import ts_emitter as ts_emitter_mod


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

    def test_load_east_defaults_to_stage3_entry_and_returns_legacy_shape(self) -> None:
        fixture = find_fixture_case("for_range")
        loaded = load_east(fixture, parser_backend="self_hosted")
        self.assertIsInstance(loaded, dict)
        self.assertEqual(loaded.get("kind"), "Module")
        self.assertEqual(loaded.get("east_stage"), 2)

    def test_stdlib_imports_use_pytra_runtime_shim_paths(self) -> None:
        fixture = find_fixture_case("import_time_from")
        east = load_east(fixture, parser_backend="self_hosted")
        ts = transpile_to_typescript(east)
        self.assertIn('from "./pytra/std/time.js"', ts)

    def test_cli_generates_pytra_runtime_shims(self) -> None:
        fixture = find_fixture_case("import_time_from")
        with tempfile.TemporaryDirectory() as td:
            out_ts = Path(td) / "import_time_from.ts"
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
            self.assertTrue((Path(td) / "pytra" / "std" / "time.js").exists())
            self.assertTrue((Path(td) / "pytra" / "runtime.js").exists())

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

    def test_cli_rejects_stage2_compat_mode(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            out_ts = Path(td) / "if_else.ts"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/py2ts.py", str(fixture), "-o", str(out_ts), "--east-stage", "2"],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertIn("--east-stage 2 is no longer supported; use EAST3 (default).", proc.stderr)

    def test_py2ts_does_not_import_src_common(self) -> None:
        src = (ROOT / "src" / "py2ts.py").read_text(encoding="utf-8")
        self.assertNotIn("src.common", src)
        self.assertNotIn("from common.", src)

    def test_ts_preview_uses_js_transpile_pipeline(self) -> None:
        original = ts_emitter_mod.transpile_to_js
        try:
            ts_emitter_mod.transpile_to_js = (
                lambda _east_doc: "const __ts_js_pipeline_marker = 1;\n"
            )
            ts = ts_emitter_mod.transpile_to_typescript(
                {"kind": "Module", "body": [], "meta": {}}
            )
        finally:
            ts_emitter_mod.transpile_to_js = original
        self.assertIn("const __ts_js_pipeline_marker = 1;", ts)

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

    def test_ts_preview_lowers_isinstance_tuple_to_or_checks(self) -> None:
        src = """class Base:
    def __init__(self):
        pass

def f(x: object) -> bool:
    return isinstance(x, (int, Base, dict, object))
"""
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "ts_isinstance_tuple_type_id.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, parser_backend="self_hosted")
            ts = transpile_to_typescript(east)

        self.assertIn("pyIsInstance(x, PY_TYPE_NUMBER)", ts)
        self.assertIn("pyIsInstance(x, Base.PYTRA_TYPE_ID)", ts)
        self.assertIn("pyIsInstance(x, PY_TYPE_MAP)", ts)
        self.assertIn("pyIsInstance(x, PY_TYPE_OBJECT)", ts)
        self.assertNotIn("isinstance(", ts)

    def test_ts_preview_lowers_isinstance_set_to_type_id_check(self) -> None:
        src = """def f(x: object) -> bool:
    return isinstance(x, set)
"""
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "ts_isinstance_set_type_id.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, parser_backend="self_hosted")
            ts = transpile_to_typescript(east)

        self.assertIn("pyIsInstance(x, PY_TYPE_SET)", ts)
        self.assertNotIn("isinstance(", ts)


if __name__ == "__main__":
    unittest.main()
