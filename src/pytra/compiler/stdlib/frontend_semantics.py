"""Compatibility shim for frontend semantic-tag helpers.

Canonical implementation moved to ``pytra.frontends.frontend_semantics``.
"""

from __future__ import annotations

from pytra.frontends.frontend_semantics import lookup_builtin_semantic_tag
from pytra.frontends.frontend_semantics import lookup_stdlib_function_semantic_tag
from pytra.frontends.frontend_semantics import lookup_stdlib_method_semantic_tag
from pytra.frontends.frontend_semantics import lookup_stdlib_symbol_semantic_tag

__all__ = [
    "lookup_builtin_semantic_tag",
    "lookup_stdlib_function_semantic_tag",
    "lookup_stdlib_method_semantic_tag",
    "lookup_stdlib_symbol_semantic_tag",
]
