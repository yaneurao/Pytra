from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class ImageRuntimeParityTest(unittest.TestCase):
    def test_python_canonical_and_cpp_runtime_match(self) -> None:
        cp = subprocess.run(
            ["python3", "tools/verify_image_runtime_parity.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(cp.returncode, 0, msg=cp.stderr)
        lines = [ln.strip() for ln in cp.stdout.replace("\r\n", "\n").split("\n") if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")


if __name__ == "__main__":
    unittest.main()
