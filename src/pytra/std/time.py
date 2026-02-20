"""pytra.std.time wrapper."""

from __future__ import annotations

import pytra.std.time_impl as _impl


def perf_counter() -> float:
    return _impl.perf_counter()


__all__ = ["perf_counter"]
