"""Compatibility exports for moved C++ hook registry helpers."""

from __future__ import annotations

from backends.cpp.emitter.hooks_registry import (
    build_cpp_hooks,
    on_render_expr_complex,
    on_stmt_omit_braces,
)

__all__ = [
    "build_cpp_hooks",
    "on_render_expr_complex",
    "on_stmt_omit_braces",
]
