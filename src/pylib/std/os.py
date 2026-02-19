"""Minimal os shim for selfhost-friendly imports."""

from __future__ import annotations

import os as _os


class _PathModule:
    """Subset of os.path used by pylib.std.pathlib and user code."""

    def join(self, a: str, b: str) -> str:
        return _os.path.join(a, b)

    def dirname(self, p: str) -> str:
        return _os.path.dirname(p)

    def basename(self, p: str) -> str:
        return _os.path.basename(p)

    def splitext(self, p: str) -> tuple[str, str]:
        root, ext = _os.path.splitext(p)
        return root, ext

    def abspath(self, p: str) -> str:
        return _os.path.abspath(p)

    def exists(self, p: str) -> bool:
        return _os.path.exists(p)


path = _PathModule()


def getcwd() -> str:
    return _os.getcwd()


def mkdir(p: str) -> None:
    _os.mkdir(p)


def makedirs(p: str, exist_ok: bool = False) -> None:
    _os.makedirs(p, exist_ok=exist_ok)

