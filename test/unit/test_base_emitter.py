"""BaseEmitter の共通ユーティリティ回帰テスト。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.common.base_emitter import BaseEmitter


class _DummyEmitter(BaseEmitter):
    def emit_stmt(self, stmt: Any) -> None:
        self.emit(f"stmt:{self.any_to_str(stmt)}")


class BaseEmitterTest(unittest.TestCase):
    def test_emit_and_emit_stmt_list_and_next_tmp(self) -> None:
        em = _DummyEmitter({})
        em.emit("root")
        em.indent = 1
        em.emit("child")
        em.emit_stmt_list(["a", "b"])
        self.assertEqual(
            em.lines,
            [
                "root",
                "    child",
                "    stmt:a",
                "    stmt:b",
            ],
        )
        self.assertEqual(em.next_tmp(), "__tmp_1")
        self.assertEqual(em.next_tmp("v"), "v_2")

    def test_any_helpers(self) -> None:
        em = BaseEmitter({})
        self.assertEqual(em.any_dict_get({"x": 1}, "x", 9), 1)
        self.assertEqual(em.any_dict_get({"x": 1}, "y", 9), 9)
        self.assertEqual(em.any_dict_get(3, "x", 9), 9)

        self.assertEqual(em.any_to_dict({"a": 1}), {"a": 1})
        self.assertIsNone(em.any_to_dict([]))

        self.assertEqual(em.any_to_list([1, 2]), [1, 2])
        self.assertEqual(em.any_to_list({"x": 1}), [])

        self.assertEqual(em.any_to_str("abc"), "abc")
        self.assertEqual(em.any_to_str(10), "")

    def test_node_helpers(self) -> None:
        em = BaseEmitter({})
        self.assertTrue(em.is_name({"kind": "Name", "id": "x"}))
        self.assertTrue(em.is_name({"kind": "Name", "id": "x"}, "x"))
        self.assertFalse(em.is_name({"kind": "Name", "id": "x"}, "y"))
        self.assertFalse(em.is_name("x"))

        self.assertTrue(em.is_call({"kind": "Call"}))
        self.assertFalse(em.is_call({"kind": "Name"}))

        self.assertTrue(em.is_attr({"kind": "Attribute", "attr": "append"}))
        self.assertTrue(em.is_attr({"kind": "Attribute", "attr": "append"}, "append"))
        self.assertFalse(em.is_attr({"kind": "Attribute", "attr": "append"}, "pop"))
        self.assertFalse(em.is_attr({"kind": "Call"}, "append"))

        self.assertEqual(em.get_expr_type({"resolved_type": "int64"}), "int64")
        self.assertEqual(em.get_expr_type({"resolved_type": 3}), "")
        self.assertEqual(em.get_expr_type(None), "")

    def test_split_helpers(self) -> None:
        em = BaseEmitter({})
        self.assertEqual(em.split_generic(""), [])
        self.assertEqual(
            em.split_generic("dict[str, list[int64]], set[str], int64"),
            ["dict[str, list[int64]]", "set[str]", "int64"],
        )
        self.assertEqual(em.split_union("int64|str|None"), ["int64", "str", "None"])
        self.assertEqual(
            em.split_union("list[int64|str]|dict[str, list[int64|str]]|None"),
            ["list[int64|str]", "dict[str, list[int64|str]]", "None"],
        )

    def test_type_helpers(self) -> None:
        em = BaseEmitter({})
        self.assertEqual(em.normalize_type_name("byte"), "uint8")
        self.assertEqual(em.normalize_type_name("any"), "Any")
        self.assertEqual(em.normalize_type_name("object"), "object")
        self.assertEqual(em.normalize_type_name("int64"), "int64")
        self.assertEqual(em.normalize_type_name(1), "")

        self.assertTrue(em.is_any_like_type("Any"))
        self.assertTrue(em.is_any_like_type("object"))
        self.assertTrue(em.is_any_like_type("unknown"))
        self.assertTrue(em.is_any_like_type("str|Any|None"))
        self.assertFalse(em.is_any_like_type("str|int64"))

        self.assertTrue(em.is_list_type("list[int64]"))
        self.assertTrue(em.is_set_type("set[str]"))
        self.assertTrue(em.is_dict_type("dict[str, int64]"))
        self.assertFalse(em.is_list_type("str"))

        self.assertTrue(em.is_indexable_sequence_type("list[int64]"))
        self.assertTrue(em.is_indexable_sequence_type("str"))
        self.assertTrue(em.is_indexable_sequence_type("bytes"))
        self.assertTrue(em.is_indexable_sequence_type("bytearray"))
        self.assertFalse(em.is_indexable_sequence_type("dict[str, int64]"))

    def test_forbidden_object_receiver_rule(self) -> None:
        em = BaseEmitter({})
        self.assertTrue(em.is_forbidden_object_receiver_type("Any"))
        self.assertTrue(em.is_forbidden_object_receiver_type("object"))
        self.assertTrue(em.is_forbidden_object_receiver_type("int64|object|None"))
        self.assertTrue(em.is_forbidden_object_receiver_type("str|any"))
        self.assertFalse(em.is_forbidden_object_receiver_type("str|int64|None"))


if __name__ == "__main__":
    unittest.main()
