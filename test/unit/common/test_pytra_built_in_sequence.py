from __future__ import annotations

import unittest

from src.pytra.built_in import sequence as seq


class BuiltInSequenceTest(unittest.TestCase):
    def test_py_range_positive_step(self) -> None:
        self.assertEqual(seq.py_range(0, 5, 2), [0, 2, 4])

    def test_py_range_negative_step(self) -> None:
        self.assertEqual(seq.py_range(5, -1, -2), [5, 3, 1])

    def test_py_range_zero_step(self) -> None:
        self.assertEqual(seq.py_range(0, 10, 0), [])

    def test_py_repeat(self) -> None:
        self.assertEqual(seq.py_repeat("ab", 3), "ababab")
        self.assertEqual(seq.py_repeat("ab", 0), "")


if __name__ == "__main__":
    unittest.main()
