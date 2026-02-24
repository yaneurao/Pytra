"""Tests for normalization helpers in check_selfhost_cpp_diff.py."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
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


if __name__ == "__main__":
    unittest.main()
