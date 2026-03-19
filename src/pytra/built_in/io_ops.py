"""Extern-marked I/O helper built-ins."""


from pytra.std import extern


@extern
def py_print(value: object) -> None:
    print(value)
