"""Minimal typing shim for selfhost-friendly imports.

This module is intentionally small and runtime-light. It provides names used in
type annotations so core modules avoid direct stdlib `typing` imports.
"""

from __future__ import annotations

Any = object
List = list
Set = set
Dict = dict
Tuple = tuple
Iterable = list
Sequence = list
Mapping = dict
Optional = object
Union = object
Callable = object
TypeAlias = object


def TypeVar(name: str) -> object:
    return object
