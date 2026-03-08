from __future__ import annotations

import unittest

from src.pytra.built_in import zip_ops as zo


class BuiltInZipOpsTest(unittest.TestCase):
    def test_zip_pairs_until_shorter_side(self) -> None:
        self.assertEqual(zo.zip([], []), [])
        self.assertEqual(zo.zip([1, 2, 3], ["a", "b"]), [(1, "a"), (2, "b")])

    def test_zip_preserves_tuple_types(self) -> None:
        pairs = zo.zip(["x", "y"], [10, 20, 30])
        self.assertEqual(pairs, [("x", 10), ("y", 20)])


if __name__ == "__main__":
    unittest.main()
