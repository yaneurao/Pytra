import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYCS = ROOT / "pycs.py"
SELF_SRC = ROOT / "src" / "pycs_transpiler.py"


class SelfTranspileTest(unittest.TestCase):
    def test_can_transpile_transpiler_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_cs = Path(tmpdir) / "self_pycs_transpiler.cs"
            run = subprocess.run(
                ["python", str(PYCS), str(SELF_SRC), str(out_cs)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(run.returncode, 0, msg=run.stderr)
            self.assertTrue(out_cs.exists())
            self.assertGreater(out_cs.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
