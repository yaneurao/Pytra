from __future__ import annotations

import importlib.util
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


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

    def test_main_returns_build_failure_before_diff(self) -> None:
        mod = _load_module()
        calls: list[list[str]] = []

        def _fake_run(cmd: list[str]) -> int:
            calls.append(cmd)
            return 7

        with patch.object(mod, "_run", side_effect=_fake_run), patch.object(
            sys,
            "argv",
            ["check_selfhost_stage2_cpp_diff.py"],
        ):
            self.assertEqual(mod.main(), 7)

        self.assertEqual(calls, [["python3", str(mod.BUILD_STAGE2)]])

    def test_main_returns_2_when_stage2_binary_is_missing(self) -> None:
        mod = _load_module()
        with tempfile.TemporaryDirectory() as td:
            mod.STAGE2_BIN = Path(td) / "missing-stage2.out"
            with patch.object(
                sys,
                "argv",
                ["check_selfhost_stage2_cpp_diff.py", "--skip-build"],
            ):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    self.assertEqual(mod.main(), 2)
        self.assertIn("[stage2 summary]", buf.getvalue())
        self.assertIn("detail=missing_output", buf.getvalue())

    def test_main_runs_build_then_diff_for_existing_stage2_binary(self) -> None:
        mod = _load_module()
        with tempfile.TemporaryDirectory() as td:
            stage2_bin = Path(td) / "py2cpp_stage2.out"
            stage2_bin.write_text("", encoding="utf-8")
            mod.STAGE2_BIN = stage2_bin
            calls: list[list[str]] = []

            def _fake_run(cmd: list[str]) -> int:
                calls.append(cmd)
                return 0

            with patch.object(mod, "_run", side_effect=_fake_run), patch.object(
                sys,
                "argv",
                [
                    "check_selfhost_stage2_cpp_diff.py",
                    "--show-diff",
                    "--mode",
                    "strict",
                    "--cases",
                    "sample/py/01_mandelbrot.py",
                ],
            ):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    self.assertEqual(mod.main(), 0)

            self.assertEqual(calls[0], ["python3", str(mod.BUILD_STAGE2)])
            self.assertEqual(
                calls[1],
                mod.build_check_diff_cmd(
                    stage2_bin,
                    cases=["sample/py/01_mandelbrot.py"],
                    show_diff=True,
                    mode="strict",
                ),
            )
            self.assertIn("[stage2 summary]", buf.getvalue())
            self.assertIn("detail=pass", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
