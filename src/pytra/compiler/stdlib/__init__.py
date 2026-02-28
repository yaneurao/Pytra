"""Compiler-side stdlib signature helpers."""

from .signature_registry import lookup_stdlib_function_return_type
from .signature_registry import lookup_stdlib_method_return_type

__all__ = [
    "lookup_stdlib_function_return_type",
    "lookup_stdlib_method_return_type",
]
