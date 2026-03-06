"""JavaScript backend lower stage: EAST3 -> JsIR (pass-through skeleton)."""

from __future__ import annotations

from typing import Any


def lower_east3_to_js_ir(
    east_doc: dict,
    *,
    options: Any = None,
) -> dict:
    """Lower EAST3 module into JsIR.

    Current phase keeps a 1:1 pass-through to stabilize 3-layer wiring.
    """
    _ = options
    if not isinstance(east_doc, dict):
        raise RuntimeError("js lower: east_doc must be dict")
    if east_doc.get("kind") != "Module":
        raise RuntimeError("js lower: root kind must be Module")
    return east_doc
