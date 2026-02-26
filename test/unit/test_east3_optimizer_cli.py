from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class East3OptimizerCliTest(unittest.TestCase):
    def test_py2rs_accepts_east3_optimizer_options(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            src_py = root / "case.py"
            out_rs = root / "case.rs"
            trace_txt = root / "east3.trace.txt"
            src_py.write_text("x: int = 1\nprint(x)\n", encoding="utf-8")
            cp = subprocess.run(
                [
                    "python3",
                    "src/py2rs.py",
                    str(src_py),
                    "-o",
                    str(out_rs),
                    "--east3-opt-level",
                    "0",
                    "--dump-east3-opt-trace",
                    str(trace_txt),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(cp.returncode, 0, msg=cp.stderr)
            self.assertTrue(out_rs.exists())
            self.assertTrue(trace_txt.exists())
            trace = trace_txt.read_text(encoding="utf-8")
            self.assertIn("opt_level: 0", trace)

    def test_py2cpp_accepts_east3_optimizer_options(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            src_py = root / "case.py"
            out_cpp = root / "case.cpp"
            trace_txt = root / "east3.trace.txt"
            src_py.write_text("x: int = 1\nprint(x)\n", encoding="utf-8")
            cp = subprocess.run(
                [
                    "python3",
                    "src/py2cpp.py",
                    str(src_py),
                    "-o",
                    str(out_cpp),
                    "--east3-opt-level",
                    "2",
                    "--east3-opt-pass",
                    "-NoOpPass",
                    "--dump-east3-opt-trace",
                    str(trace_txt),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(cp.returncode, 0, msg=cp.stderr)
            self.assertTrue(out_cpp.exists())
            self.assertTrue(trace_txt.exists())
            trace = trace_txt.read_text(encoding="utf-8")
            self.assertIn("opt_level: 2", trace)
            self.assertIn("NoOpPass enabled=false", trace)


if __name__ == "__main__":
    unittest.main()

