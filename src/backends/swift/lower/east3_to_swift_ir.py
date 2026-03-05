"""Swift backend lower stage: EAST3 -> SwiftIR (pass-through skeleton)."""

from __future__ import annotations

from typing import Any


def lower_east3_to_swift_ir(
    east_doc: dict[str, Any],
    *,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Lower EAST3 module into SwiftIR.

    Current phase keeps a 1:1 pass-through to stabilize 3-layer wiring.
    """
    _ = options
    if not isinstance(east_doc, dict):
        raise RuntimeError("swift lower: east_doc must be dict")
    if east_doc.get("kind") != "Module":
        raise RuntimeError("swift lower: root kind must be Module")
    return east_doc

