from __future__ import annotations

import unittest

from src.pytra.built_in import contains as ct


class BuiltInContainsTest(unittest.TestCase):
    def test_dict_object(self) -> None:
        self.assertTrue(ct.py_contains_dict_object({"a": 1}, "a"))
        self.assertFalse(ct.py_contains_dict_object({"a": 1}, "b"))

    def test_list_object(self) -> None:
        self.assertTrue(ct.py_contains_list_object([1, "x", True], "x"))
        self.assertFalse(ct.py_contains_list_object([1, "x", True], "y"))

    def test_set_object(self) -> None:
        self.assertTrue(ct.py_contains_set_object([1, 2, 3], 2))
        self.assertFalse(ct.py_contains_set_object([1, 2, 3], 5))

    def test_str_object(self) -> None:
        self.assertTrue(ct.py_contains_str_object("banana", "na"))
        self.assertFalse(ct.py_contains_str_object("banana", "zz"))


if __name__ == "__main__":
    unittest.main()
