"""pytra.std.math: thin wrapper over native math_impl module."""

from __future__ import annotations

from pytra.std import extern

import pytra.std.math_impl as _m

pi: float = extern(_m.pi)
e: float = extern(_m.e)

@extern
def sqrt(x: float) -> float:
    pass


@extern
def sin(x: float) -> float:
    pass


@extern
def cos(x: float) -> float:
    pass


@extern
def tan(x: float) -> float:
    pass


@extern
def exp(x: float) -> float:
    pass


@extern
def log(x: float) -> float:
    pass


@extern
def log10(x: float) -> float:
    pass


@extern
def fabs(x: float) -> float:
    pass


@extern
def floor(x: float) -> float:
    pass


@extern
def ceil(x: float) -> float:
    pass


@extern
def pow(x: float, y: float) -> float:
    pass
