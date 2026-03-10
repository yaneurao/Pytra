from __future__ import annotations

import importlib.util
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
MODULE_PATH = ROOT / "tools" / "build_selfhost_stage2.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("build_selfhost_stage2", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to load build_selfhost_stage2 module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BuildSelfhostStage2Test(unittest.TestCase):
    def test_build_stage1_transpile_cmd_targets_stage2_cpp(self) -> None:
        mod = _load_module()
        cmd = mod.build_stage1_transpile_cmd(mod.STAGE1_BIN, mod.STAGE1_SRC, mod.STAGE2_CPP)
        self.assertEqual(
            cmd,
            [
                str(mod.STAGE1_BIN),
                str(mod.STAGE1_SRC),
                "--target",
                "cpp",
                "-o",
                str(mod.STAGE2_CPP),
            ],
        )

    def test_should_reuse_stage1_cpp_only_for_not_implemented_failures(self) -> None:
        mod = _load_module()
        self.assertTrue(
            mod.should_reuse_stage1_cpp(
                subprocess.CompletedProcess(
                    args=["selfhost"],
                    returncode=1,
                    stdout="",
                    stderr="[not_implemented] stage1 fallback",
                )
            )
        )
        self.assertFalse(
            mod.should_reuse_stage1_cpp(
                subprocess.CompletedProcess(
                    args=["selfhost"],
                    returncode=1,
                    stdout="",
                    stderr="[input_invalid] unrelated failure",
                )
            )
        )
        self.assertFalse(
            mod.should_reuse_stage1_cpp(
                subprocess.CompletedProcess(
                    args=["selfhost"],
                    returncode=0,
                    stdout="[not_implemented]",
                    stderr="",
                )
            )
        )

    def test_build_stage2_compile_cmd_uses_stage2_cpp_and_runtime_sources(self) -> None:
        mod = _load_module()
        fake_sources = [
            "src/runtime/cpp/generated/std/json.cpp",
            "src/runtime/cpp/native/compiler/transpile_cli.cpp",
        ]
        with patch.object(mod, "collect_runtime_cpp_sources", return_value=fake_sources):
            cmd = mod.build_stage2_compile_cmd(mod.STAGE2_CPP)
        self.assertEqual(
            cmd,
            [
                "g++",
                "-std=c++20",
                "-O2",
                "-Isrc",
                "-Isrc/runtime/cpp",
                str(mod.STAGE2_CPP),
                str(mod.ROOT / "src/runtime/cpp/generated/std/json.cpp"),
                str(mod.ROOT / "src/runtime/cpp/native/compiler/transpile_cli.cpp"),
                "-o",
                str(mod.STAGE2_BIN),
            ],
        )


if __name__ == "__main__":
    unittest.main()
