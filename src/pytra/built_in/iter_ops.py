"""Pure-Python source-of-truth for object-based iterator helpers."""


def py_reversed_object(values: object) -> list[object]:
    out: list[object] = []
    for value in values:
        out.append(value)
    return reversed(out)


def py_enumerate_object(values: object, start: int = 0) -> list[object]:
    out: list[object] = []
    i = start
    for value in values:
        out.append((i, value))
        i += 1
    return out
