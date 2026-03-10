from __future__ import annotations

import importlib.util
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
MODULE_PATH = ROOT / "tools" / "build_selfhost.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("build_selfhost", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to load build_selfhost module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BuildSelfhostToolTest(unittest.TestCase):
    def test_build_selfhost_transpile_cmd_targets_selfhost_entry(self) -> None:
        mod = _load_module()
        self.assertEqual(
            mod.build_selfhost_transpile_cmd(Path("/tmp/py2x-selfhost.py"), Path("/tmp/py2cpp.cpp")),
            [
                "python3",
                "/tmp/py2x-selfhost.py",
                "/tmp/py2x-selfhost.py",
                "--target",
                "cpp",
                "-o",
                "/tmp/py2cpp.cpp",
            ],
        )

    def test_build_selfhost_compile_cmd_includes_runtime_sources(self) -> None:
        mod = _load_module()
        cmd = mod.build_selfhost_compile_cmd(
            Path("/tmp/py2cpp.cpp"),
            Path("/tmp/py2cpp.out"),
            ["/tmp/runtime/a.cpp", "/tmp/runtime/b.cpp"],
        )
        self.assertEqual(
            cmd,
            [
                "g++",
                "-std=c++20",
                "-O2",
                "-Isrc",
                "-Isrc/runtime/cpp",
                "/tmp/py2cpp.cpp",
                "/tmp/runtime/a.cpp",
                "/tmp/runtime/b.cpp",
                "-o",
                "/tmp/py2cpp.out",
            ],
        )

    def test_runtime_cpp_sources_resolves_relative_runtime_paths(self) -> None:
        mod = _load_module()
        with patch.object(mod, "collect_runtime_cpp_sources", return_value=["src/runtime/cpp/a.cpp", "out/b.cpp"]):
            self.assertEqual(
                mod.runtime_cpp_sources(),
                [
                    str(ROOT / "src/runtime/cpp/a.cpp"),
                    str(ROOT / "out/b.cpp"),
                ],
            )

    def test_main_runs_transpile_then_compile_and_prints_binary(self) -> None:
        mod = _load_module()
        calls: list[list[str]] = []

        def _fake_run(cmd: list[str], cwd: Path | None = None) -> None:
            calls.append(cmd)

        stdout = io.StringIO()
        with patch.object(mod, "run", side_effect=_fake_run), patch.object(
            mod,
            "runtime_cpp_sources",
            return_value=["/tmp/runtime_a.cpp", "/tmp/runtime_b.cpp"],
        ), patch.object(sys, "stdout", stdout):
            rc = mod.main()

        self.assertEqual(rc, 0)
        self.assertEqual(calls[0], mod.build_selfhost_transpile_cmd(mod.SELFHOST_ENTRY, mod.CPP_OUT))
        self.assertEqual(
            calls[1],
            mod.build_selfhost_compile_cmd(
                mod.CPP_OUT,
                mod.BIN_OUT,
                ["/tmp/runtime_a.cpp", "/tmp/runtime_b.cpp"],
            ),
        )
        self.assertEqual(stdout.getvalue().strip(), str(mod.BIN_OUT))


if __name__ == "__main__":
    unittest.main()
