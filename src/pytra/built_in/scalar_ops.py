"""Extern-marked scalar helper built-ins."""

from __future__ import annotations

import builtins as __b

from pytra.std import extern


@extern
def py_to_int64_base(v: str, base: int) -> int:
    return __b.int(v, base)


@extern
def py_ord(ch: str) -> int:
    return __b.ord(ch)


@extern
def py_chr(codepoint: int) -> str:
    return __b.chr(codepoint)
