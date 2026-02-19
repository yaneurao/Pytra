from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.pylib.std import argparse as py_argparse


class PyLibArgparseTest(unittest.TestCase):
    def test_parse_positional_and_option(self) -> None:
        p = py_argparse.ArgumentParser("x")
        p.add_argument("input")
        p.add_argument("-o", "--output")
        p.add_argument("--pretty", action="store_true")
        ns = p.parse_args(["a.py", "-o", "out.cpp", "--pretty"])
        self.assertEqual(ns.input, "a.py")
        self.assertEqual(ns.output, "out.cpp")
        self.assertTrue(ns.pretty)

    def test_parse_choices(self) -> None:
        p = py_argparse.ArgumentParser("x")
        p.add_argument("input")
        p.add_argument("--mode", choices=["a", "b"], default="a")
        ns = p.parse_args(["in.py", "--mode", "b"])
        self.assertEqual(ns.mode, "b")


if __name__ == "__main__":
    unittest.main()

