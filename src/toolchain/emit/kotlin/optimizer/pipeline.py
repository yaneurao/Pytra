"""Kotlin backend optimizer pipeline (pass-through skeleton)."""

from __future__ import annotations

from typing import Any


def optimize_kotlin_ir(
    kotlin_ir: dict[str, Any],
    *,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Optimize KotlinIR.

    Current phase keeps pass-through behavior to isolate 3-layer wiring changes.
    """
    _ = options
    if not isinstance(kotlin_ir, dict):
        raise RuntimeError("kotlin optimizer: kotlin_ir must be dict")
    if kotlin_ir.get("kind") != "Module":
        raise RuntimeError("kotlin optimizer: root kind must be Module")
    return kotlin_ir

