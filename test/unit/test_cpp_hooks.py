"""Unit tests for C++ hook functions."""

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

from src.hooks.cpp.hooks.cpp_hooks import (
    on_emit_stmt_kind,
    on_for_range_mode,
    on_render_call,
    on_render_expr_complex,
    on_render_class_method,
    on_render_expr_kind,
    on_render_module_method,
    on_render_object_method,
    on_stmt_omit_braces,
)


class _DummyEmitter:
    module_namespace_map: dict[str, str]
    emitted: list[str]

    def __init__(self) -> None:
        self.module_namespace_map = {"pytra.std.math": "pytra::std::math"}
        self.emitted = []

    def any_dict_get_str(self, obj: dict[str, Any], key: str, default_value: str = "") -> str:
        if not isinstance(obj, dict):
            return default_value
        v = obj.get(key, default_value)
        return v if isinstance(v, str) else default_value

    def render_expr(self, expr: Any) -> str:
        if isinstance(expr, dict):
            rep = expr.get("repr")
            if isinstance(rep, str):
                return rep
        return "<?>"

    def any_to_bool(self, obj: Any) -> bool:
        return bool(obj)

    def any_to_list(self, value: Any) -> list[Any]:
        if isinstance(value, list):
            return value
        return []

    def cpp_type(self, type_node: Any) -> str:
        if isinstance(type_node, str):
            if type_node == "int64":
                return "int64"
            if type_node == "float64":
                return "float64"
            if type_node == "bool":
                return "bool"
        return "auto"

    def get_expr_type(self, expr: Any) -> str:
        if isinstance(expr, dict):
            t = expr.get("resolved_type")
            if isinstance(t, str):
                return t
        return ""

    def is_any_like_type(self, t: str) -> bool:
        return t in {"Any", "object", "unknown"}

    def _contains_text(self, text: str, needle: str) -> bool:
        return needle in text

    def split_union(self, text: str) -> list[str]:
        parts = text.split("|")
        out: list[str] = []
        i = 0
        while i < len(parts):
            p = parts[i].strip()
            if p != "":
                out.append(p)
            i += 1
        return out

    def merge_call_args(self, args: list[str], kw: dict[str, str]) -> list[str]:
        out: list[str] = []
        i = 0
        while i < len(args):
            out.append(args[i])
            i += 1
        for _, v in kw.items():
            out.append(v)
        return out

    def _normalize_runtime_module_name(self, module_name: str) -> str:
        return module_name

    def _coerce_args_for_module_function(
        self, module_name: str, fn_name: str, args: list[str], arg_nodes: list[Any]
    ) -> list[str]:
        _ = module_name
        _ = fn_name
        _ = arg_nodes
        return args

    def _lookup_module_attr_runtime_call(self, owner_mod: str, attr: str) -> str:
        if owner_mod == "pytra.std.math" and attr == "pow":
            return "pytra::std::math::pow"
        return ""

    def _module_name_to_cpp_namespace(self, module_name: str) -> str:
        if module_name == "my.mod":
            return "my::mod"
        return ""

    def _render_append_call_object_method(
        self, owner_types: list[str], owner_expr: str, rendered_args: list[str]
    ) -> str | None:
        _ = owner_types
        if len(rendered_args) == 1:
            return owner_expr + ".append(" + rendered_args[0] + ")"
        return None

    def _class_method_sig(self, owner_t: str, method: str) -> list[str]:
        if owner_t == "MathUtil" and method == "twice":
            return ["int64"]
        return []

    def _coerce_args_for_class_method(
        self,
        owner_t: str,
        method: str,
        args: list[str],
        arg_nodes: list[Any],
    ) -> list[str]:
        _ = owner_t
        _ = method
        _ = arg_nodes
        return args

    def _render_attribute_expr(self, expr_d: dict[str, Any]) -> str:
        owner = self.any_dict_get_str(self.any_to_dict_or_empty(expr_d.get("value")), "id", "")
        attr = self.any_dict_get_str(expr_d, "attr", "")
        if owner != "" and attr != "":
            return owner + "::" + attr
        return "<?>::<?>"

    def any_to_dict_or_empty(self, value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return value
        return {}

    def _emit_pass_stmt(self, stmt: dict[str, Any]) -> None:
        _ = stmt
        self.emitted.append("pass")

    def _emit_break_stmt(self, stmt: dict[str, Any]) -> None:
        _ = stmt
        self.emitted.append("break")

    def _emit_continue_stmt(self, stmt: dict[str, Any]) -> None:
        _ = stmt
        self.emitted.append("continue")

    def _emit_expr_stmt(self, stmt: dict[str, Any]) -> None:
        _ = stmt
        self.emitted.append("expr")

    def _emit_return_stmt(self, stmt: dict[str, Any]) -> None:
        _ = stmt
        self.emitted.append("return")

    def _emit_noop_stmt(self, stmt: dict[str, Any]) -> None:
        _ = stmt
        self.emitted.append("noop")

    def emit_leading_comments(self, stmt: dict[str, Any]) -> None:
        _ = stmt

    def _render_joinedstr_expr(self, expr_d: dict[str, Any]) -> str:
        _ = expr_d
        return "joined-rendered"

    def _render_lambda_expr(self, expr_d: dict[str, Any]) -> str:
        _ = expr_d
        return "lambda-rendered"


class CppHooksTest(unittest.TestCase):
    def test_on_render_call_is_noop_after_runtime_migration(self) -> None:
        em = _DummyEmitter()
        call_node = {
            "kind": "Call",
            "runtime_call": "static_cast",
            "resolved_type": "int64",
            "args": [{"kind": "Name", "id": "x", "resolved_type": "str"}],
        }
        func_node = {"kind": "Name", "id": "int"}
        rendered = on_render_call(em, call_node, func_node, ["x"], {})
        self.assertIsNone(rendered)

    def test_on_stmt_omit_braces_prefers_emitter_default_impl(self) -> None:
        class _DefaultingEmitter:
            def _default_stmt_omit_braces(self, kind: str, stmt: dict[str, Any], default_value: bool) -> bool:
                _ = stmt
                _ = default_value
                return kind == "If"

        em = _DefaultingEmitter()
        self.assertTrue(on_stmt_omit_braces(em, "If", {"body": []}, False))
        self.assertFalse(on_stmt_omit_braces(em, "For", {"body": []}, False))

    def test_on_for_range_mode_prefers_emitter_default_impl(self) -> None:
        class _RangeModeEmitter:
            def render_expr(self, expr: Any) -> str:
                if isinstance(expr, dict):
                    rep = expr.get("repr")
                    if isinstance(rep, str):
                        return rep
                return ""

            def _default_for_range_mode(self, stmt: dict[str, Any], default_mode: str, step_expr: str) -> str:
                _ = stmt
                if step_expr == "1":
                    return "ascending"
                return default_mode

        em = _RangeModeEmitter()
        stmt = {"range_mode": "dynamic", "step": {"repr": "1"}}
        self.assertEqual(on_for_range_mode(em, stmt, "dynamic"), "ascending")

    def test_on_stmt_omit_braces_falls_back_without_core_default(self) -> None:
        class _FallbackEmitter:
            def _opt_ge(self, level: int) -> bool:
                _ = level
                return True

            def _dict_stmt_list(self, value: Any) -> list[dict[str, Any]]:
                if isinstance(value, list):
                    return [v for v in value if isinstance(v, dict)]
                return []

            def any_dict_get_list(self, obj: dict[str, Any], key: str) -> list[Any]:
                if not isinstance(obj, dict):
                    return []
                value = obj.get(key)
                if isinstance(value, list):
                    return value
                return []

            def any_dict_get_str(self, obj: dict[str, Any], key: str, default_value: str = "") -> str:
                if not isinstance(obj, dict):
                    return default_value
                value = obj.get(key, default_value)
                return value if isinstance(value, str) else default_value

            def any_to_dict_or_empty(self, value: Any) -> dict[str, Any]:
                if isinstance(value, dict):
                    return value
                return {}

            def _node_kind_from_dict(self, value: dict[str, Any]) -> str:
                return self.any_dict_get_str(value, "kind", "")

        em = _FallbackEmitter()
        stmt = {"body": [{"kind": "Return"}], "orelse": []}
        self.assertTrue(on_stmt_omit_braces(em, "If", stmt, False))

    def test_on_for_range_mode_falls_back_without_core_default(self) -> None:
        class _FallbackEmitter:
            def any_to_str(self, value: Any) -> str:
                return value if isinstance(value, str) else ""

        em = _FallbackEmitter()
        self.assertEqual(on_for_range_mode(em, {"range_mode": "ascending"}, "dynamic"), "ascending")
        self.assertEqual(on_for_range_mode(em, {"range_mode": "invalid"}, "dynamic"), "dynamic")

    def test_range_expr_render(self) -> None:
        em = _DummyEmitter()
        node = {
            "kind": "RangeExpr",
            "start": {"repr": "0"},
            "stop": {"repr": "n"},
            "step": {"repr": "1"},
        }
        rendered = on_render_expr_kind(em, "RangeExpr", node)
        self.assertEqual(rendered, "py_range(0, n, 1)")

    def test_compare_contains_render(self) -> None:
        em = _DummyEmitter()
        node = {
            "kind": "Compare",
            "lowered_kind": "Contains",
            "container": {"repr": "xs"},
            "key": {"repr": "x"},
            "negated": False,
        }
        rendered = on_render_expr_kind(em, "Compare", node)
        self.assertEqual(rendered, "py_contains(xs, x)")

    def test_compare_not_contains_render(self) -> None:
        em = _DummyEmitter()
        node = {
            "kind": "Compare",
            "lowered_kind": "Contains",
            "container": {"repr": "xs"},
            "key": {"repr": "x"},
            "negated": True,
        }
        rendered = on_render_expr_kind(em, "Compare", node)
        self.assertEqual(rendered, "!(py_contains(xs, x))")

    def test_object_method_str_strip_render(self) -> None:
        em = _DummyEmitter()
        rendered = on_render_object_method(em, "str", "s", "strip", [])
        self.assertEqual(rendered, "py_strip(s)")

    def test_object_method_unknown_clear_render(self) -> None:
        em = _DummyEmitter()
        rendered = on_render_object_method(em, "unknown", "xs", "clear", [])
        self.assertEqual(rendered, "xs.clear()")

    def test_object_method_append_render(self) -> None:
        em = _DummyEmitter()
        rendered = on_render_object_method(em, "list[int64]", "xs", "append", ["x"])
        self.assertEqual(rendered, "xs.append(x)")

    def test_module_method_prefers_namespace_map(self) -> None:
        em = _DummyEmitter()
        rendered = on_render_module_method(em, "pytra.std.math", "sqrt", ["x"], {}, [])
        self.assertEqual(rendered, "pytra::std::math::sqrt(x)")

    def test_module_method_runtime_mapping(self) -> None:
        em = _DummyEmitter()
        rendered = on_render_module_method(em, "pytra.std.math", "pow", ["x", "y"], {}, [])
        self.assertEqual(rendered, "pytra::std::math::pow(x, y)")

    def test_class_method_render(self) -> None:
        em = _DummyEmitter()
        func = {
            "kind": "Attribute",
            "value": {"kind": "Name", "id": "MathUtil"},
            "attr": "twice",
        }
        rendered = on_render_class_method(em, "MathUtil", "twice", func, ["x"], {}, [])
        self.assertEqual(rendered, "MathUtil::twice(x)")

    def test_on_emit_stmt_kind_terminal(self) -> None:
        em = _DummyEmitter()
        done = on_emit_stmt_kind(em, "Pass", {"kind": "Pass"})
        self.assertEqual(done, True)
        self.assertEqual(em.emitted, ["pass"])

    def test_on_emit_stmt_kind_expr_return_import(self) -> None:
        em = _DummyEmitter()
        self.assertEqual(on_emit_stmt_kind(em, "Expr", {"kind": "Expr"}), True)
        self.assertEqual(on_emit_stmt_kind(em, "Return", {"kind": "Return"}), True)
        self.assertEqual(on_emit_stmt_kind(em, "Import", {"kind": "Import"}), True)
        self.assertEqual(on_emit_stmt_kind(em, "ImportFrom", {"kind": "ImportFrom"}), True)
        self.assertEqual(em.emitted, ["expr", "return", "noop", "noop"])

    def test_on_render_expr_complex(self) -> None:
        em = _DummyEmitter()
        joined = on_render_expr_complex(em, {"kind": "JoinedStr"})
        lam = on_render_expr_complex(em, {"kind": "Lambda"})
        self.assertEqual(joined, "joined-rendered")
        self.assertEqual(lam, "lambda-rendered")


if __name__ == "__main__":
    unittest.main()
