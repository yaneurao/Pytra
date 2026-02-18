"""Compatibility shim: use pylib.east_io as canonical utilities."""

from __future__ import annotations

import sys as _bootstrap_sys

_bootstrap_src = __file__.replace("\\", "/").rsplit("/", 2)[0]
if _bootstrap_src not in _bootstrap_sys.path:
    _bootstrap_sys.path.insert(0, _bootstrap_src)

from pylib.east_io import (  # noqa: F401
    extract_module_leading_trivia,
    load_east_from_path,
)

