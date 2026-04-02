from __future__ import annotations

import unittest

from toolchain2.emit.common.common_renderer import CommonRenderer
from toolchain2.emit.common.profile_loader import load_profile_doc
from toolchain2.emit.cpp.emitter import _emit_expr as emit_cpp_expr, _emit_stmt as emit_cpp_stmt, CppEmitContext
from toolchain2.emit.cpp.emitter import _emit_tuple_unpack as emit_cpp_tuple_unpack
from toolchain2.emit.go.emitter import _emit_expr as emit_go_expr, _emit_stmt as emit_go_stmt, EmitContext


class DummyRenderer(CommonRenderer):
    def render_attribute(self, node: dict) -> str:
        return self.render_expr(node.get("value")) + "." + self._str(node, "attr")

    def render_call(self, node: dict) -> str:
        func = self.render_expr(node.get("func"))
        args = [self.render_expr(arg) for arg in self._list(node, "args")]
        return func + "(" + ", ".join(args) + ")"

    def render_assign_stmt(self, node: dict) -> str:
        target = node.get("target")
        if isinstance(target, dict):
            lhs = self.render_expr(target)
        else:
            lhs = "<?>"
        return lhs + " = " + self.render_expr(node.get("value"))

    def render_raise_value(self, node: dict) -> str:
        exc = node.get("exc")
        if isinstance(exc, dict):
            return self.render_expr(exc)
        return ""

    def render_except_open(self, handler: dict) -> str:
        name = self._str(handler, "name")
        if name != "":
            return "catch (" + name + ") {"
        return "catch (...) {"


class BoundaryRenderer(DummyRenderer):
    def render_expr_extension(self, node: dict) -> str:
        kind = self._str(node, "kind")
        if kind == "Box":
            return "BOX(" + self.render_expr(node.get("value")) + ")"
        if kind == "Unbox":
            return "UNBOX(" + self.render_expr(node.get("value")) + ")"
        raise RuntimeError("unexpected expr kind: " + kind)


class CommonRendererTests(unittest.TestCase):
    def test_profile_loader_returns_full_profile_doc(self) -> None:
        profile = load_profile_doc("go")

        self.assertEqual(profile.get("language"), "go")
        self.assertIn("operators", profile)
        self.assertIn("syntax", profile)
        self.assertIn("lowering", profile)

    def test_cpp_profile_renders_if_with_parens_and_semicolons(self) -> None:
        renderer = DummyRenderer("cpp")
        renderer.emit_stmt(
            {
                "kind": "If",
                "test": {
                    "kind": "Compare",
                    "left": {"kind": "Name", "id": "x"},
                    "ops": ["Lt"],
                    "comparators": [{"kind": "Constant", "value": 3}],
                },
                "body": [{"kind": "Return", "value": {"kind": "Constant", "value": 1}}],
                "orelse": [],
            }
        )

        rendered = renderer.finish()

        self.assertIn("if (", rendered)
        self.assertIn("x < 3", rendered)
        self.assertIn("return 1;", rendered)
        self.assertIn("}", rendered)

    def test_cpp_profile_renders_elif_chain_from_common_renderer(self) -> None:
        renderer = DummyRenderer("cpp")
        renderer.emit_stmt(
            {
                "kind": "If",
                "test": {"kind": "Name", "id": "a"},
                "body": [{"kind": "Return", "value": {"kind": "Constant", "value": 1}}],
                "orelse": [
                    {
                        "kind": "If",
                        "test": {"kind": "Name", "id": "b"},
                        "body": [{"kind": "Return", "value": {"kind": "Constant", "value": 2}}],
                        "orelse": [{"kind": "Return", "value": {"kind": "Constant", "value": 3}}],
                    }
                ],
            }
        )

        rendered = renderer.finish()

        self.assertIn("if ((a)) {", rendered)
        self.assertIn("} else if ((b)) {", rendered)
        self.assertIn("} else {", rendered)
        self.assertIn("return 3;", rendered)

    def test_go_profile_renders_while_without_condition_parens(self) -> None:
        renderer = DummyRenderer("go")
        renderer.emit_stmt(
            {
                "kind": "While",
                "test": {
                    "kind": "BoolOp",
                    "op": "And",
                    "values": [
                        {"kind": "Name", "id": "ready"},
                        {"kind": "Name", "id": "running"},
                    ],
                },
                "body": [
                    {
                        "kind": "Assign",
                        "target": {"kind": "Name", "id": "x"},
                        "value": {
                            "kind": "BinOp",
                            "left": {"kind": "Name", "id": "x"},
                            "op": "Add",
                            "right": {"kind": "Constant", "value": 1},
                        },
                    }
                ],
            }
        )

        rendered = renderer.finish()

        self.assertIn("for (ready && running) {", rendered)
        self.assertIn("x = (x + 1)", rendered)
        self.assertNotIn(";", rendered)

    def test_go_emitter_expr_dispatch_uses_common_renderer_for_shared_boolop(self) -> None:
        rendered = emit_go_expr(
            EmitContext(),
            {
                "kind": "BoolOp",
                "op": "And",
                "values": [
                    {"kind": "Name", "id": "ready"},
                    {
                        "kind": "Compare",
                        "left": {"kind": "Name", "id": "count", "resolved_type": "int"},
                        "ops": ["Gt"],
                        "comparators": [{"kind": "Constant", "value": 0, "resolved_type": "int"}],
                    },
                ],
            },
        )

        self.assertIn("ready", rendered)
        self.assertIn("count", rendered)
        self.assertIn(">", rendered)

    def test_cpp_emitter_expr_dispatch_uses_common_renderer_for_shared_binop(self) -> None:
        rendered = emit_cpp_expr(
            CppEmitContext(),
            {
                "kind": "BinOp",
                "left": {"kind": "Constant", "value": 1, "resolved_type": "int"},
                "op": "Add",
                "right": {"kind": "Constant", "value": 2, "resolved_type": "int"},
                "resolved_type": "int",
            },
        )

        self.assertEqual(rendered, "1 + 2")

    def test_cpp_emitter_expr_dispatch_respects_precedence_for_nested_binop(self) -> None:
        rendered = emit_cpp_expr(
            CppEmitContext(),
            {
                "kind": "BinOp",
                "left": {
                    "kind": "BinOp",
                    "left": {"kind": "Constant", "value": 1, "resolved_type": "int64"},
                    "op": "Add",
                    "right": {"kind": "Constant", "value": 2, "resolved_type": "int64"},
                    "resolved_type": "int64",
                },
                "op": "Mult",
                "right": {"kind": "Constant", "value": 3, "resolved_type": "int64"},
                "resolved_type": "int64",
            },
        )

        self.assertEqual(rendered, "(1 + 2) * 3")

    def test_cpp_emitter_binop_keeps_explicit_numeric_promotion_casts(self) -> None:
        rendered = emit_cpp_expr(
            CppEmitContext(),
            {
                "kind": "BinOp",
                "left": {"kind": "Name", "id": "n", "resolved_type": "int64"},
                "op": "Div",
                "right": {"kind": "Name", "id": "d", "resolved_type": "int64"},
                "resolved_type": "float64",
                "casts": [
                    {"on": "left", "from": "int64", "to": "float64", "reason": "numeric_promotion"},
                    {"on": "right", "from": "int64", "to": "float64", "reason": "numeric_promotion"},
                ],
            },
        )

        self.assertEqual(rendered, "static_cast<float64>(n) / static_cast<float64>(d)")

    def test_cpp_emitter_binop_skips_stale_integer_numeric_promotion_casts(self) -> None:
        rendered = emit_cpp_expr(
            CppEmitContext(),
            {
                "kind": "BinOp",
                "left": {"kind": "Name", "id": "s8", "resolved_type": "int32"},
                "op": "Add",
                "right": {"kind": "Name", "id": "u8b", "resolved_type": "int32"},
                "resolved_type": "int32",
                "casts": [
                    {"on": "left", "from": "int8", "to": "uint8", "reason": "numeric_promotion"},
                ],
            },
        )

        self.assertEqual(rendered, "s8 + u8b")

    def test_cpp_emitter_mod_uses_python_semantics_helper(self) -> None:
        rendered = emit_cpp_expr(
            CppEmitContext(),
            {
                "kind": "BinOp",
                "left": {"kind": "Name", "id": "x", "resolved_type": "int64"},
                "op": "Mod",
                "right": {"kind": "Constant", "value": 2, "resolved_type": "int64"},
                "resolved_type": "int64",
            },
        )

        self.assertEqual(rendered, "py_mod(x, 2)")

    def test_cpp_emitter_constant_keeps_wrap_for_narrowing_integer_types(self) -> None:
        rendered = emit_cpp_expr(
            CppEmitContext(),
            {"kind": "Constant", "value": 7, "resolved_type": "int8"},
        )

        self.assertEqual(rendered, "int8_t(7)")

    def test_cpp_emitter_constant_keeps_wrap_for_out_of_range_int64_literals(self) -> None:
        rendered = emit_cpp_expr(
            CppEmitContext(),
            {"kind": "Constant", "value": 2147483648, "resolved_type": "int64"},
        )

        self.assertEqual(rendered, "int64(2147483648)")

    def test_cpp_emitter_minmax_keep_typed_integer_literals_for_template_deduction(self) -> None:
        rendered = emit_cpp_expr(
            CppEmitContext(),
            {
                "kind": "Call",
                "lowered_kind": "BuiltinCall",
                "builtin_name": "max",
                "runtime_call": "max",
                "resolved_type": "int64",
                "args": [
                    {"kind": "Constant", "value": 0, "resolved_type": "int64"},
                    {"kind": "Name", "id": "v", "resolved_type": "int64"},
                ],
                "func": {"kind": "Name", "id": "max"},
            },
        )

        self.assertIn("int64(0)", rendered)
        self.assertIn("v", rendered)
        self.assertNotIn("(0, v)", rendered)

    def test_cpp_emitter_compare_uses_py_is_none_for_object_identity_checks(self) -> None:
        rendered = emit_cpp_expr(
            CppEmitContext(),
            {
                "kind": "Compare",
                "left": {"kind": "Name", "id": "v", "resolved_type": "object"},
                "ops": ["Is"],
                "comparators": [{"kind": "Constant", "value": None, "resolved_type": "None"}],
            },
        )

        self.assertEqual(rendered, "py_is_none(v)")

    def test_common_renderer_collapses_nested_box_with_same_target(self) -> None:
        renderer = BoundaryRenderer("cpp")

        rendered = renderer.render_expr(
            {
                "kind": "Box",
                "resolved_type": "object",
                "value": {
                    "kind": "Box",
                    "resolved_type": "object",
                    "value": {"kind": "Name", "id": "x"},
                },
            }
        )

        self.assertEqual(rendered, "BOX(x)")

    def test_common_renderer_collapses_nested_unbox_with_same_target(self) -> None:
        renderer = BoundaryRenderer("cpp")

        rendered = renderer.render_expr(
            {
                "kind": "Unbox",
                "target": "int64",
                "resolved_type": "int64",
                "value": {
                    "kind": "Unbox",
                    "target": "int64",
                    "resolved_type": "int64",
                    "value": {"kind": "Name", "id": "x"},
                },
            }
        )

        self.assertEqual(rendered, "UNBOX(x)")

    def test_common_renderer_keeps_nested_unbox_when_target_differs(self) -> None:
        renderer = BoundaryRenderer("cpp")

        rendered = renderer.render_expr(
            {
                "kind": "Unbox",
                "target": "int64",
                "resolved_type": "int64",
                "value": {
                    "kind": "Unbox",
                    "target": "float64",
                    "resolved_type": "float64",
                    "value": {"kind": "Name", "id": "x"},
                },
            }
        )

        self.assertEqual(rendered, "UNBOX(UNBOX(x))")

    def test_cpp_tuple_unpack_reuses_existing_locals_instead_of_redeclaring(self) -> None:
        ctx = CppEmitContext()
        ctx.var_types["r"] = "float64"
        ctx.var_types["g"] = "float64"
        ctx.var_types["b"] = "float64"
        ctx.visible_local_scopes = [{"r", "g", "b"}]
        emit_cpp_tuple_unpack(
            ctx,
            {
                "kind": "TupleUnpack",
                "declare": True,
                "targets": [
                    {"kind": "Name", "id": "r", "resolved_type": "float64"},
                    {"kind": "Name", "id": "g", "resolved_type": "float64"},
                    {"kind": "Name", "id": "b", "resolved_type": "float64"},
                ],
                "target_types": ["float64", "float64", "float64"],
                "value": {
                    "kind": "Tuple",
                    "resolved_type": "tuple[float64,float64,float64]",
                    "elements": [
                        {"kind": "Constant", "value": 1.0, "resolved_type": "float64"},
                        {"kind": "Constant", "value": 2.0, "resolved_type": "float64"},
                        {"kind": "Constant", "value": 3.0, "resolved_type": "float64"},
                    ],
                },
            },
        )

        rendered = "\n".join(ctx.lines)
        self.assertIn("r = ::std::get<0>(", rendered)
        self.assertIn("g = ::std::get<1>(", rendered)
        self.assertIn("b = ::std::get<2>(", rendered)
        self.assertNotIn("float64 r =", rendered)

    def test_go_emitter_common_return_hook_preserves_multi_return(self) -> None:
        ctx = EmitContext(current_return_type="multi_return[int64, int64]")
        emit_go_stmt(
            ctx,
            {
                "kind": "Return",
                "value": {
                    "kind": "Tuple",
                    "elements": [
                        {"kind": "Constant", "value": 1, "resolved_type": "int64"},
                        {"kind": "Constant", "value": 2, "resolved_type": "int64"},
                    ],
                },
            },
        )

        self.assertEqual(ctx.lines, ["return int64(1), int64(2)"])

    def test_go_emitter_common_expr_stmt_hook_preserves_doc_comment(self) -> None:
        ctx = EmitContext()
        emit_go_stmt(ctx, {"kind": "Expr", "value": {"kind": "Constant", "value": "hello\ngo"}})

        self.assertEqual(ctx.lines, ["// hello", "// go"])

    def test_cpp_emitter_common_expr_stmt_hook_preserves_doc_comment(self) -> None:
        ctx = CppEmitContext()
        emit_cpp_stmt(ctx, {"kind": "Expr", "value": {"kind": "Constant", "value": "hello\ncpp"}})

        self.assertEqual(ctx.lines, ["// hello", "// cpp"])

    def test_go_emitter_common_misc_stmt_hooks_preserve_pass_comment_blank(self) -> None:
        ctx = EmitContext()
        emit_go_stmt(ctx, {"kind": "Pass"})
        emit_go_stmt(ctx, {"kind": "comment", "text": "note"})
        emit_go_stmt(ctx, {"kind": "blank"})

        self.assertEqual(ctx.lines, ["// pass", "// note", ""])

    def test_go_emitter_common_raise_hook_preserves_go_exception_emit(self) -> None:
        ctx = EmitContext()
        emit_go_stmt(
            ctx,
            {
                "kind": "Raise",
                "exc": {
                    "kind": "Call",
                    "func": {"kind": "Name", "id": "ValueError"},
                    "args": [{"kind": "Constant", "value": "boom", "resolved_type": "str"}],
                },
            },
        )

        self.assertEqual(ctx.lines, ['panic(pytraEnsureRecoveredError(NewValueError("boom")))'])

    def test_go_emitter_common_try_hook_preserves_go_exception_flow(self) -> None:
        ctx = EmitContext()
        emit_go_stmt(
            ctx,
            {
                "kind": "Try",
                "body": [
                    {
                        "kind": "Raise",
                        "exc": {
                            "kind": "Call",
                            "func": {"kind": "Name", "id": "ValueError"},
                            "args": [{"kind": "Constant", "value": "boom", "resolved_type": "str"}],
                        },
                    }
                ],
                "handlers": [
                    {
                        "kind": "ExceptHandler",
                        "type": {"kind": "Name", "id": "ValueError"},
                        "body": [
                            {
                                "kind": "Expr",
                                "value": {"kind": "Call", "func": {"kind": "Name", "id": "print"}, "args": [{"kind": "Constant", "value": "caught", "resolved_type": "str"}]},
                            }
                        ],
                    }
                ],
                "finalbody": [],
                "orelse": [],
            },
        )

        rendered = "\n".join(ctx.lines)
        self.assertIn("defer func()", rendered)
        self.assertIn('panic(pytraEnsureRecoveredError(NewValueError("boom")))', rendered)
        self.assertIn('py_print("caught")', rendered)

    def test_cpp_emitter_common_misc_stmt_hooks_preserve_pass_comment_blank(self) -> None:
        ctx = CppEmitContext()
        emit_cpp_stmt(ctx, {"kind": "Pass"})
        emit_cpp_stmt(ctx, {"kind": "comment", "text": "note"})
        emit_cpp_stmt(ctx, {"kind": "blank"})

        self.assertEqual(ctx.lines, ["// pass", "// note", ""])

    def test_cpp_emitter_stmt_dispatch_uses_common_renderer_for_elif_chain(self) -> None:
        ctx = CppEmitContext()
        emit_cpp_stmt(
            ctx,
            {
                "kind": "If",
                "test": {"kind": "Name", "id": "ready", "resolved_type": "bool"},
                "body": [{"kind": "Return", "value": {"kind": "Constant", "value": 1, "resolved_type": "int64"}}],
                "orelse": [
                    {
                        "kind": "If",
                        "test": {"kind": "Name", "id": "retry", "resolved_type": "bool"},
                        "body": [{"kind": "Return", "value": {"kind": "Constant", "value": 2, "resolved_type": "int64"}}],
                        "orelse": [{"kind": "Return", "value": {"kind": "Constant", "value": 3, "resolved_type": "int64"}}],
                    }
                ],
            },
        )

        rendered = "\n".join(ctx.lines)

        self.assertIn("if (ready) {", rendered)
        self.assertIn("} else if (retry) {", rendered)
        self.assertIn("return 3;", rendered)

    def test_cpp_emitter_stmt_dispatch_avoids_double_condition_parens_for_compare(self) -> None:
        ctx = CppEmitContext()
        emit_cpp_stmt(
            ctx,
            {
                "kind": "If",
                "test": {
                    "kind": "Compare",
                    "left": {"kind": "Name", "id": "count", "resolved_type": "int64"},
                    "ops": ["Gt"],
                    "comparators": [{"kind": "Constant", "value": 0, "resolved_type": "int64"}],
                    "resolved_type": "bool",
                },
                "body": [{"kind": "Pass"}],
                "orelse": [],
            },
        )

        rendered = "\n".join(ctx.lines)

        self.assertIn("if (count > 0) {", rendered)
        self.assertNotIn("if ((count > 0)) {", rendered)

    def test_cpp_emitter_stmt_dispatch_preserves_container_truthiness_hook(self) -> None:
        ctx = CppEmitContext()
        ctx.var_types["stack"] = "list[int64]"
        emit_cpp_stmt(
            ctx,
            {
                "kind": "While",
                "test": {"kind": "Name", "id": "stack", "resolved_type": "list[int64]"},
                "body": [{"kind": "Pass"}],
            },
        )

        rendered = "\n".join(ctx.lines)

        self.assertIn("while (py_to_bool(stack)) {", rendered)

    def test_common_renderer_emits_raise_and_try_skeleton_for_native_throw(self) -> None:
        renderer = DummyRenderer("cpp")
        renderer.emit_stmt(
            {
                "kind": "Try",
                "body": [
                    {
                        "kind": "Raise",
                        "exc": {
                            "kind": "Call",
                            "func": {"kind": "Name", "id": "ValueError"},
                            "args": [{"kind": "Constant", "value": "boom"}],
                        },
                    }
                ],
                "handlers": [
                    {
                        "kind": "ExceptHandler",
                        "name": "err",
                        "body": [{"kind": "Return", "value": {"kind": "Constant", "value": 1}}],
                    }
                ],
                "finalbody": [],
                "orelse": [],
            }
        )

        rendered = renderer.finish()

        self.assertIn('throw ValueError("boom");', rendered)
        self.assertIn("try {", rendered)
        self.assertIn("catch (err) {", rendered)
        self.assertIn("return 1;", rendered)


if __name__ == "__main__":
    unittest.main()
