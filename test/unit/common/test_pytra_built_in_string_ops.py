from __future__ import annotations

import unittest

from src.pytra.built_in import string_ops as so


class BuiltInStringOpsTest(unittest.TestCase):
    def test_strip_family(self) -> None:
        self.assertEqual(so.py_lstrip("  x  "), "x  ")
        self.assertEqual(so.py_rstrip("  x  "), "  x")
        self.assertEqual(so.py_strip("  x  "), "x")
        self.assertEqual(so.py_strip_chars("__x__", "_"), "x")

    def test_prefix_suffix(self) -> None:
        self.assertTrue(so.py_startswith("abcdef", "abc"))
        self.assertFalse(so.py_startswith("abcdef", "abd"))
        self.assertTrue(so.py_endswith("abcdef", "def"))
        self.assertFalse(so.py_endswith("abcdef", "cef"))

    def test_find_rfind(self) -> None:
        self.assertEqual(so.py_find("banana", "na"), 2)
        self.assertEqual(so.py_find_window("banana", "na", 3, 6), 4)
        self.assertEqual(so.py_find("banana", "zz"), -1)
        self.assertEqual(so.py_rfind("banana", "na"), 4)
        self.assertEqual(so.py_rfind_window("banana", "na", 0, 4), 2)

    def test_replace(self) -> None:
        self.assertEqual(so.py_replace("banana", "na", "X"), "baXX")
        self.assertEqual(so.py_replace("abc", "", "X"), "abc")

    def test_join(self) -> None:
        self.assertEqual(so.py_join(",", []), "")
        self.assertEqual(so.py_join(",", ["a"]), "a")
        self.assertEqual(so.py_join(",", ["a", "b", "c"]), "a,b,c")

    def test_split(self) -> None:
        self.assertEqual(so.py_split("a,b,c", ",", -1), ["a", "b", "c"])
        self.assertEqual(so.py_split("a,b,c", ",", 1), ["a", "b,c"])
        self.assertEqual(so.py_split("abc", "", -1), ["abc"])

    def test_splitlines(self) -> None:
        self.assertEqual(so.py_splitlines("a\nb\r\nc"), ["a", "b", "c"])
        self.assertEqual(so.py_splitlines("x\n"), ["x", ""])

    def test_count(self) -> None:
        self.assertEqual(so.py_count("banana", "na"), 2)
        self.assertEqual(so.py_count("abc", ""), 4)


if __name__ == "__main__":
    unittest.main()
