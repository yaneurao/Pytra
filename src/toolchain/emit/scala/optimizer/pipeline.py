"""Scala backend optimizer pipeline (pass-through skeleton)."""

from __future__ import annotations

from typing import Any


def optimize_scala_ir(
    scala_ir: dict[str, Any],
    *,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Optimize ScalaIR.

    Current phase keeps pass-through behavior to isolate 3-layer wiring changes.
    """
    _ = options
    if not isinstance(scala_ir, dict):
        raise RuntimeError("scala optimizer: scala_ir must be dict")
    if scala_ir.get("kind") != "Module":
        raise RuntimeError("scala optimizer: root kind must be Module")
    return scala_ir

