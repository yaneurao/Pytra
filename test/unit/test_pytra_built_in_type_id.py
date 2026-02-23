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
        self.assertTrue(tid.py_is_subtype(tid.PYTRA_TID_BOOL, tid.PYTRA_TID_INT))
        self.assertTrue(tid.py_is_subtype(tid.PYTRA_TID_BOOL, tid.PYTRA_TID_OBJECT))
        self.assertFalse(tid.py_is_subtype(tid.PYTRA_TID_INT, tid.PYTRA_TID_BOOL))

    def test_register_class_type_and_subtype_chain(self) -> None:
        base = tid.py_register_class_type([tid.PYTRA_TID_OBJECT])
        child = tid.py_register_class_type([base])
        self.assertTrue(tid.py_is_subtype(child, base))
        self.assertTrue(tid.py_is_subtype(child, tid.PYTRA_TID_OBJECT))
        self.assertFalse(tid.py_is_subtype(base, child))

    def test_runtime_type_id_for_builtin_values(self) -> None:
        self.assertEqual(tid.py_runtime_type_id(None), tid.PYTRA_TID_NONE)
        self.assertEqual(tid.py_runtime_type_id(True), tid.PYTRA_TID_BOOL)
        self.assertEqual(tid.py_runtime_type_id(1), tid.PYTRA_TID_INT)
        self.assertEqual(tid.py_runtime_type_id(1.0), tid.PYTRA_TID_FLOAT)
        self.assertEqual(tid.py_runtime_type_id("x"), tid.PYTRA_TID_STR)
        self.assertEqual(tid.py_runtime_type_id([1]), tid.PYTRA_TID_LIST)
        self.assertEqual(tid.py_runtime_type_id({"a": 1}), tid.PYTRA_TID_DICT)
        self.assertEqual(tid.py_runtime_type_id({1}), tid.PYTRA_TID_SET)

    def test_runtime_type_id_and_isinstance_for_user_class(self) -> None:
        base = tid.py_register_class_type([tid.PYTRA_TID_OBJECT])
        child = tid.py_register_class_type([base])

        class ChildObj:
            PYTRA_TYPE_ID = child

        obj = ChildObj()
        self.assertEqual(tid.py_runtime_type_id(obj), child)
        self.assertTrue(tid.py_isinstance(obj, child))
        self.assertTrue(tid.py_isinstance(obj, base))
        self.assertTrue(tid.py_isinstance(obj, tid.PYTRA_TID_OBJECT))
        self.assertFalse(tid.py_isinstance(obj, tid.PYTRA_TID_DICT))


if __name__ == "__main__":
    unittest.main()
