# This file contains test/implementation code for `test/fixtures/comprehension.py`.
# Reader-facing comments are added to make roles easier to understand.
# When modifying this file, always verify consistency with existing specs and test results.


from pytra.utils.assertions import py_assert_stdout
def comp_like_24(x: int) -> int:
    values: list[int] = [i for i in [1, 2, 3, 4]]
    return x + 1


def _case_main() -> None:
    print(comp_like_24(5))

if __name__ == "__main__":
    print(py_assert_stdout(['6'], _case_main))
