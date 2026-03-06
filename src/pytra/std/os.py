"""pytra.std.os: extern-marked os subset with Python runtime fallback."""

from __future__ import annotations

from pytra.std import extern
from pytra.std import os_path as path

import os as __os

@extern
def getcwd() -> str:
    return __os.getcwd()


@extern
def mkdir(p: str) -> None:
    __os.mkdir(p)


@extern
def makedirs(p: str, exist_ok: bool = False) -> None:
    __os.makedirs(p, exist_ok=exist_ok)
