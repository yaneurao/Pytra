"""Minimal glob shim for selfhost-friendly imports."""

from __future__ import annotations

import glob as _glob


def glob(pattern: str) -> list[str]:
    return _glob.glob(pattern)

