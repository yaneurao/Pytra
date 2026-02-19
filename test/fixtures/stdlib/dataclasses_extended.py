from pylib.assertions import py_assert_stdout
from pylib.dataclasses import dataclass


@dataclass
class Point:
    x: int
    y: int = 0


@dataclass
class MyError(Exception):
    category: str
    summary: str


def main() -> None:
    p = Point(1)
    print(p.x)
    print(p.y)
    a = Point(1, 2)
    b = Point(1, 2)
    c = Point(2, 1)
    print(repr(a))
    print(a == b)
    print(a == c)
    e = MyError("kind", "message")
    print(e.category)
    print(e.summary)


def _case_main() -> None:
    main()


if __name__ == "__main__":
    print(
        py_assert_stdout(
            ["1", "0", "Point(x=1, y=2)", "True", "False", "kind", "message"],
            _case_main,
        )
    )
