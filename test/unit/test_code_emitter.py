"""CodeEmitter の共通ユーティリティ回帰テスト。"""

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

from src.pytra.compiler.east_parts.code_emitter import CodeEmitter


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


class CodeEmitterTest(unittest.TestCase):
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
        not_super = {
            "kind": "Call",
            "func": {"kind": "Name", "id": "f"},
            "args": [],
            "keywords": [],
        }
        self.assertFalse(em._is_redundant_super_init_call(not_super))

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

        hooks: dict[str, Any] = {
            "on_emit_stmt": on_emit_stmt,
            "on_emit_stmt_kind": on_emit_stmt_kind,
            "on_render_call": on_render_call,
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
        self.assertIn("render_expr_kind:MagicExpr", calls)
        self.assertIn("render_expr_complex", calls)


if __name__ == "__main__":
    unittest.main()
