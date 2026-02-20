from __future__ import annotations

import pytra.std.sys as _sys

argv = _sys.argv
path = _sys.path
stderr = _sys.stderr
stdout = _sys.stdout


def exit(code: int = 0) -> None:
    _sys.exit(code)


def set_argv(values: list[str]) -> None:
    _sys.set_argv(values)


def set_path(values: list[str]) -> None:
    _sys.set_path(values)


def write_stderr(text: str) -> None:
    _sys.write_stderr(text)


def write_stdout(text: str) -> None:
    _sys.write_stdout(text)
