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

    def test_ifexp_ternary_is_rendered_in_all_expression_positions(self) -> None:
        src = """def pick(flag: bool) -> int:
    x: int = 10 if flag else 20
    return x if flag else (x + 1)

def passthrough(v: int) -> int:
    return v

def as_arg(flag: bool) -> int:
    return passthrough(30 if flag else 40)

def as_list(flag: bool) -> list[int]:
    return [1 if flag else 2, 3]

def as_dict(flag: bool) -> dict[str, int]:
    return {"k": (5 if flag else 7)}
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "ifexp_regression.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertNotIn("( ?  : )", cpp)
        self.assertIn("? 10 : 20", cpp)
        self.assertIn("? x : x + 1", cpp)
        self.assertIn("passthrough((flag ? 30 : 40))", cpp)
        self.assertIn("list<int64>{(flag ? 1 : 2), 3}", cpp)
        self.assertIn("dict<str, int64>{{\"k\", (flag ? 5 : 7)}}", cpp)

    def test_dataclass_field_order_is_preserved_in_class_layout_and_ctor(self) -> None:
        src = """from dataclasses import dataclass

@dataclass
class Token:
    kind: str
    text: str
    pos: int

def make_token() -> Token:
    return Token("IDENT", "name", 3)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "dataclass_field_order.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        i_kind = cpp.find("str kind;")
        i_text = cpp.find("str text;")
        i_pos = cpp.find("int64 pos;")
        self.assertTrue(i_kind >= 0 and i_text >= 0 and i_pos >= 0)
        self.assertTrue(i_kind < i_text < i_pos)
        self.assertIn("Token(str kind, str text, int64 pos)", cpp)
        self.assertIn("::rc_new<Token>(\"IDENT\", \"name\", 3)", cpp)

    def test_yield_function_is_lowered_to_list_accumulation(self) -> None:
        src = """def gen(n: int) -> int:
    i: int = 0
    while i < n:
        yield i
        i += 1
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "yield_gen.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("list<int64> gen(int64 n)", cpp)
        self.assertIn("list<int64> __yield_values", cpp)
        self.assertIn("__yield_values", cpp)
        self.assertIn(".append(i);", cpp)
        self.assertIn("return __yield_values", cpp)

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

    def test_unknown_receiver_field_access_uses_obj_to_rc_or_raise(self) -> None:
        src = """class Box:
    v: int
    def __init__(self, v: int):
        self.v = v
    def read_from_unknown(self, other) -> int:
        return other.v
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "unknown_receiver_field.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn('return obj_to_rc_or_raise<Box>(other, "Box.v")->v;', cpp)
        self.assertNotIn("return py_obj_cast<Box>(other)->v;", cpp)

    def test_any_to_refclass_annassign_uses_obj_to_rc_or_raise(self) -> None:
        src = """from dataclasses import dataclass

@dataclass
class Box:
    v: int

def f(x: object) -> int:
    y: Box = x
    return y.v
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "any_to_ref_annassign.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn('rc<Box> y = obj_to_rc_or_raise<Box>(x, "annassign:y");', cpp)

    def test_any_to_refclass_return_uses_obj_to_rc_or_raise(self) -> None:
        src = """from dataclasses import dataclass

@dataclass
class Box:
    v: int

def f(x: object) -> Box:
    return x
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "any_to_ref_return.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn('return obj_to_rc_or_raise<Box>(x, "return:Box");', cpp)

    def test_any_to_refclass_call_arg_uses_obj_to_rc_or_raise(self) -> None:
        src = """from dataclasses import dataclass

@dataclass
class Box:
    v: int

def take_box(b: Box) -> int:
    return b.v

def f(x: object) -> int:
    return take_box(x)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "any_to_ref_call_arg.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn('return take_box(obj_to_rc_or_raise<Box>(x, "call_arg:Box"));', cpp)

    def test_nested_def_inside_method_remains_local_lambda(self) -> None:
        src = """class Box:
    def inc(self, x: int) -> int:
        def inner(y: int) -> int:
            return y + 1
        return inner(x)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "nested_def_in_method.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("int64 inc(int64 x)", cpp)
        self.assertIn("auto inner = [&](", cpp)
        self.assertNotIn("int64 inner(int64 y)", cpp)

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

    def test_dynamic_tuple_index_falls_back_to_py_at(self) -> None:
        src = """def pick(i: int) -> object:
    t: tuple[int, int, int] = (10, 20, 30)
    return t[i]
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "tuple_dynamic_index.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("py_at(t, py_to_int64(i))", cpp)

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

    def test_dict_get_typed_none_default_uses_value_default(self) -> None:
        src = """def f(d: dict[str, int]) -> int:
    return d.get("k", None)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "dict_get_typed_none.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn('d.get(py_to_string("k"), int64())', cpp)
        self.assertNotIn('d.get(py_to_string("k"), ::std::nullopt)', cpp)

    def test_dict_get_object_none_default_in_annassign_uses_typed_default(self) -> None:
        src = """def f(d: dict[str, object]) -> int:
    x: int = d.get("k", None)
    return x
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "dict_get_object_none_annassign.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn('int64 x = dict_get_node(d, "k", 0);', cpp)
        self.assertNotIn('int64 x = dict_get_node(d, "k", ::std::nullopt);', cpp)

    def test_dict_get_object_none_default_in_return_uses_typed_default(self) -> None:
        src = """def f(d: dict[str, object]) -> int:
    return d.get("k", None)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "dict_get_object_none_return.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn('return dict_get_node(d, "k", 0);', cpp)
        self.assertNotIn('return dict_get_node(d, "k", ::std::nullopt);', cpp)

    def test_annassign_dict_object_value_is_not_reboxed(self) -> None:
        src = """def f(x: object) -> dict[str, object]:
    d: dict[str, object] = {"k": x}
    return d
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "dict_object_annassign_no_rebox.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn('dict<str, object> d = dict<str, object>{{"k", x}};', cpp)
        self.assertNotIn('dict<str, object> d = dict<str, object>{{"k", make_object(x)}};', cpp)

    def test_optional_dict_object_get_int_uses_typed_wrapper(self) -> None:
        src = """def f(d: dict[str, object] | None) -> int:
    return d.get("k", 3)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "optional_dict_object_get_int.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn('return dict_get_int(d, "k", py_to_int64(3));', cpp)
        self.assertNotIn('return d.get("k", 3);', cpp)

    def test_optional_dict_object_get_bool_uses_typed_wrapper(self) -> None:
        src = """def f(d: dict[str, object] | None) -> bool:
    return d.get("k", True)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "optional_dict_object_get_bool.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn('return dict_get_bool(d, "k", true);', cpp)
        self.assertNotIn('return d.get("k", true);', cpp)

    def test_optional_dict_object_get_str_uses_typed_wrapper(self) -> None:
        src = """def f(d: dict[str, object] | None) -> str:
    return d.get("k", "x")
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "optional_dict_object_get_str.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn('return dict_get_str(d, "k", "x");', cpp)
        self.assertNotIn('return py_dict_get_default(d, "k", "x");', cpp)

    def test_optional_dict_object_get_float_uses_typed_wrapper(self) -> None:
        src = """def f(d: dict[str, object] | None) -> float:
    return d.get("k", 1.25)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "optional_dict_object_get_float.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn('return dict_get_float(d, "k", py_to_float64(1.25));', cpp)
        self.assertNotIn('return py_dict_get_default(d, "k", 1.25);', cpp)

    def test_optional_dict_object_get_list_uses_list_wrapper(self) -> None:
        src = """def f(d: dict[str, object] | None) -> list[int]:
    return d.get("k", [1, 2])
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "optional_dict_object_get_list.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn('return dict_get_list(d, "k", list<int64>{1, 2});', cpp)
        self.assertNotIn('return py_dict_get_default(d, "k", make_object(list<int64>{1, 2}));', cpp)

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
        self.assertEqual(em.infer_rendered_arg_type("x", "unknown", em.declared_var_types), "object")
        self.assertEqual(em.infer_rendered_arg_type("(x)", "", em.declared_var_types), "object")
        self.assertEqual(em.infer_rendered_arg_type("x", "int64", em.declared_var_types), "int64")

    def test_box_expr_for_any_uses_declared_type_hint_for_unknown_source(self) -> None:
        em = CppEmitter({}, load_cpp_profile(), {})
        em.declared_var_types["x"] = "object"
        # source_node が unknown でも、rendered text から object 型を推定できる場合は再 boxing しない。
        self.assertEqual("x", em._box_expr_for_any("x", {}))
        self.assertEqual("make_object(y)", em._box_expr_for_any("y", {}))

    def test_control_flow_brace_policy_uses_cpp_hooks(self) -> None:
        src = """def f(flag: bool, xs: list[tuple[int, int]]) -> int:
    total: int = 0
    if flag:
        total += 1
    else:
        total += 2
    for i in range(0, 3, 1):
        total += i
    for a, b in xs:
        total += a + b
    return total
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "control_flow_braces.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)
        lines = cpp.splitlines()
        if_lines = [line.strip() for line in lines if line.strip().startswith("if (flag)")]
        self.assertEqual(if_lines, ["if (flag)"])
        range_lines = [line.strip() for line in lines if line.strip().startswith("for (int64 i = 0; i < 3; ++i)")]
        self.assertEqual(range_lines, ["for (int64 i = 0; i < 3; ++i)"])
        unpack_lines = [line.strip() for line in lines if line.strip().startswith("for (auto __it_")]
        self.assertEqual(len(unpack_lines), 1)
        self.assertTrue(unpack_lines[0].endswith("{"))

    def test_control_flow_defaults_keep_hook_parity_when_dynamic_hooks_disabled(self) -> None:
        src = """def f(flag: bool) -> int:
    total: int = 0
    if flag:
        total += 1
    else:
        total += 2
    for i in range(0, 3, 1):
        total += i
    return total
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "control_flow_defaults.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)

        def _walk(node: object) -> list[dict[str, object]]:
            out: list[dict[str, object]] = []
            if isinstance(node, dict):
                out.append(node)
                for value in node.values():
                    out.extend(_walk(value))
                return out
            if isinstance(node, list):
                for item in node:
                    out.extend(_walk(item))
            return out

        for node in _walk(east):
            if node.get("kind") == "ForRange":
                node["range_mode"] = "dynamic"

        emitter = CppEmitter(east, {}, emit_main=False)
        emitter.set_dynamic_hooks_enabled(False)
        cpp = emitter.transpile()
        lines = cpp.splitlines()
        if_lines = [line.strip() for line in lines if line.strip().startswith("if (flag)")]
        self.assertEqual(if_lines, ["if (flag)"])
        range_lines = [line.strip() for line in lines if line.strip().startswith("for (int64 i = 0; i < 3; ++i)")]
        self.assertEqual(range_lines, ["for (int64 i = 0; i < 3; ++i)"])
        self.assertNotIn("? i < 3 : i > 3", cpp)

    def test_for_object_uses_runtime_protocol_py_dyn_range(self) -> None:
        src = """def f(x: object) -> int:
    s: int = 0
    for v in x:
        s += int(v)
    return s
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "for_object_runtime_protocol.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("for (object v : py_dyn_range(x))", cpp)
        self.assertNotIn("for (auto& v : x)", cpp)

    def test_for_list_keeps_static_fastpath(self) -> None:
        src = """def f(xs: list[int]) -> int:
    s: int = 0
    for v in xs:
        s += v
    return s
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "for_list_static_fastpath.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("for (int64 v : xs)", cpp)
        self.assertNotIn("py_dyn_range(xs)", cpp)

    def test_for_without_iter_mode_keeps_legacy_static_fastpath(self) -> None:
        src = """def f(xs):
    s = 0
    for v in xs:
        s = s + v
    return s
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "for_legacy_without_iter_mode.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            for_node: dict[str, object] | None = None
            mod_body = east.get("body", [])
            if isinstance(mod_body, list):
                for top in mod_body:
                    if not isinstance(top, dict) or top.get("kind") != "FunctionDef":
                        continue
                    fn_body = top.get("body", [])
                    if not isinstance(fn_body, list):
                        continue
                    for stmt in fn_body:
                        if isinstance(stmt, dict) and stmt.get("kind") == "For":
                            for_node = stmt
                            break
                    if for_node is not None:
                        break
            self.assertIsNotNone(for_node)
            if for_node is None:
                return
            for_node.pop("iter_mode", None)
            iter_expr = for_node.get("iter")
            if isinstance(iter_expr, dict):
                iter_expr.pop("iterable_trait", None)
                iter_expr.pop("iter_protocol", None)
                iter_expr.pop("iter_element_type", None)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("for (object v : xs)", cpp)
        self.assertNotIn("py_dyn_range(xs)", cpp)

    def test_isinstance_builtin_lowers_to_type_id_runtime_api(self) -> None:
        src = """def f(x: object) -> bool:
    return isinstance(x, int)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "isinstance_builtin.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("return py_isinstance(x, PYTRA_TID_INT);", cpp)
        self.assertNotIn("return py_is_int(x);", cpp)

    def test_any_boundary_builtin_names_route_to_obj_core_runtime_api(self) -> None:
        src = """def f_bool(x: object) -> bool:
    return bool(x)

def f_len(x: object) -> int:
    return len(x)

def f_str(x: object) -> str:
    return str(x)

def f_iter(x: object) -> object:
    return iter(x)

def f_next(it: object) -> object:
    return next(it)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "any_boundary_builtin_names.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("return py_to_bool(x);", cpp)
        self.assertIn("return py_len(x);", cpp)
        self.assertIn("return py_to_string(x);", cpp)
        self.assertIn("return make_object(py_iter_or_raise(x));", cpp)
        self.assertIn("return make_object(py_next_or_stop(it));", cpp)
        self.assertNotIn("return bool(x);", cpp)

    def test_isinstance_set_lowers_to_set_type_id_runtime_api(self) -> None:
        src = """def f(x: object) -> bool:
    return isinstance(x, set)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "isinstance_set.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("return py_isinstance(x, PYTRA_TID_SET);", cpp)
        self.assertNotIn("return isinstance(", cpp)

    def test_isinstance_tuple_lowers_to_or_of_type_id_checks(self) -> None:
        src = """class Base:
    def __init__(self):
        pass

class Child(Base):
    def __init__(self):
        super().__init__()

def f(x: object) -> bool:
    return isinstance(x, (int, Base, Child, dict, object))
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "isinstance_tuple.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("py_isinstance(x, PYTRA_TID_INT)", cpp)
        self.assertIn("py_isinstance(x, Base::PYTRA_TYPE_ID)", cpp)
        self.assertIn("py_isinstance(x, Child::PYTRA_TYPE_ID)", cpp)
        self.assertIn("py_isinstance(x, PYTRA_TID_DICT)", cpp)
        self.assertIn("py_isinstance(x, PYTRA_TID_OBJECT)", cpp)
        self.assertNotIn("return isinstance(", cpp)

    def test_gc_class_emits_type_id_and_isinstance_uses_runtime_api(self) -> None:
        src = """class Base:
    def __init__(self):
        pass

class Child(Base):
    def __init__(self):
        super().__init__()

def f(x: object) -> bool:
    return isinstance(x, Base) or isinstance(x, Child)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "isinstance_class.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("inline static uint32 PYTRA_TYPE_ID = py_register_class_type", cpp)
        self.assertIn("this->set_type_id(PYTRA_TYPE_ID);", cpp)
        self.assertIn("inline static uint32 PYTRA_TYPE_ID = py_register_class_type(list<uint32>{PYTRA_TID_OBJECT});", cpp)
        self.assertIn("inline static uint32 PYTRA_TYPE_ID = py_register_class_type(list<uint32>{Base::PYTRA_TYPE_ID});", cpp)
        self.assertIn("return (py_isinstance(x, Base::PYTRA_TYPE_ID)) || (py_isinstance(x, Child::PYTRA_TYPE_ID));", cpp)
        self.assertIn("virtual bool py_isinstance_of(uint32 expected_type_id) const override {", cpp)
        self.assertIn("if (expected_type_id == PYTRA_TID_OBJECT) return true;", cpp)
        self.assertIn("if (expected_type_id == PYTRA_TYPE_ID) return true;", cpp)
        self.assertIn("if (Base::py_isinstance_of(expected_type_id)) return true;", cpp)

    def test_inheritance_methods_are_emitted_as_virtual_with_override(self) -> None:
        src = """class Base:\n    def inc(self, x: int) -> int:\n        return x + 1\n\nclass Child(Base):\n    def inc(self, x: int) -> int:\n        return x + 2\n\n    def base_only(self, x: int) -> int:\n        return x\n"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "virtual_override.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("virtual int64 inc(int64 x) {", cpp)
        self.assertIn("int64 inc(int64 x) override {", cpp)
        self.assertIn("int64 base_only(int64 x) {", cpp)
        self.assertNotIn("virtual int64 inc(int64 x) override {", cpp)

    def test_non_overridden_base_methods_are_not_virtual(self) -> None:
        src = """class Base:\n    def inc(self, x: int) -> int:\n        return x + 1\n\n    def unused(self, x: int) -> int:\n        return x\n\nclass Child(Base):\n    def inc(self, x: int) -> int:\n        return x + 2\n"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "virtual_no_override.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("virtual int64 inc(int64 x) {", cpp)
        self.assertNotIn("virtual int64 unused(int64 x) {", cpp)


if __name__ == "__main__":
    unittest.main()
