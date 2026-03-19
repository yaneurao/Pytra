"""pytra.std.glob: extern-marked glob subset with Python runtime fallback."""


import glob as _glob_mod

from pytra.std import extern


@extern
def glob(pattern: str) -> list[str]:
    return _glob_mod.glob(pattern)
