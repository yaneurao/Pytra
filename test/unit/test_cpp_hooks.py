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
    on_render_class_method,
    on_render_expr_kind,
    on_render_module_method,
    on_render_object_method,
)


class _DummyEmitter:
    module_namespace_map: dict[str, str]

    def __init__(self) -> None:
        self.module_namespace_map = {"pytra.std.math": "pytra::std::math"}

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


class CppHooksTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
