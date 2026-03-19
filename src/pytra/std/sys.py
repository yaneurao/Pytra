"""pytra.std.sys: extern-marked sys API with Python runtime fallback."""


import sys

from pytra.std import extern

argv: list[str] = extern(sys.argv)
path: list[str] = extern(sys.path)
stderr = extern(sys.stderr)
stdout = extern(sys.stdout)


@extern
def exit(code: int = 0) -> None:
    sys.exit(code)


@extern
def set_argv(values: list[str]) -> None:
    argv.clear()
    for v in values:
        argv.append(v)


@extern
def set_path(values: list[str]) -> None:
    path.clear()
    for v in values:
        path.append(v)


@extern
def write_stderr(text: str) -> None:
    sys.stderr.write(text)


@extern
def write_stdout(text: str) -> None:
    sys.stdout.write(text)
