# pytra: builtin-declarations
"""pytra.std.os: OS 関数の宣言。"""

from pytra.std import runtime

@runtime("pytra.std.os")
def getcwd() -> str: ...

@runtime("pytra.std.os")
def mkdir(p: str, exist_ok: bool = False) -> None: ...

@runtime("pytra.std.os")
def makedirs(p: str, exist_ok: bool = False) -> None: ...
