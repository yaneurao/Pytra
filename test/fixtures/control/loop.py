# This file contains test/implementation code for `test/fixtures/loop.py`.
# Reader-facing comments are added to make roles easier to understand.
# When modifying this file, always verify consistency with existing specs and test results.


from pytra.utils.assertions import py_assert_stdout
def calc_17(values: list[int]) -> int:
    total: int = 0
    for v in values:
        if v % 2 == 0:
            total += v
        else:
            total += v * 2
    return total


def _case_main() -> None:
    print(calc_17([1, 2, 3, 4]))

if __name__ == "__main__":
    print(py_assert_stdout(['14'], _case_main))
