"""Pure-Python source-of-truth for generic zip helpers."""

from __future__ import annotations

from pytra.std import abi, template


@template("A", "B")
@abi(args={"lhs": "value", "rhs": "value"}, ret="value")
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
