from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
MODULE_PATH = ROOT / "tools" / "selfhost_transpile.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("selfhost_transpile", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to load selfhost_transpile module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SelfhostTranspileToolTest(unittest.TestCase):
    def test_build_bridge_env_prepends_src_once(self) -> None:
        mod = _load_module()
        src_path = str((ROOT / "src").resolve())
        self.assertEqual(mod.build_bridge_env({})["PYTHONPATH"], src_path)
        self.assertEqual(
            mod.build_bridge_env({"PYTHONPATH": "/tmp/site"})["PYTHONPATH"],
            src_path + ":" + "/tmp/site",
        )
        self.assertEqual(
            mod.build_bridge_env({"PYTHONPATH": src_path + ":" + "/tmp/site"})["PYTHONPATH"],
            src_path + ":" + "/tmp/site",
        )

    def test_build_selfhost_commands_include_target_only_when_nonempty(self) -> None:
        mod = _load_module()
        base = mod.build_selfhost_cmd_base(Path("/tmp/py2cpp.out"), "cpp")
        self.assertEqual(base, ["/tmp/py2cpp.out", "--target", "cpp"])
        self.assertEqual(mod.build_selfhost_cmd_base(Path("/tmp/py2cpp.out"), ""), ["/tmp/py2cpp.out"])
        self.assertEqual(
            mod.build_selfhost_transpile_cmd(base, Path("/tmp/in.py"), Path("/tmp/out.cpp")),
            ["/tmp/py2cpp.out", "--target", "cpp", "/tmp/in.py", "-o", "/tmp/out.cpp"],
        )

    def test_build_python_to_east_json_cmd_uses_convert_path_bridge(self) -> None:
        mod = _load_module()
        cmd = mod.build_python_to_east_json_cmd(Path("/tmp/in.py"), Path("/tmp/out.east.json"))
        self.assertEqual(cmd[0], sys.executable)
        self.assertEqual(cmd[1], "-c")
        self.assertIn("convert_path", cmd[2])
        self.assertIn("parser_backend='self_hosted'", cmd[2])
        self.assertEqual(cmd[-2:], ["/tmp/in.py", "/tmp/out.east.json"])

    def test_main_uses_direct_json_passthrough_command(self) -> None:
        mod = _load_module()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            selfhost_bin = root / "py2cpp.out"
            input_json = root / "in.json"
            output_cpp = root / "out.cpp"
            selfhost_bin.write_text("", encoding="utf-8")
            input_json.write_text("{}", encoding="utf-8")
            calls: list[list[str]] = []

            def _fake_run(cmd, cwd=None, capture_output=False, text=False, env=None):
                calls.append(list(cmd))
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

            with patch.object(mod.subprocess, "run", side_effect=_fake_run), patch.object(
                mod, "_resolve_selfhost_target", return_value="cpp"
            ), patch.object(
                sys,
                "argv",
                [
                    "selfhost_transpile.py",
                    str(input_json),
                    "-o",
                    str(output_cpp),
                    "--selfhost-bin",
                    str(selfhost_bin),
                ],
            ):
                rc = mod.main()

            self.assertEqual(rc, 0)
            self.assertEqual(
                calls,
                [[str(selfhost_bin), "--target", "cpp", str(input_json), "-o", str(output_cpp)]],
            )

    def test_main_converts_python_to_east_json_before_selfhost(self) -> None:
        mod = _load_module()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            selfhost_bin = root / "py2cpp.out"
            input_py = root / "in.py"
            output_cpp = root / "out.cpp"
            selfhost_bin.write_text("", encoding="utf-8")
            input_py.write_text("print(1)\n", encoding="utf-8")
            calls: list[list[str]] = []
            envs: list[dict[str, str] | None] = []

            def _fake_run(cmd, cwd=None, capture_output=False, text=False, env=None):
                calls.append(list(cmd))
                envs.append(dict(env) if env is not None else None)
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

            with patch.object(mod.subprocess, "run", side_effect=_fake_run), patch.object(
                mod, "_resolve_selfhost_target", return_value=""
            ), patch.object(
                sys,
                "argv",
                [
                    "selfhost_transpile.py",
                    str(input_py),
                    "-o",
                    str(output_cpp),
                    "--selfhost-bin",
                    str(selfhost_bin),
                ],
            ):
                rc = mod.main()

            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 2)
            conv_cmd = calls[0]
            self.assertEqual(conv_cmd[0], sys.executable)
            self.assertIn("convert_path", conv_cmd[2])
            self.assertTrue(conv_cmd[-1].endswith("in.east.json"))
            self.assertIsNotNone(envs[0])
            self.assertIn(str((ROOT / "src").resolve()), envs[0]["PYTHONPATH"].split(":"))
            self.assertEqual(
                calls[1],
                [str(selfhost_bin), conv_cmd[-1], "-o", str(output_cpp)],
            )

    def test_main_returns_1_when_selfhost_binary_is_missing(self) -> None:
        mod = _load_module()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            input_json = root / "in.json"
            output_cpp = root / "out.cpp"
            missing_bin = root / "missing.out"
            input_json.write_text("{}", encoding="utf-8")
            with patch.object(
                mod, "_resolve_selfhost_target", return_value=""
            ), patch.object(
                sys,
                "argv",
                [
                    "selfhost_transpile.py",
                    str(input_json),
                    "-o",
                    str(output_cpp),
                    "--selfhost-bin",
                    str(missing_bin),
                ],
            ):
                self.assertEqual(mod.main(), 1)

    def test_main_rejects_non_python_non_json_input(self) -> None:
        mod = _load_module()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            selfhost_bin = root / "py2cpp.out"
            bad_input = root / "in.txt"
            output_cpp = root / "out.cpp"
            selfhost_bin.write_text("", encoding="utf-8")
            bad_input.write_text("x", encoding="utf-8")
            with patch.object(
                mod, "_resolve_selfhost_target", return_value=""
            ), patch.object(
                sys,
                "argv",
                [
                    "selfhost_transpile.py",
                    str(bad_input),
                    "-o",
                    str(output_cpp),
                    "--selfhost-bin",
                    str(selfhost_bin),
                ],
            ):
                self.assertEqual(mod.main(), 1)


if __name__ == "__main__":
    unittest.main()
