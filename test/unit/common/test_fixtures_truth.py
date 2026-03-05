"""Run all fixture cases and require final stdout line to be True."""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
FIXTURE_ROOT = ROOT / "test" / "fixtures"


class FixturesTruthTest(unittest.TestCase):
    @staticmethod
    def _cleanup_possible_artifacts(case_stem: str) -> None:
        for ext in ("png", "gif"):
            for path in (ROOT / f"{case_stem}.{ext}", ROOT / "out" / f"{case_stem}.{ext}"):
                if path.exists() and path.is_file():
                    path.unlink()

    def test_all_cases_print_true(self) -> None:
        cases = sorted(
            p for p in FIXTURE_ROOT.rglob("*.py")
            if p.parent.name != "signature"
        )
        self.assertGreater(len(cases), 0, "No fixture case files found")

        env = dict(os.environ)
        env["PYTHONPATH"] = str((ROOT / "src").resolve())

        for case in cases:
            with self.subTest(case=str(case.relative_to(ROOT))):
                case_stem = case.stem
                self._cleanup_possible_artifacts(case_stem)
                with tempfile.TemporaryDirectory() as tmpdir:
                    work = Path(tmpdir)
                    (work / "out").mkdir(parents=True, exist_ok=True)
                    try:
                        cp = subprocess.run(
                            ["python3", str(case)],
                            cwd=work,
                            capture_output=True,
                            text=True,
                            env=env,
                        )
                        self.assertEqual(cp.returncode, 0, msg=cp.stderr)
                        lines = [ln.strip() for ln in cp.stdout.replace("\r\n", "\n").split("\n") if ln.strip() != ""]
                        last = lines[-1] if lines else ""
                        self.assertEqual(last, "True", msg=f"{case}: stdout={cp.stdout!r}")
                    finally:
                        self._cleanup_possible_artifacts(case_stem)


if __name__ == "__main__":
    unittest.main()
