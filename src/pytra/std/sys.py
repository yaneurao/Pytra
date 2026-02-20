"""Minimal sys shim for Pytra.

Python 実行時は `list` を保持する軽量実装として振る舞い、
トランスパイル時は `py_runtime_*` ランタイム関数へ接続される。
"""

from __future__ import annotations

import sys as _host_sys
from pytra.std.typing import Any

argv: list[str] = []
path: list[str] = []
stderr: object = None
stdout: object = None

# Python 実行時のホスト値
argv = _host_sys.argv
path = _host_sys.path
stderr = _host_sys.stderr
stdout = _host_sys.stdout


def exit(code: int = 0) -> None:
    try:
        py_runtime_exit(code)
    except NameError:
        _host_sys.exit(code)


def _to_str_list_fallback(values: Any) -> list[str]:
    try:
        return py_to_str_list_from_object(values)
    except NameError:
        pass
    out: list[str] = []
    if isinstance(values, list):
        src = list(values)
        for v in src:
            out.append(str(v))
    return out


def set_argv(values: Any) -> None:
    vals: list[str] = []
    try:
        vals = py_to_str_list_from_any(values)
    except NameError:
        vals = _to_str_list_fallback(values)
    argv.clear()
    for v in vals:
        argv.append(v)


def set_path(values: Any) -> None:
    vals: list[str] = []
    try:
        vals = py_to_str_list_from_any(values)
    except NameError:
        vals = _to_str_list_fallback(values)
    path.clear()
    for v in vals:
        path.append(v)


def write_stderr_impl(text: str) -> None:
    py_runtime_write_stderr(text)


def write_stdout_impl(text: str) -> None:
    py_runtime_write_stdout(text)


def write_stderr(text: str) -> None:
    write_stderr_impl(text)


def write_stdout(text: str) -> None:
    write_stdout_impl(text)
