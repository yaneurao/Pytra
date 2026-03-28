# pytra: builtin-declarations
"""pytra.std.math: 数学関数の宣言。"""

from pytra.std import runtime, runtime_var

pi: float = runtime_var("pytra.std.math")
e: float = runtime_var("pytra.std.math")

@runtime("pytra.std.math")
def sqrt(x: float) -> float: ...

@runtime("pytra.std.math")
def sin(x: float) -> float: ...

@runtime("pytra.std.math")
def cos(x: float) -> float: ...

@runtime("pytra.std.math")
def tan(x: float) -> float: ...

@runtime("pytra.std.math")
def exp(x: float) -> float: ...

@runtime("pytra.std.math")
def log(x: float) -> float: ...

@runtime("pytra.std.math")
def log10(x: float) -> float: ...

@runtime("pytra.std.math")
def fabs(x: float) -> float: ...

@runtime("pytra.std.math")
def floor(x: float) -> float: ...

@runtime("pytra.std.math")
def ceil(x: float) -> float: ...

@runtime("pytra.std.math")
def pow(x: float, y: float) -> float: ...
