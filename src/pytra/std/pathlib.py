"""Pure Python Path helper compatible with a subset of pathlib.Path."""

from __future__ import annotations

from pytra.typing import cast

from pytra.std import glob as py_glob
from pytra.std import os
from pytra.std import os_path as path


class Path:
    _value: str

    def __init__(self, value: str | "Path") -> None:
        if isinstance(value, Path):
            self._value = str(value)
        else:
            self._value = cast(str, value)

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return "Path(" + self._value + ")"

    def __fspath__(self) -> str:
        return self._value

    def __truediv__(self, rhs: str | "Path") -> "Path":
        if isinstance(rhs, Path):
            return Path(path.join(self._value, str(rhs)))
        return Path(path.join(self._value, cast(str, rhs)))

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

    def with_suffix(self, suffix: str) -> "Path":
        root: str
        _ext: str
        root, _ext = path.splitext(self._value)
        return Path(root + suffix)

    def relative_to(self, other: str | "Path") -> "Path":
        if isinstance(other, Path):
            base: str = str(other)
        else:
            base = cast(str, other)
        self_abs: str = path.abspath(self._value)
        base_abs: str = path.abspath(base)
        if not base_abs.endswith("/"):
            base_abs = base_abs + "/"
        if self_abs == base_abs or self_abs == base_abs[:-1]:
            return Path(".")
        if self_abs.startswith(base_abs):
            return Path(self_abs[len(base_abs):])
        raise ValueError(str(self._value) + " is not relative to " + str(base))

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
        os.mkdir(self._value, exist_ok=False)

    def read_text(self, encoding: str = "utf-8") -> str:
        with open(self._value, "r", encoding=encoding) as f:
            return f.read()

    def write_text(self, text: str, encoding: str = "utf-8") -> int:
        with open(self._value, "w", encoding=encoding) as f:
            return f.write(text)

    def joinpath(self, *parts: str | "Path") -> "Path":
        result: str = self._value
        for part in parts:
            if isinstance(part, Path):
                result = path.join(result, str(part))
            else:
                result = path.join(result, cast(str, part))
        return Path(result)

    def glob(self, pattern: str) -> list["Path"]:
        paths: list[str] = py_glob.glob(path.join(self._value, pattern))
        out: list[Path] = []
        for p in paths:
            out.append(Path(p))
        return out

    @staticmethod
    def cwd() -> "Path":
        return Path(os.getcwd())
