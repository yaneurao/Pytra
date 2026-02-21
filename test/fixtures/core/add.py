# This file contains test/implementation code for `test/fixtures/add.py`.
# Reader-facing comments are added to make roles easier to understand.
# When modifying this file, always verify consistency with existing specs and test results.


from pytra.utils.assertions import py_assert_stdout
def add(a: int, b: int) -> int:
    return a + b


def _case_main() -> None:
    print(add(3, 4))

if __name__ == "__main__":
    print(py_assert_stdout(['7'], _case_main))
