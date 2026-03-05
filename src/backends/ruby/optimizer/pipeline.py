"""Ruby backend optimizer pipeline (pass-through skeleton)."""

from __future__ import annotations

from typing import Any


def optimize_ruby_ir(
    ruby_ir: dict[str, Any],
    *,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Optimize RubyIR.

    Current phase keeps pass-through behavior to isolate 3-layer wiring changes.
    """
    _ = options
    if not isinstance(ruby_ir, dict):
        raise RuntimeError("ruby optimizer: ruby_ir must be dict")
    if ruby_ir.get("kind") != "Module":
        raise RuntimeError("ruby optimizer: root kind must be Module")
    return ruby_ir

