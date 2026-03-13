"""Pure-Python source-of-truth for predicate helpers."""

from typing import Any


def py_any(values: Any) -> bool:
    for value in values:
        if bool(value):
            return True
    return False


def py_all(values: Any) -> bool:
    for value in values:
        if not bool(value):
            return False
    return True
