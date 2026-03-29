"""Pure-Python source-of-truth for numeric helper built-ins."""


from pytra.std import template


@template("T")
def sum(values: list[T]) -> T:
    if len(values) == 0:
        return 0
    acc = values[0] - values[0]
    i = 0
    n = len(values)
    while i < n:
        acc += values[i]
        i += 1
    return acc


@template("T")
def py_min(a: T, b: T) -> T:
    if a < b:
        return a
    return b


@template("T")
def py_max(a: T, b: T) -> T:
    if a > b:
        return a
    return b
