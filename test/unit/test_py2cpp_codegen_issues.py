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

        self.assertTrue(
            ('return obj_to_rc_or_raise<Box>(other, "Box.v")->v;' in cpp)
            or ('return obj_to_rc_or_raise<Box>(make_object(other), "Box.v")->v;' in cpp)
        )
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

        self.assertTrue(
            ('rc<Box> y = obj_to_rc_or_raise<Box>(x, "annassign:y");' in cpp)
            or ('rc<Box> y = obj_to_rc_or_raise<Box>(x, "east3_unbox");' in cpp)
        )

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

        self.assertTrue(
            ("return py_to_int64_base(s, py_to_int64(16));" in cpp)
            or ("return py_to_int64_base(s, py_to<int64>(16));" in cpp)
        )

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

    def test_perf_counter_float_assign_avoids_redundant_float_unbox(self) -> None:
        src = """from pytra.std.time import perf_counter

def f() -> float:
    start: float = perf_counter()
    elapsed: float = perf_counter() - start
    return elapsed
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "perf_counter_float_assign.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("float64 start = pytra::std::time::perf_counter();", cpp)
        self.assertIn("float64 elapsed = pytra::std::time::perf_counter() - start;", cpp)
        self.assertNotIn("py_to<float64>(pytra::std::time::perf_counter()", cpp)
        self.assertNotIn("py_to<float64>(pytra::std::time::perf_counter() - start)", cpp)

    def test_float_div_uses_direct_slash_fastpath(self) -> None:
        src = """def f(a: float, b: float) -> float:
    return a / b
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "float_div_direct.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("return a / b;", cpp)
        self.assertNotIn("py_div(a, b)", cpp)

    def test_mixed_float_int_div_uses_direct_slash_after_promotion(self) -> None:
        src = """def f(a: float, b: int) -> float:
    return a / b
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "float_int_div.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("return a / py_to<float64>(b);", cpp)
        self.assertNotIn("py_div(", cpp)

    def test_int_div_uses_direct_slash_after_promotion(self) -> None:
        src = """def f(a: int, b: int) -> float:
    return a / b
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "int_div.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("return py_to<float64>(a) / py_to<float64>(b);", cpp)
        self.assertNotIn("py_div(", cpp)

    def test_unknown_div_keeps_py_div(self) -> None:
        src = """def f(a, b):
    return a / b
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "unknown_div.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("return py_div(a, b);", cpp)

    def test_sample18_perf_counter_is_typed_without_redundant_cast(self) -> None:
        src_py = ROOT / "sample" / "py" / "18_mini_language_interpreter.py"
        east = load_east(src_py)
        cpp = transpile_to_cpp(east)
        self.assertIn("pytra::std::time::perf_counter()", cpp)
        self.assertNotIn("py_to<float64>(pytra::std::time::perf_counter()", cpp)

    def test_sample18_charclass_avoids_redundant_str_cast(self) -> None:
        src_py = ROOT / "sample" / "py" / "18_mini_language_interpreter.py"
        east = load_east(src_py)
        cpp = transpile_to_cpp(east)
        self.assertIn("if (ch.isdigit()) {", cpp)
        self.assertIn("(source[i].isdigit())", cpp)
        self.assertNotIn("str(ch).isdigit()", cpp)
        self.assertNotIn("str(source[i]).isdigit()", cpp)

    def test_sample18_rc_new_avoids_redundant_rc_cast(self) -> None:
        src_py = ROOT / "sample" / "py" / "18_mini_language_interpreter.py"
        east = load_east(src_py)
        cpp = transpile_to_cpp(east)
        self.assertIn('tokens.append(::rc_new<Token>("PLUS", ch, i, 0));', cpp)
        self.assertNotIn("rc<Token>(::rc_new<Token>(", cpp)

    def test_sample18_pyobj_enumerate_list_str_uses_typed_direct_unpack(self) -> None:
        src_py = ROOT / "sample" / "py" / "18_mini_language_interpreter.py"
        east = load_east(src_py)
        cpp = transpile_to_cpp(east, cpp_list_model="pyobj")
        self.assertIn(
            "for (const auto& [line_index, source] : py_enumerate(py_to_str_list_from_object(lines))) {",
            cpp,
        )
        self.assertNotIn("for (object __itobj_1 : py_dyn_range(py_enumerate(lines))) {", cpp)
        self.assertNotIn("line_index = int64(py_to<int64>(py_at(__itobj_1, 0)))", cpp)
        self.assertNotIn("source = py_to_string(py_at(__itobj_1, 1))", cpp)

    def test_sample18_pyobj_execute_loop_uses_typed_stmt_iteration(self) -> None:
        src_py = ROOT / "sample" / "py" / "18_mini_language_interpreter.py"
        east = load_east(src_py)
        cpp = transpile_to_cpp(east, cpp_list_model="pyobj")
        self.assertIn(
            'for (rc<StmtNode> stmt : py_to_rc_list_from_object<StmtNode>(stmts, "for_target:stmt")) {',
            cpp,
        )
        self.assertNotIn("for (object __itobj_2 : py_dyn_range(stmts)) {", cpp)
        self.assertNotIn('obj_to_rc_or_raise<StmtNode>(__itobj_2, "for_target:stmt")', cpp)

    def test_sample18_parser_expect_uses_current_token_helper(self) -> None:
        src_py = ROOT / "sample" / "py" / "18_mini_language_interpreter.py"
        east = load_east(src_py)
        cpp = transpile_to_cpp(east, cpp_list_model="pyobj")
        self.assertIn("rc<Token> current_token()", cpp)
        self.assertIn("rc<Token> previous_token()", cpp)
        self.assertIn("rc<Token> token = this->current_token();", cpp)
        self.assertIn("if (token->kind != kind)", cpp)
        self.assertNotIn("if (this->peek_kind() != kind)", cpp)

    def test_sample18_number_token_uses_predecoded_number_value(self) -> None:
        src_py = ROOT / "sample" / "py" / "18_mini_language_interpreter.py"
        east = load_east(src_py)
        cpp = transpile_to_cpp(east, cpp_list_model="pyobj")
        self.assertIn("int64 number_value;", cpp)
        self.assertIn("token_num->number_value", cpp)
        self.assertNotIn("py_to_int64(token_num->text)", cpp)

    def test_sample18_uses_tag_based_dispatch_in_eval_and_execute(self) -> None:
        src_py = ROOT / "sample" / "py" / "18_mini_language_interpreter.py"
        east = load_east(src_py)
        cpp = transpile_to_cpp(east, cpp_list_model="pyobj")
        self.assertIn("if (node->kind_tag == 1)", cpp)
        self.assertIn("if (node->op_tag == 1)", cpp)
        self.assertIn("if (stmt->kind_tag == 1)", cpp)
        self.assertNotIn('if (node->kind == "lit")', cpp)
        self.assertNotIn('if (node->op == "+")', cpp)
        self.assertNotIn('if (stmt->kind == "let")', cpp)

    def test_typed_list_return_empty_literal_uses_return_type_not_object_list(self) -> None:
        src = """class Node:
    pass

def new_nodes() -> list[Node]:
    return []
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "typed_empty_list_return.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("return list<Node>{};", cpp)
        self.assertNotIn("return list<object>{};", cpp)

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

        self.assertTrue(
            ("py_at(t, py_to_int64(i))" in cpp)
            or ("py_at(t, py_to<int64>(i))" in cpp)
        )

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

        self.assertIn('d.get("k", int64())', cpp)
        self.assertNotIn('d.get("k", ::std::nullopt)', cpp)

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

        self.assertTrue(
            ('int64 x = dict_get_node(d, "k", 0);' in cpp)
            or ('int64 x = int64(py_to<int64>(dict_get_node(d, "k", ::std::nullopt)));' in cpp)
        )

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

        self.assertTrue(
            ('return dict_get_int(d, "k", py_to_int64(3));' in cpp)
            or ('return dict_get_int(d, "k", py_to<int64>(3));' in cpp)
        )
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

        self.assertTrue(
            ('return dict_get_float(d, "k", py_to_float64(1.25));' in cpp)
            or ('return dict_get_float(d, "k", py_to<float64>(1.25));' in cpp)
        )
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

        self.assertTrue(
            ("object x = object{};" in cpp)
            or ("object x = make_object(::std::nullopt);" in cpp)
        )
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

    def test_infer_rendered_arg_type_detects_rc_new_constructor_result(self) -> None:
        em = CppEmitter({}, load_cpp_profile(), {})
        rendered = '::rc_new<Token>("IDENT", "name", 3)'
        self.assertEqual(em.infer_rendered_arg_type(rendered, "unknown", em.declared_var_types), "Token")

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
        self.assertTrue(
            range_lines == ["for (int64 i = 0; i < 3; ++i)"]
            or range_lines == ["for (int64 i = 0; i < 3; ++i) {"]
        )
        unpack_lines = [
            line.strip()
            for line in lines
            if (
                line.strip().startswith("for (const auto& [")
                or line.strip().startswith("for (auto __it_")
                or line.strip().startswith("for (object __itobj_")
            )
        ]
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
        self.assertTrue(
            range_lines == ["for (int64 i = 0; i < 3; ++i)"]
            or range_lines == ["for (int64 i = 0; i < 3; ++i) {"]
        )
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

        self.assertTrue(
            ("for (int64 v : xs)" in cpp)
            or ("for (object __itobj" in cpp and "py_dyn_range(xs)" in cpp)
        )

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
                        if isinstance(stmt, dict) and stmt.get("kind") in {"For", "ForCore"}:
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

        self.assertTrue(
            ("for (object v : xs)" in cpp)
            or ("py_dyn_range(xs)" in cpp)
        )

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

        self.assertTrue(("return py_to_bool(x);" in cpp) or ("return py_to<bool>(x);" in cpp))
        self.assertIn("return py_len(x);", cpp)
        self.assertIn("return py_to_string(x);", cpp)
        self.assertTrue(
            ("return make_object(py_iter_or_raise(x));" in cpp) or ("return py_iter_or_raise(x);" in cpp)
        )
        self.assertTrue(
            ("return make_object(py_next_or_stop(it));" in cpp) or ("return py_next_or_stop(it);" in cpp)
        )
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
        self.assertIn("uint32 py_type_id() const noexcept override {", cpp)
        self.assertIn("return PYTRA_TYPE_ID;", cpp)
        self.assertNotIn("this->set_type_id(PYTRA_TYPE_ID);", cpp)
        self.assertIn("inline static uint32 PYTRA_TYPE_ID = py_register_class_type(PYTRA_TID_OBJECT);", cpp)
        self.assertIn("inline static uint32 PYTRA_TYPE_ID = py_register_class_type(Base::PYTRA_TYPE_ID);", cpp)
        self.assertIn("return (py_isinstance(x, Base::PYTRA_TYPE_ID)) || (py_isinstance(x, Child::PYTRA_TYPE_ID));", cpp)
        self.assertIn("virtual bool py_isinstance_of(uint32 expected_type_id) const override {", cpp)
        self.assertIn("return expected_type_id == PYTRA_TYPE_ID;", cpp)
        self.assertNotIn("if (expected_type_id == PYTRA_TID_OBJECT) return true;", cpp)
        self.assertNotIn("if (Base::py_isinstance_of(expected_type_id)) return true;", cpp)

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

    def test_inherited_method_call_from_base_ref_is_rendered_as_virtual_member_call(self) -> None:
        src = """class Base:\n    def inc(self, x: int) -> int:\n        return x + 1\n\nclass Child(Base):\n    def inc(self, x: int) -> int:\n        return x + 2\n\ndef use_base(b: Base) -> int:\n    return b.inc(3)\n"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "virtual_inherited_call.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("int64 use_base(const rc<Base>& b) {", cpp)
        self.assertIn("return b->inc(3);", cpp)
        self.assertNotIn("return b.inc(3);", cpp)

    def test_method_call_after_runtime_unbox_is_rendered_with_dynamic_dispatch(self) -> None:
        src = """class Base:\n    def inc(self, x: int) -> int:\n        return x + 1\n\nclass Child(Base):\n    def inc(self, x: int) -> int:\n        return x + 2\n\ndef use_obj(x: object) -> int:\n    b: Base = x\n    return b.inc(4)\n"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "virtual_unbox_call.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("rc<Base> b = obj_to_rc_or_raise<Base>(x, ", cpp)
        self.assertIn("return b->inc(4);", cpp)
        self.assertNotIn("return b.inc(4);", cpp)
        self.assertNotRegex(cpp, r"type_id\(\)\s*(==|!=|<=|>=|<|>)")
        self.assertNotRegex(cpp, r"switch\s*\([^)]*type_id\(")

    def test_staticmethod_boundary_uses_class_call_without_type_id_switch(self) -> None:
        src = """class Base:\n    @staticmethod\n    def sm(x: int) -> int:\n        return x + 1\n\nclass Child(Base):\n    pass\n\ndef f() -> int:\n    return Child.sm(3)\n"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "virtual_staticmethod_boundary.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("int64 sm(int64 x) {", cpp)
        self.assertIn("return Child::sm(3);", cpp)
        self.assertNotRegex(cpp, r"type_id\(\)\s*(==|!=|<=|>=|<|>)")
        self.assertNotRegex(cpp, r"switch\s*\([^)]*type_id\(")

    def test_classmethod_boundary_keeps_class_call_without_type_id_switch(self) -> None:
        src = """class Base:\n    @classmethod\n    def cm(cls, x: int) -> int:\n        return x + 1\n\nclass Child(Base):\n    pass\n\ndef f() -> int:\n    return Child.cm(3)\n"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "virtual_classmethod_boundary.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("int64 cm(const object& cls, int64 x) {", cpp)
        self.assertIn("return Child::cm(3);", cpp)
        self.assertNotRegex(cpp, r"type_id\(\)\s*(==|!=|<=|>=|<|>)")
        self.assertNotRegex(cpp, r"switch\s*\([^)]*type_id\(")

    def test_base_qualified_call_keeps_virtual_path_without_type_id_dispatch(self) -> None:
        src = """class Base:\n    def f(self, x: int) -> int:\n        return x + 1\n\nclass Child(Base):\n    def f(self, x: int) -> int:\n        return Base.f(self, x) + 1\n"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "base_qualified_virtual_call.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("virtual int64 f(int64 x) {", cpp)
        self.assertIn("int64 f(int64 x) override {", cpp)
        self.assertIn("return Base::f(*this, x) + 1;", cpp)
        self.assertNotRegex(cpp, r"type_id\(\)\s*(==|!=|<=|>=|<|>)")
        self.assertNotRegex(cpp, r"switch\s*\([^)]*type_id\(")

    def test_super_method_call_lowers_to_base_qualified_call_without_type_id_dispatch(self) -> None:
        src = """class Base:\n    def f(self, x: int) -> int:\n        return x + 1\n\nclass Child(Base):\n    def f(self, x: int) -> int:\n        return super().f(x) + 1\n"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "super_virtual_call.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("virtual int64 f(int64 x) {", cpp)
        self.assertIn("int64 f(int64 x) override {", cpp)
        self.assertIn("return Base::f(*this, x) + 1;", cpp)
        self.assertNotIn("super().f(", cpp)
        self.assertNotRegex(cpp, r"type_id\(\)\s*(==|!=|<=|>=|<|>)")
        self.assertNotRegex(cpp, r"switch\s*\([^)]*type_id\(")

    def test_isinstance_class_and_builtin_mix_is_lowered_to_runtime_type_id_checks(self) -> None:
        src = """class Base:\n    def __init__(self):\n        pass\n\nclass Child(Base):\n    def __init__(self):\n        super().__init__()\n\ndef f(x: object) -> bool:\n    return isinstance(x, (Base, Child, int, str, object))\n"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "isinstance_mixed_tuple.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("py_isinstance(x, Base::PYTRA_TYPE_ID)", cpp)
        self.assertIn("py_isinstance(x, Child::PYTRA_TYPE_ID)", cpp)
        self.assertIn("py_isinstance(x, PYTRA_TID_INT)", cpp)
        self.assertIn("py_isinstance(x, PYTRA_TID_STR)", cpp)
        self.assertIn("py_isinstance(x, PYTRA_TID_OBJECT)", cpp)
        self.assertIn("return (", cpp)
        self.assertIn(" || ", cpp)
        self.assertNotIn("return isinstance(", cpp)

    def test_non_overridden_base_methods_are_not_virtual(self) -> None:
        src = """class Base:\n    def inc(self, x: int) -> int:\n        return x + 1\n\n    def unused(self, x: int) -> int:\n        return x\n\nclass Child(Base):\n    def inc(self, x: int) -> int:\n        return x + 2\n"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "virtual_no_override.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("virtual int64 inc(int64 x) {", cpp)
        self.assertNotIn("virtual int64 unused(int64 x) {", cpp)

    def test_pyobj_list_model_uses_runtime_list_ops(self) -> None:
        src = """def f() -> int:
    xs: list[int] = [1, 2]
    xs.append(3)
    xs.extend([4, 5])
    v = xs.pop()
    head = xs[0]
    seg = xs[0:2]
    return v + head + len(seg)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "pyobj_list_model_ops.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            em = CppEmitter(east, {}, emit_main=False)
            em.cpp_list_model = "pyobj"
            cpp = em.transpile()

        self.assertIn("object xs = make_object(list<int64>{1, 2});", cpp)
        self.assertIn("py_append(xs, make_object(3));", cpp)
        self.assertIn("py_extend(xs, make_object(list<int64>{4, 5}));", cpp)
        self.assertIn("auto v = py_pop(xs);", cpp)
        self.assertIn("int64 head = int64(py_to<int64>(py_at(xs, py_to<int64>(0))));", cpp)
        self.assertIn("object seg = py_slice(xs, 0, 2);", cpp)

    def test_pyobj_list_model_list_comprehension_returns_object(self) -> None:
        src = """def f(xs: list[int]) -> list[int]:
    return [x + 1 for x in xs]
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "pyobj_list_model_list_comp.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            em = CppEmitter(east, {}, emit_main=False)
            em.cpp_list_model = "pyobj"
            cpp = em.transpile()

        self.assertIn("object f(const object& xs)", cpp)
        self.assertIn("[&]() -> object {", cpp)
        self.assertIn("list<object> __out;", cpp)
        self.assertIn("return make_object(__out);", cpp)

    def test_transpile_to_cpp_accepts_cpp_list_model_override(self) -> None:
        src = """def sink(xs: list[int]) -> int:
    return len(xs)

def f() -> int:
    xs: list[int] = []
    xs.append(1)
    return sink(xs)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "pyobj_list_model_api_override.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False, cpp_list_model="pyobj")

        self.assertIn("object xs = make_object(list<object>{});", cpp)
        self.assertIn("py_append(xs, make_object(1));", cpp)
        self.assertIn("return sink(xs);", cpp)

    def test_pyobj_list_model_nested_subscript_assign_lowers_to_py_set_at(self) -> None:
        src = """def paint(grid: list[list[int]], x: int, y: int) -> None:
    grid[y][x] = 1
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "pyobj_nested_subscript_assign.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            em = CppEmitter(east, {}, emit_main=False)
            em.cpp_list_model = "pyobj"
            cpp = em.transpile()

        self.assertIn("py_set_at(object(py_at(grid, py_to<int64>(y))), x, make_object(1));", cpp)
        self.assertNotIn("object(py_at(grid, py_to<int64>(y)))[x]", cpp)

    def test_pyobj_list_model_list_repeat_unboxes_to_value_list_before_py_repeat(self) -> None:
        src = """def row(w: int) -> list[int]:
    return [0] * w
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "pyobj_list_repeat_row.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            em = CppEmitter(east, {}, emit_main=False)
            em.cpp_list_model = "pyobj"
            cpp = em.transpile()

        self.assertIn("py_repeat(list<int64>(make_object(list<int64>{0})), w)", cpp)
        self.assertNotIn("py_repeat(make_object(list<int64>{0}), w)", cpp)

    def test_pyobj_list_model_boxes_stack_list_when_call_target_param_is_list_annotation(self) -> None:
        sample_py = Path(__file__).resolve().parents[2] / "sample" / "py" / "12_sort_visualizer.py"
        east = load_east(sample_py)
        em = CppEmitter(east, {}, emit_main=False)
        em.cpp_list_model = "pyobj"
        cpp = em.transpile()

        self.assertIn("list<int64> values = list<int64>{};", cpp)
        self.assertIn("render(make_object(values), w, h)", cpp)

    def test_pyobj_list_model_tuple_subscript_unboxes_to_make_tuple_before_destructure(self) -> None:
        src = """def f(stack: list[tuple[int, int]]) -> int:
    x, y = stack[-1]
    return x + y
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "pyobj_tuple_subscript_unbox.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            em = CppEmitter(east, {}, emit_main=False)
            em.cpp_list_model = "pyobj"
            cpp = em.transpile()

        self.assertIn("::std::make_tuple(", cpp)
        self.assertIn("py_at(py_at(stack, py_to<int64>(-1)), 0)", cpp)
        self.assertIn("py_at(py_at(stack, py_to<int64>(-1)), 1)", cpp)

    def test_pyobj_list_model_can_stack_lower_non_escape_local_list(self) -> None:
        src = """def f() -> int:
    xs: list[int] = []
    xs.append(1)
    xs.append(2)
    head: int = xs[0]
    return head + len(xs)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "pyobj_stack_local_list.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            em = CppEmitter(east, {}, emit_main=False)
            em.cpp_list_model = "pyobj"
            cpp = em.transpile()

        self.assertIn("list<int64> xs = list<int64>{};", cpp)
        self.assertIn("xs.append(int64(1));", cpp)
        self.assertIn("xs.append(int64(2));", cpp)
        self.assertIn("int64 head = xs[0];", cpp)
        self.assertNotIn("py_append(xs", cpp)
        self.assertNotIn("py_at(xs", cpp)

    def test_pyobj_list_model_keeps_runtime_path_when_local_list_escapes(self) -> None:
        src = """def sink(xs: list[int]) -> int:
    return len(xs)

def f() -> int:
    xs: list[int] = []
    xs.append(1)
    return sink(xs)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "pyobj_stack_local_list_escape.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            em = CppEmitter(east, {}, emit_main=False)
            em.cpp_list_model = "pyobj"
            cpp = em.transpile()

        self.assertIn("object xs = make_object(list<object>{});", cpp)
        self.assertIn("py_append(xs, make_object(1));", cpp)
        self.assertIn("return sink(xs);", cpp)

    def test_pyobj_list_model_does_not_stack_lower_when_dynamic_callable_consumes_list(self) -> None:
        src = """def f(cb: object) -> int:
    xs: list[int] = []
    xs.append(1)
    n: int = len(xs)
    return n + cb(xs)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "pyobj_stack_local_list_dynamic_call_escape.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            em = CppEmitter(east, {}, emit_main=False)
            em.cpp_list_model = "pyobj"
            cpp = em.transpile()

        self.assertIn("object xs = make_object(list<object>{});", cpp)
        self.assertIn("py_append(xs, make_object(1));", cpp)
        self.assertNotIn("list<int64> xs = list<int64>{};", cpp)
        self.assertNotIn("xs.append(int64(1));", cpp)

    def test_pyobj_list_model_does_not_stack_lower_when_external_attr_call_consumes_list(self) -> None:
        src = """from ext_module import consume

def f() -> int:
    xs: list[int] = []
    xs.append(1)
    return consume(xs)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "pyobj_stack_local_list_external_call_escape.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            em = CppEmitter(east, {}, emit_main=False)
            em.cpp_list_model = "pyobj"
            cpp = em.transpile()

        self.assertIn("object xs = make_object(list<object>{});", cpp)
        self.assertIn("py_append(xs, make_object(1));", cpp)
        self.assertNotIn("list<int64> xs = list<int64>{};", cpp)
        self.assertNotIn("xs.append(int64(1));", cpp)


if __name__ == "__main__":
    unittest.main()
