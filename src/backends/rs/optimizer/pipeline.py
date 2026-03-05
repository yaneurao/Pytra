"""Rust backend optimizer pipeline (pass-through skeleton)."""

from __future__ import annotations

from typing import Any


def optimize_rs_ir(
    rs_ir: dict[str, Any],
    *,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Optimize RustIR.

    Current phase keeps pass-through behavior to isolate 3-layer wiring changes.
    """
    _ = options
    if not isinstance(rs_ir, dict):
        raise RuntimeError("rs optimizer: rs_ir must be dict")
    if rs_ir.get("kind") != "Module":
        raise RuntimeError("rs optimizer: root kind must be Module")
    return rs_ir
