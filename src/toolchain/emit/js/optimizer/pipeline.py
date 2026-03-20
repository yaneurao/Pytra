"""JavaScript backend optimizer pipeline (pass-through skeleton)."""

from __future__ import annotations

from typing import Any


def optimize_js_ir(
    js_ir: dict,
    *,
    options: Any = None,
) -> dict:
    """Optimize JsIR.

    Current phase keeps pass-through behavior to isolate 3-layer wiring changes.
    """
    _ = options
    if not isinstance(js_ir, dict):
        raise RuntimeError("js optimizer: js_ir must be dict")
    if js_ir.get("kind") != "Module":
        raise RuntimeError("js optimizer: root kind must be Module")
    return js_ir
