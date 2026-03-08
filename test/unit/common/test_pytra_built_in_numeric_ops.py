from __future__ import annotations

import unittest

from src.pytra.built_in import numeric_ops as no


class BuiltInNumericOpsTest(unittest.TestCase):
    def test_sum(self) -> None:
        self.assertEqual(no.sum([]), 0)
        self.assertEqual(no.sum([1, 2, 3]), 6)
        self.assertEqual(no.sum([1.5, 2.0, 3.5]), 7.0)

    def test_min_max(self) -> None:
        self.assertEqual(no.py_min(5, 2), 2)
        self.assertEqual(no.py_max(5, 2), 5)
        self.assertEqual(no.py_min("b", "a"), "a")
        self.assertEqual(no.py_max("b", "a"), "b")


if __name__ == "__main__":
    unittest.main()
