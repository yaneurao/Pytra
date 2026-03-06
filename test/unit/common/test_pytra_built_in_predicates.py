from __future__ import annotations

import unittest

from src.pytra.built_in import predicates as pd


class BuiltInPredicatesTest(unittest.TestCase):
    def test_any(self) -> None:
        self.assertTrue(pd.py_any([0, "", 3]))
        self.assertFalse(pd.py_any([0, "", False]))

    def test_all(self) -> None:
        self.assertTrue(pd.py_all([1, "x", True]))
        self.assertFalse(pd.py_all([1, 0, True]))


if __name__ == "__main__":
    unittest.main()
