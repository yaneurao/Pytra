"""EAST/IR pipeline bootstrap wrappers.

This module provides a stable import path under ``toolchain.compile`` while
existing implementations remain in ``toolchain.compiler.east_parts``.
"""

from __future__ import annotations

from typing import Any

from toolchain.compile.east2_to_east3_lowering import lower_east2_to_east3 as _lower_east2_to_east3
from toolchain.compile.east3_optimizer import optimize_east3_document
from toolchain.compile.east3_optimizer import render_east3_opt_trace
from toolchain.compile.east_io import UserFacingError
from toolchain.compile.east_io import load_east_from_path


def lower_east2_to_east3(
    east_module: dict[str, Any],
    object_dispatch_mode: str = "",
) -> dict[str, Any]:
    """Lower EAST2 module document into EAST3 module document."""
    out = _lower_east2_to_east3(east_module, object_dispatch_mode=object_dispatch_mode)
    if isinstance(out, dict):
        return out
    raise RuntimeError("EAST3 root must be a dict")

