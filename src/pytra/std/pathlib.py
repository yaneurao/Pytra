"""Pure Python Path helper compatible with a subset of pathlib.Path."""

from __future__ import annotations

from pytra.std import glob as py_glob
from pytra.std import os


class _PathParents:
    def __init__(self, p: "Path") -> None:
        self._path = p

    def __getitem__(self, index: int) -> "Path":
        if index < 0:
            raise IndexError("negative index is not supported")
        cur = self._path.parent
        i = 0
        while i < index:
            cur = cur.parent
            i += 1
        return cur


class Path:
    def __init__(self, value: str | "Path") -> None:
        if isinstance(value, Path):
            self._value = value._value
        else:
            self._value = str(value)

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"Path({self._value!r})"

    def __fspath__(self) -> str:
        return self._value

    def __truediv__(self, rhs: str | "Path") -> "Path":
        rhs_txt = str(rhs)
        return Path(os.path.join(self._value, rhs_txt))

    @property
    def parent(self) -> "Path":
        parent_txt = os.path.dirname(self._value)
        if parent_txt == "":
            parent_txt = "."
        return Path(parent_txt)

    @property
    def parents(self) -> _PathParents:
        return _PathParents(self)

    @property
    def name(self) -> str:
        return os.path.basename(self._value)

    @property
    def suffix(self) -> str:
        return os.path.splitext(self.name)[1]

    @property
    def stem(self) -> str:
        return os.path.splitext(self.name)[0]

    def resolve(self) -> "Path":
        return Path(os.path.abspath(self._value))

    def exists(self) -> bool:
        return os.path.exists(self._value)

    def mkdir(self, parents: bool = False, exist_ok: bool = False) -> None:
        if parents:
            os.makedirs(self._value, exist_ok=exist_ok)
            return
        try:
            os.mkdir(self._value)
        except FileExistsError:
            if not exist_ok:
                raise

    def read_text(self, encoding: str = "utf-8") -> str:
        with open(self._value, "r", encoding=encoding) as f:
            return f.read()

    def write_text(self, text: str, encoding: str = "utf-8") -> int:
        with open(self._value, "w", encoding=encoding) as f:
            return f.write(text)

    def glob(self, pattern: str) -> list["Path"]:
        base = self._value
        paths = py_glob.glob(os.path.join(base, pattern))
        out: list[Path] = []
        for p in paths:
            out.append(Path(p))
        return out

    @staticmethod
    def cwd() -> "Path":
        return Path(os.getcwd())
