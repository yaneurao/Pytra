from __future__ import annotations

import unittest

from toolchain2.emit.common.common_renderer import CommonRenderer
from toolchain2.emit.common.profile_loader import load_profile_doc
from toolchain2.emit.cpp.emitter import _emit_expr as emit_cpp_expr, _emit_stmt as emit_cpp_stmt, CppEmitContext
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

        self.assertEqual(rendered, "(int64(1) + int64(2))")

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

        self.assertEqual(rendered, "(static_cast<float64>(n) / static_cast<float64>(d))")

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
        self.assertIn("return int64(3);", rendered)

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
