"""pytra.std.os_path: extern-marked os.path subset with Python runtime fallback."""

from __future__ import annotations

from pytra.std import extern

import os.path as __path


@extern
def join(a: str, b: str) -> str:
    return __path.join(a, b)


@extern
def dirname(p: str) -> str:
    return __path.dirname(p)


@extern
def basename(p: str) -> str:
    return __path.basename(p)


@extern
def splitext(p: str) -> tuple[str, str]:
    return __path.splitext(p)


@extern
def abspath(p: str) -> str:
    return __path.abspath(p)


@extern
def exists(p: str) -> bool:
    return __path.exists(p)
