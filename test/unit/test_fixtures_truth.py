"""Run all fixture cases and require final stdout line to be True."""

from __future__ import annotations

import os
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = ROOT / "test" / "fixtures"


class FixturesTruthTest(unittest.TestCase):
    def test_all_cases_print_true(self) -> None:
        cases = sorted(FIXTURE_ROOT.rglob("case*.py"))
        self.assertGreater(len(cases), 0, "No fixture case files found")

        env = dict(os.environ)
        env["PYTHONPATH"] = str((ROOT / "src").resolve())

        for case in cases:
            with self.subTest(case=str(case.relative_to(ROOT))):
                cp = subprocess.run(
                    ["python3", str(case)],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    env=env,
                )
                self.assertEqual(cp.returncode, 0, msg=cp.stderr)
                lines = [ln.strip() for ln in cp.stdout.replace("\r\n", "\n").split("\n") if ln.strip() != ""]
                last = lines[-1] if lines else ""
                self.assertEqual(last, "True", msg=f"{case}: stdout={cp.stdout!r}")


if __name__ == "__main__":
    unittest.main()
