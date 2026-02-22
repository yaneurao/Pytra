from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.pytra.std import re as py_re


class PyLibReTest(unittest.TestCase):
    def test_match_basic(self) -> None:
        m = py_re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$", "x = 1")
        self.assertIsNotNone(m)
        assert m is not None
        self.assertEqual(m.group(1), "x")
        self.assertEqual(m.group(2), "1")

    def test_sub_ws(self) -> None:
        out = py_re.sub(r"\s+", " ", "a   b\tc")
        self.assertEqual(out, "a b c")

    def test_import_regex_requires_whitespace_after_keyword(self) -> None:
        self.assertIsNotNone(py_re.match(r"^import\s+(.+)$", "import os"))
        self.assertIsNone(py_re.match(r"^import\s+(.+)$", "import_modules: dict[str, str] = {}"))


if __name__ == "__main__":
    unittest.main()
