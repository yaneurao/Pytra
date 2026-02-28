"""py2go (EAST based) smoke tests."""

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

from src.py2go import load_east, load_go_profile, transpile_to_go, transpile_to_go_native
from src.pytra.compiler.east_parts.core import convert_path
from comment_fidelity import assert_no_generated_comments, assert_sample01_module_comments


def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


class Py2GoSmokeTest(unittest.TestCase):
    def test_load_go_profile_contains_core_sections(self) -> None:
        profile = load_go_profile()
        self.assertIn("types", profile)
        self.assertIn("operators", profile)
        self.assertIn("syntax", profile)
        self.assertIn("runtime_calls", profile)

    def test_transpile_add_fixture_uses_native_output(self) -> None:
        fixture = find_fixture_case("add")
        east = load_east(fixture, parser_backend="self_hosted")
        go = transpile_to_go(east)
        self.assertIn("package main", go)
        assert_no_generated_comments(self, go)
        self.assertNotIn("func __pytra_truthy(v any) bool {", go)
        self.assertNotIn('exec.Command("node"', go)

    def test_go_native_emitter_skeleton_handles_module_function_class(self) -> None:
        fixture = find_fixture_case("inheritance")
        east = load_east(fixture, parser_backend="self_hosted")
        go = transpile_to_go_native(east)
        self.assertIn("package main", go)
        self.assertIn("type Animal struct {", go)
        self.assertIn("type Dog struct {", go)
        self.assertIn("func _case_main()", go)

    def test_module_leading_comments_are_emitted(self) -> None:
        sample = ROOT / "sample" / "py" / "01_mandelbrot.py"
        east = load_east(sample, parser_backend="self_hosted")
        go = transpile_to_go_native(east)
        assert_no_generated_comments(self, go)
        assert_sample01_module_comments(self, go, prefix="//")

    def test_load_east_from_json(self) -> None:
        fixture = find_fixture_case("add")
        east = convert_path(fixture)
        with tempfile.TemporaryDirectory() as td:
            east_json = Path(td) / "case.east.json"
            east_json.write_text(json.dumps(east), encoding="utf-8")
            loaded = load_east(east_json)
            go = transpile_to_go_native(loaded)
        self.assertIn("package main", go)

    def test_load_east_defaults_to_stage3_entry_and_returns_east3_shape(self) -> None:
        fixture = find_fixture_case("for_range")
        loaded = load_east(fixture, parser_backend="self_hosted")
        self.assertIsInstance(loaded, dict)
        self.assertEqual(loaded.get("kind"), "Module")
        self.assertEqual(loaded.get("east_stage"), 3)

    def test_cli_smoke_defaults_to_native_without_sidecar(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            out_go = Path(td) / "if_else.go"
            out_js = Path(td) / "if_else.js"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/py2go.py", str(fixture), "-o", str(out_go)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertTrue(out_go.exists())
            self.assertFalse(out_js.exists())
            txt = out_go.read_text(encoding="utf-8")
            self.assertIn("package main", txt)
            self.assertNotIn("Auto-generated Pytra Go native source from EAST3.", txt)
            self.assertNotIn("func __pytra_truthy(v any) bool {", txt)
            runtime_go = Path(td) / "py_runtime.go"
            self.assertTrue(runtime_go.exists())
            runtime_txt = runtime_go.read_text(encoding="utf-8")
            self.assertIn("func __pytra_truthy(v any) bool {", runtime_txt)
            self.assertFalse((Path(td) / "pytra" / "runtime.js").exists())

    def test_cli_rejects_stage2_compat_mode(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            out_go = Path(td) / "if_else.go"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/py2go.py", str(fixture), "-o", str(out_go), "--east-stage", "2"],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertIn("--east-stage 2 is no longer supported; use EAST3 (default).", proc.stderr)

    def test_py2go_does_not_import_src_common(self) -> None:
        src = (ROOT / "src" / "py2go.py").read_text(encoding="utf-8")
        self.assertNotIn("src.common", src)
        self.assertNotIn("from common.", src)

    def test_go_runtime_source_path_is_migrated(self) -> None:
        runtime_path = ROOT / "src" / "runtime" / "go" / "pytra" / "py_runtime.go"
        legacy_path = ROOT / "src" / "go_module" / "py_runtime.go"
        self.assertTrue(runtime_path.exists())
        self.assertFalse(legacy_path.exists())


if __name__ == "__main__":
    unittest.main()
