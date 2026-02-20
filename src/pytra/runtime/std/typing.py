from __future__ import annotations

import pytra.std.typing as _typing

Any = _typing.Any
List = _typing.List
Set = _typing.Set
Dict = _typing.Dict
Tuple = _typing.Tuple
Iterable = _typing.Iterable
Sequence = _typing.Sequence
Mapping = _typing.Mapping
Optional = _typing.Optional
Union = _typing.Union
Callable = _typing.Callable
TypeAlias = _typing.TypeAlias


def TypeVar(name: str) -> object:
    return _typing.TypeVar(name)
