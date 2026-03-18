"""Regression tests that pin known py2cpp codegen issues with minimal cases."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.backends.cpp.cli import CppEmitter, build_cpp_header_from_east, load_cpp_profile, load_east, transpile_to_cpp


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
        self.assertIn('return Token("IDENT", "name", 3);', cpp)

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
        src_text = (ROOT / "src" / "backends" / "cpp" / "cli.py").read_text(encoding="utf-8")
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
        src = """class Base:
    pass

class Box(Base):
    v: int
    def __init__(self, v: int):
        self.v = v

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
        src = """class Base:
    pass

class Box(Base):
    v: int
    def __init__(self, v: int):
        self.v = v

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
        src = """class Base:
    pass

class Box(Base):
    v: int
    def __init__(self, v: int):
        self.v = v

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

        self.assertIn("::std::get<0>(__tuple_1)", cpp)
        self.assertIn("::std::get<1>(__tuple_1)", cpp)
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

        self.assertIn("return int64(::std::stoll(s));", cpp)

    def test_int_cast_with_base_uses_py_to_int64_base(self) -> None:
        src = """def f(s: str) -> int:
    return int(s, 16)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "int_cast_base.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("return py_to_int64_base(s, int64(16));", cpp)

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

        self.assertIn("return a / float64(b);", cpp)
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

        self.assertIn("return float64(a) / float64(b);", cpp)
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

        self.assertIn("py_div(a, b)", cpp)

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

    def test_sample18_ident_text_avoids_redundant_py_to_string(self) -> None:
        src_py = ROOT / "sample" / "py" / "18_mini_language_interpreter.py"
        east = load_east(src_py)
        cpp = transpile_to_cpp(east, cpp_list_model="pyobj")
        self.assertIn('str let_name = this->expect("IDENT").text;', cpp)
        self.assertIn('str assign_name = this->expect("IDENT").text;', cpp)
        self.assertNotIn('py_to_string(this->expect("IDENT").text)', cpp)

    def test_sample18_rc_new_avoids_redundant_rc_cast(self) -> None:
        src_py = ROOT / "sample" / "py" / "18_mini_language_interpreter.py"
        east = load_east(src_py)
        cpp = transpile_to_cpp(east)
        self.assertIn("tokens.append(Token(", cpp)
        self.assertIn("single_char_token_kinds[single_tag - 1]", cpp)
        self.assertNotIn("::rc_new<Token>(", cpp)
        self.assertNotIn("rc<Token>(::rc_new<Token>(", cpp)

    def test_sample18_tokenize_single_char_dispatch_uses_tag_lookup(self) -> None:
        src_py = ROOT / "sample" / "py" / "18_mini_language_interpreter.py"
        east = load_east(src_py)
        cpp = transpile_to_cpp(east, cpp_list_model="pyobj")
        self.assertIn("int64 single_tag = int64(single_char_token_tags.get(ch, 0));", cpp)
        self.assertIn(
            "py_list_at_ref(rc_list_ref(single_char_token_kinds), single_tag - 1)",
            cpp,
        )
        self.assertNotIn('if (ch == "+")', cpp)
        self.assertNotIn('if (ch == "-")', cpp)
        self.assertNotIn('if (ch == "*")', cpp)
        self.assertNotIn('if (ch == "/")', cpp)
        self.assertNotIn('if (ch == "(")', cpp)
        self.assertNotIn('if (ch == ")")', cpp)
        self.assertNotIn('if (ch == "=")', cpp)

    def test_sample18_pyobj_enumerate_list_str_uses_typed_direct_unpack(self) -> None:
        src_py = ROOT / "sample" / "py" / "18_mini_language_interpreter.py"
        east = load_east(src_py)
        cpp = transpile_to_cpp(east, cpp_list_model="pyobj")
        self.assertIn(
            "for (const auto& [line_index, source] : py_enumerate(lines)) {",
            cpp,
        )
        self.assertNotIn("py_to_str_list_from_object(lines)", cpp)
        self.assertNotIn("for (object __itobj_1 : py_dyn_range(py_enumerate(lines))) {", cpp)
        self.assertNotIn("line_index = int64(py_to<int64>(py_at(__itobj_1, 0)))", cpp)
        self.assertNotIn("source = py_to_string(py_at(__itobj_1, 1))", cpp)

    def test_sample18_pyobj_execute_loop_uses_typed_stmt_iteration(self) -> None:
        src_py = ROOT / "sample" / "py" / "18_mini_language_interpreter.py"
        east = load_east(src_py)
        cpp = transpile_to_cpp(east, cpp_list_model="pyobj")
        self.assertIn("for (StmtNode stmt : rc_list_ref(stmts)) {", cpp)
        self.assertNotIn("for (object __itobj_2 : py_dyn_range(stmts)) {", cpp)
        self.assertNotIn('obj_to_rc_or_raise<StmtNode>(__itobj_2, "for_target:stmt")', cpp)
        self.assertNotIn('py_to_rc_list_from_object<StmtNode>(stmts, "for_target:stmt")', cpp)

    def test_sample18_pyobj_tokens_are_typed_containers(self) -> None:
        src_py = ROOT / "sample" / "py" / "18_mini_language_interpreter.py"
        east = load_east(src_py)
        cpp = transpile_to_cpp(east, cpp_list_model="pyobj")
        self.assertIn("rc<list<Token>> tokenize(const rc<list<str>>& lines) {", cpp)
        self.assertIn("rc<list<Token>> tokens = rc_list_from_value(list<Token>{});", cpp)
        self.assertIn("rc<list<Token>> tokens;", cpp)
        self.assertIn("rc<list<ExprNode>> expr_nodes;", cpp)
        self.assertIn("this->tokens = tokens;", cpp)
        self.assertIn("this->expr_nodes = this->new_expr_nodes();", cpp)
        self.assertIn(
            "return py_list_at_ref(rc_list_ref(this->tokens), this->pos);",
            cpp,
        )
        self.assertIn("rc_list_ref(this->expr_nodes).append(node);", cpp)
        self.assertNotIn("list<Token> tokens;", cpp)
        self.assertNotIn("list<ExprNode> expr_nodes;", cpp)
        self.assertNotIn("this->tokens = rc_list_copy_value(tokens);", cpp)
        self.assertNotIn("this->expr_nodes = rc_list_copy_value(this->new_expr_nodes());", cpp)
        self.assertNotIn("return this->tokens[this->pos];", cpp)
        self.assertNotIn(
            'obj_to_rc_or_raise<Token>(py_list_at_ref(rc_list_ref(this->tokens), py_to<int64>(this->pos)), "subscript:list")',
            cpp,
        )
        self.assertIn(
            "ExprNode node = py_list_at_ref(rc_list_ref(expr_nodes), expr_index);",
            cpp,
        )
        self.assertNotIn("const rc<ExprNode>& node = expr_nodes[expr_index];", cpp)

    def test_sample18_synthesized_ctors_use_init_list(self) -> None:
        src_py = ROOT / "sample" / "py" / "18_mini_language_interpreter.py"
        east = load_east(src_py)
        cpp = transpile_to_cpp(east, cpp_list_model="pyobj")
        self.assertIn(
            "Token(str kind, str text, int64 pos, int64 number_value) : kind(kind), text(text), pos(pos), number_value(number_value) {",
            cpp,
        )
        self.assertIn(
            "ExprNode(str kind, int64 value, str name, str op, int64 left, int64 right, int64 kind_tag, int64 op_tag) : kind(kind), value(value), name(name), op(op), left(left), right(right), kind_tag(kind_tag), op_tag(op_tag) {",
            cpp,
        )
        self.assertIn(
            "StmtNode(str kind, str name, int64 expr_index, int64 kind_tag) : kind(kind), name(name), expr_index(expr_index), kind_tag(kind_tag) {",
            cpp,
        )
        self.assertNotIn("Token(str kind, str text, int64 pos, int64 number_value) {\n        this->kind = kind;", cpp)
        self.assertNotIn(
            "ExprNode(str kind, int64 value, str name, str op, int64 left, int64 right, int64 kind_tag, int64 op_tag) {\n        this->kind = kind;",
            cpp,
        )
        self.assertNotIn("StmtNode(str kind, str name, int64 expr_index, int64 kind_tag) {\n        this->kind = kind;", cpp)

    def test_sample18_pyobj_benchmark_source_lines_use_ref_first_handles(self) -> None:
        src_py = ROOT / "sample" / "py" / "18_mini_language_interpreter.py"
        east = load_east(src_py)
        cpp = transpile_to_cpp(east, cpp_list_model="pyobj")
        self.assertIn("rc<list<str>> build_benchmark_source(int64 var_count, int64 loops) {", cpp)
        self.assertIn("rc<list<str>> lines = rc_list_from_value(list<str>{});", cpp)
        self.assertIn("rc<list<str>> demo_lines = rc_list_from_value(list<str>{});", cpp)
        self.assertIn("rc<list<str>> source_lines = build_benchmark_source(32, 120000);", cpp)
        self.assertIn("rc<list<Token>> tokens = tokenize(demo_lines);", cpp)
        self.assertIn("rc<list<Token>> tokens = tokenize(source_lines);", cpp)
        self.assertIn("rc_list_ref(lines).reserve((var_count <= 0) ? 0 : var_count);", cpp)
        self.assertNotIn("object lines = make_object(list<object>{});", cpp)
        self.assertNotIn("object demo_lines = make_object(list<object>{});", cpp)
        self.assertNotIn("py_to_str_list_from_object(demo_lines)", cpp)
        self.assertNotIn("py_to_str_list_from_object(source_lines)", cpp)

    def test_sample18_parser_expect_uses_current_token_helper(self) -> None:
        src_py = ROOT / "sample" / "py" / "18_mini_language_interpreter.py"
        east = load_east(src_py)
        cpp = transpile_to_cpp(east, cpp_list_model="pyobj")
        self.assertIn("Token current_token()", cpp)
        self.assertIn("Token previous_token()", cpp)
        self.assertIn("Token token = this->current_token();", cpp)
        self.assertIn("if (token.kind != kind)", cpp)
        self.assertNotIn("if (this->peek_kind() != kind)", cpp)

    def test_sample18_number_token_uses_predecoded_number_value(self) -> None:
        src_py = ROOT / "sample" / "py" / "18_mini_language_interpreter.py"
        east = load_east(src_py)
        cpp = transpile_to_cpp(east, cpp_list_model="pyobj")
        self.assertIn("int64 number_value;", cpp)
        self.assertIn("token_num.number_value", cpp)
        self.assertNotIn("py_to_int64(token_num.text)", cpp)

    def test_sample18_uses_tag_based_dispatch_in_eval_and_execute(self) -> None:
        src_py = ROOT / "sample" / "py" / "18_mini_language_interpreter.py"
        east = load_east(src_py)
        cpp = transpile_to_cpp(east, cpp_list_model="pyobj")
        self.assertIn("if (node.kind_tag == 1)", cpp)
        self.assertIn("if (node.op_tag == 1)", cpp)
        self.assertIn("if (stmt.kind_tag == 1)", cpp)
        self.assertNotIn('if (node.kind == "lit")', cpp)
        self.assertNotIn('if (node.op == "+")', cpp)
        self.assertNotIn('if (stmt.kind == "let")', cpp)

    def test_sample13_pyobj_expands_typed_lists_for_grid_stack_dirs_frames(self) -> None:
        src_py = ROOT / "sample" / "py" / "13_maze_generation_steps.py"
        east = load_east(src_py)
        cpp = transpile_to_cpp(east, cpp_list_model="pyobj")
        self.assertIn("while (!((rc_list_ref(stack)).empty())) {", cpp)
        self.assertNotIn("while (py_len(stack) != 0)", cpp)
        self.assertIn("bytes capture(const rc<list<list<int64>>>& grid, int64 w, int64 h, int64 scale)", cpp)
        self.assertIn("rc<list<list<int64>>> grid = rc_list_from_value(list<list<int64>>(cell_h, list<int64>(cell_w, 1)));", cpp)
        self.assertIn(
            "rc<list<::std::tuple<int64, int64>>> stack = rc_list_from_value(list<::std::tuple<int64, int64>>{::std::make_tuple(1, 1)});",
            cpp,
        )
        self.assertTrue(
            (
                "rc<list<::std::tuple<int64, int64>>> dirs = rc_list_from_value(list<::std::tuple<int64, int64>>{::std::make_tuple(2, 0), ::std::make_tuple(-2, 0), ::std::make_tuple(0, 2), ::std::make_tuple(0, -2)});"
                in cpp
            )
            or (
                "rc<list<::std::tuple<int64, int64>>> dirs = rc_list_from_value(list<::std::tuple<int64, int64>>{::std::make_tuple(2, 0), ::std::make_tuple(-(2), 0), ::std::make_tuple(0, 2), ::std::make_tuple(0, -(2))});"
                in cpp
            )
        )
        self.assertIn("rc<list<bytes>> frames = rc_list_from_value(list<bytes>{});", cpp)
        self.assertIn(
            "rc<list<::std::tuple<int64, int64, int64, int64>>> candidates = rc_list_from_value(list<::std::tuple<int64, int64, int64, int64>>{});",
            cpp,
        )
        self.assertNotIn("::std::tuple<int64, int64, int64, int64>(::std::make_tuple(", cpp)
        self.assertNotIn("::std::tuple<int64, int64>(::std::make_tuple(", cpp)
        self.assertIn("auto __idx_", cpp)
        self.assertIn(
            "= (x * 17 + y * 29 + (rc_list_ref(stack)).size() * 13) % (rc_list_ref(candidates)).size();",
            cpp,
        )
        self.assertIn(
            "::std::tuple<int64, int64, int64, int64> sel = py_list_at_ref(rc_list_ref(candidates), __idx_",
            cpp,
        )
        self.assertNotIn("candidates[__idx_", cpp)
        self.assertNotIn("int64(py_to<int64>(", cpp)
        self.assertNotIn("float64(py_to<float64>(", cpp)
        self.assertIn(
            "int64 v = (py_list_at_ref(py_list_at_ref(rc_list_ref(grid), y), x) == 0 ? 255 : 40);",
            cpp,
        )
        self.assertNotIn("object(py_at(grid, ", cpp)
        self.assertIn("rc_list_ref(frames).append(capture(grid, cell_w, cell_h, scale));", cpp)
        self.assertNotIn("object grid = ", cpp)
        self.assertNotIn("object stack = ", cpp)
        self.assertNotIn("object dirs = ", cpp)
        self.assertNotIn("object frames = ", cpp)

    def test_sample08_else_if_chain_is_flattened(self) -> None:
        src_py = ROOT / "sample" / "py" / "08_langtons_ant.py"
        east = load_east(src_py)
        cpp = transpile_to_cpp(east, cpp_list_model="pyobj")
        self.assertIn("else if (d == 1) {", cpp)
        self.assertIn("else if (d == 2) {", cpp)
        self.assertNotIn("else {\n                if (d == 1)", cpp)

    def test_sample08_capture_return_avoids_redundant_bytes_ctor(self) -> None:
        src_py = ROOT / "sample" / "py" / "08_langtons_ant.py"
        east = load_east(src_py)
        cpp = transpile_to_cpp(east, cpp_list_model="pyobj")
        self.assertIn("return frame;", cpp)
        self.assertNotIn("return bytes(frame);", cpp)

    def test_sample08_grid_init_uses_typed_fill_ctor(self) -> None:
        src_py = ROOT / "sample" / "py" / "08_langtons_ant.py"
        east = load_east(src_py)
        cpp = transpile_to_cpp(east, cpp_list_model="pyobj")
        self.assertIn("rc<list<list<int64>>> grid = rc_list_from_value(list<list<int64>>(h, list<int64>(w, 0)));", cpp)
        self.assertNotIn("grid = [&]() -> list<list<int64>>", cpp)
        self.assertNotIn("py_repeat(list<int64>(list<int64>{0}), w)", cpp)

    def test_sample08_capture_guard_keeps_mod_check_without_counter_hoist(self) -> None:
        src_py = ROOT / "sample" / "py" / "08_langtons_ant.py"
        east = load_east(src_py)
        cpp = transpile_to_cpp(east, cpp_list_model="pyobj")
        self.assertNotIn("__next_capture_", cpp)
        self.assertIn("if (i % capture_every == 0)", cpp)

    def test_sample08_frames_reserve_is_not_emitted_for_conditional_append(self) -> None:
        src_py = ROOT / "sample" / "py" / "08_langtons_ant.py"
        east = load_east(src_py)
        cpp = transpile_to_cpp(east, cpp_list_model="pyobj")
        self.assertNotIn("frames.reserve(", cpp)

    def test_static_range_unconditional_append_emits_reserve_via_east3_hint(self) -> None:
        src = """def collect(n: int) -> list[int]:
    xs: list[int] = []
    for i in range(n):
        xs.append(i)
    return xs
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "reserve_hint_collect.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False, cpp_list_model="pyobj")

        self.assertIn("rc_list_ref(xs).reserve(", cpp)
        self.assertIn("(n <= 0) ? 0 : n", cpp)
        self.assertNotIn("(n) - (0)", cpp)

    def test_static_range_reserve_hint_missing_count_expr_is_fail_closed(self) -> None:
        src = """def collect(n: int) -> list[int]:
    xs: list[int] = []
    for i in range(n):
        xs.append(i)
    return xs
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "reserve_hint_fail_closed.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            body = east.get("body")
            self.assertIsInstance(body, list)
            fn = body[0]
            self.assertIsInstance(fn, dict)
            fn_body = fn.get("body")
            self.assertIsInstance(fn_body, list)
            for_stmt = fn_body[1]
            self.assertIsInstance(for_stmt, dict)
            for_stmt["reserve_hints"] = [
                {
                    "kind": "StaticRangeReserveHint",
                    "owner": "xs",
                    "safe": True,
                    "count_expr_version": "east3_expr_v1",
                }
            ]
            cpp = transpile_to_cpp(east, emit_main=False, cpp_list_model="pyobj")

        self.assertNotIn("xs.reserve(", cpp)

    def test_typed_list_len_zero_compare_uses_empty_fastpath(self) -> None:
        src = """def has_items(xs: list[int]) -> bool:
    return len(xs) != 0

def is_empty(xs: list[int]) -> bool:
    return len(xs) == 0
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "typed_list_len_zero_compare.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False, cpp_list_model="pyobj")

        self.assertIn("return !((rc_list_ref(xs)).empty());", cpp)
        self.assertIn("return (rc_list_ref(xs)).empty();", cpp)
        self.assertNotIn("return py_len(xs) != 0;", cpp)
        self.assertNotIn("return py_len(xs) == 0;", cpp)

    def test_sample15_module_keyword_literals_do_not_emit_redundant_int_cast(self) -> None:
        src_py = ROOT / "sample" / "py" / "15_wave_interference_loop.py"
        east = load_east(src_py)
        cpp = transpile_to_cpp(east, cpp_list_model="pyobj")
        self.assertIn("pytra::utils::gif::save_gif(", cpp)
        self.assertIn("pytra::utils::gif::grayscale_palette(), 4, 0);", cpp)
        self.assertNotIn("int64(py_to<int64>(4))", cpp)
        self.assertNotIn("int64(py_to<int64>(0))", cpp)

    def test_module_keyword_reordered_call_keeps_signature_order_for_nodes_and_values(self) -> None:
        src = """from pytra.utils.gif import save_gif, grayscale_palette

def f(frames: list[bytes]) -> None:
    save_gif("x.gif", 1, 1, frames, grayscale_palette(), loop=0, delay_cs=4)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "module_kw_order.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False, cpp_list_model="pyobj")

        self.assertIn(
            "pytra::utils::gif::save_gif(\"x.gif\", 1, 1, rc_list_ref(frames), pytra::utils::gif::grayscale_palette(), 4, 0);",
            cpp,
        )
        self.assertNotIn(
            "pytra::utils::gif::save_gif(\"x.gif\", 1, 1, frames, pytra::utils::gif::grayscale_palette(), 0, 4);",
            cpp,
        )
        self.assertNotIn("int64(py_to<int64>(4))", cpp)
        self.assertNotIn("int64(py_to<int64>(0))", cpp)

    def test_sample16_float64_cast_style_uses_function_form(self) -> None:
        src_py = ROOT / "sample" / "py" / "16_glass_sculpture_chaos.py"
        east = load_east(src_py)
        cpp = transpile_to_cpp(east, cpp_list_model="pyobj")
        self.assertIn("float64 __hoisted_cast_4 = float64(width);", cpp)
        self.assertIn("::std::max<float64>(ldy, 0.0);", cpp)
        self.assertNotIn("static_cast<float64>(", cpp)

    def test_float_cast_on_any_like_keeps_runtime_conversion(self) -> None:
        src = """def f(v: object) -> float:
    return float(v)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "float_any_cast.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("return py_to_float64(v);", cpp)
        self.assertNotIn("return float64(v);", cpp)

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
            or ("py_at(t, i)" in cpp)
        )

    def test_string_negative_index_uses_str_operator(self) -> None:
        src = """def tail(s: str) -> str:
    return s[-1]
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "string_negative_index.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("return s[", cpp)
        self.assertNotIn("return py_at(s", cpp)

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

        self.assertIn("py_object_try_cast<int64>(", cpp)
        self.assertIn("return py_to<int64>(3);", cpp)
        self.assertNotIn("py_dict_get_default(", cpp)
        self.assertNotIn("dict_get_int(", cpp)

    def test_dict_get_typed_none_default_uses_value_default(self) -> None:
        src = """def f(d: dict[str, int]) -> int:
    return d.get("k", None)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "dict_get_typed_none.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn('d.get(str("k"), int64())', cpp)
        self.assertNotIn('d.get(str("k"), ::std::nullopt)', cpp)

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

        self.assertIn("int64(([&]() -> object {", cpp)
        self.assertNotIn("py_dict_get_default(", cpp)
        self.assertNotIn("dict_get_node(", cpp)
        self.assertNotIn("dict_get_int(", cpp)

    def test_dict_get_object_none_default_in_return_uses_typed_default(self) -> None:
        src = """def f(d: dict[str, object]) -> int:
    return d.get("k", None)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "dict_get_object_none_return.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("return ([&]() -> object {", cpp)
        self.assertNotIn("py_dict_get_default(", cpp)
        self.assertNotIn("dict_get_node(", cpp)

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

        self.assertIn("([&]() -> int64 {", cpp)
        self.assertIn("py_object_try_cast<int64>(", cpp)
        self.assertNotIn("dict_get_int(", cpp)
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

        self.assertIn("([&]() -> bool {", cpp)
        self.assertIn("py_object_try_cast<bool>(", cpp)
        self.assertNotIn("dict_get_bool(", cpp)
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

        self.assertIn("([&]() -> str {", cpp)
        self.assertIn('return str("x");', cpp)
        self.assertIn("return py_to_string(__dict_it_", cpp)
        self.assertNotIn("dict_get_str(", cpp)

    def test_optional_dict_object_get_float_uses_typed_wrapper(self) -> None:
        src = """def f(d: dict[str, object] | None) -> float:
    return d.get("k", 1.25)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "optional_dict_object_get_float.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("([&]() -> float64 {", cpp)
        self.assertIn("py_object_try_cast<float64>(", cpp)
        self.assertNotIn("dict_get_float(", cpp)

    def test_optional_dict_object_get_list_uses_list_wrapper(self) -> None:
        src = """def f(d: dict[str, object] | None) -> list[int]:
    return d.get("k", [1, 2])
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "optional_dict_object_get_list.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("([&]() -> list<int64> {", cpp)
        self.assertIn("return py_to<list<int64>>(__dict_it_", cpp)
        self.assertNotIn("dict_get_list(", cpp)

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

    def test_forcore_static_range_single_stmt_omits_braces(self) -> None:
        src = """def f() -> int:
    total: int = 0
    for i in range(0, 3, 1):
        total += i
    return total
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "forcore_single_stmt_brace_omit.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        loop_lines = [line.strip() for line in cpp.splitlines() if line.strip().startswith("for (int64 i = 0; i < 3; ++i)")]
        self.assertEqual(loop_lines, ["for (int64 i = 0; i < 3; ++i)"])
        self.assertNotIn("for (int64 i = 0; i < 3; ++i) {", cpp)
        self.assertIn("total += i;", cpp)

    def test_for_object_uses_runtime_protocol_explicit_iter_next(self) -> None:
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

        self.assertIn("__obj = x;", cpp)
        self.assertIn("__obj->py_iter_or_raise()", cpp)
        self.assertIn("__iter->py_next_or_stop()", cpp)
        self.assertIn("object v = *__next_", cpp)
        self.assertNotIn("py_dyn_range(x)", cpp)
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
            or ("__obj = xs;" in cpp and "__obj->py_iter_or_raise()" in cpp)
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

        self.assertIn("return py_runtime_value_isinstance(x, PYTRA_TID_INT);", cpp)
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
        self.assertIn("__obj->py_iter_or_raise()", cpp)
        self.assertIn("__iter->py_next_or_stop()", cpp)
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

        self.assertIn("return py_runtime_value_isinstance(x, PYTRA_TID_SET);", cpp)
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

        self.assertIn("py_runtime_value_isinstance(x, PYTRA_TID_INT)", cpp)
        self.assertIn("py_runtime_value_isinstance(x, Base::PYTRA_TYPE_ID)", cpp)
        self.assertIn("py_runtime_value_isinstance(x, Child::PYTRA_TYPE_ID)", cpp)
        self.assertIn("py_runtime_value_isinstance(x, PYTRA_TID_DICT)", cpp)
        self.assertIn("py_runtime_value_isinstance(x, PYTRA_TID_OBJECT)", cpp)
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

        self.assertIn("PYTRA_DECLARE_CLASS_TYPE(", cpp)
        self.assertNotIn("this->set_type_id(PYTRA_TYPE_ID);", cpp)
        self.assertIn("PYTRA_DECLARE_CLASS_TYPE(PYTRA_TID_OBJECT);", cpp)
        self.assertIn("PYTRA_DECLARE_CLASS_TYPE(Base::PYTRA_TYPE_ID);", cpp)
        self.assertIn(
            "return (py_runtime_value_isinstance(x, Base::PYTRA_TYPE_ID)) || (py_runtime_value_isinstance(x, Child::PYTRA_TYPE_ID));",
            cpp,
        )
        self.assertNotIn("virtual bool py_isinstance_of(uint32 expected_type_id) const override {", cpp)
        self.assertNotIn("if (expected_type_id == PYTRA_TID_OBJECT) return true;", cpp)
        self.assertNotIn("if (Base::py_isinstance_of(expected_type_id)) return true;", cpp)

    def test_nominal_adt_class_lane_supports_ctor_projection_and_variant_check(self) -> None:
        src = """from dataclasses import dataclass

@sealed
class Maybe:
    pass

@dataclass
class Just(Maybe):
    value: int

class Nothing(Maybe):
    pass

def mk(v: int) -> Just:
    return Just(v)

def proj(x: Just) -> int:
    return x.value

def check(x: object) -> bool:
    return isinstance(x, Just)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "nominal_adt_class_lane.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("struct Just : public Maybe {", cpp)
        self.assertIn("rc<Just> mk(int64 v) {", cpp)
        self.assertIn("return ::rc_new<Just>(v);", cpp)
        self.assertIn("int64 proj(const rc<Just>& x) {", cpp)
        self.assertIn('return obj_to_rc_or_raise<Just>(make_object(x), "Just.value")->value;', cpp)
        self.assertIn("return py_runtime_value_isinstance(x, Just::PYTRA_TYPE_ID);", cpp)

    def test_inheritance_methods_are_emitted_as_virtual_with_override(self) -> None:
        src = """class Base:\n    def inc(self, x: int) -> int:\n        return x + 1\n\nclass Child(Base):\n    def inc(self, x: int) -> int:\n        return x + 2\n\n    def base_only(self, x: int) -> int:\n        return x\n"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "virtual_override.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("virtual int64 inc(int64 x) const {", cpp)
        self.assertIn("int64 inc(int64 x) const override {", cpp)
        self.assertIn("int64 base_only(int64 x) const {", cpp)
        self.assertNotIn("virtual int64 inc(int64 x) const override {", cpp)

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

        self.assertIn("virtual int64 f(int64 x) const {", cpp)
        self.assertIn("int64 f(int64 x) const override {", cpp)
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

        self.assertIn("virtual int64 f(int64 x) const {", cpp)
        self.assertIn("int64 f(int64 x) const override {", cpp)
        self.assertIn("return Base::f(x) + 1;", cpp)
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

        self.assertIn("py_runtime_value_isinstance(x, Base::PYTRA_TYPE_ID)", cpp)
        self.assertIn("py_runtime_value_isinstance(x, Child::PYTRA_TYPE_ID)", cpp)
        self.assertIn("py_runtime_value_isinstance(x, PYTRA_TID_INT)", cpp)
        self.assertIn("py_runtime_value_isinstance(x, PYTRA_TID_STR)", cpp)
        self.assertIn("py_runtime_value_isinstance(x, PYTRA_TID_OBJECT)", cpp)
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

        self.assertIn("virtual int64 inc(int64 x) const {", cpp)
        self.assertNotIn("virtual int64 unused(int64 x) const {", cpp)

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

        self.assertIn("rc<list<int64>> xs = rc_list_from_value(list<int64>{1, 2});", cpp)
        self.assertIn("rc_list_ref(xs).append(3);", cpp)
        self.assertIn("rc_list_ref(xs).extend(list<int64>{4, 5});", cpp)
        self.assertIn("auto v = rc_list_ref(xs).pop();", cpp)
        self.assertIn(
            "int64 head = py_list_at_ref(rc_list_ref(xs), 0);",
            cpp,
        )
        self.assertIn("rc<list<int64>> seg = rc_list_from_value(py_list_slice_copy(rc_list_ref(xs), 0, 2));", cpp)

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

        self.assertIn("rc<list<int64>> f(const rc<list<int64>>& xs)", cpp)
        self.assertIn("return rc_list_from_value([&]() -> list<int64> {", cpp)
        self.assertIn("list<int64> __out;", cpp)
        self.assertIn("for (auto x : rc_list_ref(xs)) {", cpp)
        self.assertIn("return __out;", cpp)

    def test_pyobj_list_model_local_list_comprehension_keeps_rc_handle(self) -> None:
        src = """def f(xs: list[int]) -> int:
    ys: list[int] = [x + 1 for x in xs]
    return ys[0]
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "pyobj_list_model_local_list_comp.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            em = CppEmitter(east, {}, emit_main=False)
            em.cpp_list_model = "pyobj"
            cpp = em.transpile()

        self.assertIn("rc<list<int64>> ys = rc_list_from_value([&]() -> list<int64> {", cpp)
        self.assertIn("for (auto x : rc_list_ref(xs)) {", cpp)
        self.assertIn(
            "return py_list_at_ref(rc_list_ref(ys), 0);",
            cpp,
        )

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

        self.assertIn("rc<list<int64>> xs = rc_list_from_value(list<int64>{});", cpp)
        self.assertIn("rc_list_ref(xs).append(1);", cpp)
        self.assertIn("int64 sink(const rc<list<int64>>& xs) {", cpp)
        self.assertIn("return sink(xs);", cpp)

    def test_pyobj_list_model_nested_subscript_assign_uses_mutable_inner_list_ref(self) -> None:
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

        self.assertIn("void paint(rc<list<list<int64>>>& grid, int64 x, int64 y) {", cpp)
        self.assertIn(
            "py_list_at_ref(py_list_at_ref(rc_list_ref(grid), y), x) = 1;",
            cpp,
        )
        self.assertNotIn("py_set_at(", cpp)

    def test_pyobj_list_model_module_global_typed_list_subscript_assign_stays_direct(self) -> None:
        src = """state: list[int] = [1]
def bump(v: int) -> None:
    state[0] = v
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "pyobj_global_list_assign.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            em = CppEmitter(east, {}, emit_main=False)
            em.cpp_list_model = "pyobj"
            cpp = em.transpile()

        self.assertIn("list<int64> state;", cpp)
        self.assertIn("state[0] = v;", cpp)
        self.assertNotIn("py_set_at(state", cpp)

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

        self.assertIn("py_repeat(list<int64>(list<int64>{0}), w)", cpp)
        self.assertNotIn("py_repeat(make_object(list<int64>{0}), w)", cpp)

    def test_pyobj_list_model_keeps_ref_first_list_when_call_target_param_cannot_prove_non_escape(self) -> None:
        sample_py = ROOT / "sample" / "py" / "12_sort_visualizer.py"
        east = load_east(sample_py)
        em = CppEmitter(east, {}, emit_main=False)
        em.cpp_list_model = "pyobj"
        cpp = em.transpile()

        self.assertIn("rc<list<int64>> values = rc_list_from_value(list<int64>{});", cpp)
        self.assertIn("bytes render(const rc<list<int64>>& values, int64 w, int64 h) {", cpp)
        self.assertIn("render(values, w, h)", cpp)
        self.assertNotIn("list<int64> values = {};", cpp)

    def test_pyobj_list_model_module_call_handle_return_survives_unbox(self) -> None:
        src = """import random
def f(xs: list[int], ws: list[float]) -> int:
    picked: list[int] = random.choices(xs, ws)
    return picked[0]
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "pyobj_random_choices_handle.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            em = CppEmitter(east, {}, emit_main=False)
            em.cpp_list_model = "pyobj"
            cpp = em.transpile()

        self.assertIn("rc<list<int64>> picked = pytra::std::random::choices(xs, ws);", cpp)
        self.assertNotIn("rc_list_from_value(list<int64>(pytra::std::random::choices(xs, ws)))", cpp)

    def test_pyobj_list_model_dynamic_dict_values_unboxes_to_rc_list(self) -> None:
        src = """def f(d: dict[str, int]) -> int:
    ks: list[str] = d.keys()
    vs: list[int] = d.values()
    return len(ks) + vs[0]
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "pyobj_dict_values_rc_list.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            em = CppEmitter(east, {}, emit_main=False)
            em.cpp_list_model = "pyobj"
            cpp = em.transpile()

        self.assertIn("rc<list<str>> ks = rc_list_from_value(([&]() -> list<str> {", cpp)
        self.assertIn("push_back(__kv.first);", cpp)
        self.assertIn("rc<list<int64>> vs = rc_list_from_value(([&]() -> list<int64> {", cpp)
        self.assertIn("push_back(__kv.second);", cpp)
        self.assertNotIn("rc<list<int64>> vs = list<int64>(py_dict_values(d));", cpp)

    def test_pyobj_list_model_nested_list_append_copies_inner_value(self) -> None:
        src = """def f() -> list[list[int]]:
    out: list[list[int]] = []
    row: list[int] = []
    row.append(1)
    out.append(row)
    return out
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "pyobj_nested_list_append.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            em = CppEmitter(east, {}, emit_main=False)
            em.cpp_list_model = "pyobj"
            cpp = em.transpile()

        self.assertIn("rc_list_ref(out).append(rc_list_copy_value(row));", cpp)
        self.assertNotIn("py_append(out, row);", cpp)
        self.assertNotIn("render(rc_list_from_value(values), w, h)", cpp)

    def test_pyobj_list_model_tuple_subscript_uses_structured_binding_on_declare_unpack(self) -> None:
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

        self.assertIn(
            "auto [x, y] = py_list_at_ref(rc_list_ref(stack), -(1));",
            cpp,
        )
        self.assertNotIn("auto __tuple_1 = py_at(stack, -1);", cpp)
        self.assertNotIn("::std::get<0>(__tuple_1)", cpp)
        self.assertNotIn("::std::get<1>(__tuple_1)", cpp)

    def test_pyobj_list_model_tuple_subscript_reassign_keeps_get_fallback(self) -> None:
        src = """def f(stack: list[tuple[int, int]]) -> int:
    x: int = 0
    y: int = 0
    x, y = stack[-1]
    return x + y
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "pyobj_tuple_subscript_reassign.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            em = CppEmitter(east, {}, emit_main=False)
            em.cpp_list_model = "pyobj"
            cpp = em.transpile()

        self.assertIn(
            "auto __tuple_1 = py_list_at_ref(rc_list_ref(stack), -(1));",
            cpp,
        )
        self.assertIn("x = ::std::get<0>(__tuple_1);", cpp)
        self.assertIn("y = ::std::get<1>(__tuple_1);", cpp)
        self.assertNotIn("auto [x, y] = py_at(stack, -1);", cpp)

    def test_pyobj_list_model_keeps_rc_handle_when_typed_list_aliases(self) -> None:
        src = """def f() -> int:
    xs: list[int] = []
    ys = xs
    ys.append(1)
    return xs[0]
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "pyobj_typed_list_alias.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            em = CppEmitter(east, {}, emit_main=False)
            em.cpp_list_model = "pyobj"
            cpp = em.transpile()

        self.assertIn("rc<list<int64>> xs = rc_list_from_value(list<int64>{});", cpp)
        self.assertIn("rc<list<int64>> ys = xs;", cpp)
        self.assertIn("rc_list_ref(ys).append(1);", cpp)
        self.assertIn(
            "return py_list_at_ref(rc_list_ref(xs), 0);",
            cpp,
        )
        self.assertNotIn("list<int64> ys = xs;", cpp)

    def test_pyobj_list_model_keeps_rc_handle_until_typed_call_boundary(self) -> None:
        src = """def sink(xs: list[str]) -> str:
    return xs[0]

def f() -> str:
    xs: list[str] = []
    ys = xs
    ys.append("a")
    return sink(ys)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "pyobj_typed_list_alias_call.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            em = CppEmitter(east, {}, emit_main=False)
            em.cpp_list_model = "pyobj"
            cpp = em.transpile()

        self.assertIn("rc<list<str>> xs = rc_list_from_value(list<str>{});", cpp)
        self.assertIn("rc<list<str>> ys = xs;", cpp)
        self.assertIn('rc_list_ref(ys).append("a");', cpp)
        self.assertIn("return sink(ys);", cpp)
        self.assertNotIn("list<str> ys = xs;", cpp)

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

        self.assertIn("list<int64> xs = {};", cpp)
        self.assertIn("xs.append(1);", cpp)
        self.assertIn("xs.append(2);", cpp)
        self.assertIn("int64 head = xs[0];", cpp)
        self.assertNotIn("py_append(xs", cpp)
        self.assertNotIn("py_at(xs", cpp)

    def test_pyobj_list_model_optimizer_off_keeps_safe_local_list_ref_first(self) -> None:
        src = """def f() -> int:
    xs: list[int] = []
    xs.append(1)
    xs.append(2)
    head: int = xs[0]
    return head + len(xs)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "pyobj_stack_local_list_opt0.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, east3_opt_level="0")
            em = CppEmitter(east, {}, emit_main=False)
            em.cpp_list_model = "pyobj"
            cpp = em.transpile()

        self.assertIn("rc<list<int64>> xs = rc_list_from_value(list<int64>{});", cpp)
        self.assertIn("rc_list_ref(xs).append(1);", cpp)
        self.assertIn("rc_list_ref(xs).append(2);", cpp)
        self.assertIn(
            "int64 head = py_list_at_ref(rc_list_ref(xs), 0);",
            cpp,
        )
        self.assertNotIn("list<int64> xs = {};", cpp)
        self.assertNotIn("xs.append(int64(1));", cpp)
        self.assertNotIn("int64 head = xs[0];", cpp)

    def test_pyobj_list_model_optimizer_off_keeps_nested_grid_ref_first_and_mutable(self) -> None:
        src = """def paint(w: int, h: int, x: int, y: int) -> int:
    grid: list[list[int]] = [[0] * w for _ in range(h)]
    grid[y][x] = 1
    return grid[y][x]
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "pyobj_nested_grid_opt0.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, east3_opt_level="0")
            em = CppEmitter(east, {}, emit_main=False)
            em.cpp_list_model = "pyobj"
            cpp = em.transpile()

        self.assertIn("rc<list<list<int64>>> grid = py_to<rc<list<list<int64>>>>([&]() -> object {", cpp)
        self.assertIn(
            "py_list_at_ref(py_list_at_ref(rc_list_ref(grid), y), x) = 1;",
            cpp,
        )
        self.assertIn(
            "return py_list_at_ref(py_list_at_ref(rc_list_ref(grid), y), x);",
            cpp,
        )
        self.assertNotIn("rc_list_from_value([&]() -> object {", cpp)

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

        self.assertIn("rc<list<int64>> xs = rc_list_from_value(list<int64>{});", cpp)
        self.assertIn("rc_list_ref(xs).append(1);", cpp)
        self.assertIn("return sink(xs);", cpp)

    def test_pyobj_list_model_call_subscript_uses_typed_list_helper(self) -> None:
        src = """def make() -> list[int]:
    xs: list[int] = []
    xs.append(1)
    return xs

def f() -> int:
    return make()[0]
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "pyobj_call_subscript.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            em = CppEmitter(east, {}, emit_main=False)
            em.cpp_list_model = "pyobj"
            cpp = em.transpile()

        self.assertIn(
            "return py_list_at_ref(rc_list_ref(make()), 0);",
            cpp,
        )
        self.assertNotIn("return make()[0];", cpp)

    def test_pyobj_list_model_typed_for_loop_uses_ref_first_iterable(self) -> None:
        src = """def f(xs: list[int]) -> int:
    s: int = 0
    for x in xs:
        s += x
    return s
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "pyobj_for_param_list.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            em = CppEmitter(east, {}, emit_main=False)
            em.cpp_list_model = "pyobj"
            cpp = em.transpile()

        self.assertIn("for (int64 x : rc_list_ref(xs)) {", cpp)
        self.assertNotIn("for (object __itobj_", cpp)
        self.assertNotIn("py_dyn_range(xs)", cpp)

    def test_pyobj_list_model_call_returned_list_iteration_hoists_handle_tmp(self) -> None:
        src = """def make() -> list[int]:
    xs: list[int] = []
    xs.append(1)
    return xs

def f() -> int:
    s: int = 0
    for x in make():
        s += x
    return s
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "pyobj_for_call_list.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            em = CppEmitter(east, {}, emit_main=False)
            em.cpp_list_model = "pyobj"
            cpp = em.transpile()

        self.assertIn("auto __iter_list_", cpp)
        self.assertIn("for (int64 x : rc_list_ref(__iter_list_", cpp)
        self.assertNotIn("py_dyn_range(make())", cpp)

    def test_pyobj_list_model_call_enumerate_uses_typed_unpack(self) -> None:
        src = """def make() -> list[int]:
    xs: list[int] = []
    xs.append(1)
    return xs

def f() -> int:
    s: int = 0
    for i, x in enumerate(make()):
        s += x
    return s
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "pyobj_enumerate_call_list.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            em = CppEmitter(east, {}, emit_main=False)
            em.cpp_list_model = "pyobj"
            cpp = em.transpile()

        self.assertIn("for (const auto& [i, x] : py_enumerate(make())) {", cpp)
        self.assertNotIn("for (object __itobj_", cpp)
        self.assertNotIn("py_dyn_range(py_enumerate(make()))", cpp)

    def test_pyobj_list_model_call_reversed_uses_typed_loop(self) -> None:
        src = """def make() -> list[int]:
    xs: list[int] = []
    xs.append(1)
    return xs

def f() -> int:
    total: int = 0
    for x in reversed(make()):
        total += x
    return total
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "pyobj_reversed_call_list.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            em = CppEmitter(east, {}, emit_main=False)
            em.cpp_list_model = "pyobj"
            cpp = em.transpile()

        self.assertIn("for (int64 x : py_reversed(make())) {", cpp)
        self.assertNotIn("for (object x : py_dyn_range(py_reversed(make()))) {", cpp)

    def test_pyobj_list_model_call_method_dispatch_uses_py_helpers(self) -> None:
        src = """def make() -> list[int]:
    xs: list[int] = []
    return xs

def f() -> list[int]:
    make().append(1)
    return make()
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "pyobj_call_method_dispatch.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            em = CppEmitter(east, {}, emit_main=False)
            em.cpp_list_model = "pyobj"
            cpp = em.transpile()

        self.assertIn("([&]() { auto __list_1 = make(); rc_list_ref(__list_1).append(1); }());", cpp)
        self.assertNotIn("make().append(int64(1));", cpp)

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

        self.assertIn("rc<list<int64>> xs = rc_list_from_value(list<int64>{});", cpp)
        self.assertIn("rc_list_ref(xs).append(1);", cpp)
        self.assertIn("int64 n = (rc_list_ref(xs)).size();", cpp)

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

        self.assertIn("rc<list<int64>> xs = rc_list_from_value(list<int64>{});", cpp)
        self.assertIn("rc_list_ref(xs).append(1);", cpp)

    def test_pyobj_list_model_abi_value_helper_uses_value_signature_and_adapters(self) -> None:
        src = """from pytra.std import abi

@abi(args={"xs": "value"}, ret="value")
def clone(xs: list[int]) -> list[int]:
    return xs

def make() -> list[int]:
    xs: list[int] = []
    xs.append(1)
    xs.append(2)
    return xs

def use(xs: list[int]) -> list[int]:
    ys: list[int] = clone(xs)
    zs: list[int] = clone(make())
    return clone(zs)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "abi_value_helper.py"
            out_h = Path(tmpdir) / "abi_value_helper.h"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False, cpp_list_model="pyobj")
            header = build_cpp_header_from_east(east, src_py, out_h, cpp_list_model="pyobj")

        self.assertIn("list<int64> clone(const list<int64>& xs)", cpp)
        self.assertIn("rc<list<int64>> make()", cpp)
        self.assertIn("rc<list<int64>> use(const rc<list<int64>>& xs)", cpp)
        self.assertIn("return xs;", cpp)
        self.assertIn("rc<list<int64>> ys = rc_list_from_value(clone(rc_list_ref(xs)));", cpp)
        self.assertIn("rc<list<int64>> zs = rc_list_from_value(clone(rc_list_copy_value(make())));", cpp)
        self.assertIn("return rc_list_from_value(clone(rc_list_ref(zs)));", cpp)
        self.assertIn("list<int64> clone(const list<int64>& xs);", header)
        self.assertIn("rc<list<int64>> use(const rc<list<int64>>& xs);", header)

    def test_pyobj_list_model_extern_and_abi_helper_still_uses_value_signature(self) -> None:
        src = """from pytra.std import extern, abi

@extern
@abi(args={"xs": "value"}, ret="value")
def clone(xs: list[int]) -> list[int]:
    return xs

def use(xs: list[int]) -> list[int]:
    return clone(xs)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "extern_abi_value_helper.py"
            out_h = Path(tmpdir) / "extern_abi_value_helper.h"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False, cpp_list_model="pyobj")
            header = build_cpp_header_from_east(east, src_py, out_h, cpp_list_model="pyobj")

        self.assertIn("list<int64> clone(const list<int64>& xs)", cpp)
        self.assertIn("rc<list<int64>> use(const rc<list<int64>>& xs)", cpp)
        self.assertIn("return rc_list_from_value(clone(rc_list_ref(xs)));", cpp)
        self.assertIn("list<int64> clone(const list<int64>& xs);", header)
        self.assertIn("rc<list<int64>> use(const rc<list<int64>>& xs);", header)


    # --- S3-01: subscript index identity cast elision tests ---

    def test_subscript_index_int64_var_elides_py_to_int64(self) -> None:
        """int64 型変数を list 添字に使う場合は py_to<int64> ラップを省略する。"""
        src = """def f(xs: list[int], i: int) -> int:
    return xs[i]
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "subscript_int64_var.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertNotIn("py_to<int64>(i)", cpp)
        self.assertIn("xs[i]", cpp)

    def test_subscript_index_int64_const_elides_py_to_int64(self) -> None:
        """resolved_type が int64 の定数 index は py_to<int64> ラップを省略する。"""
        src = """def f(xs: list[int]) -> int:
    return xs[0]
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "subscript_int64_const.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertNotIn("py_to<int64>(0)", cpp)

    def test_subscript_index_any_keeps_py_to_int64(self) -> None:
        """object/Any 境界の index は py_to<int64> を維持する（fail-closed）。"""
        src = """def f(xs: list[int], idx: object) -> int:
    return xs[idx]
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "subscript_any_idx.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("py_to<int64>(idx)", cpp)

    def test_tuple_const_index_emits_std_get(self) -> None:
        """タプル定数 index アクセスは std::get<I> を直接 emit する。"""
        src = """def f(t: tuple[int, str]) -> int:
    return t[0]
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "tuple_const_index.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("::std::get<0>(t)", cpp)
        self.assertNotIn("py_at(t,", cpp)
        self.assertNotIn("py_to<int64>", cpp)

    def test_tuple_dynamic_index_with_int64_var_elides_py_to_int64_in_py_at(self) -> None:
        """タプル非定数 index で index 型が int64 の場合は py_at の引数の py_to<int64> を省略する。"""
        src = """def f(i: int) -> object:
    t: tuple[int, int, int] = (10, 20, 30)
    return t[i]
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "tuple_dynamic_int64_index.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)

        self.assertIn("py_at(t, i)", cpp)
        self.assertNotIn("py_to<int64>(i)", cpp)

    def test_subscript_lvalue_int64_var_elides_py_to_int64(self) -> None:
        """左辺値文脈でも index が int64 の場合は py_to<int64> を省略する。"""
        src = """def f(xs: list[int], i: int, v: int) -> None:
    xs[i] = v
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "subscript_lval_int64.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            em = CppEmitter(east, {}, emit_main=False)
            em.cpp_list_model = "pyobj"
            cpp = em.transpile()

        self.assertIn("py_list_at_ref(rc_list_ref(xs), i) = v;", cpp)
        self.assertNotIn("py_to<int64>(i)", cpp)


if __name__ == "__main__":
    unittest.main()
