# pytra: builtin-declarations
"""pytra.std.time: 時間関数の宣言。"""

from pytra.std import runtime

@runtime("pytra.std.time")
def perf_counter() -> float: ...
