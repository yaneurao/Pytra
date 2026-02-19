"""pytra.std.dataclasses の最小互換テスト。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.pytra.std.dataclasses import dataclass


@dataclass
class Point:
    x: int
    y: int = 0


@dataclass
class MyError(Exception):
    category: str
    summary: str


class PylibDataclassesTest(unittest.TestCase):
    def test_init_defaults(self) -> None:
        p = Point(1)
        self.assertEqual(p.x, 1)
        self.assertEqual(p.y, 0)

    def test_repr_and_eq(self) -> None:
        a = Point(1, 2)
        b = Point(1, 2)
        c = Point(2, 1)
        self.assertEqual(repr(a), "Point(x=1, y=2)")
        self.assertTrue(a == b)
        self.assertFalse(a == c)

    def test_exception_subclass(self) -> None:
        e = MyError("kind", "message")
        self.assertEqual(e.category, "kind")
        self.assertEqual(e.summary, "message")


if __name__ == "__main__":
    unittest.main()

