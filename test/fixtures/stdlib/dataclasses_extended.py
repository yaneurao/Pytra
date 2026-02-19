from pylib.tra.assertions import py_assert_all, py_assert_eq
from pylib.std.dataclasses import dataclass


@dataclass
class Point:
    x: int
    y: int = 0


@dataclass
class MyError(Exception):
    category: str
    summary: str


def run_dataclasses_extended() -> bool:
    checks: list[bool] = []
    p = Point(1)
    checks.append(py_assert_eq(p.x, 1, "p.x"))
    checks.append(py_assert_eq(p.y, 0, "p.y"))
    a = Point(1, 2)
    b = Point(1, 2)
    c = Point(2, 1)
    checks.append(py_assert_eq(repr(a), "Point(x=1, y=2)", "repr"))
    checks.append(py_assert_eq(a == b, True, "eq"))
    checks.append(py_assert_eq(a == c, False, "neq"))
    e = MyError("kind", "message")
    checks.append(py_assert_eq(e.category, "kind", "category"))
    checks.append(py_assert_eq(e.summary, "message", "summary"))
    return py_assert_all(checks, "dataclasses_extended")


if __name__ == "__main__":
    print(run_dataclasses_extended())
