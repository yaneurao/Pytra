# pytra: builtin-declarations
"""pytra.std.glob: glob 関数の宣言。"""

from pytra.std import runtime

@runtime("pytra.std.glob")
def glob(pattern: str) -> list[str]: ...
