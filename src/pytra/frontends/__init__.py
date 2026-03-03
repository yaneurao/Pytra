"""Frontend bootstrap namespace (`src/pytra/frontends`).

This package is introduced as the stable import root for input-language
frontends while migration from ``pytra.compiler`` is in progress.
"""

from .python_frontend import add_common_transpile_args
from .python_frontend import load_east3_document
from .python_frontend import normalize_common_transpile_args

__all__ = [
    "add_common_transpile_args",
    "normalize_common_transpile_args",
    "load_east3_document",
]

