# pytra: builtin-declarations
"""pytra.std.pathlib: Path クラスの宣言。"""

from pytra.std import runtime


@runtime("pytra.std.pathlib")
def Path(s: str) -> Path: ...


@runtime("pytra.std.pathlib")
class Path:
    def write_text(self, content: str) -> None: ...
    def write_bytes(self, data: bytes) -> None: ...
    def read_text(self) -> str: ...
