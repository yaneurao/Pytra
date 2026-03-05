"""pytra.std.glob: extern-marked glob subset with Python runtime fallback."""

from __future__ import annotations

from pytra.std import extern

import glob as __glob

@extern
def glob(pattern: str) -> list[str]:
    return __glob.glob(pattern)
