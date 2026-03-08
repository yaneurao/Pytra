from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from tools.check_selfhost_stage2_sample_parity import build_verify_cmd, default_sample_cases


class CheckSelfhostStage2SampleParityTest(unittest.TestCase):
    def test_default_sample_cases_match_sample_tree(self) -> None:
        expected = [str(path.relative_to(ROOT)) for path in sorted((ROOT / "sample" / "py").glob("*.py"))]
        self.assertEqual(default_sample_cases(), expected)

    def test_build_verify_cmd_uses_stage2_binary_and_skip_build(self) -> None:
        stage2 = ROOT / "selfhost" / "py2cpp_stage2.out"
        cmd = build_verify_cmd(stage2, ["sample/py/01_mandelbrot.py", "sample/py/18_mini_language_interpreter.py"])
        self.assertEqual(
            cmd,
            [
                "python3",
                str(ROOT / "tools" / "verify_selfhost_end_to_end.py"),
                "--skip-build",
                "--selfhost-bin",
                str(stage2),
                "--cases",
                "sample/py/01_mandelbrot.py",
                "sample/py/18_mini_language_interpreter.py",
            ],
        )


if __name__ == "__main__":
    unittest.main()
