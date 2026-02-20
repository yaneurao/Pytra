"""pytra.std.dataclasses: thin wrapper over dataclasses_impl."""

from __future__ import annotations

import pytra.std.dataclasses_impl as _impl
from pytra.std.typing import Any


def dataclass(
    _cls: Any,
    init: bool = True,
    repr: bool = True,
    eq: bool = True,
) -> Any:
    """`@dataclass` の最小互換入口。実装本体は dataclasses_impl 側。"""
    return _impl.dataclass(_cls, init, repr, eq)
