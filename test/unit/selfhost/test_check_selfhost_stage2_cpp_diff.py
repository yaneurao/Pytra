from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
MODULE_PATH = ROOT / "tools" / "check_selfhost_stage2_cpp_diff.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("check_selfhost_stage2_cpp_diff", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to load check_selfhost_stage2_cpp_diff module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CheckSelfhostStage2CppDiffTest(unittest.TestCase):
    def test_build_check_diff_cmd_uses_stage2_binary_and_direct_driver(self) -> None:
        mod = _load_module()
        stage2 = ROOT / "selfhost" / "py2cpp_stage2.out"
        cmd = mod.build_check_diff_cmd(
            stage2,
            cases=["sample/py/01_mandelbrot.py", "sample/py/17_monte_carlo_pi.py"],
            show_diff=True,
            mode="allow-not-implemented",
        )
        self.assertEqual(
            cmd,
            [
                "python3",
                str(mod.CHECK_DIFF),
                "--selfhost-bin",
                str(stage2),
                "--selfhost-driver",
                "direct",
                "--mode",
                "allow-not-implemented",
                "--show-diff",
                "--cases",
                "sample/py/01_mandelbrot.py",
                "sample/py/17_monte_carlo_pi.py",
            ],
        )

    def test_build_check_diff_cmd_omits_optional_flags_when_unused(self) -> None:
        mod = _load_module()
        stage2 = ROOT / "selfhost" / "py2cpp_stage2.out"
        cmd = mod.build_check_diff_cmd(stage2, cases=[], show_diff=False, mode="strict")
        self.assertEqual(
            cmd,
            [
                "python3",
                str(mod.CHECK_DIFF),
                "--selfhost-bin",
                str(stage2),
                "--selfhost-driver",
                "direct",
                "--mode",
                "strict",
            ],
        )


if __name__ == "__main__":
    unittest.main()
