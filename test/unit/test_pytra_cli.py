"""Regression tests for src/pytra/cli.py."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import src.pytra.cli as pytra_cli_mod

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))


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
            if str(pytra_cli_mod.PY2CPP) in " ".join(cmd_list):
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
            with patch("src.pytra.cli.subprocess.run", side_effect=runner):
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
            self.assertTrue(any(str(pytra_cli_mod.PY2CPP) in item for item in calls[0][0]))
            self.assertTrue(any(str(pytra_cli_mod.GEN_MAKEFILE) in " ".join(call[0]) for call in calls))
            self.assertIn("make", rendered[2])

    def test_build_cpp_rejects_non_cpp_target(self) -> None:
        with patch("src.pytra.cli.subprocess.run"):
            rc = pytra_cli_mod.main(["test/fixtures/core/top_level.py", "--target", "rs", "--build"])
        self.assertEqual(rc, 1)

    def test_build_cpp_rejects_output_with_build(self) -> None:
        with patch("src.pytra.cli.subprocess.run"):
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
        with patch("src.pytra.cli.subprocess.run", side_effect=runner):
            rc = pytra_cli_mod.main(["test/fixtures/core/top_level.py", "--target", "cpp", "--output", "tmp/main.cpp"])
        self.assertEqual(rc, 0)
        self.assertIn(str(pytra_cli_mod.PY2CPP), " ".join(calls[0][0]))

    def test_transpile_only_invokes_py2rs_with_explicit_output(self) -> None:
        calls: list[tuple[list[str], str | None]] = []
        runner = self._fake_run(calls)
        with patch("src.pytra.cli.subprocess.run", side_effect=runner):
            rc = pytra_cli_mod.main(["test/fixtures/core/top_level.py", "--target", "rs", "--output", "tmp/main.rs"])
        self.assertEqual(rc, 0)
        self.assertIn(str(pytra_cli_mod.PY2RS), " ".join(calls[0][0]))
        self.assertIn("--output", calls[0][0])
        out_idx = calls[0][0].index("--output")
        self.assertEqual(calls[0][0][out_idx + 1], "tmp/main.rs")

    def test_transpile_rs_uses_output_dir_with_input_stem(self) -> None:
        calls: list[tuple[list[str], str | None]] = []
        runner = self._fake_run(calls)
        with tempfile.TemporaryDirectory() as work:
            src = Path(work) / "my_case.py"
            src.write_text("print(1)\\n", encoding="utf-8")
            out_dir = Path(work) / "out_rs"
            with patch("src.pytra.cli.subprocess.run", side_effect=runner):
                rc = pytra_cli_mod.main([str(src), "--target", "rs", "--output-dir", str(out_dir)])
            self.assertEqual(rc, 0)
            self.assertIn(str(pytra_cli_mod.PY2RS), " ".join(calls[0][0]))
            out_idx = calls[0][0].index("--output")
            self.assertEqual(Path(calls[0][0][out_idx + 1]), out_dir / "my_case.rs")
