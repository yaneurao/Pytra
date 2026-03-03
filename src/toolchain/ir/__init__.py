"""IR bootstrap namespace (`src/pytra/ir`).

This package centralizes EAST/IR operations while migration from
``toolchain.compiler.east_parts`` is in progress.
"""

from .east1 import load_east1_document
from .east1 import normalize_east1_root_document
from .east2 import normalize_east1_to_east2_document
from .east2_to_east3_lowering import lower_east2_to_east3
from .east3 import load_east3_document
from .east3_optimizer import optimize_east3_document
from .east3_optimizer import render_east3_opt_trace
from .east_io import UserFacingError
from .east_io import load_east_from_path

__all__ = [
    "UserFacingError",
    "load_east_from_path",
    "load_east1_document",
    "normalize_east1_root_document",
    "normalize_east1_to_east2_document",
    "load_east3_document",
    "lower_east2_to_east3",
    "optimize_east3_document",
    "render_east3_opt_trace",
]
