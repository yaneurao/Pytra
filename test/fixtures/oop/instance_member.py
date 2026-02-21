# This file contains test/implementation code for `test/fixtures/instance_member.py`.
# Reader-facing comments are added to make roles easier to understand.
# When modifying this file, always verify consistency with existing specs and test results.


from pytra.utils.assertions import py_assert_stdout
class Point:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def total(self) -> int:
        return self.x + self.y


def _case_main() -> None:
    p: Point = Point(2, 5)
    print(p.total())

if __name__ == "__main__":
    print(py_assert_stdout(['7'], _case_main))
