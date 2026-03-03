"""IR bootstrap namespace (`src/pytra/ir`).

This package centralizes EAST/IR operations while migration from
``pytra.compiler.east_parts`` is in progress.
"""

from .pipeline import UserFacingError
from .pipeline import load_east_from_path
from .pipeline import lower_east2_to_east3
from .pipeline import optimize_east3_document
from .pipeline import render_east3_opt_trace

__all__ = [
    "UserFacingError",
    "load_east_from_path",
    "lower_east2_to_east3",
    "optimize_east3_document",
    "render_east3_opt_trace",
]

