"""Regression tests that pin known py2cpp codegen issues with minimal cases."""

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

from src.py2cpp import CppEmitter, load_cpp_profile, load_east, transpile_to_cpp


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
        self.assertIn("return item_sep + key_sep;", cpp)

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

    def test_py2cpp_kind_lookup_is_centralized(self) -> None:
        src_text = (ROOT / "src" / "py2cpp.py").read_text(encoding="utf-8")
        bad_lines: list[str] = []
        line_no = 0
        for line in src_text.splitlines():
            line_no += 1
            if 'get("kind")' not in line:
                continue
            # Handle `kind` via `_dict_any_kind` / `_node_kind_from_dict`.
            if 'src.get("kind")' in line:
                continue
            bad_lines.append(f"{line_no}: {line.strip()}")
        self.assertEqual([], bad_lines, "\n".join(bad_lines))

    def test_method_bare_self_name_is_lowered_to_this_object(self) -> None:
        src = """class Box:
    def identity(self) -> "Box":
        return self
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "bare_self.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("return *this;", cpp)
        self.assertNotIn("return self;", cpp)

    def test_unknown_tuple_destructure_uses_auto_not_std_any(self) -> None:
        src = """from pytra.std import os

def f(p: str) -> None:
    root, ext = os.path.splitext(p)
    print(root, ext)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "tuple_unpack_auto.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east)

        self.assertIn("auto root = py_at(", cpp)
        self.assertIn("auto ext = py_at(", cpp)
        self.assertNotIn("::std::any root =", cpp)
        self.assertNotIn("::std::any ext =", cpp)

    def test_none_default_for_non_optional_param_uses_typed_default(self) -> None:
        src = """def f(x: int = None, y: str = None) -> int:
    return x
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "typed_default.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east)

        self.assertIn("int64 x = 0", cpp)
        self.assertIn("str()", cpp)
        self.assertNotIn("int64 x = ::std::nullopt", cpp)

    def test_list_constructor_same_typed_source_is_passthrough(self) -> None:
        src = """def f(xs: list[int]) -> list[int]:
    return list(xs)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "list_ctor_passthrough.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("return xs;", cpp)
        self.assertNotIn("return list(xs);", cpp)

    def test_int_cast_from_str_uses_py_to_int64(self) -> None:
        src = """def f(s: str) -> int:
    return int(s)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "int_cast_str.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("return py_to_int64(s);", cpp)

    def test_int_cast_with_base_uses_py_to_int64_base(self) -> None:
        src = """def f(s: str) -> int:
    return int(s, 16)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "int_cast_base.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("return py_to_int64_base(s, py_to_int64(16));", cpp)

    def test_from_import_symbol_call_uses_runtime_namespace(self) -> None:
        src = """from pytra.std.time import perf_counter

def f() -> float:
    return perf_counter()
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "from_import_symbol_call.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("return pytra::std::time::perf_counter();", cpp)

    def test_dict_get_on_object_value_dict_int_uses_typed_wrapper(self) -> None:
        src = """def f(d: dict[str, object]) -> int:
    x: int = d.get("k", 3)
    return x
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "dict_get_object_int.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("dict_get_int(", cpp)
        self.assertNotIn("py_dict_get_default(", cpp)

    def test_none_constant_for_any_like_uses_object_empty(self) -> None:
        src = """def f() -> object:
    x: object = None
    return x
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "none_object.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("object x = object{};", cpp)
        self.assertNotIn("make_object(1)", cpp)

    def test_list_any_object_element_is_not_double_boxed(self) -> None:
        src = """def f() -> list[object]:
    x: object = None
    return [x]
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "list_any_object.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("list<object>{x}", cpp)
        self.assertNotIn("make_object(x)", cpp)

    def test_py_assert_eq_with_object_args_does_not_rebox(self) -> None:
        src = """from pytra.utils.assertions import py_assert_eq

def f(x: object) -> None:
    py_assert_eq(x, x)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "py_assert_eq_object.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("py_assert_eq(x, x);", cpp)
        self.assertNotIn("py_assert_eq(make_object(x), make_object(x))", cpp)

    def test_infer_rendered_arg_type_uses_declared_var_type(self) -> None:
        em = CppEmitter({}, load_cpp_profile(), {})
        em.declared_var_types["x"] = "object"
        self.assertEqual(em._infer_rendered_arg_type("x", "unknown"), "object")
        self.assertEqual(em._infer_rendered_arg_type("(x)", ""), "object")
        self.assertEqual(em._infer_rendered_arg_type("x", "int64"), "int64")


if __name__ == "__main__":
    unittest.main()
