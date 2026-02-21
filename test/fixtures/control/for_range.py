# This file contains test/implementation code for `test/fixtures/for_range.py`.
# Reader-facing comments are added to make roles easier to understand.
# When modifying this file, always verify consistency with existing specs and test results.


from pytra.utils.assertions import py_assert_stdout
def sum_range_29(n: int) -> int:
    total: int = 0
    for i in range(n):
        total += i
    return total


def _case_main() -> None:
    print(sum_range_29(5))

if __name__ == "__main__":
    print(py_assert_stdout(['10'], _case_main))
