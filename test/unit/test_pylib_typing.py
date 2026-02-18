from __future__ import annotations

import sys as std_sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in std_sys.path:
    std_sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in std_sys.path:
    std_sys.path.insert(0, str(ROOT / "src"))

from src.pylib import typing as py_typing


class PyLibTypingTest(unittest.TestCase):
    def test_exports_exist(self) -> None:
        self.assertIsNotNone(py_typing.Any)
        self.assertIsNotNone(py_typing.List)
        self.assertIsNotNone(py_typing.Set)
        self.assertIsNotNone(py_typing.Dict)
        self.assertIsNotNone(py_typing.Tuple)
        self.assertIsNotNone(py_typing.Iterable)
        self.assertIsNotNone(py_typing.Optional)
        self.assertIsNotNone(py_typing.Union)
        self.assertIsNotNone(py_typing.Callable)

    def test_typevar_callable(self) -> None:
        t = py_typing.TypeVar("T")
        self.assertIsNotNone(t)


if __name__ == "__main__":
    unittest.main()

