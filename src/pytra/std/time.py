"""pytra.std.time: extern-marked time API with Python runtime fallback."""


import time

from pytra.std import extern


@extern
def perf_counter() -> float:
    return time.perf_counter()
