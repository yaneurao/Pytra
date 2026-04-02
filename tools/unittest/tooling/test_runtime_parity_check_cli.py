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

from toolchain2.link.shared_types import LinkedModule


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
        self.assertEqual(stems[-5:], ["tuple_assign", "type_alias_pep695", "type_ignore_from_import", "typing_extended", "yield_generator_min"])

    def test_resolve_case_stems_defaults(self) -> None:
        stems_fixture, err_fixture = self.rpc.resolve_case_stems([], "fixture", False)
        self.assertEqual(err_fixture, "")
        self.assertEqual(len(stems_fixture), 132)
        self.assertEqual(stems_fixture[0], "add")
        self.assertEqual(stems_fixture[-1], "yield_generator_min")

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

    def test_can_run_accepts_local_go_toolchain_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            go_bin = Path(tmp) / "go"
            go_bin.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            go_bin.chmod(0o755)
            target = self.rpc.Target(name="go", transpile_cmd="noop", run_cmd="noop", needs=("python", "go"))

            with patch.object(self.rpc, "_LOCAL_TOOL_FALLBACKS", {"go": (go_bin,)}), patch.object(
                self.rpc.shutil, "which", side_effect=lambda tool: sys.executable if tool == "python" else None
            ):
                self.assertTrue(self.rpc.can_run(target))
                env = self.rpc._tool_env_for_target(target)

        self.assertIn(str(go_bin.parent), env.get("PATH", ""))

    def test_check_case_passes_target_env_to_transpile_and_run(self) -> None:
        records: list = []
        target = self.rpc.Target(name="go", transpile_cmd="transpile", run_cmd="run", needs=("python", "go"))
        envs: list[dict[str, str] | None] = []
        call_index = {"value": 0}

        def _side_effect(
            cmd: str,
            cwd: Path,
            *,
            env: dict[str, str] | None = None,
            timeout_sec: int | None = None,
        ):
            _ = cmd
            _ = timeout_sec
            envs.append(env)
            idx = call_index["value"]
            call_index["value"] = idx + 1
            if idx == 0:
                return subprocess.CompletedProcess(args="python fake.py", returncode=0, stdout="True\n", stderr="")
            return subprocess.CompletedProcess(args="noop", returncode=0, stdout="True\n", stderr="")

        with patch.object(self.rpc, "find_case_path", return_value=ROOT / "sample" / "py" / "01_mandelbrot.py"), patch.object(
            self.rpc, "run_shell", side_effect=_side_effect
        ), patch.object(self.rpc, "build_targets", return_value=[target]), patch.object(
            self.rpc, "can_run", return_value=True
        ), patch.object(
            self.rpc, "_tool_env_for_target", return_value={"PATH": "/tmp/go-bin"}
        ):
            code = self.rpc.check_case(
                "01_mandelbrot",
                {"go"},
                case_root="sample",
                ignore_stdout=False,
                east3_opt_level="1",
                records=records,
            )

        self.assertEqual(code, 0)
        self.assertEqual(len(envs), 3)
        self.assertEqual(envs[0], {"PYTHONPATH": "src"})
        self.assertEqual(envs[1], {"PATH": "/tmp/go-bin"})
        self.assertEqual(envs[2], {"PATH": "/tmp/go-bin"})

    def test_check_case_cpp_reuses_transpiled_emit_dir_for_run(self) -> None:
        records: list = []
        target = self.rpc.Target(
            name="cpp",
            transpile_cmd="transpile",
            run_cmd="legacy-build-run",
            needs=("python", "g++"),
            output_dir="work/transpile/cpp/case_123",
        )
        py_success = subprocess.CompletedProcess(args="python fake.py", returncode=0, stdout="OK\n", stderr="")
        tr_success = subprocess.CompletedProcess(args="transpile", returncode=0, stdout="", stderr="")
        rr_success = subprocess.CompletedProcess(args="app.out", returncode=0, stdout="OK\n", stderr="")

        with patch.object(self.rpc, "find_case_path", return_value=ROOT / "sample" / "py" / "01_mandelbrot.py"), patch.object(
            self.rpc, "run_shell", side_effect=[py_success, tr_success]
        ) as run_shell_mock, patch.object(
            self.rpc, "build_targets", return_value=[target]
        ), patch.object(
            self.rpc, "can_run", return_value=True
        ), patch.object(
            self.rpc, "_run_cpp_emit_dir", return_value=rr_success
        ) as run_cpp_mock, patch.object(
            self.rpc, "_tool_env_for_target", return_value={"PATH": "/tmp/cpp-bin"}
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
        self.assertEqual(run_shell_mock.call_count, 2)
        run_cpp_mock.assert_called_once()
        args = run_cpp_mock.call_args.args
        kwargs = run_cpp_mock.call_args.kwargs
        self.assertTrue(str(args[0]).endswith("work/transpile/cpp/case_123/emit"))
        self.assertIn("01_mandelbrot_", str(kwargs["cwd"]))
        self.assertEqual(kwargs["env"], {"PATH": "/tmp/cpp-bin"})

    def test_build_targets_includes_ruby_entry(self) -> None:
        case_path = ROOT / "sample" / "py" / "01_mandelbrot.py"
        targets = self.rpc.build_targets("01_mandelbrot", case_path, "1")
        names = {t.name for t in targets}
        self.assertIn("ruby", names)
        ruby_target = next(t for t in targets if t.name == "ruby")
        self.assertIn("src/pytra-cli.py", ruby_target.transpile_cmd)
        self.assertIn("--target ruby", ruby_target.transpile_cmd)
        self.assertIn("--output-dir work/transpile/ruby/01_mandelbrot_", ruby_target.transpile_cmd)
        self.assertIn("src/pytra-cli.py", ruby_target.run_cmd)
        self.assertIn("--build --run", ruby_target.run_cmd)
        self.assertEqual(ruby_target.needs, ("python", "ruby"))

    def test_build_targets_cpp_can_forward_codegen_opt(self) -> None:
        case_path = ROOT / "sample" / "py" / "01_mandelbrot.py"
        targets = self.rpc.build_targets("01_mandelbrot", case_path, "2", "3")
        cpp_target = next(t for t in targets if t.name == "cpp")
        self.assertIn("--codegen-opt 3", cpp_target.transpile_cmd)
        self.assertIn("--codegen-opt 3", cpp_target.run_cmd)
        ruby_target = next(t for t in targets if t.name == "ruby")
        self.assertNotIn("--codegen-opt", ruby_target.transpile_cmd)

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
                east3_opt_level=1,
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

    def test_build_targets_includes_scala_entry(self) -> None:
        case_path = ROOT / "sample" / "py" / "01_mandelbrot.py"
        targets = self.rpc.build_targets("01_mandelbrot", case_path, "1")
        names = {t.name for t in targets}
        self.assertIn("scala", names)
        scala_target = next(t for t in targets if t.name == "scala")
        self.assertIn("src/pytra-cli.py", scala_target.transpile_cmd)
        self.assertIn("--target scala", scala_target.transpile_cmd)
        self.assertIn("--output-dir work/transpile/scala/01_mandelbrot_", scala_target.transpile_cmd)
        self.assertIn("src/pytra-cli.py", scala_target.run_cmd)
        self.assertIn("--build --run", scala_target.run_cmd)
        self.assertEqual(scala_target.needs, ("python", "scala-cli"))

    def test_build_targets_includes_nim_entry(self) -> None:
        case_path = ROOT / "sample" / "py" / "01_mandelbrot.py"
        targets = self.rpc.build_targets("01_mandelbrot", case_path, "1")
        names = {t.name for t in targets}
        self.assertIn("nim", names)
        nim_target = next(t for t in targets if t.name == "nim")
        self.assertIn("src/pytra-cli.py", nim_target.transpile_cmd)
        self.assertIn("--target nim", nim_target.transpile_cmd)
        self.assertIn("--output-dir work/transpile/nim/01_mandelbrot_", nim_target.transpile_cmd)
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
                cp = subprocess.CompletedProcess(args="python src/pytra-cli.py --target ruby ...", returncode=0, stdout="", stderr="")
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
                cp = subprocess.CompletedProcess(args="python src/pytra-cli.py --target php ...", returncode=0, stdout="", stderr="")
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
                cp = subprocess.CompletedProcess(args="python src/pytra-cli.py --target scala ...", returncode=0, stdout="", stderr="")
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
