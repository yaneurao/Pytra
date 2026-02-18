"""pylib sys wrapper.

This module centralizes process/runtime access so transpiler code avoids direct
imports of Python stdlib `sys`.
"""

from __future__ import annotations

import sys as _sys
from typing import Any

argv = _sys.argv
path = _sys.path
stderr = _sys.stderr
stdout = _sys.stdout


def exit(code: int = 0) -> None:
    raise SystemExit(code)


def set_argv(values: list[str]) -> None:
    global argv
    argv = values


def set_path(values: list[str]) -> None:
    global path
    path = values


def write_stderr(text: str) -> None:
    stderr.write(text)


def write_stdout(text: str) -> None:
    stdout.write(text)

