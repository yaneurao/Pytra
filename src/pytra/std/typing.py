"""Minimal typing shim for selfhost-friendly imports.

This module is intentionally small and runtime-light. It provides names used in
type annotations so core modules avoid direct stdlib `typing` imports.
"""

from __future__ import annotations

Any = "Any"
List = "List"
Set = "Set"
Dict = "Dict"
Tuple = "Tuple"
Iterable = "Iterable"
Sequence = "Sequence"
Mapping = "Mapping"
Optional = "Optional"
Union = "Union"
Callable = "Callable"
TypeAlias = "TypeAlias"


def TypeVar(name: str) -> str:
    return name
