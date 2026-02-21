# This file contains test/implementation code for `test/fixtures/control/ifexp_ternary_regression.py`.
# Reader-facing comments are added to make roles easier to understand.
# When modifying this file, always verify consistency with existing specs and test results.


from pytra.utils.assertions import py_assert_stdout


def pick(flag: bool) -> int:
    value: int = 10 if flag else 20
    return value if flag else (value + 1)


def passthrough(x: int) -> int:
    return x


def pass_arg(flag: bool) -> int:
    return passthrough(30 if flag else 40)


def make_list(flag: bool) -> list[int]:
    return [1 if flag else 2, 3]


def make_dict(flag: bool) -> dict[str, int]:
    return {"k": (5 if flag else 7)}


def _case_main() -> None:
    print(pick(True))
    print(pick(False))
    print(pass_arg(True))
    print(pass_arg(False))
    xs = make_list(False)
    print(xs[0], xs[1])
    d = make_dict(True)
    print(d["k"])


if __name__ == "__main__":
    print(py_assert_stdout(["10", "21", "30", "40", "2 3", "5"], _case_main))
