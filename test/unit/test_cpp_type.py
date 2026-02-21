"""Regression tests for CppEmitter.cpp_type/_cpp_type_text."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.py2cpp import CppEmitter


class CppTypeTest(unittest.TestCase):
    def test_union_optional_and_dedup(self) -> None:
        em = CppEmitter({"body": []}, emit_main=False)
        self.assertEqual(em._cpp_type_text("str|None"), "::std::optional<str>")
        self.assertEqual(em._cpp_type_text("list[int64]|None|None"), "::std::optional<list<int64>>")
        self.assertEqual(em._cpp_type_text("dict[str, int64]|None|None"), "::std::optional<dict<str, int64>>")
        self.assertEqual(em._cpp_type_text("int64|int64"), "int64")

    def test_union_any_and_bytes_priority(self) -> None:
        em = CppEmitter({"body": []}, emit_main=False)
        self.assertEqual(em._cpp_type_text("Any|None"), "object")
        self.assertEqual(em._cpp_type_text("bytes|bytearray|None"), "bytes")


if __name__ == "__main__":
    unittest.main()

