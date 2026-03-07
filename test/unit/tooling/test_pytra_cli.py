"""Regression tests for src/pytra-cli.py."""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

_CLI_PATH = ROOT / "src" / "pytra-cli.py"
_SPEC = importlib.util.spec_from_file_location("pytra_cli_mod", str(_CLI_PATH))
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("failed to load pytra-cli module spec")
pytra_cli_mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(pytra_cli_mod)


class PytraCliTest(unittest.TestCase):
    def _fake_run(self, calls: list[tuple[list[str], str | None]]) -> callable:
        def _runner(
            cmd: list[str] | tuple[str, ...],
            *,
            cwd: str | None = None,
            capture_output: bool = True,
            text: bool = True,
            timeout: float | None = None,
        ) -> subprocess.CompletedProcess[str]:
            cmd_list = list(cmd)
            calls.append((cmd_list, cwd))
            if str(pytra_cli_mod.PY2X) in " ".join(cmd_list):
                if "--link-only" in cmd_list:
                    output_dir = ROOT
                    if "--output-dir" in cmd_list:
                        idx = cmd_list.index("--output-dir")
                        if idx + 1 < len(cmd_list):
                            output_dir = Path(cwd) / Path(cmd_list[idx + 1]) if cwd is not None else Path(cmd_list[idx + 1])
                    link_output_path = Path(output_dir).resolve() / "link-output.json"
                    link_output_path.parent.mkdir(parents=True, exist_ok=True)
                    link_output_path.write_text(
                        """
{
  "schema": "pytra.link_output.v1",
  "entry_modules": ["main"],
  "modules": [{"module_id": "main", "path": "linked/main.east3.json"}]
}
""".strip()
                        + "\n",
                        encoding="utf-8",
                    )
                    return subprocess.CompletedProcess(cmd_list, 0, stdout="generated: " + str(link_output_path), stderr="")
                if "--from-link-output" in cmd_list:
                    output_dir = ROOT
                    if "--output-dir" in cmd_list:
                        idx = cmd_list.index("--output-dir")
                        if idx + 1 < len(cmd_list):
                            output_dir = Path(cwd) / Path(cmd_list[idx + 1]) if cwd is not None else Path(cmd_list[idx + 1])
                    manifest_path = Path(output_dir).resolve() / "manifest.json"
                    manifest_path.parent.mkdir(parents=True, exist_ok=True)
                    manifest_path.write_text(
                        """
{
  "modules": [{"source": "src/main.cpp"}],
  "include_dir": "include"
}
""".strip()
                        + "\n",
                        encoding="utf-8",
                    )
                    return subprocess.CompletedProcess(
                        cmd_list,
                        0,
                        stdout="multi-file output generated at: ...\nmanifest: " + str(manifest_path),
                        stderr="",
                    )
                if "--multi-file" not in cmd_list:
                    return subprocess.CompletedProcess(cmd_list, 0, stdout="", stderr="")
                output_dir = ROOT
                if "--output-dir" in cmd_list:
                    idx = cmd_list.index("--output-dir")
                    if idx + 1 < len(cmd_list):
                        output_dir = Path(cwd) / Path(cmd_list[idx + 1]) if cwd is not None else Path(cmd_list[idx + 1])
                manifest_path = Path(output_dir).resolve() / "manifest.json"
                manifest_path.parent.mkdir(parents=True, exist_ok=True)
                manifest_path.write_text(
                    """
{
  "modules": [{"source": "src/main.cpp"}],
  "include_dir": "include"
}
""".strip()
                    + "\n",
                    encoding="utf-8",
                )
                return subprocess.CompletedProcess(cmd_list, 0, stdout="multi-file output generated at: ...\nmanifest: " + str(manifest_path), stderr="")
            if str(pytra_cli_mod.GEN_MAKEFILE) in " ".join(cmd_list):
                makefile_path = Path(cwd) / "Makefile"
                if "-o" in cmd_list:
                    idx = cmd_list.index("-o")
                    if idx + 1 < len(cmd_list):
                        makefile_path = Path(cmd_list[idx + 1])
                makefile_path.parent.mkdir(parents=True, exist_ok=True)
                makefile_path.write_text("all:\n\t@true\n", encoding="utf-8")
                return subprocess.CompletedProcess(cmd_list, 0, stdout="generated: " + str(makefile_path), stderr="")
            if cmd_list and Path(cmd_list[0]).name == "make":
                return subprocess.CompletedProcess(cmd_list, 0, stdout="make ok", stderr="")
            return subprocess.CompletedProcess(cmd_list, 0, stdout="", stderr="")

        return _runner

    def test_build_cpp_generates_and_invokes_make(self) -> None:
        calls: list[tuple[list[str], str | None]] = []
        runner = self._fake_run(calls)

        with tempfile.TemporaryDirectory() as work:
            input_py = Path(work) / "hello.py"
            input_py.write_text("print(1)\\n", encoding="utf-8")
            with patch.object(pytra_cli_mod.subprocess, "run", side_effect=runner):
                rc = pytra_cli_mod.main(
                    [
                        str(input_py),
                        "--target",
                        "cpp",
                        "--build",
                        "--output-dir",
                        str(Path(work) / "out"),
                        "--compiler",
                        "g++",
                        "--std",
                        "c++17",
                        "--opt",
                        "-O3",
                        "--exe",
                        "a.out",
                    ]
                )
            self.assertEqual(rc, 0)
            rendered = [str(item[0][0]) for item in calls]
            self.assertIn(pytra_cli_mod.PYTHON, rendered[0])
            self.assertTrue(any(str(pytra_cli_mod.PY2X) in item for item in calls[0][0]))
            self.assertTrue(any(str(pytra_cli_mod.GEN_MAKEFILE) in " ".join(call[0]) for call in calls))
            self.assertIn("make", rendered[2])

    def test_build_cpp_prefers_reported_manifest_path(self) -> None:
        calls: list[tuple[list[str], str | None]] = []

        with tempfile.TemporaryDirectory() as work:
            workdir = Path(work)
            input_py = workdir / "hello.py"
            input_py.write_text("print(1)\\n", encoding="utf-8")
            reported_manifest = workdir / "reported" / "linked-manifest.json"

            def _runner(
                cmd: list[str] | tuple[str, ...],
                *,
                cwd: str | None = None,
                capture_output: bool = True,
                text: bool = True,
                timeout: float | None = None,
            ) -> subprocess.CompletedProcess[str]:
                _ = capture_output
                _ = text
                _ = timeout
                cmd_list = list(cmd)
                calls.append((cmd_list, cwd))
                if str(pytra_cli_mod.PY2X) in " ".join(cmd_list):
                    reported_manifest.parent.mkdir(parents=True, exist_ok=True)
                    reported_manifest.write_text(
                        """
{
  "modules": [{"source": "src/main.cpp"}],
  "include_dir": "include"
}
""".strip()
                        + "\n",
                        encoding="utf-8",
                    )
                    return subprocess.CompletedProcess(
                        cmd_list,
                        0,
                        stdout="multi-file output generated at: ...\nmanifest: " + str(reported_manifest) + "\n",
                        stderr="",
                    )
                if str(pytra_cli_mod.GEN_MAKEFILE) in " ".join(cmd_list):
                    self.assertEqual(Path(cmd_list[2]), reported_manifest)
                    makefile_path = workdir / "out" / "Makefile"
                    if "-o" in cmd_list:
                        idx = cmd_list.index("-o")
                        if idx + 1 < len(cmd_list):
                            makefile_path = Path(cmd_list[idx + 1])
                    makefile_path.parent.mkdir(parents=True, exist_ok=True)
                    makefile_path.write_text("all:\n\t@true\n", encoding="utf-8")
                    return subprocess.CompletedProcess(cmd_list, 0, stdout="generated: " + str(makefile_path), stderr="")
                if cmd_list and Path(cmd_list[0]).name == "make":
                    return subprocess.CompletedProcess(cmd_list, 0, stdout="make ok", stderr="")
                return subprocess.CompletedProcess(cmd_list, 0, stdout="", stderr="")

            with patch.object(pytra_cli_mod.subprocess, "run", side_effect=_runner):
                rc = pytra_cli_mod.main(
                    [
                        str(input_py),
                        "--target",
                        "cpp",
                        "--build",
                        "--output-dir",
                        str(workdir / "out"),
                    ]
                )

            self.assertEqual(rc, 0)
            self.assertTrue(any(str(pytra_cli_mod.GEN_MAKEFILE) in " ".join(call[0]) for call in calls))

    def test_build_cpp_codegen_opt_3_uses_linked_program_route(self) -> None:
        calls: list[tuple[list[str], str | None]] = []
        runner = self._fake_run(calls)

        with tempfile.TemporaryDirectory() as work:
            input_py = Path(work) / "hello.py"
            input_py.write_text("print(1)\\n", encoding="utf-8")
            with patch.object(pytra_cli_mod.subprocess, "run", side_effect=runner):
                rc = pytra_cli_mod.main(
                    [
                        str(input_py),
                        "--target",
                        "cpp",
                        "--build",
                        "--codegen-opt",
                        "3",
                        "--output-dir",
                        str(Path(work) / "out"),
                    ]
                )

        self.assertEqual(rc, 0)
        py2x_calls = [call[0] for call in calls if call[0] and str(pytra_cli_mod.PY2X) in " ".join(call[0])]
        self.assertEqual(len(py2x_calls), 2)
        self.assertIn("--link-only", py2x_calls[0])
        self.assertIn("--from-link-output", py2x_calls[1])
        self.assertNotIn("-O3", py2x_calls[0])
        self.assertIn("--east3-opt-level", py2x_calls[0])
        self.assertIn("2", py2x_calls[0])
        self.assertIn("--optimizer-option", py2x_calls[1])
        opt_idx = py2x_calls[1].index("--optimizer-option")
        self.assertEqual(py2x_calls[1][opt_idx + 1], "cpp_opt_level=2")
        self.assertTrue(any(str(pytra_cli_mod.GEN_MAKEFILE) in " ".join(call[0]) for call in calls))

    def test_build_cpp_codegen_opt_3_run_uses_make_run_fallback(self) -> None:
        calls: list[tuple[list[str], str | None]] = []
        runner = self._fake_run(calls)

        with tempfile.TemporaryDirectory() as work:
            input_py = Path(work) / "hello.py"
            input_py.write_text("print(1)\\n", encoding="utf-8")
            with patch.object(pytra_cli_mod.subprocess, "run", side_effect=runner):
                rc = pytra_cli_mod.main(
                    [
                        str(input_py),
                        "--target",
                        "cpp",
                        "--build",
                        "--run",
                        "--codegen-opt",
                        "3",
                        "--output-dir",
                        str(Path(work) / "out"),
                    ]
                )

        self.assertEqual(rc, 0)
        make_calls = [call[0] for call in calls if call[0] and Path(call[0][0]).name == "make"]
        self.assertEqual(len(make_calls), 2)
        self.assertEqual(make_calls[-1][-1], "run")

    def test_build_noncpp_target_is_supported(self) -> None:
        calls: list[tuple[list[str], str | None]] = []
        runner = self._fake_run(calls)
        with tempfile.TemporaryDirectory() as work:
            src = Path(work) / "case.py"
            src.write_text("print(1)\\n", encoding="utf-8")
            out_dir = Path(work) / "out_rs"
            with patch.object(pytra_cli_mod.subprocess, "run", side_effect=runner):
                rc = pytra_cli_mod.main([str(src), "--target", "rs", "--build", "--output-dir", str(out_dir)])
        self.assertEqual(rc, 0)
        self.assertTrue(any(call[0] and call[0][0] == "rustc" for call in calls))

    def test_build_cpp_rejects_output_with_build(self) -> None:
        with patch.object(pytra_cli_mod.subprocess, "run"):
            rc = pytra_cli_mod.main(
                [
                    "test/fixtures/core/top_level.py",
                    "--target",
                    "cpp",
                    "--build",
                    "--output",
                    "out/main.cpp",
                ]
            )
        self.assertEqual(rc, 1)

    def test_transpile_only_invokes_py2cpp(self) -> None:
        calls: list[tuple[list[str], str | None]] = []
        runner = self._fake_run(calls)
        with tempfile.TemporaryDirectory() as work:
            output = Path(work) / "main.cpp"
            with patch.object(pytra_cli_mod.subprocess, "run", side_effect=runner):
                rc = pytra_cli_mod.main(
                    ["test/fixtures/core/top_level.py", "--target", "cpp", "--output", str(output)]
                )
        self.assertEqual(rc, 0)
        self.assertIn(str(pytra_cli_mod.PY2X), " ".join(calls[0][0]))
        self.assertIn("--target", calls[0][0])
        self.assertIn("cpp", calls[0][0])

    def test_transpile_cpp_codegen_opt_3_uses_linked_program_route(self) -> None:
        calls: list[tuple[list[str], str | None]] = []
        runner = self._fake_run(calls)
        with tempfile.TemporaryDirectory() as work:
            src = Path(work) / "case.py"
            src.write_text("print(1)\\n", encoding="utf-8")
            out_dir = Path(work) / "out_cpp"
            with patch.object(pytra_cli_mod.subprocess, "run", side_effect=runner):
                rc = pytra_cli_mod.main(
                    [
                        str(src),
                        "--target",
                        "cpp",
                        "--codegen-opt",
                        "3",
                        "--output-dir",
                        str(out_dir),
                    ]
                )
        self.assertEqual(rc, 0)
        py2x_calls = [call[0] for call in calls if call[0] and str(pytra_cli_mod.PY2X) in " ".join(call[0])]
        self.assertEqual(len(py2x_calls), 2)
        self.assertIn("--link-only", py2x_calls[0])
        self.assertIn("--from-link-output", py2x_calls[1])
        self.assertNotIn("-O3", py2x_calls[0])

    def test_transpile_cpp_codegen_opt_3_rejects_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as work:
            src = Path(work) / "case.py"
            src.write_text("print(1)\\n", encoding="utf-8")
            with patch.object(pytra_cli_mod.subprocess, "run"):
                rc = pytra_cli_mod.main(
                    [
                        str(src),
                        "--target",
                        "cpp",
                        "--codegen-opt",
                        "3",
                        "--output",
                        str(Path(work) / "main.cpp"),
                    ]
                )
        self.assertEqual(rc, 1)

    def test_transpile_only_invokes_py2rs_with_explicit_output(self) -> None:
        calls: list[tuple[list[str], str | None]] = []
        runner = self._fake_run(calls)
        with tempfile.TemporaryDirectory() as work:
            output = Path(work) / "main.rs"
            with patch.object(pytra_cli_mod.subprocess, "run", side_effect=runner):
                rc = pytra_cli_mod.main(
                    ["test/fixtures/core/top_level.py", "--target", "rs", "--output", str(output)]
                )
        self.assertEqual(rc, 0)
        self.assertIn(str(pytra_cli_mod.PY2X), " ".join(calls[0][0]))
        self.assertIn("--target", calls[0][0])
        self.assertIn("rs", calls[0][0])
        self.assertIn("--output", calls[0][0])
        out_idx = calls[0][0].index("--output")
        self.assertEqual(calls[0][0][out_idx + 1], str(output))

    def test_transpile_rs_uses_output_dir_with_input_stem(self) -> None:
        calls: list[tuple[list[str], str | None]] = []
        runner = self._fake_run(calls)
        with tempfile.TemporaryDirectory() as work:
            src = Path(work) / "my_case.py"
            src.write_text("print(1)\\n", encoding="utf-8")
            out_dir = Path(work) / "out_rs"
            with patch.object(pytra_cli_mod.subprocess, "run", side_effect=runner):
                rc = pytra_cli_mod.main([str(src), "--target", "rs", "--output-dir", str(out_dir)])
            self.assertEqual(rc, 0)
            self.assertIn(str(pytra_cli_mod.PY2X), " ".join(calls[0][0]))
            self.assertIn("--target", calls[0][0])
            self.assertIn("rs", calls[0][0])
            out_idx = calls[0][0].index("--output")
            self.assertEqual(Path(calls[0][0][out_idx + 1]), out_dir / "my_case.rs")

    def test_transpile_scala_uses_output_dir_with_input_stem(self) -> None:
        calls: list[tuple[list[str], str | None]] = []
        runner = self._fake_run(calls)
        with tempfile.TemporaryDirectory() as work:
            src = Path(work) / "my_case.py"
            src.write_text("print(1)\\n", encoding="utf-8")
            out_dir = Path(work) / "out_scala"
            with patch.object(pytra_cli_mod.subprocess, "run", side_effect=runner):
                rc = pytra_cli_mod.main([str(src), "--target", "scala", "--output-dir", str(out_dir)])
            self.assertEqual(rc, 0)
            self.assertIn(str(pytra_cli_mod.PY2X), " ".join(calls[0][0]))
            self.assertIn("--target", calls[0][0])
            self.assertIn("scala", calls[0][0])
            out_idx = calls[0][0].index("--output")
            self.assertEqual(Path(calls[0][0][out_idx + 1]), out_dir / "my_case.scala")

    def test_codegen_opt_rejected_for_noncpp_target(self) -> None:
        with tempfile.TemporaryDirectory() as work:
            src = Path(work) / "case.py"
            src.write_text("print(1)\\n", encoding="utf-8")
            with patch.object(pytra_cli_mod.subprocess, "run"):
                rc = pytra_cli_mod.main([str(src), "--target", "rs", "--codegen-opt", "2"])
        self.assertEqual(rc, 1)

    def test_cpp_build_only_options_rejected_for_noncpp_build(self) -> None:
        with tempfile.TemporaryDirectory() as work:
            src = Path(work) / "case.py"
            src.write_text("print(1)\\n", encoding="utf-8")
            with patch.object(pytra_cli_mod.subprocess, "run"):
                rc = pytra_cli_mod.main(
                    [str(src), "--target", "rs", "--build", "--compiler", "clang++"]
                )
        self.assertEqual(rc, 1)

    def test_build_noncpp_run_command_keeps_stdout(self) -> None:
        with tempfile.TemporaryDirectory() as work:
            src = Path(work) / "case.py"
            src.write_text("print(1)\\n", encoding="utf-8")
            profile = pytra_cli_mod.TargetProfile(
                target="java",
                extension=".java",
                build_driver="noncpp",
                fixed_output_name="Main.java",
                allow_codegen_opt=False,
                runner_needs=("python", "javac", "java"),
            )
            args = argparse.Namespace(output="", output_dir=str(Path(work) / "out"), run=True)
            calls: list[bool] = []

            def _fake_run(
                cmd: list[str],
                cwd: Path | None = None,
                timeout: float | None = None,
                *,
                stdout_to_stderr: bool = False,
            ) -> int:
                _ = cmd
                _ = cwd
                _ = timeout
                calls.append(bool(stdout_to_stderr))
                return 0

            with patch.object(pytra_cli_mod, "_run_py2x_target", return_value=0), patch.object(
                pytra_cli_mod,
                "make_noncpp_build_plan",
                return_value=type("Plan", (), {"build_cmd": ["javac", "Main.java"], "run_cmd": ["java", "Main"]})(),
            ), patch.object(pytra_cli_mod, "_run", side_effect=_fake_run):
                rc = pytra_cli_mod._build_noncpp(src, profile, args, [])

        self.assertEqual(rc, 0)
        self.assertEqual(calls, [True, False])
