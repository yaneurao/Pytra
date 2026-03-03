"""Compatibility shim for EAST1 frontend helpers.

Canonical implementation moved to ``pytra.frontends.east1_build``.
"""

from __future__ import annotations

from pytra.frontends.east1_build import East1BuildHelpers
from pytra.frontends.east1_build import analyze_import_graph
from pytra.frontends.east1_build import build_east1_document
from pytra.frontends.east1_build import build_module_east_map
from pytra.frontends.east1_build import build_module_symbol_index
from pytra.frontends.east1_build import build_module_type_schema

__all__ = [
    "build_east1_document",
    "analyze_import_graph",
    "build_module_east_map",
    "build_module_symbol_index",
    "build_module_type_schema",
    "East1BuildHelpers",
]
