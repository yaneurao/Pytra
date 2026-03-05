"""Go backend optimizer pipeline (pass-through skeleton)."""

from __future__ import annotations

from typing import Any


def optimize_go_ir(
    go_ir: dict[str, Any],
    *,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Optimize GoIR.

    Current phase keeps pass-through behavior to isolate 3-layer wiring changes.
    """
    _ = options
    if not isinstance(go_ir, dict):
        raise RuntimeError("go optimizer: go_ir must be dict")
    if go_ir.get("kind") != "Module":
        raise RuntimeError("go optimizer: root kind must be Module")
    return go_ir

