"""pylib.std.enum の最小互換テスト。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.pylib.std.enum import Enum, IntEnum, IntFlag


class Color(Enum):
    RED = 1
    BLUE = 2


class Status(IntEnum):
    OK = 0
    ERROR = 1


class Perm(IntFlag):
    READ = 1
    WRITE = 2
    EXEC = 4


class PylibEnumTest(unittest.TestCase):
    def test_enum_basic(self) -> None:
        self.assertTrue(Color.RED == Color.RED)
        self.assertFalse(Color.RED == Color.BLUE)

    def test_intenum_basic(self) -> None:
        self.assertTrue(Status.OK == 0)
        self.assertEqual(int(Status.ERROR), 1)

    def test_intflag_bitops(self) -> None:
        rw = Perm.READ | Perm.WRITE
        self.assertEqual(int(rw), 3)
        self.assertEqual(int(rw & Perm.WRITE), 2)
        self.assertEqual(int(rw ^ Perm.WRITE), 1)


if __name__ == "__main__":
    unittest.main()

