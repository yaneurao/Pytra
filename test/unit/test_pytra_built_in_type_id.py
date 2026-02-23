import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.pytra.built_in import type_id as tid


class PytraBuiltInTypeIdTest(unittest.TestCase):
    def setUp(self) -> None:
        tid._py_reset_type_registry_for_test()

    def test_builtin_subtype_bool_is_int_and_object(self) -> None:
        self.assertTrue(tid.py_tid_is_subtype(tid._tid_bool(), tid._tid_int()))
        self.assertTrue(tid.py_tid_is_subtype(tid._tid_bool(), tid._tid_object()))
        self.assertFalse(tid.py_tid_is_subtype(tid._tid_int(), tid._tid_bool()))

    def test_register_class_type_and_subtype_chain(self) -> None:
        base = tid.py_tid_register_class_type([tid._tid_object()])
        child = tid.py_tid_register_class_type([base])
        self.assertTrue(tid.py_tid_is_subtype(child, base))
        self.assertTrue(tid.py_tid_is_subtype(child, tid._tid_object()))
        self.assertFalse(tid.py_tid_is_subtype(base, child))

    def test_runtime_type_id_for_builtin_values(self) -> None:
        self.assertEqual(tid.py_tid_runtime_type_id(None), tid._tid_none())
        self.assertEqual(tid.py_tid_runtime_type_id(True), tid._tid_bool())
        self.assertEqual(tid.py_tid_runtime_type_id(1), tid._tid_int())
        self.assertEqual(tid.py_tid_runtime_type_id(1.0), tid._tid_float())
        self.assertEqual(tid.py_tid_runtime_type_id("x"), tid._tid_str())
        self.assertEqual(tid.py_tid_runtime_type_id([1]), tid._tid_list())
        self.assertEqual(tid.py_tid_runtime_type_id({"a": 1}), tid._tid_dict())
        self.assertEqual(tid.py_tid_runtime_type_id({1}), tid._tid_set())

    def test_runtime_type_id_and_isinstance_for_user_class(self) -> None:
        base = tid.py_tid_register_class_type([tid._tid_object()])
        child = tid.py_tid_register_class_type([base])

        class ChildObj:
            PYTRA_TYPE_ID = child

        obj = ChildObj()
        self.assertEqual(tid.py_tid_runtime_type_id(obj), tid._tid_object())
        self.assertTrue(tid.py_tid_isinstance(obj, tid._tid_object()))
        self.assertFalse(tid.py_tid_isinstance(obj, child))
        self.assertFalse(tid.py_tid_isinstance(obj, base))
        self.assertFalse(tid.py_tid_isinstance(obj, tid._tid_dict()))


if __name__ == "__main__":
    unittest.main()
