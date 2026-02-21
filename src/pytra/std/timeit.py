"""pytra.std.timeit compatibility shim."""

from __future__ import annotations

from pytra.std.time import perf_counter


def default_timer() -> float:
    """`timeit.default_timer` compatible entrypoint."""
    return perf_counter()


__all__ = ["default_timer"]

