import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYCS = ROOT / "pycs.py"
PY_DIR = ROOT / "test" / "py"
CS_DIR = ROOT / "test" / "cs"


class TranspileGoldenTest(unittest.TestCase):
    def test_cases_match_expected_cs(self) -> None:
        py_cases = sorted(PY_DIR.glob("case*.py"))
        self.assertEqual(len(py_cases), 100, "Expected exactly 100 Python test cases")

        for py_case in py_cases:
            with self.subTest(case=py_case.name):
                expected_cs = CS_DIR / f"{py_case.stem}.cs"
                self.assertTrue(expected_cs.exists(), f"Missing expected C# file: {expected_cs}")

                with tempfile.TemporaryDirectory() as tmpdir:
                    generated_cs = Path(tmpdir) / f"{py_case.stem}.cs"
                    run = subprocess.run(
                        ["python", str(PYCS), str(py_case), str(generated_cs)],
                        cwd=ROOT,
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(run.returncode, 0, msg=run.stderr)

                    actual = generated_cs.read_text(encoding="utf-8")
                    expected = expected_cs.read_text(encoding="utf-8")
                    self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
