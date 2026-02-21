# This file contains test/implementation code for `test/fixtures/ifexp_bool.py`.
# Reader-facing comments are added to make roles easier to understand.
# When modifying this file, always verify consistency with existing specs and test results.


from pytra.utils.assertions import py_assert_stdout
def pick_25(a: int, b: int, flag: bool) -> int:
    c: int = a if (flag and (a > b)) else b
    return c


def _case_main() -> None:
    print(pick_25(10, 3, True))

if __name__ == "__main__":
    print(py_assert_stdout(['10'], _case_main))
