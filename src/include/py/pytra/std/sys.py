# pytra: builtin-declarations
"""pytra.std.sys: sys モジュールの宣言。"""

from pytra.std import runtime, runtime_var

argv: list[str] = runtime_var("pytra.std.sys")
path: list[str] = runtime_var("pytra.std.sys")
stderr: str = runtime_var("pytra.std.sys")
stdout: str = runtime_var("pytra.std.sys")

@runtime("pytra.std.sys")
def exit(code: int = 0) -> None: ...

@runtime("pytra.std.sys")
def set_argv(values: list[str]) -> None: ...

@runtime("pytra.std.sys")
def set_path(values: list[str]) -> None: ...

@runtime("pytra.std.sys")
def write_stderr(text: str) -> None: ...

@runtime("pytra.std.sys")
def write_stdout(text: str) -> None: ...
