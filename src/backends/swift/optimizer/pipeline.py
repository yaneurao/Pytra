"""Swift backend optimizer pipeline (pass-through skeleton)."""

from __future__ import annotations

from typing import Any


def optimize_swift_ir(
    swift_ir: dict[str, Any],
    *,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Optimize SwiftIR.

    Current phase keeps pass-through behavior to isolate 3-layer wiring changes.
    """
    _ = options
    if not isinstance(swift_ir, dict):
        raise RuntimeError("swift optimizer: swift_ir must be dict")
    if swift_ir.get("kind") != "Module":
        raise RuntimeError("swift optimizer: root kind must be Module")
    return swift_ir

