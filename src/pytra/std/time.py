"""pytra.std.time: extern-marked time API with Python runtime fallback."""

from __future__ import annotations

from pytra.std import extern

import time as __t


@extern
def perf_counter() -> float:
    return __t.perf_counter()
