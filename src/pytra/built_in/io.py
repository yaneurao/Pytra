"""Built-in I/O class declarations.

These are @extern class declarations for Python's io module types.
The actual implementations are provided by each language's runtime.

Python's open() returns different types depending on the mode:
  - "r", "w", "a"       → io.TextIOWrapper
  - "rb"                 → io.BufferedReader
  - "wb", "ab"           → io.BufferedWriter

All are subclasses of io.IOBase and implement the context manager
protocol (__enter__ / __exit__).

In Pytra, we model this with IOBase as the base class so that
open() can return IOBase regardless of mode, and __enter__ /
__exit__ / close are always callable on the result.

Emitters do not read this file directly. They use EAST3 metadata
that resolve derives from these declarations.
"""


@extern
class IOBase:
    """Base class for all I/O types. Provides context manager protocol."""

    def close(self: mut[IOBase]) -> None: ...

    def __enter__(self) -> "IOBase": ...

    def __exit__(self: mut[IOBase], exc_type: object, exc_val: object, exc_tb: object) -> None: ...


@extern
class TextIOWrapper(IOBase):
    """Text mode file object (open with "r", "w", "a")."""

    def __enter__(self) -> "TextIOWrapper": ...

    def read(self) -> str: ...

    def write(self: mut[TextIOWrapper], text: str) -> int: ...


@extern
class BufferedWriter(IOBase):
    """Binary mode write file object (open with "wb", "ab")."""

    def __enter__(self) -> "BufferedWriter": ...

    def write(self: mut[BufferedWriter], data: bytes) -> int: ...


@extern
class BufferedReader(IOBase):
    """Binary mode read file object (open with "rb")."""

    def __enter__(self) -> "BufferedReader": ...

    def read(self) -> bytes: ...
