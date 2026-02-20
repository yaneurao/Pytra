from __future__ import annotations

import pytra.std.math_impl as _m

pi: float = _m.pi
e: float = _m.e


def sqrt(x: float) -> float:
    return _m.sqrt(x)


def sin(x: float) -> float:
    return _m.sin(x)


def cos(x: float) -> float:
    return _m.cos(x)


def tan(x: float) -> float:
    return _m.tan(x)


def exp(x: float) -> float:
    return _m.exp(x)


def log(x: float) -> float:
    return _m.log(x)


def log10(x: float) -> float:
    return _m.log10(x)


def fabs(x: float) -> float:
    return _m.fabs(x)


def floor(x: float) -> float:
    return _m.floor(x)


def ceil(x: float) -> float:
    return _m.ceil(x)


def pow(x: float, y: float) -> float:
    return _m.pow(x, y)
