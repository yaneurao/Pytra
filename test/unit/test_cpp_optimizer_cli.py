from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class CppOptimizerCliTest(unittest.TestCase):
    def test_py2cpp_accepts_cpp_optimizer_options_and_writes_dumps(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            src_py = root / "case.py"
            out_cpp = root / "case.cpp"
            before_json = root / "cpp.before.json"
            after_json = root / "cpp.after.json"
            trace_txt = root / "cpp.trace.txt"
            src_py.write_text("x: int = 1\nprint(x)\n", encoding="utf-8")
            cp = subprocess.run(
                [
                    "python3",
                    "src/py2cpp.py",
                    str(src_py),
                    "-o",
                    str(out_cpp),
                    "--cpp-opt-level",
                    "2",
                    "--cpp-opt-pass",
                    "-CppNoOpPass",
                    "--dump-cpp-ir-before-opt",
                    str(before_json),
                    "--dump-cpp-ir-after-opt",
                    str(after_json),
                    "--dump-cpp-opt-trace",
                    str(trace_txt),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(cp.returncode, 0, msg=cp.stderr)
            self.assertTrue(out_cpp.exists())
            self.assertTrue(before_json.exists())
            self.assertTrue(after_json.exists())
            self.assertTrue(trace_txt.exists())
            before_obj = json.loads(before_json.read_text(encoding="utf-8"))
            after_obj = json.loads(after_json.read_text(encoding="utf-8"))
            self.assertEqual(before_obj.get("kind"), "Module")
            self.assertEqual(after_obj.get("kind"), "Module")
            trace = trace_txt.read_text(encoding="utf-8")
            self.assertIn("cpp_optimizer_trace:", trace)
            self.assertIn("opt_level: 2", trace)
            self.assertIn("CppNoOpPass enabled=false", trace)

    def test_py2cpp_rejects_invalid_cpp_opt_level(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            src_py = root / "case.py"
            out_cpp = root / "case.cpp"
            src_py.write_text("print(1)\n", encoding="utf-8")
            cp = subprocess.run(
                [
                    "python3",
                    "src/py2cpp.py",
                    str(src_py),
                    "-o",
                    str(out_cpp),
                    "--cpp-opt-level",
                    "9",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(cp.returncode, 0)
            self.assertIn("invalid --cpp-opt-level", cp.stderr)


if __name__ == "__main__":
    unittest.main()
