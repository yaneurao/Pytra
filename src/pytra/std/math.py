"""pytra.std.math: extern-marked math API with Python runtime fallback."""

from __future__ import annotations

from pytra.std import extern

import math as _m

pi: float = extern(_m.pi)
e: float = extern(_m.e)

@extern
def sqrt(x: float) -> float:
    return _m.sqrt(x)


@extern
def sin(x: float) -> float:
    return _m.sin(x)


@extern
def cos(x: float) -> float:
    return _m.cos(x)


@extern
def tan(x: float) -> float:
    return _m.tan(x)


@extern
def exp(x: float) -> float:
    return _m.exp(x)


@extern
def log(x: float) -> float:
    return _m.log(x)


@extern
def log10(x: float) -> float:
    return _m.log10(x)


@extern
def fabs(x: float) -> float:
    return _m.fabs(x)


@extern
def floor(x: float) -> float:
    return _m.floor(x)


@extern
def ceil(x: float) -> float:
    return _m.ceil(x)


@extern
def pow(x: float, y: float) -> float:
    return _m.pow(x, y)
