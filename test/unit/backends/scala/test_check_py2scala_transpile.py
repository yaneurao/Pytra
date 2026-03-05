"""Unit tests for tools/check_py2x_transpile.py Scala profile behavior."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
SCRIPT = ROOT / "tools" / "check_py2x_transpile.py"
PROFILE_PATH = ROOT / "tools" / "check_py2x_profiles.json"

SPEC = importlib.util.spec_from_file_location("check_py2x_transpile", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("failed to load check_py2x_transpile.py")
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)


class CheckPy2XScalaProfileTest(unittest.TestCase):
    def test_scala_expected_failures_drop_stale_untyped_param(self) -> None:
        profiles = MOD._load_profiles(PROFILE_PATH)
        scala = profiles["scala"]
        expected = MOD._expected_map(scala)
        self.assertNotIn("test/fixtures/signature/ng_untyped_param.py", expected)
        self.assertIn("test/fixtures/signature/ng_varargs.py", expected)

    def test_extract_user_error_category_parses_marker(self) -> None:
        text = (
            "RuntimeError: __PYTRA_USER_ERROR__|unsupported_by_design|This syntax is unsupported by language design.\n"
            "unsupported_syntax: object receiver attribute/method access is forbidden by language constraints\n"
        )
        self.assertEqual(MOD._extract_user_error_category(text), "unsupported_by_design")

    def test_scala_sample01_quality_hook_detects_boundary_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "out.scala"
            out.write_text("boundary: // should not appear", encoding="utf-8")
            msg = MOD._run_quality_hook("scala_sample01", "sample/py/01_mandelbrot.py", out)
            self.assertIn("boundary labels reintroduced", msg)

    def test_stage2_contract_preflight_skip_returns_ok(self) -> None:
        profiles = MOD._load_profiles(PROFILE_PATH)
        scala = profiles["scala"]
        ok, msg = MOD._run_east3_contract_preflight(scala, skip=True)
        self.assertTrue(ok)
        self.assertEqual(msg, "")


if __name__ == "__main__":
    unittest.main()
