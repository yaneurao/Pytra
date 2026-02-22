"""pytra.std.random: minimal deterministic random helpers.

This module is intentionally self-contained and avoids Python stdlib imports,
so it can be transpiled to target runtimes.
"""

from __future__ import annotations

import pytra.std.math as _math

_state_box: list[int] = [2463534242]
_gauss_has_spare: list[int] = [0]
_gauss_spare: list[float] = [0.0]


def seed(value: int) -> None:
    """Set generator seed (32-bit)."""
    v = int(value) & 2147483647
    if v == 0:
        v = 1
    _state_box[0] = v
    _gauss_has_spare[0] = 0


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


def choices(population: list[int], weights: list[float], k: int = 1) -> list[int]:
    """Return k sampled elements with replacement.

    Supported call forms:
    - choices(population, weights)
    - choices(population, weights, k)
    """
    n = len(population)
    if n <= 0:
        return []

    draws = int(k)
    if draws < 0:
        draws = 0

    weight_vals: list[float] = []
    for w in weights:
        weight_vals.append(float(w))

    out: list[int] = []
    if len(weight_vals) == n:
        total = 0.0
        for w in weight_vals:
            if w > 0.0:
                total += w
        if total > 0.0:
            for _ in range(draws):
                r = random() * total
                acc = 0.0
                picked_i = n - 1
                for i in range(n):
                    w = weight_vals[i]
                    if w > 0.0:
                        acc += w
                    if r < acc:
                        picked_i = i
                        break
                out.append(population[picked_i])
            return out

    for _ in range(draws):
        out.append(population[randint(0, n - 1)])
    return out


def gauss(mu: float = 0.0, sigma: float = 1.0) -> float:
    """Return a pseudo-random Gaussian sample."""
    if _gauss_has_spare[0] != 0:
        _gauss_has_spare[0] = 0
        return float(mu) + float(sigma) * _gauss_spare[0]

    u1 = 0.0
    while u1 <= 1.0e-12:
        u1 = random()
    u2 = random()
    mag = _math.sqrt(-2.0 * _math.log(u1))
    z0 = mag * _math.cos(2.0 * _math.pi * u2)
    z1 = mag * _math.sin(2.0 * _math.pi * u2)
    _gauss_spare[0] = z1
    _gauss_has_spare[0] = 1
    return float(mu) + float(sigma) * z0


def shuffle(xs: list[int]) -> None:
    """Shuffle list in place."""
    i = len(xs) - 1
    while i > 0:
        j = randint(0, i)
        if j != i:
            tmp = xs[i]
            xs[i] = xs[j]
            xs[j] = tmp
        i -= 1


__all__ = ["seed", "random", "randint", "choices", "gauss", "shuffle"]
