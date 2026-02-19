from __future__ import annotations

import sys as std_sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in std_sys.path:
    std_sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in std_sys.path:
    std_sys.path.insert(0, str(ROOT / "src"))

from src.pylib.std import sys as py_sys


class PyLibSysTest(unittest.TestCase):
    def test_wrapper_exports(self) -> None:
        self.assertIsInstance(py_sys.argv, list)
        self.assertIsNotNone(py_sys.stderr)
        self.assertIsNotNone(py_sys.stdout)
        self.assertIsInstance(py_sys.path, list)

    def test_setters(self) -> None:
        old_argv = py_sys.argv
        old_path = py_sys.path
        try:
            py_sys.set_argv(["a", "b"])
            py_sys.set_path(["x"])
            self.assertEqual(py_sys.argv, ["a", "b"])
            self.assertEqual(py_sys.path, ["x"])
        finally:
            py_sys.set_argv(old_argv)
            py_sys.set_path(old_path)


if __name__ == "__main__":
    unittest.main()

