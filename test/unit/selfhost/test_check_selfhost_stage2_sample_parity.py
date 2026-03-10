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
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))


MODULE_PATH = ROOT / "tools" / "check_selfhost_stage2_sample_parity.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("check_selfhost_stage2_sample_parity", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to load check_selfhost_stage2_sample_parity module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CheckSelfhostStage2SampleParityTest(unittest.TestCase):
    def test_stage2_summary_row_maps_missing_binary_to_regression(self) -> None:
        mod = _load_module()
        row = mod.build_stage2_summary_row("stage2_binary", "missing_binary", "/tmp/missing.out")
        self.assertEqual(row.top_level_category, "regression")
        self.assertEqual(row.detail_category, "missing_output")

    def test_default_sample_cases_match_sample_tree(self) -> None:
        mod = _load_module()
        expected = [str(path.relative_to(ROOT)) for path in sorted((ROOT / "sample" / "py").glob("*.py"))]
        self.assertEqual(mod.default_sample_cases(), expected)

    def test_build_verify_cmd_uses_stage2_binary_and_skip_build(self) -> None:
        mod = _load_module()
        stage2 = ROOT / "selfhost" / "py2cpp_stage2.out"
        cmd = mod.build_verify_cmd(stage2, ["sample/py/01_mandelbrot.py", "sample/py/18_mini_language_interpreter.py"])
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

    def test_main_returns_2_when_stage2_binary_is_missing(self) -> None:
        mod = _load_module()
        with tempfile.TemporaryDirectory() as td:
            mod.STAGE2_BIN = Path(td) / "missing-stage2.out"
            with patch.object(
                sys,
                "argv",
                ["check_selfhost_stage2_sample_parity.py", "--skip-build"],
            ):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    self.assertEqual(mod.main(), 2)
        self.assertIn("[stage2 summary]", buf.getvalue())
        self.assertIn("detail=missing_output", buf.getvalue())

    def test_main_runs_build_then_verify_for_existing_stage2_binary(self) -> None:
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
                    "check_selfhost_stage2_sample_parity.py",
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
                mod.build_verify_cmd(stage2_bin, ["sample/py/01_mandelbrot.py"]),
            )
            self.assertIn("[stage2 summary]", buf.getvalue())
            self.assertIn("detail=pass", buf.getvalue())

    def test_main_marks_verify_failure_as_direct_parity_fail(self) -> None:
        mod = _load_module()
        with tempfile.TemporaryDirectory() as td:
            stage2_bin = Path(td) / "py2cpp_stage2.out"
            stage2_bin.write_text("", encoding="utf-8")
            mod.STAGE2_BIN = stage2_bin

            def _fake_run(cmd: list[str]) -> int:
                if cmd == ["python3", str(mod.BUILD_STAGE2)]:
                    return 0
                return 1

            with patch.object(mod, "_run", side_effect=_fake_run), patch.object(
                sys,
                "argv",
                [
                    "check_selfhost_stage2_sample_parity.py",
                    "--cases",
                    "sample/py/01_mandelbrot.py",
                ],
            ):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    self.assertEqual(mod.main(), 1)

            self.assertIn("[stage2 summary]", buf.getvalue())
            self.assertIn("detail=direct_parity_fail", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
