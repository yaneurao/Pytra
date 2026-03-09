"""Extern-marked I/O helper built-ins."""

from __future__ import annotations

import builtins as __b

from pytra.std import extern


@extern
def py_print(value: object) -> None:
    __b.print(value)
