"""Smoke tests for py2cpp CLI stage selection behavior."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PY2CPP = ROOT / "src" / "py2cpp.py"
STAGE2_REMOVED_ERROR = "error: --east-stage 2 is removed; py2cpp supports only --east-stage 3."
STAGE2_COMPAT_WARNING = "warning: --east-stage 2 is compatibility mode; default is 3."


class Py2CppSmokeTest(unittest.TestCase):
    def test_default_run_has_no_stage2_compat_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "ok.py"
            out_cpp = Path(tmpdir) / "ok.cpp"
            src_py.write_text("print(1)\n", encoding="utf-8")
            proc = subprocess.run(
                ["python3", str(PY2CPP), str(src_py), "-o", str(out_cpp)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            self.assertNotIn(STAGE2_COMPAT_WARNING, proc.stderr)

    def test_stage2_mode_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "ok.py"
            out_cpp = Path(tmpdir) / "ok.cpp"
            src_py.write_text("print(1)\n", encoding="utf-8")
            proc = subprocess.run(
                ["python3", str(PY2CPP), str(src_py), "--east-stage", "2", "-o", str(out_cpp)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn(STAGE2_REMOVED_ERROR, proc.stderr)


if __name__ == "__main__":
    unittest.main()
