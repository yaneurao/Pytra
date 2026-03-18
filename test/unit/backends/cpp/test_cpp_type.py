"""Regression tests for CppEmitter.cpp_type/_cpp_type_text."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.backends.cpp.cli import CppEmitter
from src.toolchain.frontends.type_expr import parse_type_expr_text
from src.backends.cpp.emitter.header_builder import _header_cpp_type_from_east


class CppTypeTest(unittest.TestCase):
    def test_union_optional_and_dedup(self) -> None:
        em = CppEmitter({"body": []}, {}, emit_main=False)
        self.assertEqual(em._cpp_type_text("str|None"), "::std::optional<str>")
        self.assertEqual(em._cpp_type_text("list[int64]|None|None"), "::std::optional<list<int64>>")
        self.assertEqual(em._cpp_type_text("dict[str, int64]|None|None"), "::std::optional<dict<str, int64>>")
        self.assertEqual(em._cpp_type_text("int64|int64"), "int64")

    def test_union_any_and_bytes_priority(self) -> None:
        em = CppEmitter({"body": []}, {}, emit_main=False)
        self.assertEqual(em._cpp_type_text("Any|None"), "object")
        self.assertEqual(em._cpp_type_text("bytes|bytearray|None"), "bytes")

    def test_general_union_emits_std_variant(self) -> None:
        em = CppEmitter({"body": []}, {}, emit_main=False)
        self.assertEqual(em._cpp_type_text("int64|bool"), "::std::variant<int64, bool>")
        self.assertEqual(
            _header_cpp_type_from_east("int64|bool", set(), set()),
            "::std::variant<int64, bool>",
        )

    def test_list_type_text_can_switch_to_pyobj_model(self) -> None:
        em = CppEmitter({"body": []}, {}, emit_main=False)
        em.cpp_list_model = "pyobj"
        self.assertEqual(em._cpp_type_text("list[int64]"), "list<int64>")
        self.assertEqual(em._cpp_type_text("list[str]"), "list<str>")
        self.assertEqual(em._cpp_type_text("list[Any]"), "object")

    def test_deque_type_text_and_header_builder_lower_to_std_deque(self) -> None:
        em = CppEmitter({"body": []}, {}, emit_main=False)
        self.assertEqual(em._cpp_type_text("deque[float64]"), "::std::deque<float64>")
        self.assertEqual(
            _header_cpp_type_from_east("deque[float64]", set(), set()),
            "::std::deque<float64>",
        )

    def test_type_expr_path_emits_general_union_as_variant(self) -> None:
        em = CppEmitter({"body": []}, {}, emit_main=False)
        result = em.cpp_type(parse_type_expr_text("int | bool"))
        self.assertIn("variant", result)
        result2 = em.cpp_signature_type(parse_type_expr_text("list[int | bool]"))
        self.assertIn("variant", result2)


if __name__ == "__main__":
    unittest.main()
