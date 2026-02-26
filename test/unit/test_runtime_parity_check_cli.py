from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
RUNTIME_PARITY_CHECK = ROOT / "tools" / "runtime_parity_check.py"


def _load_runtime_parity_module():
    spec = importlib.util.spec_from_file_location("runtime_parity_check", RUNTIME_PARITY_CHECK)
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to load runtime_parity_check module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RuntimeParityCheckCliTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rpc = _load_runtime_parity_module()

    def test_collect_sample_case_stems_is_fixed_to_18_samples(self) -> None:
        stems = self.rpc.collect_sample_case_stems()
        self.assertEqual(len(stems), 18)
        self.assertEqual(stems[0], "01_mandelbrot")
        self.assertEqual(stems[-1], "18_mini_language_interpreter")
        self.assertNotIn("__init__", stems)

    def test_resolve_case_stems_defaults(self) -> None:
        stems_fixture, err_fixture = self.rpc.resolve_case_stems([], "fixture", False)
        self.assertEqual(err_fixture, "")
        self.assertEqual(stems_fixture, ["math_extended", "pathlib_extended"])

        stems_sample, err_sample = self.rpc.resolve_case_stems([], "sample", False)
        self.assertEqual(err_sample, "")
        self.assertEqual(len(stems_sample), 18)

    def test_resolve_case_stems_all_samples_validation(self) -> None:
        stems_root_err, err_root = self.rpc.resolve_case_stems([], "fixture", True)
        self.assertEqual(stems_root_err, [])
        self.assertIn("--all-samples requires --case-root sample", err_root)

        stems_arg_err, err_arg = self.rpc.resolve_case_stems(["01_mandelbrot"], "sample", True)
        self.assertEqual(stems_arg_err, [])
        self.assertIn("--all-samples cannot be combined", err_arg)

    def test_check_case_records_toolchain_missing_category(self) -> None:
        records: list = []
        target = self.rpc.Target(name="cpp", transpile_cmd="noop", run_cmd="noop", needs=("g++",))
        py_success = subprocess.CompletedProcess(args="python fake.py", returncode=0, stdout="True\n", stderr="")

        with patch.object(self.rpc, "find_case_path", return_value=ROOT / "sample" / "py" / "01_mandelbrot.py"), patch.object(
            self.rpc, "run_shell", return_value=py_success
        ), patch.object(self.rpc, "build_targets", return_value=[target]), patch.object(
            self.rpc, "can_run", return_value=False
        ):
            code = self.rpc.check_case(
                "01_mandelbrot",
                {"cpp"},
                case_root="sample",
                ignore_stdout=False,
                east3_opt_level="1",
                records=records,
            )

        self.assertEqual(code, 0)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].category, "toolchain_missing")
        self.assertEqual(records[0].target, "cpp")


if __name__ == "__main__":
    unittest.main()
