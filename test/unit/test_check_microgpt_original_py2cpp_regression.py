from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = ROOT / "tools" / "check_microgpt_original_py2cpp_regression.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("check_microgpt_original_py2cpp_regression", TOOL_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to load check_microgpt_original_py2cpp_regression module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CheckMicrogptOriginalRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool = _load_tool_module()

    def test_cli_defaults_are_stage_f_and_phase_syntax_check(self) -> None:
        parser = self.tool._build_parser()
        args = parser.parse_args([])
        self.assertEqual(args.expect_stage, "F")
        self.assertEqual(args.expect_phase, "syntax-check")

    def test_main_accepts_default_baseline_on_stage_f_compile_failure(self) -> None:
        def fake_run(cmd: list[str]) -> tuple[int, str]:
            if len(cmd) > 0 and cmd[0] == "g++":
                return 1, "work/out/microgpt_revival.cpp: In member function ‘rc<Value> Value::log()’:"
            return 0, ""

        with patch.object(self.tool, "_run", side_effect=fake_run), patch.object(
            sys, "argv", ["check_microgpt_original_py2cpp_regression.py"]
        ):
            code = self.tool.main()
        self.assertEqual(code, 0)

    def test_main_detects_phase_mismatch_when_failure_is_transpile(self) -> None:
        def fake_run(cmd: list[str]) -> tuple[int, str]:
            _ = cmd
            return 1, "unsupported_syntax: self_hosted parser requires type annotation for parameter: data at 33:0"

        with patch.object(self.tool, "_run", side_effect=fake_run), patch.object(
            sys,
            "argv",
            [
                "check_microgpt_original_py2cpp_regression.py",
                "--expect-stage",
                "any-known",
            ],
        ):
            code = self.tool.main()
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
