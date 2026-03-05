"""pytra.std.math: extern-marked math API with Python runtime fallback."""

from __future__ import annotations

from pytra.std import extern

import math as __m

pi: float = extern(__m.pi)
e: float = extern(__m.e)

@extern
def sqrt(x: float) -> float:
    return __m.sqrt(x)


@extern
def sin(x: float) -> float:
    return __m.sin(x)


@extern
def cos(x: float) -> float:
    return __m.cos(x)


@extern
def tan(x: float) -> float:
    return __m.tan(x)


@extern
def exp(x: float) -> float:
    return __m.exp(x)


@extern
def log(x: float) -> float:
    return __m.log(x)


@extern
def log10(x: float) -> float:
    return __m.log10(x)


@extern
def fabs(x: float) -> float:
    return __m.fabs(x)


@extern
def floor(x: float) -> float:
    return __m.floor(x)


@extern
def ceil(x: float) -> float:
    return __m.ceil(x)


@extern
def pow(x: float, y: float) -> float:
    return __m.pow(x, y)
