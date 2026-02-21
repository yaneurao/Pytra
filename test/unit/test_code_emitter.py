"""Regression tests for shared CodeEmitter utilities."""

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

from src.pytra.compiler.east_parts.code_emitter import CodeEmitter, EmitterHooks


class _DummyEmitter(CodeEmitter):
    def emit_stmt(self, stmt: Any) -> None:
        self.emit(f"stmt:{self.any_to_str(stmt)}")

    def render_expr(self, expr: Any) -> str:
        if isinstance(expr, dict):
            rep = expr.get("repr")
            if isinstance(rep, str):
                return rep
        return "<?>"


class _HookedEmitter(_DummyEmitter):
    def hook_on_emit_stmt(self, stmt: dict[str, Any]) -> Any:
        if isinstance(stmt, dict) and stmt.get("kind") == "Pass":
            self.emit("// hooked")
            return True
        return None

    def hook_on_emit_stmt_kind(self, kind: str, stmt: dict[str, Any]) -> Any:
        if kind == "Return":
            self.emit("// hooked-kind-return")
            return True
        return None

    def hook_on_render_call(
        self,
        call_node: dict[str, Any],
        func_node: dict[str, Any],
        rendered_args: list[str],
        rendered_kwargs: dict[str, str],
    ) -> Any:
        if func_node.get("kind") == "Name" and func_node.get("id") == "hooked":
            return "hooked_call()"
        return None

    def hook_on_render_expr_kind(
        self,
        kind: str,
        expr_node: dict[str, Any],
    ) -> Any:
        if kind == "MagicExpr":
            return "magic_expr()"
        return None

    def hook_on_render_expr_complex(self, expr_node: dict[str, Any]) -> Any:
        if expr_node.get("kind") == "JoinedStr":
            return "complex_expr()"
        return None

    def hook_on_render_binop(
        self,
        binop_node: dict[str, Any],
        left: str,
        right: str,
    ) -> Any:
        if binop_node.get("kind") == "BinOp":
            return f"hooked_binop({left}, {right})"
        return None


class CodeEmitterTest(unittest.TestCase):
    class _KindLike:
        def __init__(self, text: str) -> None:
            self.text = text

        def __str__(self) -> str:
            return self.text

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
        em = CodeEmitter({})
        self.assertEqual(em.any_dict_get({"x": 1}, "x", 9), 1)
        self.assertEqual(em.any_dict_get({"x": 1}, "y", 9), 9)
        self.assertEqual(em.any_dict_get(3, "x", 9), 9)

        self.assertEqual(em.any_to_dict({"a": 1}), {"a": 1})
        self.assertIsNone(em.any_to_dict([]))

        self.assertEqual(em.any_to_list([1, 2]), [1, 2])
        self.assertEqual(em.any_to_list({"x": 1}), [])
        self.assertEqual(em.any_to_dict_list([{"x": 1}, 2, "s"]), [{"x": 1}])
        self.assertEqual(em.any_to_dict_list(None), [])

        self.assertEqual(em.any_to_str("abc"), "abc")
        self.assertEqual(em.any_to_str(10), "")

    def test_any_helpers_boundary_cases(self) -> None:
        em = CodeEmitter({})
        self.assertEqual(em.any_to_dict_or_empty({"k": 1}), {"k": 1})
        self.assertEqual(em.any_to_dict_or_empty(None), {})
        self.assertEqual(em.any_to_dict_or_empty([]), {})
        self.assertEqual(em.any_to_dict_or_empty("x"), {})
        self.assertEqual(em.any_to_dict_or_empty(0), {})

        self.assertEqual(em.any_to_list(["a", 1]), ["a", 1])
        self.assertEqual(em.any_to_list(None), [])
        self.assertEqual(em.any_to_list({"x": 1}), [])
        self.assertEqual(em.any_to_dict_list([{"x": 1}, None, {"y": 2}]), [{"x": 1}, {"y": 2}])
        self.assertEqual(em.any_to_str_dict_or_empty({"a": "b", "c": 1}), {"a": "b", "c": ""})
        self.assertEqual(em.any_to_str_dict_or_empty(None), {})

        self.assertEqual(em.any_dict_get_str({"x": "ok"}, "x", "ng"), "ok")
        self.assertEqual(em.any_dict_get_str({"x": 1}, "x", "ng"), "ng")
        self.assertEqual(em.any_dict_get_str(None, "x", "ng"), "ng")
        self.assertEqual(em.any_dict_get_int({"x": 2}, "x", 9), 2)
        self.assertEqual(em.any_dict_get_int({"x": "2"}, "x", 9), 9)
        self.assertEqual(em.any_dict_get_int(None, "x", 9), 9)
        self.assertTrue(em.any_dict_get_bool({"x": True}, "x", False))
        self.assertFalse(em.any_dict_get_bool({"x": 1}, "x", False))
        self.assertEqual(em.any_dict_get_list({"x": [1, 2]}, "x"), [1, 2])
        self.assertEqual(em.any_dict_get_list({"x": "not-list"}, "x"), [])
        self.assertEqual(em.any_dict_get_dict({"x": {"k": 1}}, "x"), {"k": 1})
        self.assertEqual(em.any_dict_get_dict({"x": 3}, "x"), {})

    def test_merge_call_args(self) -> None:
        em = CodeEmitter({})
        self.assertEqual(em.merge_call_args(["a", "b"], {}), ["a", "b"])
        self.assertEqual(
            em.merge_call_args(["a"], {"k1": "x", "k2": "y"}),
            ["a", "x", "y"],
        )
        self.assertEqual(
            em.merge_call_kw_values(["a"], ["x", "y"]),
            ["a", "x", "y"],
        )
        self.assertEqual(
            em.merge_call_arg_nodes([{"k": 1}], ["n1", "n2"]),
            [{"k": 1}, "n1", "n2"],
        )
        self.assertEqual(
            em._dict_stmt_list([{"x": 1}, 2, "s", {"y": 2}]),
            [{"x": 1}, {"y": 2}],
        )
        unpacked = em.unpack_prepared_call_parts(
            {
                "fn": {"kind": "Name", "id": "f"},
                "fn_name": "f",
                "arg_nodes": [{"kind": "Name", "id": "x"}],
                "args": ["x"],
                "kw": {"k": "v"},
                "kw_values": ["v"],
                "kw_nodes": [{"kind": "Constant", "value": 1}],
                "first_arg": {"kind": "Name", "id": "x"},
            }
        )
        self.assertEqual(unpacked.get("fn"), {"kind": "Name", "id": "f"})
        self.assertEqual(unpacked.get("fn_name"), "f")
        self.assertEqual(unpacked.get("arg_nodes"), [{"kind": "Name", "id": "x"}])
        self.assertEqual(unpacked.get("args"), ["x"])
        self.assertEqual(unpacked.get("kw"), {"k": "v"})
        self.assertEqual(unpacked.get("kw_values"), ["v"])
        self.assertEqual(unpacked.get("kw_nodes"), [{"kind": "Constant", "value": 1}])

    def test_node_helpers(self) -> None:
        em = CodeEmitter({})
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
        self.assertEqual(em.get_expr_type({"resolved_type": self._KindLike("list[int64]")}), "list[int64]")
        self.assertEqual(em.node_kind({"kind": "Call"}), "Call")
        self.assertEqual(em.node_kind({"kind": self._KindLike("Attribute")}), "Attribute")
        self.assertEqual(em.node_kind({"kind": 1}), "")
        self.assertEqual(
            em.render_name_ref({"kind": "Name", "id": "class"}, {"class"}, "py_", {}, "_"),
            "py_class",
        )
        self.assertEqual(
            em.render_name_ref({"kind": "Name", "id": self._KindLike("value")}, set(), "_", {}, "_"),
            "value",
        )
        self.assertEqual(em.render_name_ref({}, set(), "_", {}, "_"), "_")

    def test_scope_and_expr_helpers(self) -> None:
        em = CodeEmitter({})
        self.assertEqual(em.current_scope(), set())
        em.current_scope().add("x")
        self.assertTrue(em.is_declared("x"))
        em.scope_stack.append(set(["y"]))
        self.assertTrue(em.is_declared("x"))
        self.assertTrue(em.is_declared("y"))
        self.assertFalse(em.is_declared("z"))

        self.assertTrue(em._is_identifier_expr("abc_1"))
        self.assertFalse(em._is_identifier_expr("1abc"))
        self.assertFalse(em._is_identifier_expr("a-b"))

        self.assertEqual(em._strip_outer_parens(" ( (x + 1) ) "), "x + 1")
        self.assertEqual(em._strip_outer_parens("(x) + (y)"), "(x) + (y)")
        self.assertEqual(em._strip_outer_parens('(")")'), '")"')

        self.assertTrue(em.is_plain_name_expr({"kind": "Name", "id": "v"}))
        self.assertFalse(em.is_plain_name_expr({"kind": "Call"}))
        self.assertTrue(em._expr_repr_eq({"repr": "a + b "}, {"repr": "a + b"}))
        self.assertFalse(em._expr_repr_eq({"repr": "a + b"}, {"repr": "a - b"}))
        self.assertTrue(em._contains_text("abcdef", "cd"))
        self.assertFalse(em._contains_text("abcdef", "xy"))
        self.assertEqual(em._last_dotted_name("a.b.c"), "c")
        self.assertEqual(em._last_dotted_name("name"), "name")

    def test_import_resolution_helpers(self) -> None:
        em = CodeEmitter(
            {
                "meta": {
                    "qualified_symbol_refs": [
                        {"module_id": "m.a", "symbol": "f", "local_name": "af"},
                    ],
                    "import_bindings": [
                        {
                            "module_id": "m.b",
                            "export_name": "g",
                            "local_name": "bg",
                            "binding_kind": "symbol",
                        },
                    ],
                }
            }
        )
        em.import_modules = {"m": "pkg.mod"}
        em.import_symbols = {"s": {"module": "pkg.sym", "name": "fn"}}
        self.assertEqual(em._resolve_imported_module_name("m"), "pkg.mod")
        self.assertEqual(em._resolve_imported_module_name("s"), "pkg.sym.fn")
        self.assertEqual(em._resolve_imported_module_name("x"), "")
        self.assertEqual(em._resolve_imported_symbol("s"), {"module": "pkg.sym", "name": "fn"})
        self.assertEqual(em._resolve_imported_symbol("af"), {"module": "m.a", "name": "f"})
        self.assertEqual(em._resolve_imported_symbol("bg"), {"module": "m.b", "name": "g"})
        self.assertEqual(em._resolve_imported_symbol("none"), {})

    def test_imported_module_name_fallback_via_meta(self) -> None:
        em = CodeEmitter(
            {
                "meta": {
                    "qualified_symbol_refs": [
                        {"module_id": "pytra.runtime", "symbol": "png", "local_name": "png"},
                    ],
                    "import_bindings": [
                        {
                            "module_id": "pytra.std",
                            "export_name": "math",
                            "local_name": "m",
                            "binding_kind": "symbol",
                        },
                    ],
                }
            }
        )
        self.assertEqual(em.import_symbols, {})
        self.assertEqual(em._resolve_imported_module_name("png"), "pytra.runtime.png")
        self.assertEqual(em._resolve_imported_module_name("m"), "pytra.std.math")

    def test_attribute_owner_context_and_type_helpers(self) -> None:
        em = _DummyEmitter({})
        em.import_modules = {"png": "pytra.runtime.png"}
        owner_ctx = em.resolve_attribute_owner_context(
            {"kind": "Name", "id": "png", "repr": "png"},
            "png",
        )
        self.assertEqual(owner_ctx.get("kind"), "Name")
        self.assertEqual(owner_ctx.get("expr"), "png")
        self.assertEqual(owner_ctx.get("module"), "pytra.runtime.png")
        self.assertEqual(em.attr_name({"kind": "Attribute", "attr": "write_rgb_png"}), "write_rgb_png")
        self.assertEqual(em.attr_name({"kind": "Attribute", "attr": None}), "")
        declared = {"items": "list[int64]"}
        owner_t = em.resolve_attribute_owner_type(
            {"kind": "Name", "id": "items", "resolved_type": "unknown"},
            {"kind": "Name", "id": "items"},
            declared,
        )
        self.assertEqual(owner_t, "list[int64]")
        owner_t_unknown = em.resolve_attribute_owner_type(
            {"kind": "Name", "id": "x", "resolved_type": "unknown"},
            {"kind": "Name", "id": "x"},
            {"x": "unknown"},
        )
        self.assertEqual(owner_t_unknown, "unknown")

    def test_can_runtime_cast_target(self) -> None:
        em = CodeEmitter({})
        self.assertFalse(em._can_runtime_cast_target(""))
        self.assertFalse(em._can_runtime_cast_target("unknown"))
        self.assertFalse(em._can_runtime_cast_target("Any"))
        self.assertFalse(em._can_runtime_cast_target("object"))
        self.assertFalse(em._can_runtime_cast_target("int64|None"))
        self.assertTrue(em._can_runtime_cast_target("int64"))
        self.assertTrue(em._can_runtime_cast_target("float64"))
        self.assertTrue(em._is_std_runtime_call("std::sqrt"))
        self.assertTrue(em._is_std_runtime_call("::std::abs"))
        self.assertFalse(em._is_std_runtime_call("py_len"))

    def test_validate_call_receiver_or_raise(self) -> None:
        em = CodeEmitter({})
        em.validate_call_receiver_or_raise({"kind": "Name", "id": "f"})
        em.validate_call_receiver_or_raise(
            {
                "kind": "Attribute",
                "attr": "append",
                "value": {"kind": "Name", "id": "xs", "resolved_type": "list[int64]"},
            }
        )
        with self.assertRaises(RuntimeError):
            em.validate_call_receiver_or_raise(
                {
                    "kind": "Attribute",
                    "attr": "append",
                    "value": {"kind": "Name", "id": "v", "resolved_type": "object"},
                }
            )

    def test_trivia_and_cond_helpers(self) -> None:
        em = _DummyEmitter(
            {
                "module_leading_trivia": [
                    {"kind": "comment", "text": "file header"},
                    {"kind": "blank", "count": 1},
                ]
            }
        )
        em.emit_module_leading_trivia()
        em.emit_leading_comments(
            {
                "leading_trivia": [
                    "invalid",
                    {"kind": "comment", "text": "stmt comment"},
                    {"kind": "blank", "count": 2},
                ]
            }
        )
        self.assertEqual(
            em.lines,
            [
                "// file header",
                "",
                "// stmt comment",
                "",
                "",
            ],
        )

        self.assertEqual(
            em.render_cond({"resolved_type": "bool", "repr": "(flag)"}),
            "flag",
        )
        self.assertEqual(
            em.render_cond({"resolved_type": "list[int64]", "repr": " (xs) "}),
            "py_len(xs) != 0",
        )
        self.assertEqual(em.render_cond(None), "false")

        # Base CodeEmitter.render_expr returns an empty string, so
        # lock the repr-fallback path here (for selfhost stabilization).
        em_base = CodeEmitter({})
        self.assertEqual(
            em_base.render_cond(
                {
                    "resolved_type": self._KindLike("str"),
                    "repr": self._KindLike("xs"),
                }
            ),
            "py_len(xs) != 0",
        )
        self.assertEqual(
            em_base.render_cond(
                {
                    "resolved_type": self._KindLike("bool"),
                    "repr": self._KindLike("(flag)"),
                }
            ),
            "flag",
        )

    def test_negative_index_and_super_helpers(self) -> None:
        em = CodeEmitter({})
        self.assertTrue(em._is_negative_const_index({"kind": "Constant", "value": -1}))
        self.assertTrue(
            em._is_negative_const_index(
                {
                    "kind": "UnaryOp",
                    "op": "USub",
                    "operand": {"kind": "Constant", "value": 2},
                }
            )
        )
        self.assertFalse(em._is_negative_const_index({"kind": "Constant", "value": 0}))
        self.assertFalse(em._is_negative_const_index({"kind": "Name", "id": "i"}))

        super_init = {
            "kind": "Call",
            "func": {
                "kind": "Attribute",
                "attr": "__init__",
                "value": {
                    "kind": "Call",
                    "func": {"kind": "Name", "id": "super"},
                    "args": [],
                    "keywords": [],
                },
            },
            "args": [],
            "keywords": [],
        }
        self.assertTrue(em._is_redundant_super_init_call(super_init))
        super_init_dynamic_kind = {
            "kind": self._KindLike("Call"),
            "func": {
                "kind": self._KindLike("Attribute"),
                "attr": "__init__",
                "value": {
                    "kind": self._KindLike("Call"),
                    "func": {"kind": self._KindLike("Name"), "id": "super"},
                    "args": [],
                    "keywords": [],
                },
            },
            "args": [],
            "keywords": [],
        }
        self.assertTrue(em._is_redundant_super_init_call(super_init_dynamic_kind))
        not_super = {
            "kind": "Call",
            "func": {"kind": "Name", "id": "f"},
            "args": [],
            "keywords": [],
        }
        self.assertFalse(em._is_redundant_super_init_call(not_super))

    def test_literal_helpers(self) -> None:
        em = CodeEmitter({})
        self.assertEqual(em._one_char_str_const({"kind": "Constant", "value": "a"}), "a")
        self.assertEqual(em._one_char_str_const({"kind": "Constant", "value": "\\n"}), "\n")
        self.assertEqual(em._one_char_str_const({"kind": "Constant", "value": "ab"}), "")
        self.assertEqual(em._const_int_literal({"kind": "Constant", "value": 12}), 12)
        self.assertEqual(
            em._const_int_literal(
                {
                    "kind": "UnaryOp",
                    "op": "USub",
                    "operand": {"kind": "Constant", "value": 7},
                }
            ),
            -7,
        )
        self.assertIsNone(em._const_int_literal({"kind": "Constant", "value": "x"}))

    def test_prepare_call_parts_and_ifexp_helpers(self) -> None:
        class _CastEmitter(_DummyEmitter):
            def apply_cast(self, rendered_expr: str, to_type: str) -> str:
                return f"cast<{to_type}>({rendered_expr})"

        em = _CastEmitter({})
        call_node = {
            "kind": "Call",
            "func": {"kind": "Name", "repr": "fn"},
            "args": [{"kind": "Name", "repr": "a"}],
            "keywords": [
                {"arg": "k", "value": {"kind": "Name", "repr": "b"}},
            ],
        }
        parts = em._prepare_call_parts(call_node)
        self.assertEqual(parts.get("fn_name"), "fn")
        self.assertEqual(parts.get("args"), ["a"])
        self.assertEqual(parts.get("kw_values"), ["b"])
        self.assertEqual(parts.get("kw"), {"k": "b"})

        ifexp = {
            "kind": "IfExp",
            "test": {"kind": "Name", "repr": "cond"},
            "body": {"kind": "Name", "repr": "x"},
            "orelse": {"kind": "Name", "repr": "y"},
            "casts": [
                {"on": "body", "to": "int64"},
                {"on": "orelse", "to": "str"},
            ],
        }
        self.assertEqual(
            em._render_ifexp_expr(ifexp),
            "(cond ? cast<int64>(x) : cast<str>(y))",
        )

    def test_split_helpers(self) -> None:
        em = CodeEmitter({})
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

    def test_binop_helpers(self) -> None:
        em = CodeEmitter({})
        self.assertEqual(em._binop_precedence("Mult"), 12)
        self.assertEqual(em._binop_precedence("Add"), 11)
        self.assertEqual(em._binop_precedence("BitOr"), 7)
        self.assertEqual(em._binop_precedence("Unknown"), 0)

        child = {"kind": "BinOp", "op": "Add"}
        wrapped = em._wrap_for_binop_operand("a + b", child, "Mult")
        self.assertEqual(wrapped, "(a + b)")
        right_same_prec = em._wrap_for_binop_operand("a - b", {"kind": "BinOp", "op": "Sub"}, "Sub", True)
        self.assertEqual(right_same_prec, "(a - b)")
        no_wrap = em._wrap_for_binop_operand("x", {"kind": "Name", "id": "x"}, "Add")
        self.assertEqual(no_wrap, "x")
        self.assertTrue(em._opt_ge(2))
        em.opt_level = "1"
        self.assertTrue(em._opt_ge(1))
        self.assertFalse(em._opt_ge(2))

    def test_type_helpers(self) -> None:
        em = CodeEmitter({})
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
        em = CodeEmitter({})
        self.assertTrue(em.is_forbidden_object_receiver_type("Any"))
        self.assertTrue(em.is_forbidden_object_receiver_type("object"))
        self.assertTrue(em.is_forbidden_object_receiver_type("int64|object|None"))
        self.assertTrue(em.is_forbidden_object_receiver_type("str|any"))
        self.assertFalse(em.is_forbidden_object_receiver_type("str|int64|None"))

    def test_profile_syntax_helpers(self) -> None:
        em = CodeEmitter(
            {},
            profile={
                "syntax": {
                    "if_open": "IF({cond})",
                }
            },
        )
        self.assertEqual(em.syntax_text("if_open", "if ({cond}) {"), "IF({cond})")
        self.assertEqual(em.syntax_line("if_open", "if ({cond}) {", {"cond": "x"}), "IF(x)")
        self.assertEqual(em.syntax_line("missing", "while ({cond}) {", {"cond": "y"}), "while (y) {")

    def test_emit_block_open_close_helpers(self) -> None:
        em = CodeEmitter({})
        em.emit_function_open("int64", "f", "int64 x")
        em.emit_ctor_open("Point", "int64 x, int64 y")
        em.emit_dtor_open("Point")
        em.emit_class_open("Point", "")
        em.emit_class_close()
        em.emit_block_close()
        self.assertEqual(
            em.lines,
            [
                "int64 f(int64 x) {",
                "Point(int64 x, int64 y) {",
                "~Point() {",
                "struct Point {",
                "};",
                "}",
            ],
        )

    def test_emit_scoped_stmt_list_helper(self) -> None:
        em = _DummyEmitter({})
        em.emit("before")
        em.emit_scoped_stmt_list(["a", "b"], {"x"})
        em.emit("after")
        self.assertEqual(
            em.lines,
            [
                "before",
                "    stmt:a",
                "    stmt:b",
                "after",
            ],
        )

    def test_emit_with_scope_helper(self) -> None:
        em = _DummyEmitter({})
        em.emit("before")
        em.emit_with_scope({"x"}, ["a", "b"])
        em.emit("after")
        self.assertEqual(
            em.lines,
            [
                "before",
                "    stmt:a",
                "    stmt:b",
                "after",
            ],
        )

    def test_emit_scoped_block_helper(self) -> None:
        em = _DummyEmitter({})
        em.emit_scoped_block("if (cond) {", ["a", "b"], {"x"})
        self.assertEqual(
            em.lines,
            [
                "if (cond) {",
                "    stmt:a",
                "    stmt:b",
                "}",
            ],
        )

    def test_hook_invocation_helpers(self) -> None:
        em = _HookedEmitter({})
        stmt_handled = em.hook_on_emit_stmt({"kind": "Pass"})
        self.assertTrue(stmt_handled)
        self.assertIn("// hooked", em.lines)
        kind_handled = em.hook_on_emit_stmt_kind("Return", {"kind": "Return"})
        self.assertTrue(kind_handled)
        self.assertIn("// hooked-kind-return", em.lines)
        hook_call = em.hook_on_render_call(
            {"kind": "Call"},
            {"kind": "Name", "id": "hooked"},
            [],
            {},
        )
        self.assertEqual(hook_call, "hooked_call()")
        hook_binop = em.hook_on_render_binop({"kind": "BinOp"}, "x", "y")
        self.assertEqual(hook_binop, "hooked_binop(x, y)")
        hook_expr = em.hook_on_render_expr_kind("MagicExpr", {"kind": "MagicExpr"})
        self.assertEqual(hook_expr, "magic_expr()")
        hook_complex = em.hook_on_render_expr_complex({"kind": "JoinedStr"})
        self.assertEqual(hook_complex, "complex_expr()")

    def test_hook_invocation_helpers_with_dict_hooks(self) -> None:
        calls: list[str] = []

        def on_emit_stmt(_em: CodeEmitter, stmt: dict[str, Any]) -> Any:
            calls.append("emit_stmt:" + str(stmt.get("kind")))
            return True

        def on_emit_stmt_kind(_em: CodeEmitter, kind: str, _stmt: dict[str, Any]) -> Any:
            calls.append("emit_stmt_kind:" + kind)
            return True

        def on_render_call(
            _em: CodeEmitter,
            _call_node: dict[str, Any],
            _func_node: dict[str, Any],
            _rendered_args: list[str],
            _rendered_kwargs: dict[str, str],
        ) -> Any:
            calls.append("render_call")
            return "dict_hook_call()"

        def on_render_expr_kind(_em: CodeEmitter, kind: str, _expr_node: dict[str, Any]) -> Any:
            calls.append("render_expr_kind:" + kind)
            return "dict_hook_expr()"

        def on_render_expr_complex(_em: CodeEmitter, _expr_node: dict[str, Any]) -> Any:
            calls.append("render_expr_complex")
            return "dict_hook_complex()"

        def on_render_binop(
            _em: CodeEmitter,
            _binop_node: dict[str, Any],
            _left: str,
            _right: str,
        ) -> Any:
            calls.append("render_binop")
            return "dict_hook_binop()"

        hooks: dict[str, Any] = {
            "on_emit_stmt": on_emit_stmt,
            "on_emit_stmt_kind": on_emit_stmt_kind,
            "on_render_call": on_render_call,
            "on_render_binop": on_render_binop,
            "on_render_expr_kind": on_render_expr_kind,
            "on_render_expr_complex": on_render_expr_complex,
        }
        em = CodeEmitter({}, {}, hooks)
        self.assertTrue(em.hook_on_emit_stmt({"kind": "Pass"}))
        self.assertTrue(em.hook_on_emit_stmt_kind("Return", {"kind": "Return"}))
        self.assertEqual(
            em.hook_on_render_call({"kind": "Call"}, {"kind": "Name"}, [], {}),
            "dict_hook_call()",
        )
        self.assertEqual(
            em.hook_on_render_binop({"kind": "BinOp"}, "l", "r"),
            "dict_hook_binop()",
        )
        self.assertEqual(
            em.hook_on_render_expr_kind("MagicExpr", {"kind": "MagicExpr"}),
            "dict_hook_expr()",
        )
        self.assertEqual(
            em.hook_on_render_expr_complex({"kind": "JoinedStr"}),
            "dict_hook_complex()",
        )
        self.assertIn("emit_stmt:Pass", calls)
        self.assertIn("emit_stmt_kind:Return", calls)
        self.assertIn("render_call", calls)
        self.assertIn("render_binop", calls)
        self.assertIn("render_expr_kind:MagicExpr", calls)
        self.assertIn("render_expr_complex", calls)

    def test_emitter_hooks_container(self) -> None:
        hooks = EmitterHooks()
        hooks.add("", None)
        hooks.add("on_render_call", "fn1")
        hooks.add("on_render_expr_kind", "fn2")
        out = hooks.to_dict()
        self.assertNotIn("", out)
        self.assertEqual(out.get("on_render_call"), "fn1")
        self.assertEqual(out.get("on_render_expr_kind"), "fn2")


if __name__ == "__main__":
    unittest.main()
