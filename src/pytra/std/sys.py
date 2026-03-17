"""pytra.std.sys: extern-marked sys API with Python runtime fallback."""

from __future__ import annotations

from pytra.std import extern

import sys as __s

argv: list[str] = extern(__s.argv)
path: list[str] = extern(__s.path)
stderr = extern(__s.stderr)
stdout = extern(__s.stdout)


@extern
def exit(code: int = 0) -> None:
    __s.exit(code)


@extern
def set_argv(values: list[str]) -> None:
    argv.clear()
    for v in values:
        argv.append(v)


@extern
def set_path(values: list[str]) -> None:
    path.clear()
    for v in values:
        path.append(v)


@extern
def write_stderr(text: str) -> None:
    __s.stderr.write(text)


@extern
def write_stdout(text: str) -> None:
    __s.stdout.write(text)
