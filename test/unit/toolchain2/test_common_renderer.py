from __future__ import annotations

import unittest

from toolchain2.emit.common.common_renderer import CommonRenderer
from toolchain2.emit.common.profile_loader import load_profile_doc
from toolchain2.emit.cpp.emitter import _emit_expr as emit_cpp_expr, CppEmitContext
from toolchain2.emit.go.emitter import _emit_expr as emit_go_expr, EmitContext


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


if __name__ == "__main__":
    unittest.main()
