"""Tests for normalization helpers in check_selfhost_cpp_diff.py."""

from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
MODULE_PATH = ROOT / "tools" / "check_selfhost_cpp_diff.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("check_selfhost_cpp_diff", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to load check_selfhost_cpp_diff module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CheckSelfhostCppDiffNormalizeTest(unittest.TestCase):
    def test_canonicalize_none_init_declaration(self) -> None:
        mod = _load_module()
        src = "    int64 r = int64(py_to_int64(/* none */));"
        out = mod._canonicalize_cpp_line(src)
        self.assertEqual(out, "    int64 r;")

    def test_canonicalize_perf_counter_float_cast(self) -> None:
        mod = _load_module()
        src = "float64 elapsed = py_to_float64(pytra::std::time::perf_counter() - start);"
        out = mod._canonicalize_cpp_line(src)
        self.assertEqual(out, "float64 elapsed = pytra::std::time::perf_counter() - start;")

    def test_load_expected_diff_cases_ignores_blank_and_comment(self) -> None:
        mod = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "expected.txt"
            p.write_text(
                "# comment\n\n"
                "test/fixtures/core/add.py\n"
                "  sample/py/01_mandelbrot.py  \n",
                encoding="utf-8",
            )
            got = mod._load_expected_diff_cases(p)
        self.assertEqual(
            got,
            {
                "test/fixtures/core/add.py",
                "sample/py/01_mandelbrot.py",
            },
        )

    def test_resolve_selfhost_target_auto_prefers_cpp_only_when_help_advertises_target(self) -> None:
        mod = _load_module()
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
        self.assertEqual(mod._resolve_selfhost_target(selfhost_bin, "bridge"), "bridge")

    def test_build_host_transpile_cmd_uses_py2x_selfhost_cpp_target(self) -> None:
        mod = _load_module()
        src = ROOT / "test" / "fixtures" / "core" / "add.py"
        out_cpp = Path("/tmp/out.cpp")
        self.assertEqual(
            mod.build_host_transpile_cmd(src, out_cpp),
            [
                "python3",
                str(ROOT / "src" / "py2x-selfhost.py"),
                str(src),
                "--target",
                "cpp",
                "-o",
                str(out_cpp),
            ],
        )

    def test_build_selfhost_diff_cmd_uses_bridge_driver_and_optional_target(self) -> None:
        mod = _load_module()
        src = ROOT / "test" / "fixtures" / "core" / "add.py"
        out_cpp = Path("/tmp/out.cpp")
        selfhost_bin = ROOT / "selfhost" / "py2cpp.out"
        bridge_tool = ROOT / "tools" / "selfhost_transpile.py"
        self.assertEqual(
            mod.build_selfhost_diff_cmd(src, out_cpp, selfhost_bin, "cpp", "bridge", bridge_tool),
            [
                "python3",
                str(bridge_tool),
                str(src),
                "-o",
                str(out_cpp),
                "--selfhost-bin",
                str(selfhost_bin),
                "--target",
                "cpp",
            ],
        )
        self.assertEqual(
            mod.build_selfhost_diff_cmd(src, out_cpp, selfhost_bin, "", "direct", bridge_tool),
            [
                str(selfhost_bin),
                str(src),
                "-o",
                str(out_cpp),
            ],
        )

    def test_stage2_diff_summary_row_maps_not_implemented_to_known_block(self) -> None:
        mod = _load_module()
        row = mod.build_stage2_diff_summary_row(
            "test/fixtures/core/add.py",
            "selfhost_not_implemented",
            "[not_implemented] bridge path is not ready",
        )
        self.assertEqual(row.top_level_category, "known_block")
        self.assertEqual(row.detail_category, "not_implemented")

    def test_stage2_diff_summary_row_maps_expected_diff_to_known_block(self) -> None:
        mod = _load_module()
        row = mod.build_stage2_diff_summary_row(
            "test/fixtures/core/add.py",
            "known_diff",
            "normalized artifact diff",
        )
        self.assertEqual(row.top_level_category, "known_block")
        self.assertEqual(row.detail_category, "known_block")

    def test_render_stage2_diff_summary_formats_shared_summary_line(self) -> None:
        mod = _load_module()
        row = mod.build_stage2_diff_summary_row(
            "test/fixtures/core/add.py",
            "artifact_diff",
            "normalized artifact diff",
        )
        buf = StringIO()
        with redirect_stdout(buf):
            for line in mod.render_summary_block("stage2_diff", [row], skip_pass=True):
                print(line)
        text = buf.getvalue()
        self.assertIn("[stage2_diff summary]", text)
        self.assertIn("subject=test/fixtures/core/add.py", text)
        self.assertIn("category=regression", text)
        self.assertIn("detail=stage2_diff_fail", text)


if __name__ == "__main__":
    unittest.main()
