"""py2cpp の既知コード生成不具合を最小ケースで固定する回帰テスト。"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.py2cpp import load_east, transpile_to_cpp


class Py2CppCodegenIssueTest(unittest.TestCase):
    def test_branch_first_assignment_is_hoisted_before_if(self) -> None:
        src = """def choose_sep(use_default: bool) -> str:
    if use_default:
        item_sep = ","
        key_sep = ":"
    else:
        item_sep = ";"
        key_sep = "="
    return item_sep + key_sep
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "branch_scope.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east)

        self.assertIn("str item_sep;", cpp)
        self.assertIn("str key_sep;", cpp)
        self.assertIn("item_sep = \",\";", cpp)
        self.assertIn("key_sep = \":\";", cpp)
        self.assertIn("item_sep = \";\";", cpp)
        self.assertIn("key_sep = \"=\";", cpp)
        self.assertNotIn("str item_sep = \",\";", cpp)
        self.assertNotIn("str key_sep = \":\";", cpp)
        self.assertNotIn("str item_sep = \";\";", cpp)
        self.assertNotIn("str key_sep = \"=\";", cpp)
        self.assertIn("return py_to_string(item_sep + key_sep);", cpp)

    def test_optional_tuple_destructure_keeps_str_type(self) -> None:
        src = """def dump_like(indent: int | None, separators: tuple[str, str] | None) -> str:
    if separators is None:
        if indent is None:
            item_sep = ","
            key_sep = ":"
        else:
            item_sep = ","
            key_sep = ": "
    else:
        item_sep, key_sep = separators
    return item_sep + key_sep
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "optional_tuple.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east)

        self.assertNotIn("::std::any item_sep", cpp)
        self.assertNotIn("::std::any key_sep", cpp)
        self.assertNotIn("::std::get<0>(separators)", cpp)
        self.assertNotIn("::std::get<1>(separators)", cpp)
        self.assertIn("auto __tuple_", cpp)
        self.assertIn("= *(separators);", cpp)
        self.assertIn("item_sep", cpp)
        self.assertIn("key_sep", cpp)


if __name__ == "__main__":
    unittest.main()
