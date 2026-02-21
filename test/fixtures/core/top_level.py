# This file contains test/implementation code for `test/fixtures/top_level.py`.
# Reader-facing comments are added to make roles easier to understand.
# When modifying this file, always verify consistency with existing specs and test results.


from pytra.utils.assertions import py_assert_stdout
def mul3(n: int) -> int:
    return n * 3


value: int = 7


def _case_main() -> None:
    print(mul3(value))

if __name__ == "__main__":
    print(py_assert_stdout(['21'], _case_main))
