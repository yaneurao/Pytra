from pytra.runtime.assertions import py_assert_all, py_assert_eq
from pytra.std.dataclasses import dataclass


@dataclass
class Point:
    x: int
    y: int = 0


@dataclass
class MyError:
    category: str
    summary: str


def run_dataclasses_extended() -> bool:
    checks: list[bool] = []
    p = Point(1)
    checks.append(py_assert_eq(p.x, 1, "p.x"))
    checks.append(py_assert_eq(p.y, 0, "p.y"))
    a = Point(1, 2)
    checks.append(py_assert_eq(a.x, 1, "a.x"))
    checks.append(py_assert_eq(a.y, 2, "a.y"))
    e = MyError("kind", "message")
    checks.append(py_assert_eq(e.category, "kind", "category"))
    checks.append(py_assert_eq(e.summary, "message", "summary"))
    return py_assert_all(checks, "dataclasses_extended")


if __name__ == "__main__":
    print(run_dataclasses_extended())
