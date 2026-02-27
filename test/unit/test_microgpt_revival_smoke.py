from __future__ import annotations

import shutil
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class MicrogptRevivalSmokeTest(unittest.TestCase):
    def test_microgpt_original_regression_guard_baseline(self) -> None:
        if shutil.which("g++") is None:
            self.skipTest("g++ toolchain is not installed in this environment")
        proc = subprocess.run(
            [
                sys.executable,
                "tools/check_microgpt_original_py2cpp_regression.py",
                "--expect-stage",
                "F",
                "--expect-phase",
                "syntax-check",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
        self.assertIn("stage=F", proc.stdout)
        self.assertIn("owner=runtime", proc.stdout)


if __name__ == "__main__":
    unittest.main()
