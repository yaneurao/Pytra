"""C# backend optimizer pipeline (pass-through skeleton)."""

from __future__ import annotations

from typing import Any


def optimize_cs_ir(
    cs_ir: dict[str, Any],
    *,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Optimize CsIR.

    Current phase keeps pass-through behavior to isolate 3-layer wiring changes.
    """
    _ = options
    if not isinstance(cs_ir, dict):
        raise RuntimeError("cs optimizer: cs_ir must be dict")
    if cs_ir.get("kind") != "Module":
        raise RuntimeError("cs optimizer: root kind must be Module")
    return cs_ir

