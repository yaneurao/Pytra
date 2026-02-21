# This file contains test/implementation code for `test/fixtures/dataclass.py`.
# Reader-facing comments are added to make roles easier to understand.
# When modifying this file, always verify consistency with existing specs and test results.


from pytra.utils.assertions import py_assert_stdout
from dataclasses import dataclass


@dataclass
class Point99:
    x: int
    y: int = 10

    def total(self) -> int:
        return self.x + self.y


def _case_main() -> None:
    p: Point99 = Point99(3)
    print(p.total())

if __name__ == "__main__":
    print(py_assert_stdout(['13'], _case_main))
