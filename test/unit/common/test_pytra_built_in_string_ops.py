from __future__ import annotations

import unittest

from src.pytra.built_in import string_ops as so


class BuiltInStringOpsTest(unittest.TestCase):
    def test_strip_family(self) -> None:
        self.assertEqual(so.py_bi_lstrip("  x  "), "x  ")
        self.assertEqual(so.py_bi_rstrip("  x  "), "  x")
        self.assertEqual(so.py_bi_strip("  x  "), "x")
        self.assertEqual(so.py_bi_strip_chars("__x__", "_"), "x")

    def test_prefix_suffix(self) -> None:
        self.assertTrue(so.py_bi_startswith("abcdef", "abc"))
        self.assertFalse(so.py_bi_startswith("abcdef", "abd"))
        self.assertTrue(so.py_bi_endswith("abcdef", "def"))
        self.assertFalse(so.py_bi_endswith("abcdef", "cef"))

    def test_find_rfind(self) -> None:
        self.assertEqual(so.py_bi_find("banana", "na"), 2)
        self.assertEqual(so.py_bi_find_window("banana", "na", 3, 6), 4)
        self.assertEqual(so.py_bi_find("banana", "zz"), -1)
        self.assertEqual(so.py_bi_rfind("banana", "na"), 4)
        self.assertEqual(so.py_bi_rfind_window("banana", "na", 0, 4), 2)

    def test_replace(self) -> None:
        self.assertEqual(so.py_bi_replace("banana", "na", "X"), "baXX")
        self.assertEqual(so.py_bi_replace("abc", "", "X"), "abc")


if __name__ == "__main__":
    unittest.main()
