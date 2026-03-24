# This file contains test/implementation code for `test/fixtures/tuple_assign.py`.
# Reader-facing comments are added to make roles easier to understand.
# When modifying this file, always verify consistency with existing specs and test results.


from pytra.utils.assertions import py_assert_stdout
def swap_sum_18(a: int, b: int) -> int:
    x: int = a
    y: int = b
    x, y = y, x
    return x + y


def _case_main() -> None:
    print(swap_sum_18(10, 20))

if __name__ == "__main__":
    print(py_assert_stdout(['30'], _case_main))
