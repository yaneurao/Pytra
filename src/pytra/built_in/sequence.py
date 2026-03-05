"""Pure-Python source-of-truth for sequence helpers used by runtime built-ins."""


def py_range(start: int, stop: int, step: int) -> list[int]:
    out: list[int] = []
    if step == 0:
        return out
    if step > 0:
        i = start
        while i < stop:
            out.append(i)
            i += step
    else:
        i = start
        while i > stop:
            out.append(i)
            i += step
    return out


def py_repeat(v: str, n: int) -> str:
    if n <= 0:
        return ""
    out = ""
    i = 0
    while i < n:
        out += v
        i += 1
    return out
