"""pytra.std.random: minimal deterministic random helpers.

This module is intentionally self-contained and avoids Python stdlib imports,
so it can be transpiled to target runtimes.
"""

from __future__ import annotations

_state_box: list[int] = [2463534242]


def seed(value: int) -> None:
    """Set generator seed (32-bit)."""
    v = int(value) & 2147483647
    if v == 0:
        v = 1
    _state_box[0] = v


def _next_u31() -> int:
    """Advance internal LCG and return a 31-bit value."""
    s = _state_box[0]
    s = (1103515245 * s + 12345) & 2147483647
    _state_box[0] = s
    return s


def random() -> float:
    """Return pseudo-random float in [0.0, 1.0)."""
    return _next_u31() / 2147483648.0


def randint(a: int, b: int) -> int:
    """Return pseudo-random integer in [a, b]."""
    lo = int(a)
    hi = int(b)
    if hi < lo:
        lo, hi = hi, lo
    span = hi - lo + 1
    return lo + int(random() * span)


__all__ = ["seed", "random", "randint"]
