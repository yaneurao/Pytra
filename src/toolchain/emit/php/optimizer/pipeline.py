"""PHP backend optimizer pipeline (pass-through skeleton)."""

from __future__ import annotations

from typing import Any


def optimize_php_ir(
    php_ir: dict[str, Any],
    *,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Optimize PhpIR.

    Current phase keeps pass-through behavior to isolate 3-layer wiring changes.
    """
    _ = options
    if not isinstance(php_ir, dict):
        raise RuntimeError("php optimizer: php_ir must be dict")
    if php_ir.get("kind") != "Module":
        raise RuntimeError("php optimizer: root kind must be Module")
    return php_ir

