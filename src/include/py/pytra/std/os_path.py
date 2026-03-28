# pytra: builtin-declarations
"""pytra.std.os_path: os.path 関数の宣言。"""

from pytra.std import runtime

@runtime("pytra.std.os_path")
def join(a: str, b: str) -> str: ...

@runtime("pytra.std.os_path")
def dirname(p: str) -> str: ...

@runtime("pytra.std.os_path")
def basename(p: str) -> str: ...

@runtime("pytra.std.os_path")
def splitext(p: str) -> tuple[str, str]: ...

@runtime("pytra.std.os_path")
def abspath(p: str) -> str: ...

@runtime("pytra.std.os_path")
def exists(p: str) -> bool: ...
