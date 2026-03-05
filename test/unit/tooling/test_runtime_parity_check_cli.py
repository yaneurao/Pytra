from __future__ import annotations

import importlib.util
import os
import shlex
import subprocess
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
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
        self.assertEqual(stems_fixture, ["math_extended", "pathlib_extended", "inheritance_virtual_dispatch_multilang"])

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

    def test_build_targets_includes_ruby_entry(self) -> None:
        case_path = ROOT / "sample" / "py" / "01_mandelbrot.py"
        targets = self.rpc.build_targets("01_mandelbrot", case_path, "1")
        names = {t.name for t in targets}
        self.assertIn("ruby", names)
        ruby_target = next(t for t in targets if t.name == "ruby")
        self.assertIn("src/pytra-cli.py", ruby_target.transpile_cmd)
        self.assertIn("--target ruby", ruby_target.transpile_cmd)
        self.assertIn("--output-dir test/transpile/ruby/01_mandelbrot", ruby_target.transpile_cmd)
        self.assertIn("src/pytra-cli.py", ruby_target.run_cmd)
        self.assertIn("--build --run", ruby_target.run_cmd)
        self.assertEqual(ruby_target.needs, ("python", "ruby"))

    def test_build_targets_includes_scala_entry(self) -> None:
        case_path = ROOT / "sample" / "py" / "01_mandelbrot.py"
        targets = self.rpc.build_targets("01_mandelbrot", case_path, "1")
        names = {t.name for t in targets}
        self.assertIn("scala", names)
        scala_target = next(t for t in targets if t.name == "scala")
        self.assertIn("src/pytra-cli.py", scala_target.transpile_cmd)
        self.assertIn("--target scala", scala_target.transpile_cmd)
        self.assertIn("--output-dir test/transpile/scala/01_mandelbrot", scala_target.transpile_cmd)
        self.assertIn("src/pytra-cli.py", scala_target.run_cmd)
        self.assertIn("--build --run", scala_target.run_cmd)
        self.assertEqual(scala_target.needs, ("python", "scala"))

    def test_build_targets_includes_nim_entry(self) -> None:
        case_path = ROOT / "sample" / "py" / "01_mandelbrot.py"
        targets = self.rpc.build_targets("01_mandelbrot", case_path, "1")
        names = {t.name for t in targets}
        self.assertIn("nim", names)
        nim_target = next(t for t in targets if t.name == "nim")
        self.assertIn("src/pytra-cli.py", nim_target.transpile_cmd)
        self.assertIn("--target nim", nim_target.transpile_cmd)
        self.assertIn("--output-dir test/transpile/nim/01_mandelbrot", nim_target.transpile_cmd)
        self.assertIn("src/pytra-cli.py", nim_target.run_cmd)
        self.assertIn("--build --run", nim_target.run_cmd)
        self.assertEqual(nim_target.needs, ("python", "nim"))

    def test_build_targets_swift_uses_optimized_compile_flag(self) -> None:
        case_path = ROOT / "sample" / "py" / "01_mandelbrot.py"
        targets = self.rpc.build_targets("01_mandelbrot", case_path, "1")
        swift_target = next(t for t in targets if t.name == "swift")
        self.assertIn("src/pytra-cli.py", swift_target.run_cmd)
        self.assertIn("--target swift", swift_target.run_cmd)
        self.assertIn("--build --run", swift_target.run_cmd)

    def test_run_shell_timeout_kills_process_group(self) -> None:
        marker = f"RPC_TIMEOUT_MARKER_{os.getpid()}"
        py_cmd = (
            "import subprocess, sys, time; "
            + "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)', "
            + repr(marker)
            + "]); "
            + "time.sleep(30)"
        )
        cmd = shlex.quote(sys.executable) + " -c " + shlex.quote(py_cmd)
        cp = self.rpc.run_shell(cmd, ROOT, timeout_sec=1)
        self.assertEqual(cp.returncode, 124)
        self.assertIn("[TIMEOUT] exceeded 1s", cp.stderr)
        time.sleep(0.2)
        ps = subprocess.run(["ps", "-ef"], check=False, capture_output=True, text=True)
        self.assertNotIn(marker, ps.stdout)

    def test_normalize_output_keeps_artifact_size_line(self) -> None:
        raw = "output: sample/out/x.png\nartifact_size: 123\nelapsed_sec: 0.12\n"
        norm = self.rpc._normalize_output_for_compare(raw)
        self.assertIn("artifact_size: 123", norm)
        self.assertNotIn("elapsed_sec:", norm)

    def test_check_case_detects_artifact_size_mismatch(self) -> None:
        records: list = []
        target = self.rpc.Target(name="ruby", transpile_cmd="noop", run_cmd="noop", needs=())
        call_index = {"value": 0}

        def _side_effect(
            cmd: str,
            cwd: Path,
            *,
            env: dict[str, str] | None = None,
            timeout_sec: int | None = None,
        ):
            _ = cmd
            _ = env
            _ = timeout_sec
            out_path = cwd / "tmp" / "out.bin"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            idx = call_index["value"]
            if idx == 0:
                out_path.write_bytes(b"a" * 100)
                cp = subprocess.CompletedProcess(
                    args="python fake.py",
                    returncode=0,
                    stdout="output: tmp/out.bin\nelapsed_sec: 0.1\n",
                    stderr="",
                )
            elif idx == 1:
                cp = subprocess.CompletedProcess(args="python src/py2x.py --target ruby ...", returncode=0, stdout="", stderr="")
            else:
                out_path.write_bytes(b"b" * 101)
                cp = subprocess.CompletedProcess(
                    args="ruby out.rb",
                    returncode=0,
                    stdout="output: tmp/out.bin\nelapsed_sec: 0.2\n",
                    stderr="",
                )
            call_index["value"] = idx + 1
            return cp

        with patch.object(self.rpc, "find_case_path", return_value=ROOT / "sample" / "py" / "01_mandelbrot.py"), patch.object(
            self.rpc, "run_shell", side_effect=_side_effect
        ), patch.object(self.rpc, "build_targets", return_value=[target]), patch.object(self.rpc, "can_run", return_value=True):
            code = self.rpc.check_case("01_mandelbrot", {"ruby"}, case_root="sample", ignore_stdout=True, east3_opt_level="1", records=records)

        self.assertEqual(code, 1)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].category, "artifact_size_mismatch")
        self.assertEqual(records[0].target, "ruby")

    def test_check_case_detects_artifact_crc32_mismatch(self) -> None:
        records: list = []
        target = self.rpc.Target(name="php", transpile_cmd="noop", run_cmd="noop", needs=())
        call_index = {"value": 0}

        def _side_effect(
            cmd: str,
            cwd: Path,
            *,
            env: dict[str, str] | None = None,
            timeout_sec: int | None = None,
        ):
            _ = cmd
            _ = env
            _ = timeout_sec
            out_path = cwd / "tmp" / "out.bin"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            idx = call_index["value"]
            if idx == 0:
                out_path.write_bytes(b"A" * 100)
                cp = subprocess.CompletedProcess(
                    args="python fake.py",
                    returncode=0,
                    stdout="output: tmp/out.bin\nelapsed_sec: 0.1\n",
                    stderr="",
                )
            elif idx == 1:
                cp = subprocess.CompletedProcess(args="python src/py2x.py --target php ...", returncode=0, stdout="", stderr="")
            else:
                out_path.write_bytes(b"B" * 100)
                cp = subprocess.CompletedProcess(
                    args="php out.php",
                    returncode=0,
                    stdout="output: tmp/out.bin\nelapsed_sec: 0.2\n",
                    stderr="",
                )
            call_index["value"] = idx + 1
            return cp

        with patch.object(self.rpc, "find_case_path", return_value=ROOT / "sample" / "py" / "01_mandelbrot.py"), patch.object(
            self.rpc, "run_shell", side_effect=_side_effect
        ), patch.object(self.rpc, "build_targets", return_value=[target]), patch.object(self.rpc, "can_run", return_value=True):
            code = self.rpc.check_case("01_mandelbrot", {"php"}, case_root="sample", ignore_stdout=True, east3_opt_level="1", records=records)

        self.assertEqual(code, 1)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].category, "artifact_crc32_mismatch")
        self.assertEqual(records[0].target, "php")

    def test_check_case_scala_enforces_artifact_presence(self) -> None:
        records: list = []
        target = self.rpc.Target(name="scala", transpile_cmd="noop", run_cmd="noop", needs=())
        call_index = {"value": 0}

        def _side_effect(
            cmd: str,
            cwd: Path,
            *,
            env: dict[str, str] | None = None,
            timeout_sec: int | None = None,
        ):
            _ = cmd
            _ = env
            _ = timeout_sec
            out_path = cwd / "tmp" / "out.bin"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            idx = call_index["value"]
            if idx == 0:
                out_path.write_bytes(b"a" * 100)
                cp = subprocess.CompletedProcess(
                    args="python fake.py",
                    returncode=0,
                    stdout="output: tmp/out.bin\nelapsed_sec: 0.1\n",
                    stderr="",
                )
            elif idx == 1:
                cp = subprocess.CompletedProcess(args="python src/py2x.py --target scala ...", returncode=0, stdout="", stderr="")
            else:
                cp = subprocess.CompletedProcess(
                    args="scala run out.scala",
                    returncode=0,
                    stdout="output: tmp/out.bin\nelapsed_sec: 0.2\n",
                    stderr="",
                )
            call_index["value"] = idx + 1
            return cp

        with patch.object(self.rpc, "find_case_path", return_value=ROOT / "sample" / "py" / "01_mandelbrot.py"), patch.object(
            self.rpc, "run_shell", side_effect=_side_effect
        ), patch.object(self.rpc, "build_targets", return_value=[target]), patch.object(self.rpc, "can_run", return_value=True):
            code = self.rpc.check_case("01_mandelbrot", {"scala"}, case_root="sample", ignore_stdout=True, east3_opt_level="1", records=records)

        self.assertEqual(code, 1)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].category, "artifact_missing")
        self.assertEqual(records[0].target, "scala")


if __name__ == "__main__":
    unittest.main()
