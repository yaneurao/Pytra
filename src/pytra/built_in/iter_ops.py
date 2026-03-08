"""Pure-Python source-of-truth for object-based iterator helpers."""


def py_reversed_object(values: object) -> object:
    out: list[object] = []
    i = len(values) - 1
    while i >= 0:
        out.append(values[i])
        i -= 1
    return out


def py_enumerate_object(values: object, start: int = 0) -> object:
    out: list[object] = []
    i = 0
    n = len(values)
    while i < n:
        out.append([start + i, values[i]])
        i += 1
    return out
