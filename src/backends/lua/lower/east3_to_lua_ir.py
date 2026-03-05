"""Lua backend lower stage: EAST3 -> LuaIR (pass-through skeleton)."""

from __future__ import annotations

from typing import Any


def lower_east3_to_lua_ir(
    east_doc: dict[str, Any],
    *,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Lower EAST3 module into LuaIR.

    Current phase keeps a 1:1 pass-through to stabilize 3-layer wiring.
    """
    _ = options
    if not isinstance(east_doc, dict):
        raise RuntimeError("lua lower: east_doc must be dict")
    if east_doc.get("kind") != "Module":
        raise RuntimeError("lua lower: root kind must be Module")
    return east_doc

