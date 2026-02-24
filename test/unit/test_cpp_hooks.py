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
    build_cpp_hooks,
    on_render_expr_complex,
    on_stmt_omit_braces,
)


class _DummyEmitter:
    def any_dict_get_str(self, obj: dict[str, Any], key: str, default_value: str = "") -> str:
        if not isinstance(obj, dict):
            return default_value
        v = obj.get(key, default_value)
        return v if isinstance(v, str) else default_value

    def _render_joinedstr_expr(self, expr_d: dict[str, Any]) -> str:
        _ = expr_d
        return "joined-rendered"

    def _render_lambda_expr(self, expr_d: dict[str, Any]) -> str:
        _ = expr_d
        return "lambda-rendered"


class CppHooksTest(unittest.TestCase):
    def test_build_cpp_hooks_registers_only_syntax_hooks(self) -> None:
        hooks = build_cpp_hooks()
        self.assertEqual(set(hooks.keys()), {"on_stmt_omit_braces", "on_render_expr_complex"})
        self.assertNotIn("on_render_module_method", hooks)
        self.assertNotIn("on_render_class_method", hooks)
        self.assertNotIn("on_render_expr_leaf", hooks)

    def test_on_stmt_omit_braces_prefers_emitter_default_impl(self) -> None:
        class _DefaultingEmitter:
            def _default_stmt_omit_braces(self, kind: str, stmt: dict[str, Any], default_value: bool) -> bool:
                _ = stmt
                _ = default_value
                return kind == "If"

        em = _DefaultingEmitter()
        self.assertTrue(on_stmt_omit_braces(em, "If", {"body": []}, False))
        self.assertFalse(on_stmt_omit_braces(em, "For", {"body": []}, False))

    def test_on_stmt_omit_braces_falls_back_without_core_default(self) -> None:
        class _FallbackEmitter:
            pass

        em = _FallbackEmitter()
        stmt = {"body": [{"kind": "Return"}], "orelse": []}
        self.assertFalse(on_stmt_omit_braces(em, "If", stmt, False))
        self.assertTrue(on_stmt_omit_braces(em, "If", stmt, True))

    def test_on_stmt_omit_braces_uses_default_impl_when_available(self) -> None:
        class _EmitterWithDefault:
            def _default_stmt_omit_braces(self, kind: str, stmt: dict[str, Any], default_value: bool) -> bool:
                _ = kind
                _ = stmt
                _ = default_value
                return True

        em = _EmitterWithDefault()
        self.assertTrue(on_stmt_omit_braces(em, "If", {"body": []}, False))

    def test_on_render_expr_complex(self) -> None:
        em = _DummyEmitter()
        joined = on_render_expr_complex(em, {"kind": "JoinedStr"})
        lam = on_render_expr_complex(em, {"kind": "Lambda"})
        self.assertEqual(joined, "joined-rendered")
        self.assertEqual(lam, "lambda-rendered")


if __name__ == "__main__":
    unittest.main()
