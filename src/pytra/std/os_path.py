"""pytra.std.os_path: extern-marked os.path subset with Python runtime fallback."""


import os.path

from pytra.std import extern


@extern
def join(a: str, b: str) -> str:
    return os.path.join(a, b)


@extern
def dirname(p: str) -> str:
    return os.path.dirname(p)


@extern
def basename(p: str) -> str:
    return os.path.basename(p)


@extern
def splitext(p: str) -> tuple[str, str]:
    return os.path.splitext(p)


@extern
def abspath(p: str) -> str:
    return os.path.abspath(p)


@extern
def exists(p: str) -> bool:
    return os.path.exists(p)
