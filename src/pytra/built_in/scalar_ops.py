"""Extern-marked scalar helper built-ins."""


from pytra.std import extern


@extern
def py_to_int64_base(v: str, base: int) -> int:
    return int(v, base)


@extern
def py_ord(ch: str) -> int:
    return ord(ch)


@extern
def py_chr(codepoint: int) -> str:
    return chr(codepoint)
