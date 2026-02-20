from __future__ import annotations

Any: int = 1
List: int = 1
Set: int = 1
Dict: int = 1
Tuple: int = 1
Iterable: int = 1
Sequence: int = 1
Mapping: int = 1
Optional: int = 1
Union: int = 1
Callable: int = 1
TypeAlias: int = 1


def TypeVar(name: str) -> int:
    _ = name
    return 1
