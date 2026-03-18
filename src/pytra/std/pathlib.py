"""Pure Python Path helper compatible with a subset of pathlib.Path."""

from __future__ import annotations

from pytra.std import glob as py_glob
from pytra.std import os
from pytra.std import os_path as path


class Path:
    __pytra_class_storage_hint__ = "value"

    def __init__(self, value: str | "Path") -> None:
        if isinstance(value, Path):
            self._value = value._value
        else:
            self._value = value

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return "Path(" + self._value + ")"

    def __fspath__(self) -> str:
        return self._value

    def __truediv__(self, rhs: str | "Path") -> "Path":
        if isinstance(rhs, Path):
            return Path(path.join(self._value, rhs._value))
        return Path(path.join(self._value, rhs))

    @property
    def parent(self) -> "Path":
        parent_txt = path.dirname(self._value)
        if parent_txt == "":
            parent_txt = "."
        return Path(parent_txt)

    @property
    def parents(self) -> list["Path"]:
        out: list[Path] = []
        current: str = path.dirname(self._value)
        while True:
            if current == "":
                current = "."
            out.append(Path(current))
            next_current: str = path.dirname(current)
            if next_current == "":
                next_current = "."
            if next_current == current:
                break
            current = next_current
        return out

    @property
    def name(self) -> str:
        return path.basename(self._value)

    @property
    def suffix(self) -> str:
        _, ext = path.splitext(path.basename(self._value))
        return ext

    @property
    def stem(self) -> str:
        root, _ = path.splitext(path.basename(self._value))
        return root

    def resolve(self) -> "Path":
        return Path(path.abspath(self._value))

    def exists(self) -> bool:
        return path.exists(self._value)

    def mkdir(self, parents: bool = False, exist_ok: bool = False) -> None:
        if parents:
            os.makedirs(self._value, exist_ok=exist_ok)
            return
        if exist_ok and path.exists(self._value):
            return
        os.mkdir(self._value)

    def read_text(self, encoding: str = "utf-8") -> str:
        with open(self._value, "r", encoding=encoding) as f:
            return f.read()

    def write_text(self, text: str, encoding: str = "utf-8") -> int:
        with open(self._value, "w", encoding=encoding) as f:
            return f.write(text)

    def glob(self, pattern: str) -> list["Path"]:
        paths: list[str] = py_glob.glob(path.join(self._value, pattern))
        out: list[Path] = []
        for p in paths:
            out.append(Path(p))
        return out

    @staticmethod
    def cwd() -> "Path":
        return Path(os.getcwd())
