"""Java backend optimizer pipeline (pass-through skeleton)."""

from __future__ import annotations

from typing import Any


def optimize_java_ir(
    java_ir: dict[str, Any],
    *,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Optimize JavaIR.

    Current phase keeps pass-through behavior to isolate 3-layer wiring changes.
    """
    _ = options
    if not isinstance(java_ir, dict):
        raise RuntimeError("java optimizer: java_ir must be dict")
    if java_ir.get("kind") != "Module":
        raise RuntimeError("java optimizer: root kind must be Module")
    return java_ir

