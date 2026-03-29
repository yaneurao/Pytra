"""Pure-Python source-of-truth for generic zip helpers."""


from pytra.std import template


@template("A", "B")
def zip(lhs: list[A], rhs: list[B]) -> list[tuple[A, B]]:
    out: list[tuple[A, B]] = []
    i = 0
    n = len(lhs)
    if len(rhs) < n:
        n = len(rhs)
    while i < n:
        out.append((lhs[i], rhs[i]))
        i += 1
    return out
