"""Pure-Python source-of-truth for predicate helpers."""

from typing import Any


def py_bi_any(values: Any) -> bool:
    i = 0
    n = len(values)
    while i < n:
        if bool(values[i]):
            return True
        i += 1
    return False


def py_bi_all(values: Any) -> bool:
    i = 0
    n = len(values)
    while i < n:
        if not bool(values[i]):
            return False
        i += 1
    return True
