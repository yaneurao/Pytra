from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class EastStageBoundaryGuardTest(unittest.TestCase):
    def test_east_stage_boundary_guard_passes(self) -> None:
        cp = subprocess.run(
            ["python3", "tools/check_east_stage_boundary.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(cp.returncode, 0, msg=cp.stdout + "\n" + cp.stderr)


if __name__ == "__main__":
    unittest.main()
