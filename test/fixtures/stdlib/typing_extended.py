from pylib.std import typing
from pylib.tra.assertions import py_assert_all, py_assert_eq


def run_typing_extended() -> bool:
    checks: list[bool] = []
    checks.append(py_assert_eq(typing.Any is not None, True, "Any"))
    checks.append(py_assert_eq(typing.List is not None, True, "List"))
    checks.append(py_assert_eq(typing.Set is not None, True, "Set"))
    checks.append(py_assert_eq(typing.Dict is not None, True, "Dict"))
    checks.append(py_assert_eq(typing.Tuple is not None, True, "Tuple"))
    checks.append(py_assert_eq(typing.Iterable is not None, True, "Iterable"))
    checks.append(py_assert_eq(typing.Optional is not None, True, "Optional"))
    checks.append(py_assert_eq(typing.Union is not None, True, "Union"))
    checks.append(py_assert_eq(typing.Callable is not None, True, "Callable"))
    checks.append(py_assert_eq(typing.TypeVar("T") is not None, True, "TypeVar"))
    return py_assert_all(checks, "typing_extended")


if __name__ == "__main__":
    print(run_typing_extended())
