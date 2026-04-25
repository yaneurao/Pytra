from __future__ import annotations

import importlib.util
import os
import shlex
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
RUNTIME_PARITY_CHECK = ROOT / "tools" / "check" / "runtime_parity_check.py"
RUNTIME_PARITY_CHECK_FAST = ROOT / "tools" / "check" / "runtime_parity_check_fast.py"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from toolchain.link.shared_types import LinkedModule


def _load_runtime_parity_module():
    spec = importlib.util.spec_from_file_location("runtime_parity_check", RUNTIME_PARITY_CHECK)
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to load runtime_parity_check module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_runtime_parity_fast_module():
    spec = importlib.util.spec_from_file_location("runtime_parity_check_fast", RUNTIME_PARITY_CHECK_FAST)
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to load runtime_parity_check_fast module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RuntimeParityCheckCliTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rpc = _load_runtime_parity_module()
        cls.rpc_fast = _load_runtime_parity_fast_module()

    def test_collect_sample_case_stems_is_fixed_to_18_samples(self) -> None:
        stems = self.rpc.collect_sample_case_stems()
        self.assertEqual(len(stems), 18)
        self.assertEqual(stems[0], "01_mandelbrot")
        self.assertEqual(stems[-1], "18_mini_language_interpreter")
        self.assertNotIn("__init__", stems)

    def test_collect_fixture_case_stems_is_fixed_to_132_cases(self) -> None:
        stems = self.rpc.collect_fixture_case_stems()
        self.assertGreaterEqual(len(stems), 132)
        self.assertEqual(stems[:5], ["add", "alias_arg", "assign", "bitwise_invert_basic", "bom_from_import"])
        self.assertIn("tuple_assign", stems)
        self.assertIn("type_alias_pep695", stems)
        self.assertEqual(stems[-1], "yield_generator_min")

    def test_resolve_case_stems_defaults(self) -> None:
        stems_fixture, err_fixture = self.rpc.resolve_case_stems([], "fixture", False)
        self.assertEqual(err_fixture, "")
        self.assertGreaterEqual(len(stems_fixture), 132)
        self.assertEqual(stems_fixture[0], "add")
        self.assertEqual(stems_fixture[-1], "yield_generator_min")

        stems_sample, err_sample = self.rpc.resolve_case_stems([], "sample", False)
        self.assertEqual(err_sample, "")
        self.assertEqual(len(stems_sample), 18)

    def test_resolve_case_stems_category_validation(self) -> None:
        stems_root_err, err_root = self.rpc.resolve_case_stems([], "sample", False, "core")
        self.assertEqual(stems_root_err, [])
        self.assertIn("--category requires --case-root fixture", err_root)

        stems_arg_err, err_arg = self.rpc.resolve_case_stems(["add"], "fixture", False, "core")
        self.assertEqual(stems_arg_err, [])
        self.assertIn("--category cannot be combined", err_arg)

    def test_fast_check_case_records_toolchain_missing_category(self) -> None:
        records: list = []
        py_success = subprocess.CompletedProcess(args="python fake.py", returncode=0, stdout="True\n", stderr="")

        with patch.object(self.rpc_fast, "find_case_path", return_value=ROOT / "sample" / "py" / "01_mandelbrot.py"), patch.object(
            self.rpc_fast, "run_shell", return_value=py_success
        ), patch.object(
            self.rpc_fast,
            "get_target_profile",
            return_value=type("Profile", (), {"runner_needs": ("python", "g++")})(),
        ), patch.object(
            self.rpc_fast, "can_run", return_value=False
        ):
            code = self.rpc_fast.check_case(
                "01_mandelbrot",
                {"cpp"},
                case_root="sample",
                records=records,
            )

        self.assertEqual(code, 0)
        target_records = [r for r in records if r.target == "cpp"]
        self.assertEqual(len(target_records), 1)
        self.assertEqual(target_records[0].category, "toolchain_missing")

    def test_can_run_accepts_local_go_toolchain_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            go_bin = Path(tmp) / "go"
            go_bin.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            go_bin.chmod(0o755)
            target = self.rpc.Target(name="go", transpile_cmd="noop", run_cmd="noop", needs=("python", "go"))

            with patch.dict(self.rpc._LOCAL_TOOL_FALLBACKS, {"go": (go_bin,)}, clear=True), patch.object(
                self.rpc.shutil, "which", side_effect=lambda tool: sys.executable if tool == "python" else None
            ):
                self.assertTrue(self.rpc.can_run(target))
                env = self.rpc._tool_env_for_target(target)

        self.assertIn(str(go_bin.parent), env.get("PATH", ""))

    def test_fast_check_case_passes_target_env_to_run(self) -> None:
        records: list = []
        py_success = subprocess.CompletedProcess(args="python fake.py", returncode=0, stdout="True\n", stderr="")
        rr_success = subprocess.CompletedProcess(args="run", returncode=0, stdout="True\n", stderr="")

        with patch.object(self.rpc_fast, "find_case_path", return_value=ROOT / "sample" / "py" / "01_mandelbrot.py"), patch.object(
            self.rpc_fast, "run_shell", return_value=py_success
        ), patch.object(
            self.rpc_fast,
            "get_target_profile",
            return_value=type("Profile", (), {"runner_needs": ("python", "go")})(),
        ), patch.object(
            self.rpc_fast, "can_run", return_value=True
        ), patch.object(
            self.rpc_fast, "_tool_env_for_target", return_value={"PATH": "/workspace/Pytra/work/tmp/go-bin"}
        ), patch.object(
            self.rpc_fast, "_transpile_in_memory", return_value=(True, "")
        ), patch.object(
            self.rpc_fast, "_run_target", return_value=rr_success
        ) as run_target_mock:
            code = self.rpc_fast.check_case("01_mandelbrot", {"go"}, case_root="sample", records=records)

        self.assertEqual(code, 0)
        run_target_mock.assert_called_once()
        self.assertEqual(run_target_mock.call_args.kwargs["env"], {"PATH": "/workspace/Pytra/work/tmp/go-bin"})

    def test_runtime_parity_check_fast_forwards_subscript_optimizer_modes(self) -> None:
        records: list = []
        py_success = subprocess.CompletedProcess(args="python fake.py", returncode=0, stdout="OK\n", stderr="")
        rr_success = subprocess.CompletedProcess(args="run", returncode=0, stdout="OK\n", stderr="")

        with patch.object(
            self.rpc_fast,
            "find_case_path",
            return_value=ROOT / "sample" / "py" / "01_mandelbrot.py",
        ), patch.object(
            self.rpc_fast,
            "run_shell",
            return_value=py_success,
        ), patch.object(
            self.rpc_fast,
            "get_target_profile",
            return_value=type("Profile", (), {"runner_needs": ("python", "g++")})(),
        ), patch.object(
            self.rpc_fast,
            "can_run",
            return_value=True,
        ), patch.object(
            self.rpc_fast,
            "_tool_env_for_target",
            return_value={"PATH": "/tmp/cpp-bin"},
        ), patch.object(
            self.rpc_fast,
            "_transpile_in_memory",
            return_value=(True, ""),
        ) as transpile_mock, patch.object(
            self.rpc_fast,
            "_run_target",
            return_value=rr_success,
        ):
            code = self.rpc_fast.check_case(
                "01_mandelbrot",
                {"cpp"},
                case_root="sample",
                opt_level=1,
                negative_index_mode="always",
                bounds_check_mode="debug",
                records=records,
            )

        self.assertEqual(code, 0)
        transpile_mock.assert_called_once()
        self.assertEqual(transpile_mock.call_args.args[3:], (1, "always", "debug"))

    def test_runtime_parity_check_fast_optimizes_linked_runtime_modules_only(self) -> None:
        user = LinkedModule("app.main", "", "", True, {"kind": "Module", "east_stage": 3}, "user")
        runtime = LinkedModule("pytra.utils.png", "", "", False, {"kind": "Module", "east_stage": 3}, "runtime")
        helper = LinkedModule("__linked_helper__.x", "", "", False, {"kind": "Module", "east_stage": 3}, "helper")
        with patch.object(self.rpc_fast, "optimize_east3_doc_only", side_effect=lambda doc, **_: {"kind": "Module", "optimized": doc.get("kind")}) as optimize_doc:
            self.rpc_fast._optimize_linked_runtime_modules_in_place(
                [user, runtime, helper],
                opt_level=1,
                debug_flags={"negative_index_mode": "const_only", "bounds_check_mode": "off"},
            )
        self.assertEqual(optimize_doc.call_count, 2)
        self.assertNotIn("optimized", user.east_doc)
        self.assertEqual(runtime.east_doc.get("optimized"), "Module")
        self.assertEqual(helper.east_doc.get("optimized"), "Module")

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

        with patch.object(self.rpc_fast, "find_case_path", return_value=ROOT / "sample" / "py" / "01_mandelbrot.py"), patch.object(
            self.rpc_fast, "run_shell", side_effect=_side_effect
        ), patch.object(
            self.rpc_fast,
            "get_target_profile",
            return_value=type("Profile", (), {"runner_needs": ()})(),
        ), patch.object(self.rpc_fast, "can_run", return_value=True), patch.object(
            self.rpc_fast, "_tool_env_for_target", return_value={}
        ), patch.object(self.rpc_fast, "_transpile_in_memory", return_value=(True, "")), patch.object(
            self.rpc_fast, "_run_target", side_effect=lambda *args, **kwargs: _side_effect("run", kwargs["work_dir"])
        ):
            code = self.rpc_fast.check_case("01_mandelbrot", {"ruby"}, case_root="sample", records=records)

        self.assertEqual(code, 1)
        target_records = [r for r in records if r.target == "ruby"]
        self.assertEqual(len(target_records), 1)
        self.assertEqual(target_records[0].category, "artifact_size_mismatch")

    def test_check_case_detects_artifact_crc32_mismatch(self) -> None:
        records: list = []
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

        with patch.object(self.rpc_fast, "find_case_path", return_value=ROOT / "sample" / "py" / "01_mandelbrot.py"), patch.object(
            self.rpc_fast, "run_shell", side_effect=_side_effect
        ), patch.object(
            self.rpc_fast,
            "get_target_profile",
            return_value=type("Profile", (), {"runner_needs": ()})(),
        ), patch.object(self.rpc_fast, "can_run", return_value=True), patch.object(
            self.rpc_fast, "_tool_env_for_target", return_value={}
        ), patch.object(self.rpc_fast, "_transpile_in_memory", return_value=(True, "")), patch.object(
            self.rpc_fast, "_run_target", side_effect=lambda *args, **kwargs: _side_effect("run", kwargs["work_dir"])
        ):
            code = self.rpc_fast.check_case("01_mandelbrot", {"php"}, case_root="sample", records=records)

        self.assertEqual(code, 1)
        target_records = [r for r in records if r.target == "php"]
        self.assertEqual(len(target_records), 1)
        self.assertEqual(target_records[0].category, "artifact_crc32_mismatch")

    def test_check_case_scala_enforces_artifact_presence(self) -> None:
        records: list = []
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
            else:
                cp = subprocess.CompletedProcess(
                    args="scala run out.scala",
                    returncode=0,
                    stdout="output: tmp/out.bin\nelapsed_sec: 0.2\n",
                    stderr="",
                )
            call_index["value"] = idx + 1
            return cp

        with patch.object(self.rpc_fast, "find_case_path", return_value=ROOT / "sample" / "py" / "01_mandelbrot.py"), patch.object(
            self.rpc_fast, "run_shell", side_effect=_side_effect
        ), patch.object(
            self.rpc_fast,
            "get_target_profile",
            return_value=type("Profile", (), {"runner_needs": ()})(),
        ), patch.object(self.rpc_fast, "can_run", return_value=True), patch.object(
            self.rpc_fast, "_tool_env_for_target", return_value={}
        ), patch.object(self.rpc_fast, "_transpile_in_memory", return_value=(True, "")), patch.object(
            self.rpc_fast, "_run_target", side_effect=lambda *args, **kwargs: _side_effect("run", kwargs["work_dir"])
        ):
            code = self.rpc_fast.check_case("01_mandelbrot", {"scala"}, case_root="sample", records=records)

        self.assertEqual(code, 1)
        target_records = [r for r in records if r.target == "scala"]
        self.assertEqual(len(target_records), 1)
        self.assertEqual(target_records[0].category, "artifact_missing")


if __name__ == "__main__":
    unittest.main()
