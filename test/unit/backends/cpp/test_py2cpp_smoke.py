"""Smoke tests for py2cpp CLI stage selection behavior."""

# Language-specific smoke suite.
# Shared py2x target-parameterized checks live in test_py2x_smoke_common.py.

from __future__ import annotations

import ast
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
PY2X = ROOT / "src" / "py2x.py"
CPP_CLI = ROOT / "src" / "backends" / "cpp" / "cli.py"
STAGE2_REMOVED_ERROR = "error: --east-stage 2 is removed; py2cpp supports only --east-stage 3."
STAGE2_COMPAT_WARNING = "warning: --east-stage 2 is compatibility mode; default is 3."
if str(ROOT / "test" / "unit") not in sys.path:
    sys.path.insert(0, str(ROOT / "test" / "unit"))

from comment_fidelity import assert_no_generated_comments, assert_sample01_module_comments


class Py2CppSmokeTest(unittest.TestCase):
    def test_cpp_emitter_not_implemented_in_py2cpp(self) -> None:
        text = CPP_CLI.read_text(encoding="utf-8")
        ast_root = ast.parse(text)

        top_level_classes = {
            node.name
            for node in ast_root.body
            if isinstance(node, ast.ClassDef)
        }
        self.assertNotIn("CppEmitter", top_level_classes)

        has_emitter_import = False
        for node in ast_root.body:
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.module != "toolchain.emit.cpp.emitter":
                continue
            has_emitter_import = any(alias.name == "CppEmitter" for alias in node.names)
            if has_emitter_import:
                break
        self.assertTrue(has_emitter_import)

    def test_stage2_mode_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "ok.py"
            out_cpp = Path(tmpdir) / "ok.cpp"
            src_py.write_text("print(1)\n", encoding="utf-8")
            proc = subprocess.run(
                ["python3", str(PY2X), str(src_py), "--target", "cpp", "--east-stage", "2", "-o", str(out_cpp)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn(STAGE2_REMOVED_ERROR, proc.stderr)

    def test_comment_fidelity_preserves_source_comments(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sample = ROOT / "sample" / "py" / "01_mandelbrot.py"
            out_cpp = Path(tmpdir) / "sample01.cpp"
            proc = subprocess.run(
                ["python3", str(PY2X), str(sample), "--target", "cpp", "-o", str(out_cpp)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            cpp = out_cpp.read_text(encoding="utf-8")
        assert_no_generated_comments(self, cpp)
        assert_sample01_module_comments(self, cpp, prefix="//")


if __name__ == "__main__":
    unittest.main()
