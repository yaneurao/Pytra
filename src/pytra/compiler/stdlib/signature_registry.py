"""Compatibility shim for stdlib signature registry.

Canonical implementation moved to ``toolchain.frontends.signature_registry``.
"""

from __future__ import annotations

from toolchain.frontends.signature_registry import is_stdlib_path_type
from toolchain.frontends.signature_registry import lookup_stdlib_attribute_type
from toolchain.frontends.signature_registry import lookup_stdlib_function_return_type
from toolchain.frontends.signature_registry import lookup_stdlib_function_runtime_call
from toolchain.frontends.signature_registry import lookup_stdlib_imported_symbol_return_type
from toolchain.frontends.signature_registry import lookup_stdlib_imported_symbol_runtime_call
from toolchain.frontends.signature_registry import lookup_stdlib_method_return_type
from toolchain.frontends.signature_registry import lookup_stdlib_method_runtime_call

__all__ = [
    "is_stdlib_path_type",
    "lookup_stdlib_attribute_type",
    "lookup_stdlib_function_return_type",
    "lookup_stdlib_function_runtime_call",
    "lookup_stdlib_imported_symbol_return_type",
    "lookup_stdlib_imported_symbol_runtime_call",
    "lookup_stdlib_method_return_type",
    "lookup_stdlib_method_runtime_call",
]
