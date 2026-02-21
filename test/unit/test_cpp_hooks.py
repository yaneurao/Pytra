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

from src.hooks.cpp.hooks.cpp_hooks import on_render_expr_kind, on_render_object_method


class _DummyEmitter:
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


class CppHooksTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
