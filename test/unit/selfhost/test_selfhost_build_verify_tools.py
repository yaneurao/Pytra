from __future__ import annotations

import importlib.util
import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
BUILD_STAGE2_PATH = ROOT / "tools" / "build_selfhost_stage2.py"
VERIFY_E2E_PATH = ROOT / "tools" / "verify_selfhost_end_to_end.py"


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BuildSelfhostStage2ToolTest(unittest.TestCase):
    def test_build_stage1_transpile_cmd_targets_selfhost_cpp_source(self) -> None:
        mod = _load_module(BUILD_STAGE2_PATH, "build_selfhost_stage2_mod")
        cmd = mod.build_stage1_transpile_cmd(
            Path("/tmp/py2cpp.out"),
            Path("/tmp/py2x-selfhost.py"),
            Path("/tmp/py2cpp_stage2.cpp"),
        )
        self.assertEqual(
            cmd,
            [
                "/tmp/py2cpp.out",
                "/tmp/py2x-selfhost.py",
                "--target",
                "cpp",
                "-o",
                "/tmp/py2cpp_stage2.cpp",
            ],
        )

    def test_should_reuse_stage1_cpp_only_for_not_implemented_failures(self) -> None:
        mod = _load_module(BUILD_STAGE2_PATH, "build_selfhost_stage2_mod")
        self.assertTrue(
            mod.should_reuse_stage1_cpp(
                subprocess.CompletedProcess(["stage1"], 1, stdout="", stderr="[not_implemented] fallback")
            )
        )
        self.assertFalse(
            mod.should_reuse_stage1_cpp(
                subprocess.CompletedProcess(["stage1"], 1, stdout="", stderr="other failure")
            )
        )
        self.assertFalse(
            mod.should_reuse_stage1_cpp(
                subprocess.CompletedProcess(["stage1"], 0, stdout="[not_implemented]", stderr="")
            )
        )

    def test_main_reuses_stage1_cpp_when_stage1_transpile_is_not_implemented(self) -> None:
        mod = _load_module(BUILD_STAGE2_PATH, "build_selfhost_stage2_mod")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            mod.BUILD_STAGE1 = root / "build_selfhost.py"
            mod.STAGE1_BIN = root / "py2cpp.out"
            mod.STAGE1_SRC = root / "py2x-selfhost.py"
            mod.STAGE2_CPP = root / "py2cpp_stage2.cpp"
            mod.STAGE2_BIN = root / "py2cpp_stage2.out"
            mod.STAGE1_CPP = root / "py2cpp.cpp"
            mod.STAGE1_BIN.write_text("", encoding="utf-8")
            mod.STAGE1_SRC.write_text("print('selfhost')\n", encoding="utf-8")
            mod.STAGE1_CPP.write_text("// stage1 fallback\n", encoding="utf-8")

            run_calls: list[list[str]] = []

            def _fake_run(cmd: list[str]) -> None:
                run_calls.append(cmd)
                if cmd and cmd[0] == "g++":
                    mod.STAGE2_BIN.write_text("", encoding="utf-8")

            def _fake_run_capture(cmd: list[str]) -> subprocess.CompletedProcess[str]:
                run_calls.append(cmd)
                return subprocess.CompletedProcess(
                    cmd,
                    1,
                    stdout="",
                    stderr="[not_implemented] selfhost transpile fallback",
                )

            with patch.object(mod, "_run", side_effect=_fake_run), patch.object(
                mod, "_run_capture", side_effect=_fake_run_capture
            ), patch.object(mod, "collect_runtime_cpp_sources", return_value=[]), patch.object(
                sys, "argv", ["build_selfhost_stage2.py", "--skip-stage1-build"]
            ):
                rc = mod.main()

            self.assertEqual(rc, 0)
            self.assertEqual(mod.STAGE2_CPP.read_text(encoding="utf-8"), "// stage1 fallback\n")
            self.assertEqual(
                run_calls[0],
                mod.build_stage1_transpile_cmd(mod.STAGE1_BIN, mod.STAGE1_SRC, mod.STAGE2_CPP),
            )
            self.assertEqual(run_calls[1][0], "g++")
            self.assertIn(str(mod.STAGE2_CPP), run_calls[1])
            self.assertIn(str(mod.STAGE2_BIN), run_calls[1])


class VerifySelfhostEndToEndToolTest(unittest.TestCase):
    def _run_single_case_main(
        self,
        mod,
        *,
        py_run: subprocess.CompletedProcess[str],
        transpile_run: subprocess.CompletedProcess[str],
        compile_run: subprocess.CompletedProcess[str],
        exec_run: subprocess.CompletedProcess[str],
        target: str = "cpp",
    ) -> tuple[int, list[list[str]], str]:
        with tempfile.TemporaryDirectory() as td:
            selfhost_bin = Path(td) / "py2cpp.out"
            selfhost_bin.write_text("", encoding="utf-8")
            calls: list[list[str]] = []

            def _clone(cmd: list[str], template: subprocess.CompletedProcess[str]) -> subprocess.CompletedProcess[str]:
                return subprocess.CompletedProcess(
                    cmd,
                    template.returncode,
                    stdout=template.stdout,
                    stderr=template.stderr,
                )

            def _fake_run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
                calls.append(cmd)
                if len(cmd) >= 2 and cmd[0] == "python3" and cmd[1].endswith("add.py"):
                    return _clone(cmd, py_run)
                if cmd and cmd[0] == str(selfhost_bin):
                    return _clone(cmd, transpile_run)
                if cmd and cmd[0] == "g++":
                    return _clone(cmd, compile_run)
                return _clone(cmd, exec_run)

            with patch.object(mod, "_run", side_effect=_fake_run), patch.object(
                mod, "_resolve_selfhost_target", return_value=target
            ), patch.object(mod, "collect_runtime_cpp_sources", return_value=[]), patch.object(
                sys,
                "argv",
                [
                    "verify_selfhost_end_to_end.py",
                    "--skip-build",
                    "--selfhost-bin",
                    str(selfhost_bin),
                    "--cases",
                    "test/fixtures/core/add.py",
                ],
            ):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    rc = mod.main()
        return rc, calls, buf.getvalue()

    def test_resolve_selfhost_target_auto_prefers_cpp_only_when_help_advertises_target(self) -> None:
        mod = _load_module(VERIFY_E2E_PATH, "verify_selfhost_end_to_end_mod")
        selfhost_bin = ROOT / "selfhost" / "py2cpp.out"
        with patch.object(
            mod.subprocess,
            "run",
            return_value=subprocess.CompletedProcess(["--help"], 0, stdout="usage: py2cpp --target cpp", stderr=""),
        ):
            self.assertEqual(mod._resolve_selfhost_target(selfhost_bin, "auto"), "cpp")
        with patch.object(
            mod.subprocess,
            "run",
            return_value=subprocess.CompletedProcess(["--help"], 0, stdout="usage: py2cpp", stderr=""),
        ):
            self.assertEqual(mod._resolve_selfhost_target(selfhost_bin, "auto"), "")
        self.assertEqual(mod._resolve_selfhost_target(selfhost_bin, "rs"), "rs")

    def test_normalize_stdout_strips_sample_timing_lines(self) -> None:
        mod = _load_module(VERIFY_E2E_PATH, "verify_selfhost_end_to_end_mod")
        text = "  hello  \nelapsed_sec: 1.2\nelapsed: 0.4\nworld\n"
        self.assertEqual(mod._normalize_stdout(text, ["elapsed_sec:", "elapsed:"]), "hello\nworld")
        self.assertEqual(mod._ignore_prefixes_for_case("sample/py/17_monte_carlo_pi.py"), ["elapsed_sec:", "elapsed:", "time_sec:"])
        self.assertEqual(mod._ignore_prefixes_for_case("test/fixtures/core/add.py"), [])

    def test_direct_summary_row_maps_not_implemented_to_known_block(self) -> None:
        mod = _load_module(VERIFY_E2E_PATH, "verify_selfhost_end_to_end_mod")
        row = mod.build_direct_e2e_summary_row(
            "test/fixtures/core/add.py",
            "selfhost_transpile_fail",
            "[not_implemented] direct transpile is not ready",
        )
        self.assertEqual(row.top_level_category, "known_block")
        self.assertEqual(row.detail_category, "not_implemented")

    def test_direct_summary_row_maps_stdout_failure_to_regression(self) -> None:
        mod = _load_module(VERIFY_E2E_PATH, "verify_selfhost_end_to_end_mod")
        row = mod.build_direct_e2e_summary_row(
            "test/fixtures/core/add.py",
            "stdout_fail",
            "python='7' selfhost='8'",
        )
        self.assertEqual(row.top_level_category, "regression")
        self.assertEqual(row.detail_category, "direct_parity_fail")

    def test_print_direct_summary_formats_shared_summary_line(self) -> None:
        mod = _load_module(VERIFY_E2E_PATH, "verify_selfhost_end_to_end_mod")
        row = mod.build_direct_e2e_summary_row(
            "test/fixtures/core/add.py",
            "stdout_fail",
            "python='7' selfhost='8'",
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            mod.print_summary_block("direct_e2e", [row], skip_pass=True)
        text = buf.getvalue()
        self.assertIn("[direct_e2e summary]", text)
        self.assertIn("subject=test/fixtures/core/add.py", text)
        self.assertIn("category=regression", text)
        self.assertIn("detail=direct_parity_fail", text)

    def test_main_uses_auto_target_result_in_transpile_command(self) -> None:
        mod = _load_module(VERIFY_E2E_PATH, "verify_selfhost_end_to_end_mod")
        with tempfile.TemporaryDirectory() as td:
            selfhost_bin = Path(td) / "py2cpp.out"
            selfhost_bin.write_text("", encoding="utf-8")
            calls: list[list[str]] = []

            def _fake_run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
                calls.append(cmd)
                if len(cmd) >= 2 and cmd[0] == "python3" and cmd[1].endswith("add.py"):
                    return subprocess.CompletedProcess(cmd, 0, stdout="7\n", stderr="")
                if cmd and cmd[0] == str(selfhost_bin):
                    return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
                if cmd and cmd[0] == "g++":
                    return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
                return subprocess.CompletedProcess(cmd, 0, stdout="7\n", stderr="")

            with patch.object(mod, "_run", side_effect=_fake_run), patch.object(
                mod, "_resolve_selfhost_target", return_value="cpp"
            ), patch.object(mod, "collect_runtime_cpp_sources", return_value=[]), patch.object(
                sys,
                "argv",
                [
                    "verify_selfhost_end_to_end.py",
                    "--skip-build",
                    "--selfhost-bin",
                    str(selfhost_bin),
                    "--cases",
                    "test/fixtures/core/add.py",
                ],
            ):
                rc = mod.main()

            self.assertEqual(rc, 0)
            transpile_cmd = next(cmd for cmd in calls if cmd and cmd[0] == str(selfhost_bin))
            self.assertIn("--target", transpile_cmd)
            self.assertIn("cpp", transpile_cmd)

            calls.clear()
            with patch.object(mod, "_run", side_effect=_fake_run), patch.object(
                mod, "_resolve_selfhost_target", return_value=""
            ), patch.object(mod, "collect_runtime_cpp_sources", return_value=[]), patch.object(
                sys,
                "argv",
                [
                    "verify_selfhost_end_to_end.py",
                    "--skip-build",
                    "--selfhost-bin",
                    str(selfhost_bin),
                    "--cases",
                    "test/fixtures/core/add.py",
                ],
            ):
                rc = mod.main()

            self.assertEqual(rc, 0)
            transpile_cmd = next(cmd for cmd in calls if cmd and cmd[0] == str(selfhost_bin))
            self.assertNotIn("--target", transpile_cmd)

    def test_main_returns_2_when_build_selfhost_fails(self) -> None:
        mod = _load_module(VERIFY_E2E_PATH, "verify_selfhost_end_to_end_mod")
        selfhost_bin = ROOT / "selfhost" / "missing.out"

        def _fake_run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
            self.assertEqual(cmd, ["python3", str(mod.BUILD_SELFHOST)])
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="build failed")

        with patch.object(mod, "_run", side_effect=_fake_run), patch.object(
            sys,
            "argv",
            ["verify_selfhost_end_to_end.py", "--selfhost-bin", str(selfhost_bin)],
        ):
            self.assertEqual(mod.main(), 2)

    def test_main_returns_2_when_selfhost_binary_is_missing(self) -> None:
        mod = _load_module(VERIFY_E2E_PATH, "verify_selfhost_end_to_end_mod")
        with tempfile.TemporaryDirectory() as td:
            missing_bin = Path(td) / "missing.out"
            with patch.object(
                sys,
                "argv",
                [
                    "verify_selfhost_end_to_end.py",
                    "--skip-build",
                    "--selfhost-bin",
                    str(missing_bin),
                ],
            ):
                self.assertEqual(mod.main(), 2)

    def test_main_returns_1_when_selfhost_transpile_fails(self) -> None:
        mod = _load_module(VERIFY_E2E_PATH, "verify_selfhost_end_to_end_mod")
        rc, calls, out = self._run_single_case_main(
            mod,
            py_run=subprocess.CompletedProcess(["python3"], 0, stdout="7\n", stderr=""),
            transpile_run=subprocess.CompletedProcess(["selfhost"], 3, stdout="", stderr="transpile failed"),
            compile_run=subprocess.CompletedProcess(["g++"], 0, stdout="", stderr=""),
            exec_run=subprocess.CompletedProcess(["out"], 0, stdout="7\n", stderr=""),
        )
        self.assertEqual(rc, 1)
        self.assertFalse(any(cmd and cmd[0] == "g++" for cmd in calls))
        self.assertIn("[direct_e2e summary]", out)
        self.assertIn("detail=sample_transpile_fail", out)

    def test_main_returns_1_when_compile_fails(self) -> None:
        mod = _load_module(VERIFY_E2E_PATH, "verify_selfhost_end_to_end_mod")
        rc, calls, out = self._run_single_case_main(
            mod,
            py_run=subprocess.CompletedProcess(["python3"], 0, stdout="7\n", stderr=""),
            transpile_run=subprocess.CompletedProcess(["selfhost"], 0, stdout="", stderr=""),
            compile_run=subprocess.CompletedProcess(["g++"], 4, stdout="", stderr="compile failed"),
            exec_run=subprocess.CompletedProcess(["out"], 0, stdout="7\n", stderr=""),
        )
        self.assertEqual(rc, 1)
        self.assertTrue(any(cmd and cmd[0] == "g++" for cmd in calls))
        self.assertIn("detail=direct_compile_fail", out)

    def test_main_returns_1_when_executable_fails(self) -> None:
        mod = _load_module(VERIFY_E2E_PATH, "verify_selfhost_end_to_end_mod")
        rc, _calls, out = self._run_single_case_main(
            mod,
            py_run=subprocess.CompletedProcess(["python3"], 0, stdout="7\n", stderr=""),
            transpile_run=subprocess.CompletedProcess(["selfhost"], 0, stdout="", stderr=""),
            compile_run=subprocess.CompletedProcess(["g++"], 0, stdout="", stderr=""),
            exec_run=subprocess.CompletedProcess(["out"], 5, stdout="", stderr="run failed"),
        )
        self.assertEqual(rc, 1)
        self.assertIn("detail=direct_run_fail", out)

    def test_main_returns_1_when_stdout_differs(self) -> None:
        mod = _load_module(VERIFY_E2E_PATH, "verify_selfhost_end_to_end_mod")
        rc, _calls, out = self._run_single_case_main(
            mod,
            py_run=subprocess.CompletedProcess(["python3"], 0, stdout="7\n", stderr=""),
            transpile_run=subprocess.CompletedProcess(["selfhost"], 0, stdout="", stderr=""),
            compile_run=subprocess.CompletedProcess(["g++"], 0, stdout="", stderr=""),
            exec_run=subprocess.CompletedProcess(["out"], 0, stdout="8\n", stderr=""),
        )
        self.assertEqual(rc, 1)
        self.assertIn("detail=direct_parity_fail", out)

    def test_main_emits_pass_summary_when_all_cases_pass(self) -> None:
        mod = _load_module(VERIFY_E2E_PATH, "verify_selfhost_end_to_end_mod")
        rc, _calls, out = self._run_single_case_main(
            mod,
            py_run=subprocess.CompletedProcess(["python3"], 0, stdout="7\n", stderr=""),
            transpile_run=subprocess.CompletedProcess(["selfhost"], 0, stdout="", stderr=""),
            compile_run=subprocess.CompletedProcess(["g++"], 0, stdout="", stderr=""),
            exec_run=subprocess.CompletedProcess(["out"], 0, stdout="7\n", stderr=""),
        )
        self.assertEqual(rc, 0)
        self.assertIn("[direct_e2e summary]", out)
        self.assertIn("subject=all", out)
        self.assertIn("category=pass", out)
        self.assertIn("detail=pass", out)


if __name__ == "__main__":
    unittest.main()
