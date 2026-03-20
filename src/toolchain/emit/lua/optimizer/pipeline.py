"""Lua backend optimizer pipeline (pass-through skeleton)."""

from __future__ import annotations

from typing import Any


def optimize_lua_ir(
    lua_ir: dict[str, Any],
    *,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Optimize LuaIR.

    Current phase keeps pass-through behavior to isolate 3-layer wiring changes.
    """
    _ = options
    if not isinstance(lua_ir, dict):
        raise RuntimeError("lua optimizer: lua_ir must be dict")
    if lua_ir.get("kind") != "Module":
        raise RuntimeError("lua optimizer: root kind must be Module")
    return lua_ir

