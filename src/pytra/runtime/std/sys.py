from __future__ import annotations

argv: list[str] = py_sys_argv()
path: list[str] = py_sys_path()
stderr: int = 1
stdout: int = 1


def exit(code: int = 0) -> None:
    py_sys_exit(code)


def set_argv(values: object) -> None:
    vals: list[str] = py_to_str_list_from_any(values)
    argv.clear()
    for v in vals:
        argv.append(v)
    py_sys_set_argv(argv)


def set_path(values: object) -> None:
    vals: list[str] = py_to_str_list_from_any(values)
    path.clear()
    for v in vals:
        path.append(v)
    py_sys_set_path(path)


def write_stderr(text: str) -> None:
    py_sys_write_stderr(text)


def write_stdout(text: str) -> None:
    py_sys_write_stdout(text)
