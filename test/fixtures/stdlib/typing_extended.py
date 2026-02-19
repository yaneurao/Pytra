from pylib.std import typing
from pylib.tra.assertions import py_assert_stdout


def main() -> None:
    print(typing.Any is not None)
    print(typing.List is not None)
    print(typing.Set is not None)
    print(typing.Dict is not None)
    print(typing.Tuple is not None)
    print(typing.Iterable is not None)
    print(typing.Optional is not None)
    print(typing.Union is not None)
    print(typing.Callable is not None)
    print(typing.TypeVar("T") is not None)


def _case_main() -> None:
    main()


if __name__ == "__main__":
    print(
        py_assert_stdout(
            ["True", "True", "True", "True", "True", "True", "True", "True", "True", "True"],
            _case_main,
        )
    )
