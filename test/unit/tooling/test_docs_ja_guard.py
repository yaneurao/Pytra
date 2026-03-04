from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())


class DocsJaGuardTest(unittest.TestCase):
    def test_docs_ja_guard_passes(self) -> None:
        cp = subprocess.run(
            ["python3", "tools/check_docs_ja_guard.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(cp.returncode, 0, msg=cp.stdout + "\n" + cp.stderr)


if __name__ == "__main__":
    unittest.main()
