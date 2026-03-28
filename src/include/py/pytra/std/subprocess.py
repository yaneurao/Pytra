# pytra: builtin-declarations
"""pytra.std.subprocess: subprocess 関数の宣言。"""

from pytra.std import runtime


class CompletedProcess:
    returncode: int
    stdout: str
    stderr: str

@runtime("pytra.std.subprocess", symbol="run", tag="stdlib.fn.subprocess_run")
def run(cmd: list[str], cwd: str = "", capture_output: bool = False, env: dict[str, str] = {}) -> CompletedProcess: ...
