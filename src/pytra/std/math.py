"""pytra.std.math: extern-marked math API with Python runtime fallback."""


import math

from pytra.std import extern

pi: float = extern(math.pi)
e: float = extern(math.e)

@extern
def sqrt(x: float) -> float:
    return math.sqrt(x)


@extern
def sin(x: float) -> float:
    return math.sin(x)


@extern
def cos(x: float) -> float:
    return math.cos(x)


@extern
def tan(x: float) -> float:
    return math.tan(x)


@extern
def exp(x: float) -> float:
    return math.exp(x)


@extern
def log(x: float) -> float:
    return math.log(x)


@extern
def log10(x: float) -> float:
    return math.log10(x)


@extern
def fabs(x: float) -> float:
    return math.fabs(x)


@extern
def floor(x: float) -> float:
    return math.floor(x)


@extern
def ceil(x: float) -> float:
    return math.ceil(x)


@extern
def pow(x: float, y: float) -> float:
    return math.pow(x, y)
